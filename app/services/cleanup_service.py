import os

def delete_audio_file(audio_path: str):
    file_path = os.path.join("uploads", audio_path)
    if os.path.exists(file_path):
        os.remove(file_path)
