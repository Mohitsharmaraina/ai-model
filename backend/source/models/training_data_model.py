from typing import Annotated
from datetime import datetime, timezone
from beanie import Document, Indexed
from pydantic import Field


class TrainingDataset(Document):
    dataset_name: str
    version: int = 1
    system_prompt: str
    sample_count: int
    status: str
    # Reference to the actual file in GridFS
    gridfs_id:Annotated[str, Indexed()]
    created_at: datetime = Field(default_factory= lambda: datetime.now(timezone.utc))

    class Settings:
        name = "training_datasets"
        