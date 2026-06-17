import os

def list_files_in_dir(directory):
    try:
        files = os.listdir(directory)
        return {"files": files}
    except Exception as e:
        return {"error": str(e)}

def read_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        return {"content": content}
    except Exception as e:
        return {"error": str(e)}