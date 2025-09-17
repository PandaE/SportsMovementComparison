import os

from azure.storage.blob import BlobServiceClient
from core.azure_blob_config import AzureBlobConfig

class AzureBlobReader:
    def __init__(self, connection_string=None, container_name=None):
        # 优先参数传入，否则从配置文件读取
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
        列出blob某个文件夹下的所有文件
        :param folder_path: blob中的文件夹路径（如 'videos/'）
        :return: 文件名列表
        """
        blob_list = self.container_client.list_blobs(name_starts_with=folder_path)
        return [blob.name for blob in blob_list if not blob.name.endswith('/')]

    def read_file(self, blob_path):
        """
        读取blob中某个文件内容
        :param blob_path: blob中的文件路径（如 'videos/standard1.mp4'）
        :return: 文件内容（bytes）
        """
        blob_client = self.container_client.get_blob_client(blob_path)
        stream = blob_client.download_blob()
        return stream.readall()

# 用法示例：
# reader = AzureBlobReader('<your_connection_string>', '<your_container_name>')
# files = reader.list_files('videos/')
# data = reader.read_file('videos/standard1.mp4')
