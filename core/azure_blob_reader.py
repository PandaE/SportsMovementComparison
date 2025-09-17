import os

from azure.storage.blob import BlobServiceClient
from core.azure_blob_config import AzureBlobConfig

class AzureBlobReader:
    def __init__(self, connection_string=None, container_name=None):
        """
        Prefer parameters, otherwise read from config file
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
        List all files under a specific folder in the blob
        :param folder_path: Folder path in blob (e.g. 'videos/')
        :return: List of file names
        """
        blob_list = self.container_client.list_blobs(name_starts_with=folder_path)
        return [blob.name for blob in blob_list if not blob.name.endswith('/')]

    def read_file(self, blob_path):
        """
        Read the content of a file in the blob
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
