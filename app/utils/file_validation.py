import os
from fastapi import UploadFile, HTTPException
from typing import Tuple

ALLOWED_EXTENSIONS = {'.mp3', '.wav', '.m4a'}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB

def get_secure_filename(filename: str) -> str:
    return os.path.basename(filename).replace(' ', '_')

def validate_extension(filename: str):
    ext = os.path.splitext(filename)[-1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Unsupported file extension. Allowed: .mp3, .wav, .m4a")
    return ext

def validate_file_size(file: UploadFile):
    file.file.seek(0, os.SEEK_END)
    size = file.file.tell()
    file.file.seek(0)
    if size > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large. Max size is 5MB.")
    return size

def check_duplicate_file(upload_dir: str, filename: str):
    path = os.path.join(upload_dir, filename)
    if os.path.exists(path):
        raise HTTPException(status_code=400, detail="Duplicate filename detected. Please rename your file.")
    return path

def is_valid_audio(file: UploadFile):
    # EXTENSION step handled above. Quick read for header can be added here.
    # For thorough check, use an audio parsing lib if needed.
    try:
        header = file.file.read(10)
        file.file.seek(0)
        if header[:4] not in [b'RIFF', b'fLaC'] and header[:3] != b'ID3':
            raise HTTPException(status_code=400, detail="File does not appear to be a valid audio file.")
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid/corrupted audio file.")
    return True
