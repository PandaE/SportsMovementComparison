import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import pytest
from core.azure_blob_reader import AzureBlobReader

def test_list_files():
    reader = AzureBlobReader()
    # Assume there is a forehandhighclear/ directory in the blob
    files = reader.list_files('forehandhighclear/')
    assert isinstance(files, list)
    print('file list:', files)

    # Optional: assert at least one file exists
    # assert len(files) > 0

def test_read_file():
    reader = AzureBlobReader()
    files = reader.list_files('forehandhighclear/')
    if files:
        data = reader.read_file(files[0])
        assert isinstance(data, bytes)
        print(f'File {files[0]} size: {len(data)} bytes')
    else:
        print('No readable files, skipping read_file test')
