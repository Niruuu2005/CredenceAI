import os
from app.services.storage import StorageClient

def test_storage_client_local_fallback():
    client = StorageClient()
    
    # Payload details
    bucket = "raw-tests"
    key = "job_999.json"
    payload = {"query": "fallback test", "success": True}
    
    # Upload
    ref_uri = client.upload_raw_payload(bucket, key, payload)
    assert ref_uri.startswith("file://") or ref_uri.startswith("s3://")
    
    # Retrieve
    retrieved = client.get_raw_payload(bucket, key)
    assert retrieved["query"] == "fallback test"
    assert retrieved["success"] is True

    # Clean up local file if created
    if ref_uri.startswith("file:///"):
        local_path = ref_uri.replace("file:///", "").replace("/", os.sep)
        if os.path.exists(local_path):
            os.remove(local_path)
            # Remove empty parent directories if clean
            parent_dir = os.path.dirname(local_path)
            if not os.listdir(parent_dir):
                os.rmdir(parent_dir)
            grandparent_dir = os.path.dirname(parent_dir)
            if not os.listdir(grandparent_dir):
                os.rmdir(grandparent_dir)
