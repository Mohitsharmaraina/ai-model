from typing import Annotated
from fastapi import APIRouter, Depends, File, Form, Response, UploadFile, HTTPException
import io
from app.dependencies import get_admin_user
from app.utils.xlsx_or_csv_to_jsonl import process_mixed_data_v2
from app.utils.training_file_gridfs_storage import DatasetStorageService

router = APIRouter(prefix="/api/v1/admin", tags=["Admin"])

@router.post("/convert-mixed")
async def convert_mixed_endpoint(
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
    
       
        # 2. Determine Stats
        sample_count = len(jsonl_str.strip().split("\n"))

        # 3. Store via Service
        try:
            new_entry = await DatasetStorageService.save_to_gridfs(
                jsonl_content=jsonl_str,
                metadata={
                    "name": dataset_name,
                    "version": 1, 
                    "system_prompt": system_prompt,
                    "sample_count": sample_count
                }
            )
            return {"id": str(new_entry.id), "samples": sample_count, "status": "archived"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Database storage failed: {e}")
