import base64
from uuid import uuid4
import cloudinary
import cloudinary.uploader
from fastapi import UploadFile

async def upload_image_to_cloudinary(file: UploadFile) -> str:
    """
    Uploads base64 image to Cloudinary and returns hosted URL
    """
    try:
        result = cloudinary.uploader.upload(
            file.file,
            folder="chat_uploads",
            resource_type="image",
            public_id=str(uuid4())
        )
        return result["secure_url"]
    except Exception as e:
        print("Cloudinary upload failed:", e)
        raise
