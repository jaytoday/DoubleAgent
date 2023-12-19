import os

class FileSystemTool:

    @classmethod
    def read(cls, file_path: str) -> str:
        with open(file_path, "r") as f:
            return f.read()

    @classmethod
    def append(cls, file_path: str, file_content: str) -> None:
        with open(file_path, "a") as f:
            f.write(file_content)
            return None
    
    @classmethod
    def write(cls, file_path: str, file_content: str) -> None:
        with open(file_path, "w") as f:
            f.write(file_content)
            return None
    
    @classmethod
    def delete(cls, file_path: str) -> None:
        os.remove(file_path)
        return None
