import pytest
from core.azure_blob_reader import AzureBlobReader

def test_list_files():
    reader = AzureBlobReader()
    # 假设 blob 里有 videos/ 目录
    files = reader.list_files('videos/')
    assert isinstance(files, list)
    print('文件列表:', files)

    # 可选：断言至少有一个文件
    # assert len(files) > 0

def test_read_file():
    reader = AzureBlobReader()
    files = reader.list_files('videos/')
    if files:
        data = reader.read_file(files[0])
        assert isinstance(data, bytes)
        print(f'文件 {files[0]} 大小: {len(data)} bytes')
    else:
        print('没有可读文件，跳过 read_file 测试')
