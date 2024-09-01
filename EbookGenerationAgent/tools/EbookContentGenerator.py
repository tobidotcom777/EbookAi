from agency_swarm.agents import Agent
from agency_swarm.tools import BaseTool
from pydantic import Field
import os
from openai import OpenAI

# Instantiate the OpenAI client
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")  # The API key is retrieved from the environment variable
)

class EbookContentGenerator(BaseTool):
    """
    This tool generates engaging ebook content based on a given topic or outline.
    It structures the content into chapters, sections, and paragraphs, ensuring coherence
    and readability. The tool also allows for customization of writing style and tone.
    """

    topic: str = Field(
        ..., description="The main topic or outline for the ebook content."
    )
    chapters: int = Field(
        ..., description="The number of chapters to generate."
    )
    sections_per_chapter: int = Field(
        ..., description="The number of sections per chapter."
    )
    paragraphs_per_section: int = Field(
        ..., description="The number of paragraphs per section."
    )
    writing_style: str = Field(
        ..., description="The desired writing style (e.g., 'formal', 'informal', 'technical')."
    )
    tone: str = Field(
        ..., description="The desired tone (e.g., 'serious', 'humorous', 'inspirational')."
    )

    def run(self):
        """
        The implementation of the run method, where the tool's main functionality is executed.
        This method generates the ebook content based on the provided parameters.
        """
        ebook_content = f"Title: {self.topic}\n\n"
        
        for chapter_num in range(1, self.chapters + 1):
            ebook_content += f"Chapter {chapter_num}: {self.topic} - Part {chapter_num}\n\n"
            
            for section_num in range(1, self.sections_per_chapter + 1):
                ebook_content += f"Section {chapter_num}.{section_num}: {self.topic} - Section {section_num}\n\n"
                
                for paragraph_num in range(1, self.paragraphs_per_section + 1):
                    prompt = (
                        f"Write a {self.writing_style} and {self.tone} paragraph about {self.topic} "
                        f"for Chapter {chapter_num}, Section {section_num}, Paragraph {paragraph_num}."
                    )
                    
                    # Generate text using the OpenAI chat completion API
                    response = client.chat.completions.create(
                        model="gpt-4",  # You can adjust the model as needed
                        messages=[
                            {"role": "system", "content": "You are a helpful assistant."},
                            {"role": "user", "content": prompt}
                        ],
                        max_tokens=150,
                        temperature=0.7
                    )
                    generated_text = response.choices[0].message.content.strip()
                    ebook_content += f"{generated_text}\n\n"
        
        return ebook_content


class EbookGenerationAgent(Agent):
    def __init__(self, **kwargs):
        super().__init__(
            name="EbookGenerationAgent",
            description="This agent generates engaging ebook content.",
            instructions="./instructions.md",
            files_folder="./files",
            schemas_folder="./schemas",
            tools=[EbookContentGenerator],
            tools_folder="./tools",
            **kwargs
        )

    def response_validator(self, message):
        return message

    # Additional methods for further functionality can be added here.


if __name__ == "__main__":
    tool = EbookContentGenerator(
        topic="The Future of AI",
        chapters=3,
        sections_per_chapter=2,
        paragraphs_per_section=3,
        writing_style="formal",
        tone="inspirational"
    )
    content = tool.run()
    print("Ebook content generated:")
    print(content)
