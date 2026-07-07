import io
import os
import sys
import logging

# Dynamically construct absolute path to central-hub-backend and prepend it to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
backend_path = os.path.join(project_root, "apps", "central-hub-backend")
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

# Prevent monorepo conflicts by clearing pre-cached 'src' modules from other paths
if "src" in sys.modules:
    src_module = sys.modules["src"]
    src_file = getattr(src_module, "__file__", None)
    if src_file is None or not src_file.startswith(backend_path):
        del sys.modules["src"]

# pyrefly: ignore [missing-import]
from src.services.storage_service import upload_file, download_file_to_temp, BUCKET_NAME, client

class MockUploadFile:
    def __init__(self, filename, content, content_type):
        self.filename = filename
        self.file = io.BytesIO(content)
        self.content_type = content_type

def test_download_file_to_temp():
    print("=== STARTING MINIO DOWNLOAD INTEGRATION TEST ===")
    
    # 1. Prepare dummy file content
    content = b"PDF-1.4 Dummy document content for MinIO file download validation."
    filename = "policy_document.pdf"
    file = MockUploadFile(filename, content, "application/pdf")
    
    # 2. Upload file to MinIO
    print(f"Uploading file '{filename}' to MinIO...")
    storage_path = upload_file(file, bot_id="test_bot_invalidation")
    print(f"File uploaded. Storage path: {storage_path}")

    # 3. Download file from MinIO
    print("Downloading file to local temp path...")
    temp_path = download_file_to_temp(storage_path)
    print(f"Download complete. Temp path: {temp_path}")

    # 4. Verify assertions
    assert os.path.exists(temp_path), f"Temporary file does not exist: {temp_path}"
    assert temp_path.endswith(".pdf"), f"Temporary file extension mismatch: {temp_path}"
    
    with open(temp_path, "rb") as f:
        downloaded_content = f.read()
    
    assert downloaded_content == content, "Downloaded content does not match uploaded content"
    print("Success validation assertions passed.")

    # 5. Clean up temporary file
    print("Removing temporary test file...")
    os.remove(temp_path)
    assert not os.path.exists(temp_path), "Failed to delete temporary test file"

    # 6. Verify exception handling on non-existent object
    print("\nVerifying exception handling for non-existent file...")
    non_existent_path = "bot_test_bot_invalidation/does_not_exist.pdf"
    try:
        download_file_to_temp(non_existent_path)
        assert False, "Expected FileNotFoundError was not raised"
    except FileNotFoundError as err:
        print(f"Caught expected FileNotFoundError: {str(err)}")
    except Exception as exc:
        assert False, f"Expected FileNotFoundError, but caught: {type(exc).__name__}: {str(exc)}"

    print("=== ALL MINIO DOWNLOAD TESTS PASSED SUCCESSFULLY ===")

if __name__ == "__main__":
    test_download_file_to_temp()
