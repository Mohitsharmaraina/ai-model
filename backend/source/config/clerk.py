from clerk_backend_api import Clerk
from config_secrets import settings

clerk = Clerk(bearer_auth=settings.clerk_secret_key)