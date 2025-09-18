import os

from azure.storage.blob import BlobServiceClient
from core.azure_blob_config import AzureBlobConfig

class AzureBlobReader:
    def download_blob_to_path(self, blob_path, local_path):
        """
        Download the specified blob to a local file path if not already exists.
        :param blob_path: Path to the blob
        :param local_path: Local file path to save
        """
        if os.path.exists(local_path):
            return  # File already exists, do nothing
        blob_client = self.container_client.get_blob_client(blob_path)
        with open(local_path, 'wb') as f:
            stream = blob_client.download_blob()
            f.write(stream.readall())
    
    def download_blob_to_path(self, blob_path, local_path, progress_callback=None):
        if os.path.exists(local_path):
            return
        blob_client = self.container_client.get_blob_client(blob_path)
        stream = blob_client.download_blob()
        total = stream.size
        downloaded = 0
        with open(local_path, 'wb') as f:
            for chunk in stream.chunks():
                f.write(chunk)
                downloaded += len(chunk)
                if progress_callback and total:
                    percent = int(downloaded * 100 / total)
                    progress_callback(percent)
    def __init__(self, connection_string=None, container_name=None):
        """
        Prefer parameters, otherwise read from config file.
        """
        if connection_string is None or container_name is None:
            cfg = AzureBlobConfig()
            connection_string = cfg.get_connection_string()
            container_name = cfg.get_container_name()
        self.connection_string = connection_string
        self.container_name = container_name
        self.service_client = BlobServiceClient.from_connection_string(connection_string)
        self.container_client = self.service_client.get_container_client(container_name)

    def list_files(self, folder_path):
        """
        List all files under a specific folder in the blob storage.
        :param folder_path: Folder path in blob (e.g. 'videos/')
        :return: List of file names
        """
        blob_list = self.container_client.list_blobs(name_starts_with=folder_path)
        return [blob.name for blob in blob_list if not blob.name.endswith('/')]

    def read_file(self, blob_path):
        """
        Read the content of a file in the blob storage.
        :param blob_path: File path in blob (e.g. 'videos/standard1.mp4')
        :return: File content (bytes)
        """
        blob_client = self.container_client.get_blob_client(blob_path)
        stream = blob_client.download_blob()
        return stream.readall()

# Example usage:
# reader = AzureBlobReader('<your_connection_string>', '<your_container_name>')
# files = reader.list_files('videos/')
# data = reader.read_file('videos/standard1.mp4')
