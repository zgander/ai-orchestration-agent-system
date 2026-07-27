import zipfile
from pathlib import Path
import os
from app.utils.logger import get_logger

logger = get_logger(__name__)

class CorruptedArchiveError(Exception):
    pass

class UnsupportedFormatError(Exception):
    pass

class ZipSlipError(Exception):
    pass

class ZipService:
    def validate_archive(self, file_path: Path) -> bool:
        """Check if the file is a valid ZIP archive."""
        if not zipfile.is_zipfile(file_path):
            raise UnsupportedFormatError(f"File is not a valid ZIP archive: {file_path}")
        return True

    def extract(self, zip_path: Path, target_dir: Path) -> Path:
        """
        Extract ZIP file securely, preventing Zip Slip.
        Returns the root path of the extracted repository.
        """
        self.validate_archive(zip_path)
        
        logger.info(f"Extracting {zip_path} to {target_dir}")
        try:
            with zipfile.ZipFile(zip_path, 'r') as zf:
                # Zip Slip Prevention
                target_dir_str = os.path.abspath(target_dir)
                for member in zf.infolist():
                    extracted_path = os.path.abspath(os.path.join(target_dir_str, member.filename))
                    if not extracted_path.startswith(target_dir_str + os.path.sep) and extracted_path != target_dir_str:
                        raise ZipSlipError(f"Attempted path traversal in ZIP archive: {member.filename}")
                
                zf.extractall(target_dir)
            
            return self.detect_root(target_dir)
        except zipfile.BadZipFile as e:
            logger.error(f"Corrupted ZIP archive: {e}")
            raise CorruptedArchiveError(f"Corrupted ZIP archive: {e}") from e

    def detect_root(self, extracted_dir: Path) -> Path:
        """
        If a ZIP contains a single top-level directory (like GitHub downloads),
        return that directory as the root. Otherwise, return the extraction dir.
        """
        entries = list(extracted_dir.iterdir())
        if len(entries) == 1 and entries[0].is_dir():
            return entries[0]
        return extracted_dir
