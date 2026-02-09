from typing import Annotated
from fastapi import APIRouter, Depends, File, Form, Request, UploadFile, HTTPException
import io
from source.dependencies import get_admin_user
from source.utils.xlsx_or_csv_to_jsonl import process_mixed_data_v2
from source.utils.training_file_gridfs_storage import DatasetStorageService
from source.utils.validate_jsonl_file import validate_finetuning_jsonl, DatasetValidationError
import logging

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

        logging.info("generated jsonl file", jsonl_str)

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
            get_training_file = await DatasetStorageService.get_file_content(req.app.state.db, req.app.state.gridfs_bucket, str(new_entry.id))
            return {"id": str(new_entry.id), "samples": sample_count, "status": "archived", "file_content": get_training_file}
        
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Database storage failed: {e}")
