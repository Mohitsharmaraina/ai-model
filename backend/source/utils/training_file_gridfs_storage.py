import io

from bson import ObjectId
from source.models.training_data_model import TrainingDataset # Import the model defined above


# https://www.mongodb.com/docs/languages/python/pymongo-driver/current/crud/gridfs/  (official PyMongo async GridFS docs)
class DatasetStorageService:
    @staticmethod
    async def save_to_gridfs(bucket, jsonl_content: str, metadata: dict) -> TrainingDataset:

        """
        Uses native PyMongo async GridFS to store the file.
        """
        
        # 3. Upload the file binary
        file_bytes = jsonl_content.encode("utf-8")
        gridfs_id = await bucket.upload_from_stream(
            filename=f"{metadata['name']}_v{metadata['version']}.jsonl",
            source=io.BytesIO(file_bytes),
            metadata={"content_type": "application/jsonl"}
        )

        # 4. Create the Beanie Document record
        dataset_record = TrainingDataset(
            dataset_name=metadata['name'],
            version=metadata['version'],
            system_prompt=metadata['system_prompt'],
            status=metadata['status'],
            sample_count=metadata['sample_count'],
            gridfs_id=str(gridfs_id)
        )

        await dataset_record.insert()
        return dataset_record

    @staticmethod
    async def get_file_content(dataset, bucket, dataset_id: str) -> str:
        """
        Retrieves the JSONL string back for fine-tuning.
        """
        dataset = await TrainingDataset.get(dataset_id)
        if not dataset:
            raise ValueError("Dataset record not found")


        # Stream the chunks back into memory
        output = io.BytesIO()
        file_id = ObjectId(dataset.gridfs_id)
        await bucket.download_to_stream(file_id, output)
        
        return output.getvalue().decode("utf-8")