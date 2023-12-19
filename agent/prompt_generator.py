from typing import Dict

from agent.models import FileSystemOperationResult

class FilesystemOperationPromptGenerator:

    @classmethod
    def initial_system_prompt(cls, file_map: Dict[str,str]) -> str:
        return f"""You are FileSystemAgent, an AI agent capable of reading, writing to, and deleting files in order to provide answers or complete tasks specified in the user's prompt. 

   Here is an initial mapping of files and descriptions of what those files contain:
    ```
    {file_map}
    ```

        Think step-by-step about what operation to make, and what file to make the operation on. If your first operation does not succeed, try again.

        If the user's prompt requires information from a file, or the modification or deletion of a file, call the filesystem_operation function with the following parameters:
            - operation_type: either "read", "write", "append", or "delete".
            - reason: A string value describing the specific reason for the operation and the file that was chosen.
            - file_path: the path to the file to read, write, or delete.
            - file_content: the contents of the file to write, if the operation_type is "write". If the operation_type is not "write", this parameter is not required.
    """

    @classmethod
    def operation_result_prompt(cls, operation_result: FileSystemOperationResult) -> str:
        return f"""The system has completed the requested filesystem operation. Here is the result:

    Operation Type: {operation_result.operation}
    File Path: {operation_result.file_path}
    {f"File Content: {operation_result.file_content}" if operation_result.file_content else ""}
    
    """
