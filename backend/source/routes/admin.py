from asyncio import events
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
    system_prompt: str = Form('''You are PZWind AI — an advanced engineering assistant specialized in:
        - Aeroelasticity of wind turbines  
        - Structural and aerodynamic loads  
        - Wind turbine control systems  
        - Stability analysis  
        - Wind turbine siting and wind resource  assessment  
        - IEC 61400 and DNV standards compliance  
        - Wind energy engineering  
        When responding:
        1. Use engineering terminology.
        2. Clearly state assumptions before calculations.
        3. Distinguish between:
           - Theoretical background
           - Engineering implementation
        4. Include governing equations where relevant.      
        5. Reference applicable standards (IEC 61400, DNV, etc.).
        6. Structure responses using sections:
           - Introduction
           - Governing Principles
           - Equations (if applicable)
           - Practical Implementation
           - Engineering Considerations
        7. If data is insufficient, explicitly state assumptions.
        8. Avoid speculation.
        When asked about your capabilities, describe them technically rather than repeating a predefined list.''')
    ):
        #  5. Use SI units unless otherwise specified.
        #  10. Do NOT answer questions outside wind turbine engineering. Politely decline.
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


        # -----------------------------------------only if you want to append to previous dataset, otherwise skip to storage -----------------------------------------
        # version  = 1.0

        # # 3. check previous dataset used for successful training

        # latest_dataset = await TrainingDataset.find_one(
        #     {
        #         # "is_active": True,
        #         "status": "succeeded"
        #     },
        #     sort = [("version", -1)]
        # )
        # if latest_dataset:
        #     previous_bytes = await DatasetStorageService.get_file_bytes(
        #         req.app.state.gridfs_bucket,
        #         latest_dataset.id
        #     )
        #     previous_str = previous_bytes.decode("utf-8")
        #     jsonl_str = previous_str.strip() + "\n" + jsonl_str.strip()
        #     version = latest_dataset.version + 0.1
        #     sample_count = latest_dataset.sample_count + sample_count


        # 3.--------------------------------------------- Store via Service---------------------------------------------
        try:
            new_entry = await DatasetStorageService.save_to_gridfs(
                bucket=req.app.state.gridfs_bucket,
                jsonl_content=jsonl_str,
                metadata={
                    "name": dataset_name,
                    # "version": version, 
                    "system_prompt": system_prompt,
                    "sample_count": sample_count,
                    "status": "locally validated",
                    # "parent_dataset_id": str(latest_dataset.id) if latest_dataset else None
                }
            )
            # training_file_bytes = await DatasetStorageService.get_file_bytes( req.app.state.gridfs_bucket, str(new_entry.id))

            return {"id": str(new_entry.id), "samples": sample_count, "status": "archived", "message": "file uploaded successfuly"}
        
        except Exception as e:
            logging.exception(f"Database storage failed : {str(e)}")
            raise HTTPException(status_code=500, detail="Internal server error")
# --------------------getting list of trained models------------------------------
@router.get("/trained-models")
async def get_trained_models(req: Request, admin: Annotated[str, Depends(get_admin_user)]):
    models = await TrainingDataset.find({"status": "succeeded"}).to_list()
    return models

