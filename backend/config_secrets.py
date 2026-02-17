# for using environment variables from a .env file
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # If this is missing in .env, the app will crash 
    mongo_uri: str
    jwt_secret_key: str
    jwt_algorithm: str
    access_token_expire_hours: int

    # openai
    open_ai_access_key: str

    # # Cloudinary settings
    # cloudinary_cloud_name: str
    # cloudinary_api_key: str     
    # cloudinary_api_secret: str

    # aws settings
    aws_access_key_id: str
    aws_secret_access_key:str
    aws_bucket_name:str
    aws_region_name:str
    
    # Redis settings
    redis_host: str
    redis_port: int
    redis_username: str
    redis_password: str

    REDIS_SSL: bool = False
    # Critical for Migration:
    # Set to True when you move to AWS ElastiCache Cluster
    REDIS_CLUSTER_MODE: bool = False
    
    # Superadmin credentials
    super_admin_email : str
    super_admin_password : str

    # Tells Pydantic to read from a .env file
    model_config = SettingsConfigDict(env_file=".env")

# Create a global instance
settings = Settings()