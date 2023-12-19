import os

class FileSystemTool:

    @classmethod
    def _is_safe_path(cls, file_path: str) -> bool:
        current_working_dir = os.path.abspath(os.getcwd())
        absolute_file_path = os.path.abspath(file_path)
        return os.path.commonpath([current_working_dir]) == os.path.commonpath([current_working_dir, absolute_file_path])

    @classmethod
    def read(cls, file_path: str) -> str:
        if not cls._is_safe_path(file_path):
            raise ValueError("Access to the file outside the current working directory is not allowed.")
        with open(file_path, "r") as f:
            return f.read()

    @classmethod
    def append(cls, file_path: str, file_content: str) -> None:
        if not cls._is_safe_path(file_path):
            raise ValueError("Access to the file outside the current working directory is not allowed.")
        with open(file_path, "a") as f:
            f.write(file_content)
            return None
    
    @classmethod
    def write(cls, file_path: str, file_content: str) -> None:
        if not cls._is_safe_path(file_path):
            raise ValueError("Access to the file outside the current working directory is not allowed.")
        with open(file_path, "w") as f:
            f.write(file_content)
            return None
    
    @classmethod
    def delete(cls, file_path: str) -> None:
        if not cls._is_safe_path(file_path):
            raise ValueError("Access to the file outside the current working directory is not allowed.")
        os.remove(file_path)
        return None
