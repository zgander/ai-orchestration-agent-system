import pytest
import zipfile
from pathlib import Path
from app.services.zip_service import ZipService, UnsupportedFormatError, ZipSlipError

def test_validate_archive_invalid(tmp_path):
    invalid_file = tmp_path / "test.txt"
    invalid_file.write_text("not a zip")
    
    service = ZipService()
    with pytest.raises(UnsupportedFormatError):
        service.validate_archive(invalid_file)

def test_extract_valid(tmp_path):
    # Create a valid zip
    zip_path = tmp_path / "test.zip"
    with zipfile.ZipFile(zip_path, 'w') as zf:
        zf.writestr("test.txt", "hello")
        
    target_dir = tmp_path / "target"
    target_dir.mkdir()
    
    service = ZipService()
    root = service.extract(zip_path, target_dir)
    
    assert (root / "test.txt").exists()
    assert (root / "test.txt").read_text() == "hello"

def test_detect_root(tmp_path):
    # Create a zip with a single top-level folder
    zip_path = tmp_path / "test.zip"
    with zipfile.ZipFile(zip_path, 'w') as zf:
        zf.writestr("myrepo/test.txt", "hello")
        
    target_dir = tmp_path / "target"
    target_dir.mkdir()
    
    service = ZipService()
    root = service.extract(zip_path, target_dir)
    
    assert root.name == "myrepo"
    assert (root / "test.txt").exists()
