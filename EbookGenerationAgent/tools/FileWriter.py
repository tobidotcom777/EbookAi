from typing import List, Literal, Optional
import os
import re
from pydantic import Field, field_validator
from agency_swarm.tools import BaseTool
from agency_swarm import get_openai_client
from agency_swarm.util.validators import llm_validator
from .util import format_file_deps

class FileWriter(BaseTool):
    """
    This tool allows you to write new files or modify existing files according to specified requirements.
    In 'write' mode, it creates a new file or overwrites an existing one.
    In 'modify' mode, it modifies an existing file according to the provided requirements.
    """
    file_path: str = Field(
        ..., description="The path of the file to write or modify. Will create directories if they don't exist."
    )
    requirements: str = Field(
        ...,
        description="The comprehensive requirements explaining how the file should be written or modified. This should be a detailed description of what the file should contain, including example inputs, desired behaviour, and ideal outputs. It must not contain any code or implementation details."
    )
    details: Optional[str] = Field(
        None, description="Additional details like error messages, or class, function, and variable names from other files that this file depends on."
    )
    documentation: Optional[str] = Field(
        None, description="Relevant documentation extracted with the myfiles_browser tool. You must pass all the relevant code from the documentation, as this tool does not have access to those files."
    )
    mode: Literal["write", "modify"] = Field(
        ..., description="The mode of operation for the tool. 'write' is used to create a new file or overwrite an existing one. 'modify' is used to modify an existing file."
    )
    file_dependencies: List[str] = Field(
        [],
        description="Paths to other files that the file being written depends on.",
        examples=["/path/to/dependency1.py", "/path/to/dependency2.css", "/path/to/dependency3.js"]
    )
    library_dependencies: List[str] = Field(
        [],
        description="Any library dependencies required for the file to be written.",
        examples=["numpy", "pandas"]
    )

    class ToolConfig:
        one_call_at_a_time = True

    def run(self):
        client = get_openai_client()

        file_dependencies = format_file_deps(self.file_dependencies)
        library_dependencies = ", ".join(self.library_dependencies)
        filename = os.path.basename(self.file_path)

        if self.mode == "write":
            message = f"Please write {filename} file that meets the following requirements: '{self.requirements}'.\n"
        else:
            message = f"Please rewrite the {filename} file according to the following requirements: '{self.requirements}'.\n"

        if file_dependencies:
            message += f"\nHere are the dependencies from other project files: {file_dependencies}."
        if library_dependencies:
            message += f"\nUse the following libraries: {library_dependencies}"
        if self.details:
            message += f"\nAdditional Details: {self.details}"
        if self.documentation:
            message += f"\nDocumentation: {self.documentation}"

        if self.mode == "modify":
            message += f"\nThe existing file content is as follows:"

            try:
                with open(self.file_path, 'r') as file:
                    prev_content = file.read()
                    message += f"\n\n```{prev_content}```"
            except Exception as e:
                return f'Error reading {self.file_path}: {e}'

        # API call without unsupported parameters
        try:
            response = client.chat.completions.create(
                model="gpt-4",  # Ensure using a valid model
                messages=[{"role": "system", "content": "You are a helpful assistant."}, {"role": "user", "content": message}],
                max_tokens=1500,  # Adjust token limit as needed
                temperature=0.5,
            )
            content = response.choices[0].message.content

            # Extract code from the response
            code = self.extract_code(content)
            if not code:
                raise ValueError("Error: Could not find the code block in the response.")

            # Write the code to the specified file path
            self.write_to_file(code)

            return f'Successfully wrote to file: {self.file_path}. Please make sure to now test the program. Below is the content of the file:\n\n```{content}```\n\nPlease now verify the integrity of the file and test it.'

        except Exception as e:
            return f"Error: {e}"

    def extract_code(self, content: str) -> str:
        """Extract code from the assistant's response."""
        pattern = r"```(?:[a-zA-Z]+\n)?(.*?)```"
        match = re.findall(pattern, content, re.DOTALL)
        if match:
            return match[-1].strip()
        return ""

    def write_to_file(self, code: str):
        """Write code to the specified file path, creating directories if necessary."""
        try:
            dir_path = os.path.dirname(self.file_path)
            if dir_path and not os.path.exists(dir_path):
                os.makedirs(dir_path, exist_ok=True)

            with open(self.file_path, 'w') as file:
                file.write(code)
        except Exception as e:
            raise IOError(f"Error writing to file: {e}")

    @field_validator("file_dependencies", mode="after")
    @classmethod
    def validate_file_dependencies(cls, v):
        for file in v:
            if not os.path.exists(file):
                raise ValueError(f"File dependency '{file}' does not exist.")
        return v

    @field_validator("requirements", mode="after")
    @classmethod
    def validate_requirements(cls, v):
        if "placeholder" in v:
            raise ValueError("Requirements contain placeholders. Please never use placeholders. Instead, implement only the code that you are confident about.")

        # check if code is included in requirements
        pattern = r'(```)((.*\n){5,})(```)'
        if re.search(pattern, v):
            raise ValueError(
                "Requirements contain a code snippet. Please never include code snippets in requirements. "
                "Requirements must be a description of the complete file to be written. You can include specific class, function, and variable names, but not the actual code."
            )

        return v

    @field_validator("details", mode="after")
    @classmethod
    def validate_details(cls, v):
        if len(v) == 0:
            raise ValueError("Details are required. Remember: this tool does not have access to other files. Please provide additional details like relevant documentation, error messages, or class, function, and variable names from other files that this file depends on.")
        return v

    @field_validator("documentation", mode="after")
    @classmethod
    def validate_documentation(cls, v):
        # check if documentation contains code
        pattern = r'(```)((.*\n){5,})(```)'
        pattern2 = r'(`)(.*)(`)'
        if not (re.search(pattern, v) or re.search(pattern2, v)):
            raise ValueError(
                "Documentation does not contain a code snippet. Please provide relevant documentation extracted with the myfiles_browser tool. You must pass all the relevant code snippets information, as this tool does not have access to those files."
            )

if __name__ == "__main__":
    tool = FileWriter(
        requirements="Write a program that takes a list of integers as input and returns the sum of all the integers in the list.",
        mode="write",
        file_path="test.py",
    )
    print(tool.run())
