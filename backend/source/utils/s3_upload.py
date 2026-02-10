# import base64
# from uuid import uuid4
# import cloudinary
# import cloudinary.uploader
# from fastapi import UploadFile

# async def upload_image_to_cloudinary(file: UploadFile) -> str:
#     """
#     Uploads base64 image to Cloudinary and returns hosted URL
#     """
#     try:
#         result = cloudinary.uploader.upload(
#             file.file,
#             folder="chat_uploads",
#             resource_type="image",
#             public_id=str(uuid4())
#         )
#         return result["secure_url"]
#     except Exception as e:
#         print("Cloudinary upload failed:", e)
#         raise


from fastapi import UploadFile, Request
from config_secrets import settings

async def upload_to_s3(request:Request, file: UploadFile)-> str:

    s3_client = request.app.state.s3_client
  
    s3_client.upload_fileobj(
        file.file,
        settings.aws_bucket_name,
        file.filename,
        ExtraArgs = {"ContentType": file.content_type},
    )
    return f"https://{settings.aws_bucket_name}.s3.amazonaws.com/{file.filename}"