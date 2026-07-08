import os
import tempfile
import logging
from minio import Minio
from minio.error import S3Error
from uuid import uuid4

client = Minio(
    os.getenv("MINIO_ENDPOINT", "localhost:9000"),
    access_key=os.getenv("MINIO_ACCESS_KEY", "minioadmin"),
    secret_key=os.getenv("MINIO_SECRET_KEY", "minioadmin"),
    secure=False
)

BUCKET_NAME = "documents"

logger = logging.getLogger("storage_service")
if not logger.handlers:
    import sys
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

def initialize_bucket():
    if not client.bucket_exists(BUCKET_NAME):
        client.make_bucket(BUCKET_NAME)

def upload_file(file, bot_id: str):
    object_name = f"bot_{bot_id}/{uuid4()}_{file.filename}"

    client.put_object(
        bucket_name=BUCKET_NAME,
        object_name=object_name,
        data=file.file,
        length=-1,
        part_size=10 * 1024 * 1024,
        content_type=file.content_type,
    )

    return object_name

def download_file_to_temp(storage_path: str) -> str:
    """
    Downloads an object from MinIO and saves it to a local temporary file.
    
    Args:
        storage_path: The object name/path in MinIO bucket.
        
    Returns:
        The absolute path of the generated temporary file.
    """
    logger.info("Downloading file from MinIO...")
    
    # Extract file extension
    _, ext = os.path.splitext(storage_path)
    
    temp_file_path = None
    try:
        # Create unique temporary file path and close descriptor immediately
        fd, temp_file_path = tempfile.mkstemp(suffix=ext)
        os.close(fd)
        
        logger.info(f"Temporary file created: {temp_file_path}")
        
        # Download stream from MinIO
        response = client.get_object(
            bucket_name=BUCKET_NAME,
            object_name=storage_path
        )
        
        try:
            with open(temp_file_path, "wb") as f:
                for chunk in response.stream(32 * 1024):
                    f.write(chunk)
        finally:
            response.close()
            response.release_conn()
            
        logger.info("Download successful.")
        return temp_file_path
        
    except S3Error as err:
        logger.error(f"Download failed: {storage_path}")
        if temp_file_path and os.path.exists(temp_file_path):
            logger.info("Cleaning temporary resources...")
            try:
                os.remove(temp_file_path)
            except Exception:
                pass
        
        # Parse common errors
        if err.code == "NoSuchKey":
            raise FileNotFoundError(f"Object not found in MinIO: {storage_path}") from err
        elif err.code == "NoSuchBucket":
            raise ValueError(f"Bucket does not exist: {BUCKET_NAME}") from err
        else:
            raise RuntimeError(f"MinIO download error: {str(err)}") from err
            
    except Exception as exc:
        logger.error(f"Download failed: {storage_path}")
        if temp_file_path and os.path.exists(temp_file_path):
            logger.info("Cleaning temporary resources...")
            try:
                os.remove(temp_file_path)
            except Exception:
                pass
        raise RuntimeError(f"Failed to write file locally: {str(exc)}") from exc