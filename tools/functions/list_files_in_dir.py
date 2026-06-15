import os

def list_files_in_dir(directory):
    try:
        files = os.listdir(directory)
        return {"files": files}
    except Exception as e:
        return {"error": str(e)}