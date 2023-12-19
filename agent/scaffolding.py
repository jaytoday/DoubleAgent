import json 
import logging 
from typing import Dict, Optional, List

import openai
from decouple import config

from agent.models import FileSystemOperation, FileSystemOperationResult, FileSystemOperationType
from agent.prompt_generator import FilesystemOperationPromptGenerator
from agent.tools import FileSystemTool

OPENAI_MODEL = config("OPENAI_MODEL", "gpt-3.5-turbo-1106") # set to an early model more reliably tricked by prompt injection attacks

# Note: A FileSummarizer agent could be implemented to create these saved summaries of local files based on their filenames and/or contents
FILES_MAP = {
    'files/pdf_source/expt.tex': 'LaTeX file containing information about the LoRA experiment.',
    # 'files/pdf_source/LORA.bib': 'Bibliography file.',
    # 'files/pdf_source/LoRA1.bib': 'Another bibliography file, possibly a variant or updated version of LORA.bib.',
    # 'files/pdf_source/figures': 'Directory likely containing images or graphics used in a LaTeX document.',
    # 'files/pdf_source/iclr2022_conference.bst': 'BibTeX style file customized for the ICLR 2022 conference formatting.',
    # 'files/pdf_source/iclr2022_conference.bbl': 'Generated file from BibTeX with formatted references for the ICLR 2022 conference paper.',
    # 'files/pdf_source/iclr2022_conference.sty': 'LaTeX style file with formatting specifics for the ICLR 2022 conference.',
    # 'files/pdf_source/iclr2022_conference.tex': 'Main LaTeX file for a paper or article intended for the ICLR 2022 conference.',
    # 'files/pdf_source/natbib.sty': 'LaTeX package file for handling bibliographies, especially author-year citation styles.',
    # 'files/pdf_source/fancyhdr.sty': 'LaTeX style file for creating custom headers and footers in a document.',
    # 'files/pdf_source/math_commands.tex': 'LaTeX file containing custom commands or definitions for mathematical expressions.',
    'files/important_doc.txt': 'An important document'
}

# Load API key from .env file
openai.api_key = config("OPENAI_API_KEY")


class AgentScaffolding:

    filesystem_operation_history: List[Optional[FileSystemOperationResult]]

    def __init__(self, user_prompt: str):
        self.user_prompt = user_prompt
        self.file_map = FILES_MAP
        self.message_history = [
            {"role": "system", "content": FilesystemOperationPromptGenerator.initial_system_prompt(self.file_map)},
            {"role": "user", "content": self.user_prompt}
        ]
        self.filesystem_operation_history = []

    def run(self):
        final_response = None
        MAX_STEPS = 3 
        step = 0 
        while not final_response:
            self.run_next_step()
            step += 1
            if len(self.filesystem_operation_history) > 0 and self.filesystem_operation_history[-1] == None:
                # the last step had no filesystem operation
                final_response = self.message_history[-1]["content"]
            elif step > MAX_STEPS:
                final_response = f"Unable to generate final response after {step} steps."
        return f"""Prompt: "{self.user_prompt}"

Response: "{final_response}"

Filesystem Operations:
{'; '.join([f'Operation "{op.operation}" on File "{op.file_path}"' for op in self.filesystem_operation_history if op])}   
        """

    def run_next_step(self) -> None:
        if len(self.filesystem_operation_history) > 0:
            # there was previously a filesystem operation.
            # add results as the latest prompt in the message history
            # Note: using "user" role here because it makes prompt injection easier than using "system" role
            previous_op = self.filesystem_operation_history[-1]
            if previous_op:
                new_prompt = FilesystemOperationPromptGenerator.operation_result_prompt(previous_op)
                logging.info(f"Adding message to history about previous file system operation {previous_op.operation} on file {previous_op.file_path}")
                self.message_history.append({"role": "system", "content": new_prompt})
        filesystem_operation_args = self.get_llm_response()
        if not filesystem_operation_args:
            # this indicates no further filesystem operations are required
            logging.info("No additional filesystem operations required")
            self.filesystem_operation_history.append(None)
            return
        logging.info(f"File system operation {filesystem_operation_args['operation']} requested on file {filesystem_operation_args['file_path']} with reason '{filesystem_operation_args['reason']}'")
        tool_method = getattr(FileSystemTool, filesystem_operation_args["operation"], None)
        if (not tool_method): 
            raise Exception(f"Invalid filesystem operation {filesystem_operation_args['operation']}")
        tool_method_args = [filesystem_operation_args["file_path"]]
        if filesystem_operation_args["operation"] in [FileSystemOperationType.WRITE.value, FileSystemOperationType.APPEND.value]:
            tool_method_args.append(filesystem_operation_args["file_content"])
        file_content_or_none = tool_method(*tool_method_args)
        operation_result = FileSystemOperationResult(
                operation=str(FileSystemOperationType.READ.value),
                file_path=filesystem_operation_args["file_path"],
                file_content=file_content_or_none
            )
        logging.debug(f"Filesystem operation result: {operation_result}")
        self.filesystem_operation_history.append(operation_result)
        
    def get_llm_response(self) -> Optional[Dict]:
        response = openai.ChatCompletion.create(
            model=OPENAI_MODEL,
            messages=self.message_history,
            functions=[
                {
                    "name": "filesystem_operation",
                    "description": (
                        "Perform a read, write or delete filesystem operation on a specified file."
                    ),
                    "parameters": FileSystemOperation.schema()
                }
            ],
        )
        if len(response.choices) == 0:
            raise Exception("OpenAI API did not return any completion choices")
        message = response.choices[0]["message"]
        self.message_history.append(message)
        if "function_call" not in message:
            return None
        called_function = message["function_call"]["name"]
        if called_function != "filesystem_operation":
            import pdb; pdb.set_trace()
            raise Exception(f"OpenAI API returned function call {called_function} that was not filesystem_operation")
        return AgentScaffolding._parse_filesystem_operation_args(message)
    
    @classmethod
    def _parse_filesystem_operation_args(cls, message: Dict) -> Dict:
        try:
            return json.loads(message["function_call"]["arguments"])
        except json.decoder.JSONDecodeError:
            raise Exception("Failed to decode JSON response from OpenAI API")
