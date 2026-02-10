# import cloudinary
# from config_secrets import settings

# async def init_cloudinary():
#     cloudinary.config(
#         cloud_name=settings.cloudinary_cloud_name,
#         api_key=settings.cloudinary_api_key,
#         api_secret=settings.cloudinary_api_secret,
#         secure=True
#     )

import boto3
from config_secrets import settings

async def init_s3():
    boto3.client(
        's3',
        aws_access_key_id = settings.aws_access_key_id,
        aws_secret_access_key = settings.aws_secret_access_key,
        region_name = settings.aws_region_name
    )