from google.cloud import storage
import os


storage_client = storage.Client()

def get_list_of_files(bucket_name):
    """Lists all the blobs in the bucket."""
    print("\n")
    print("get_list_of_files: " + bucket_name)

    
    blobs = storage_client.list_blobs(bucket_name, prefix="files/")
    files = [blob.name.replace("files/", "") for blob in blobs if not blob.name.endswith("/")]  

    return files

def upload_file(bucket_name, file_name):
    """Upload a file to the bucket under the 'files/' folder."""
    print("\n")
    print("upload_file: " + bucket_name + "/files/" + os.path.basename(file_name))

    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(f"files/{os.path.basename(file_name)}")  

    blob.upload_from_filename(file_name)  
    return

def download_file(bucket_name, file_name):
    """Retrieve a file from the bucket and save locally under the 'files/' folder."""
    print("\n")
    print("download_file: " + bucket_name + "/files/" + file_name)

   
    os.makedirs("./files", exist_ok=True)

    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(f"files/{file_name}")  
    local_file_path = f"./files/{file_name}"

    
    blob.download_to_filename(local_file_path)
    print(f"File downloaded to: {local_file_path}")

    return