@router.post("/start-finetune/{dataset_id}")
async def start_finetune(dataset_id: str, req: Request,  admin: Annotated[str, Depends(get_admin_user)]):

    client = req.app.state.client

    dataset = await TrainingDataset.get(dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    # Prevent duplicate training
    if dataset.status in ["queued", "running", "validating_files"]:
        raise HTTPException(
            status_code=400,
            detail="Fine-tuning already in progress"
        )
    # prevent new training if previous is succedded
    if dataset.status == "succeeded":
        raise HTTPException(
            status_code=400,
            detail="Model already fine-tuned on provided dataset successfully"
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
        # find last successful fine-tune to use as base model
        last_dataset = await TrainingDataset.find_one(
            {
                "status": "succeeded"
            },
            sort=[("created_at", -1)]
        )
        if last_dataset and last_dataset.fine_tuned_model:
            base_model = last_dataset.fine_tuned_model
        else:
            base_model = "gpt-4o-2024-08-06"  # default base model

        job = client.fine_tuning.jobs.create(
            training_file=file_response.id,
            model=base_model,
            # hyperparameters={
            #     "n_epochs": 1,
            # }
        )
    except OpenAIError as e:
         # OpenAI-related error
        dataset.status = "error"
        dataset.last_event_message = f" failed: {str(e)}"
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
        dataset.last_event_message = f"failed: {str(e)}"
        await dataset.save()

        raise HTTPException(
            status_code=500,
            detail="Failed to start fine-tuning"
        )

    dataset.openai_file_id = file_response.id
    dataset.openai_job_id = job.id
    dataset.status = job.status  # likely "queued"
    dataset.trained_from_model = base_model
    await dataset.save()

    return {
        "job_id": job.id,
        "status": job.status
    }

@router.get("/finetune-status/{dataset_id}")
async def finetune_status(dataset_id: str, req: Request, admin: Annotated[str, Depends(get_admin_user)]):
    client = req.app.state.client

    dataset = await TrainingDataset.get(dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="job not found")

    # If there's no job id, you can decide what to do (optional guard)
    if not dataset.openai_job_id:
        return {"status": dataset.status, "model": dataset.fine_tuned_model, "events": []}

    try:
        job = client.fine_tuning.jobs.retrieve(dataset.openai_job_id)
    except OpenAIError:
        raise HTTPException(status_code=502, detail="Failed to fetch job status")

    updated = False
    events_out: list[str] = []

    # Sync status
    if dataset.status != job.status:
        dataset.status = job.status
        updated = True

    # Sync model when finished
    if job.status == "succeeded" and dataset.fine_tuned_model != job.fine_tuned_model:
        dataset.fine_tuned_model = job.fine_tuned_model
        updated = True

    # Capture error message on failure (if available)
    if job.status == "failed":
        msg = job.error.message if getattr(job, "error", None) else "Training failed. Try again with a different dataset."
        if dataset.last_event_message != msg:
            dataset.last_event_message = msg
            updated = True

    # Decide when to poll events:
    # - definitely during running
    # - optionally during failed/succeeded to catch last messages
    if job.status in ["validating_files", "queued", "running", "failed", "succeeded", "cancelled"]:
        events = client.fine_tuning.jobs.list_events(
    fine_tuning_job_id=dataset.openai_job_id,
    limit=100
)

    # normalize to oldest -> newest
    events_list = list(reversed(events.data))

    start_idx = 0
    if dataset.last_event_id:
        for i, e in enumerate(events_list):
            if e.id == dataset.last_event_id:
                start_idx = i + 1
                break

    new_events = events_list[start_idx:]

    if new_events:
        dataset.last_event_id = new_events[-1].id
        dataset.last_event_message = new_events[-1].message
        updated = True
        events_out = [e.message for e in new_events]
    else:
        events_out = []

    if updated:
        await dataset.save()

    return {
        "status": job.status,                 # could be validating_files/queued/running/paused/succeeded/failed/cancelled
        "model": job.fine_tuned_model,        # None until succeeded
        "events": events_out,                 # only new events since last_event_id
    }


@router.post("/cancel-finetune/{dataset_id}")
async def cancel_finetune(dataset_id: str, req: Request,  admin: Annotated[str, Depends(get_admin_user)]):

    client = req.app.state.client

    dataset = await TrainingDataset.get(dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="job not found")

    if dataset.status in ["succeeded", "failed", "cancelled"]:
        raise HTTPException(status_code=400, detail="Cannot cancel a completed job")

    try:
        response = client.fine_tuning.jobs.cancel(dataset.openai_job_id)
    except OpenAIError:
        raise HTTPException(status_code=502, detail="Failed to cancel fine-tuning job")

    dataset.status = response.status  # should be "cancelled"
    await dataset.save()

    return {"message": "Fine-tuning job cancelled successfully"}

@router.post("/pause-finetune/{dataset_id}")
async def pause_finetune(dataset_id: str, req: Request,  admin: Annotated[str, Depends(get_admin_user)]):

    client = req.app.state.client

    dataset = await TrainingDataset.get(dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="job not found")

    if dataset.status in ["succeeded", "failed", "cancelled"]:
        raise HTTPException(status_code=400, detail="Cannot pause a completed job")

    try:
        response = client.fine_tuning.jobs.pause(dataset.openai_job_id)
    except OpenAIError as e:
        raise HTTPException(status_code=502, detail=f"Failed to pause fine-tuning job: {str(e)}")

    dataset.status = response.status  # should be "paused"
    await dataset.save()

    return {"message": "Fine-tuning job paused successfully"}

@router.post("/resume-finetune/{dataset_id}")
async def resume_finetune(dataset_id: str, req: Request,  admin: Annotated[str, Depends(get_admin_user)]):

    client = req.app.state.client

    dataset = await TrainingDataset.get(dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="job not found")

    if dataset.status in ["succeeded", "failed", "cancelled"]:
        raise HTTPException(status_code=400, detail="Cannot resume a completed job")

    try:
        response = client.fine_tuning.jobs.resume(dataset.openai_job_id)
    except OpenAIError as e:
        raise HTTPException(status_code=502, detail=f"Failed to resume fine-tuning job: {str(e)}")

    dataset.status = response.status  # should be "running"
    await dataset.save()

    return {"message": "Fine-tuning job resumed successfully"}