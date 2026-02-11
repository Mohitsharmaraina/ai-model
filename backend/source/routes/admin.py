from typing import Annotated
from fastapi import APIRouter, Depends, File, Form, Request, UploadFile, HTTPException
import io
from io import BytesIO
from source.dependencies import get_admin_user
from source.utils.xlsx_or_csv_to_jsonl import process_mixed_data_v2
from source.utils.training_file_gridfs_storage import DatasetStorageService
from source.utils.validate_jsonl_file import validate_finetuning_jsonl, DatasetValidationError
from source.models.training_data_model import TrainingDataset 

router = APIRouter(prefix="/api/v1/admin", tags=["Admin"])

@router.post("/convert-mixed")
async def convert_mixed_endpoint(
    req: Request,
    admin: Annotated[str, Depends(get_admin_user)],
    dataset_name: str = Form(...),
    file: UploadFile = File(...), 
    system_prompt: str = Form("You are a helpful assistant."),
    
):
   
        # 1. Read raw bytes from the uploaded file
        content_bytes = await file.read()
        
        # 2. Wrap in BytesIO (Treats bytes like a file object)
        input_stream = io.BytesIO(content_bytes)

        # 3. Call your  function

        jsonl_str = process_mixed_data_v2(input_stream, system_prompt, filename=file.filename)

       # Validate BEFORE storing 
        try: 
            validation = validate_finetuning_jsonl(jsonl_str) 
        except DatasetValidationError as e: 
            raise HTTPException(status_code=400, detail=str(e))
       
        # 2. Determine Stats
        sample_count = len(jsonl_str.strip().split("\n"))

        # 3. Store via Service
        try:
            new_entry = await DatasetStorageService.save_to_gridfs(
                bucket=req.app.state.gridfs_bucket,
                jsonl_content=jsonl_str,
                metadata={
                    "name": dataset_name,
                    "version": 1, 
                    "system_prompt": system_prompt,
                    "sample_count": sample_count,
                    "status": "locally validated"
                }
            )
            training_file_bytes = await DatasetStorageService.get_file_bytes( req.app.state.gridfs_bucket, str(new_entry.id))
            print("file ready to pass to openai", training_file_bytes)
            return {"id": str(new_entry.id), "samples": sample_count, "status": "archived", "file_content": training_file_bytes}
        
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Database storage failed: {e}")
        
@router.post("/start-finetune/{dataset_id}")
async def start_finetune(dataset_id: str, req: Request):

    client = req.app.state.client

    dataset = await TrainingDataset.get(dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

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

    dataset.openai_file_id = file_response.id
    dataset.openai_job_id = job.id
    dataset.status = job.status  # likely "queued"
    await dataset.save()

    return {
        "job_id": job.id,
        "status": job.status
    }

@router.get("/finetune-status/{dataset_id}")
async def finetune_status(dataset_id: str, req: Request):

    client = req.app.state.client

    dataset = await TrainingDataset.get(dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="job not found")

    job = client.fine_tuning.jobs.retrieve(dataset.openai_job_id)


    updated = False

    if job.status in ["succeeded", "failed"] and dataset.status != job.status: 
        dataset.status = job.status
        updated = True

    if job.status == "succeeded" and dataset.fine_tuned_model != job.fine_tuned_model:
        dataset.fine_tuned_model = job.fine_tuned_model
        updated = True

    if updated:
        await dataset.save()   # Only ONE write

    return {
        "status": job.status,
        "model": job.fine_tuned_model
    }

