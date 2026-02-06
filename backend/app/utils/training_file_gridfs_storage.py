import io
from app.models.training_data_model import TrainingDataset # Import the model defined above
from fastapi import Request


# https://www.mongodb.com/docs/languages/python/pymongo-driver/current/crud/gridfs/  (official PyMongo async GridFS docs)
class DatasetStorageService:
    @staticmethod
    async def save_to_gridfs(bucket, jsonl_content: str, metadata: dict) -> TrainingDataset:

        """
        Uses native PyMongo async GridFS to store the file.
        """
        print("Saving to GridFS with metadata:", metadata)
        
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
            sample_count=metadata['sample_count'],
            gridfs_id=gridfs_id
        )
        print("Beanie initialized:", TrainingDataset._document_settings is not None)
        await dataset_record.insert()
        return dataset_record

    @staticmethod
    async def get_file_content(dataset, bucket, dataset_id: str) -> str:
        """
        Retrieves the JSONL string back for fine-tuning.
        """
        dataset = await dataset.get(dataset_id)
        if not dataset:
            raise ValueError("Dataset record not found")


        # Stream the chunks back into memory
        output = io.BytesIO()
        await bucket.download_to_stream(dataset.gridfs_id, output)
        
        return output.getvalue().decode("utf-8")