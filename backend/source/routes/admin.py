from typing import Annotated, Optional
from openai import OpenAIError
from fastapi import APIRouter, Depends, File, Form, Request, UploadFile, HTTPException
import io
import os
from io import BytesIO
from source.dependencies import get_admin_user
from source.utils.xlsx_or_csv_to_jsonl import process_mixed_data_v2
from source.utils.training_file_gridfs_storage import DatasetStorageService
from source.utils.validate_jsonl_file import validate_finetuning_jsonl, DatasetValidationError
from source.models.training_data_model import TrainingDataset 
import logging

router = APIRouter(prefix="/api/v1/admin", tags=["Admin"])

@router.post("/convert-mixed")
async def convert_mixed_endpoint(
    req: Request,
    admin: Annotated[str, Depends(get_admin_user)],
    dataset_name: Optional[str] = Form(None),
    file: UploadFile = File(...), 
    system_prompt: str = Form('''    You are a senior wind energy engineer specializing in structural loads analysis, control systems, and engineering tool development for utility-scale wind turbines.

You provide technically accurate, engineering-grade responses grounded in wind turbine aerodynamics, structural mechanics, control theory, and aeroelastic simulation practices.

When answering:
- Use precise engineering terminology.
- State assumptions clearly.
- Include equations when relevant.
- Use SI units unless specified otherwise.
- Reference industry standards when applicable (IEC 61400, DNV, etc.).
- Distinguish between theoretical explanation and practical implementation.
- Avoid speculation; if data is insufficient, explicitly state assumptions.
- Provide structured responses suitable for engineering documentation or internal technical review.

You support topics including:
- Load case development and IEC design load cases (DLCs)
- Extreme and fatigue load analysis
- Aeroelastic simulation tools (e.g., FAST, Bladed, HAWC2)
- Pitch and torque control strategies
- Stability analysis and controller tuning
- Turbine dynamics (tower, blades, drivetrain)
- Sensor filtering and signal processing
- Tool development for automation and post-processing

Your responses should reflect industry-level rigor appropriate for experienced engineers.'''),
    
):
        if not dataset_name:
            dataset_name = os.path.splitext(file.filename)[0]
   
        # 1. Read raw bytes from the uploaded file
        content_bytes = await file.read()
        
        # 2. Wrap in BytesIO (Treats bytes like a file object)
        input_stream = io.BytesIO(content_bytes)

        # 3. Call your  function

        jsonl_str = process_mixed_data_v2(input_stream, system_prompt, filename=file.filename)

       # Validate BEFORE storing 
        try: 
           result = validate_finetuning_jsonl(jsonl_str) 
        except DatasetValidationError as e: 
            logging.exception(f"Couldn't validate file : {str(e)}")
            raise HTTPException(status_code=500, detail="Internal Server Error")
        # 2. Determine Stats
        # sample_count = len(jsonl_str.strip().split("\n"))
        sample_count = result["samples"]
        version  = 1

        # 3. check previous dataset used for successful training

        latest_dataset = await TrainingDataset.find_one(
            {
                "is_active": True,
                "status": "succeeded"
            }
        )
        if latest_dataset:
            previous_bytes = await DatasetStorageService.get_file_bytes(
                req.app.state.gridfs_bucket,
                latest_dataset.id
            )
            previous_str = previous_bytes.decode("utf-8")
            jsonl_str = previous_str.strip() + "\n" + jsonl_str.strip()
            version = latest_dataset.version + 1
            sample_count = latest_dataset.sample_count + sample_count


        # 3. Store via Service
        try:
            new_entry = await DatasetStorageService.save_to_gridfs(
                bucket=req.app.state.gridfs_bucket,
                jsonl_content=jsonl_str,
                metadata={
                    "name": dataset_name,
                    "version": version, 
                    "system_prompt": system_prompt,
                    "sample_count": sample_count,
                    "status": "locally validated",
                    "parent_dataset_id": str(latest_dataset.id) if latest_dataset else None
                }
            )
            training_file_bytes = await DatasetStorageService.get_file_bytes( req.app.state.gridfs_bucket, str(new_entry.id))

            return {"id": str(new_entry.id), "samples": sample_count, "status": "archived", "file_content": training_file_bytes}
        
        except Exception as e:
            logging.exception(f"Database storage failed : {str(e)}")
            raise HTTPException(status_code=500, detail="Internal server error")
        
@router.post("/start-finetune/{dataset_id}")
async def start_finetune(dataset_id: str, req: Request,  admin: Annotated[str, Depends(get_admin_user)]):

    client = req.app.state.client

    dataset = await TrainingDataset.get(dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    # Prevent duplicate training
    if dataset.status in ["queued", "running"]:
        raise HTTPException(
            status_code=400,
            detail="Fine-tuning already in progress"
        )
    
    try:
        file_bytes = await DatasetStorageService.get_file_bytes(
        req.app.state.gridfs_bucket,
        dataset_id
        )

        file_response = client.files.create(
            file=BytesIO(file_bytes),
            purpose="fine-tune"
        )

        job = client.fine_tuning.jobs.create(
            training_file=file_response.id,
            model="gpt-4o-mini"
        )
    except OpenAIError as e:
         # OpenAI-related error
        dataset.status = "error"
        await dataset.save()

        if "file_response" in locals():
            client.files.delete(file_response.id)
        logging.exception(f"OpenAI error: {str(e)}")
        raise HTTPException(
            
            status_code=502,
            detail="Internal server error"
        )
    except Exception as e:
        # Unexpected error
        dataset.status = "error"
        await dataset.save()

        raise HTTPException(
            status_code=500,
            detail="Failed to start fine-tuning"
        )

    dataset.openai_file_id = file_response.id
    dataset.openai_job_id = job.id
    dataset.status = job.status  # likely "queued"
    await dataset.save()

    return {
        "job_id": job.id,
        "status": job.status
    }

@router.get("/finetune-status/{dataset_id}")
async def finetune_status(dataset_id: str, req: Request,  admin: Annotated[str, Depends(get_admin_user)]):

    client = req.app.state.client

    dataset = await TrainingDataset.get(dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="job not found")

    if dataset.status in ["succeeded", "failed", "cancelled"]:
        return {
            "status": dataset.status,
            "model": dataset.fine_tuned_model,
            "message": dataset.last_event_message
        }
    
    job = client.fine_tuning.jobs.retrieve(dataset.openai_job_id)
   
    updated = False

    if dataset.status != job.status:
        dataset.status = job.status
        updated = True

    if job.status == "succeeded" and dataset.fine_tuned_model != job.fine_tuned_model:
        dataset.fine_tuned_model = job.fine_tuned_model
        updated = True

    # only fetch event if job is running

    last_event_message = dataset.last_event_message

    if job.status == "running":
         events = client.fine_tuning.jobs.list_events(
            fine_tuning_job_id=dataset.openai_job_id,
            limit=1
        )
         if events.data:
            new_message = events.data[0].message

            if dataset.last_event_message != new_message:
                dataset.last_event_message = new_message
                last_event_message = new_message
                updated = True

    if updated:
        await dataset.save()   # Only ONE write

    return {
        "status": job.status,
        "model": job.fine_tuned_model,
        "message": last_event_message.data[0].message
    }

