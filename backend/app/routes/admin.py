from typing import Annotated
from fastapi import APIRouter, Depends, File, Form, Response, UploadFile
import io
from app.dependencies import get_admin_user
from app.utils.csv_to_jsonl import process_mixed_data

router = APIRouter(prefix="/api/v1/admin", tags=["Admin"])



@router.post("/convert-mixed")
async def convert_mixed_endpoint(
     admin: Annotated[str, Depends(get_admin_user)],
    file: UploadFile = File(...), 
    system_prompt: str = Form("You are a helpful assistant."),
   
    
):
    content_bytes = await file.read()
    content_str = content_bytes.decode("utf-8")
    input_stream = io.StringIO(content_str)
    
    jsonl_result = process_mixed_data(input_stream, system_prompt)
    
    return Response(
        content=jsonl_result,
        media_type="application/jsonl",
        headers={
            "Content-Disposition": "attachment; filename=mixed_training_data.jsonl"
        }
    )