import configparser
import os

class AzureBlobConfig:
    def __init__(self, config_path=None):
        if config_path is None:
            config_path = os.path.join(os.path.dirname(__file__), 'azure_blob_settings.ini')
        self.config_path = config_path
        self.config = configparser.ConfigParser()
        self.config.read(self.config_path, encoding='utf-8')

    def get_connection_string(self):
        return self.config.get('azure', 'connection_string', fallback=None)

    def get_container_name(self):
        return self.config.get('azure', 'container_name', fallback=None)

# 用法示例：
# cfg = AzureBlobConfig()
# conn_str = cfg.get_connection_string()
# container = cfg.get_container_name()
