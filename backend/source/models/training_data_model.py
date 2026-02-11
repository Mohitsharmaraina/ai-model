from typing import Annotated, Optional
from datetime import datetime, timezone
from beanie import Document, Indexed
from pydantic import Field


class TrainingDataset(Document):
    dataset_name: str
    version: int = 1
    system_prompt: str
    sample_count: int
    status: str
    openai_file_id : Optional[str] = None
    openai_job_id: Optional[str]  =None
    fine_tuned_model : Optional[str] = None
    # Reference to the actual file in GridFS
    gridfs_id:Annotated[str, Indexed()]
    created_at: datetime = Field(default_factory= lambda: datetime.now(timezone.utc))

    class Settings:
        name = "training_datasets"
        