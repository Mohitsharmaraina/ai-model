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
from PIL import Image
import io


MAX_DIMENSION = 768

async def upload_to_s3(request:Request, file: UploadFile)-> str:

    s3_client = request.app.state.s3_client

     # Read file into memory
    contents = await file.read()

    image = Image.open(io.BytesIO(contents))

    width, height = image.size
    max_side = max(width, height)

    output_buffer = io.BytesIO()

    #  Resize only if needed
    if max_side > MAX_DIMENSION:
        image.thumbnail((MAX_DIMENSION, MAX_DIMENSION))
        image = image.convert("RGB")
        image.save(output_buffer, format="JPEG", quality=75)
        content_type = "image/jpeg"
    else:
        # Keep original resolution but still compress if not JPEG
        if image.format != "JPEG":
            image = image.convert("RGB")
            image.save(output_buffer, format="JPEG", quality=85)
            content_type = "image/jpeg"
        else:
            image.save(output_buffer, format="JPEG", quality=85)
            content_type = "image/jpeg"

    output_buffer.seek(0)
    
    s3_client.upload_fileobj(
        # file.file,
        output_buffer,
        settings.aws_bucket_name,
        file.filename,
        ExtraArgs = {"ContentType": content_type}
        # ExtraArgs = {"ContentType": file.content_type},
    )
    return f"https://{settings.aws_bucket_name}.s3.{settings.aws_region_name}.amazonaws.com/{file.filename}"