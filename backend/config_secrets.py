# for using environment variables from a .env file
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # If this is missing in .env, the app will crash 
    mongo_uri: str
    jwt_secret_key: str
    jwt_algorithm: str
    access_token_expire_hours: int
    cloudinary_cloud_name: str
    cloudinary_api_key: str     
    cloudinary_api_secret: str

    # Tells Pydantic to read from a .env file
    model_config = SettingsConfigDict(env_file=".env")

# Create a global instance
settings = Settings()