from minio import Minio
from minio.error import S3Error
from uuid import uuid4

client = Minio(
    "localhost:9000",
    access_key="minioadmin",
    secret_key="minioadmin",
    secure=False
)

BUCKET_NAME = "documents"

def initialize_bucket():
    if not client.bucket_exists(BUCKET_NAME):
        client.make_bucket(BUCKET_NAME)
def upload_file(file):
    object_name = f"{uuid4()}_{file.filename}"

    client.put_object(
        bucket_name=BUCKET_NAME,
        object_name=object_name,
        data=file.file,
        length=-1,
        part_size=10 * 1024 * 1024,
        content_type=file.content_type,
    )

    return object_name