from agency_swarm.agents import Agent
from agency_swarm.tools import BaseTool
from pydantic import Field
import os
from openai import OpenAI
import requests
from fpdf import FPDF

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
        Generates the ebook content based on the provided parameters.
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
                        model="gpt-4",
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

class EbookCoverGenerator(BaseTool):
    """
    This tool generates an ebook cover using the DALL·E 3 image generation API.
    It takes a prompt describing the desired cover and allows customization of
    image quality, size, and style.
    """

    prompt: str = Field(
        ..., description="A text description of the desired ebook cover image."
    )
    quality: str = Field(
        "standard", description="The quality of the image. Options: 'standard', 'hd'."
    )
    size: str = Field(
        "1024x1024", description="The size of the generated image. Options: '1024x1024', '1792x1024', '1024x1792'."
    )
    style: str = Field(
        "vivid", description="The style of the generated image. Options: 'vivid', 'natural'."
    )

    def run(self):
        """
        Generates an ebook cover image using the provided prompt and specified
        quality, size, and style parameters.
        """
        api_url = "https://api.openai.com/v1/images/generations"
        headers = {
            "Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}",
            "Content-Type": "application/json"
        }
        data = {
            "model": "dall-e-3",
            "prompt": self.prompt,
            "n": 1,
            "quality": self.quality,
            "size": self.size,
            "style": self.style,
            "response_format": "url"
        }

        response = requests.post(api_url, headers=headers, json=data)

        if response.status_code == 200:
            image_url = response.json().get("data", [])[0].get("url")
            return image_url
        else:
            raise Exception(f"Failed to generate ebook cover: {response.status_code} - {response.text}")

class EbookPDFGenerator(BaseTool):
    """
    This tool generates a well-formatted PDF ebook using the provided cover image
    and content. It structures the content into chapters and sections and includes
    the cover image as the first page of the ebook.
    """

    cover_image_url: str = Field(
        ..., description="URL of the cover image to be included in the ebook."
    )
    content: str = Field(
        ..., description="The content of the ebook, including chapters, sections, and paragraphs."
    )
    output_filename: str = Field(
        "ebook.pdf", description="The name of the output PDF file."
    )

    def run(self):
        """
        Generates a PDF ebook with the provided cover image and content.
        """
        # Fetch the cover image from the provided URL
        cover_image_filename = "cover_image.jpg"
        try:
            response = requests.get(self.cover_image_url)
            if response.status_code == 200:
                with open(cover_image_filename, 'wb') as img_file:
                    img_file.write(response.content)
            else:
                raise Exception(f"Failed to fetch the cover image: {response.status_code} - {response.text}")
        except Exception as e:
            raise Exception(f"Error occurred while fetching the cover image: {str(e)}")
        
        # Initialize the PDF
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)

        # Add cover page
        pdf.add_page()
        pdf.image(cover_image_filename, x=10, y=10, w=pdf.w - 20)

        # Add title page
        pdf.add_page()
        pdf.set_font("Arial", size=24)
        pdf.multi_cell(0, 10, self.content.split('\n')[0], align="C")  # Title from content
        
        # Add content pages
        pdf.set_font("Arial", size=12)
        content_lines = self.content.split('\n')
        for line in content_lines[1:]:
            if line.startswith("Chapter"):
                pdf.add_page()
                pdf.set_font("Arial", size=18, style='B')
                pdf.cell(0, 10, line, ln=True)
                pdf.set_font("Arial", size=12)
            elif line.startswith("Section"):
                pdf.set_font("Arial", size=14, style='B')
                pdf.cell(0, 10, line, ln=True)
                pdf.set_font("Arial", size=12)
            else:
                pdf.multi_cell(0, 10, line)
        
        # Save the PDF to the specified output file
        try:
            pdf.output(self.output_filename)
            return f"PDF ebook generated successfully: {self.output_filename}"
        except Exception as e:
            raise Exception(f"Failed to generate PDF ebook: {str(e)}")

class EbookGenerationAgent(Agent):
    def __init__(self, **kwargs):
        super().__init__(
            name="EbookGenerationAgent",
            description="This agent generates engaging ebook content, designs ebook covers, and compiles them into a well-formatted PDF.",
            instructions="./instructions.md",
            files_folder="./files",
            schemas_folder="./schemas",
            tools=[EbookContentGenerator, EbookCoverGenerator, EbookPDFGenerator],
            tools_folder="./tools",
            **kwargs
        )

    def create_ebook(self, topic, chapters, sections_per_chapter, paragraphs_per_section, writing_style, tone):
        """
        Orchestrates the generation of the entire ebook including content, cover, and PDF compilation.
        """
        # Step 1: Generate the ebook content
        content_tool = EbookContentGenerator(
            topic=topic,
            chapters=chapters,
            sections_per_chapter=sections_per_chapter,
            paragraphs_per_section=paragraphs_per_section,
            writing_style=writing_style,
            tone=tone
        )
        content = content_tool.run()
        
        # Step 2: Generate the ebook cover
        cover_tool = EbookCoverGenerator(
            prompt=f"A beautiful cover for an ebook titled '{topic}', designed with a {tone} tone.",
            quality="hd",
            size="1024x1024",
            style="vivid"
        )
        cover_image_url = cover_tool.run()
        
        # Step 3: Compile the content and cover into a PDF
        pdf_tool = EbookPDFGenerator(
            cover_image_url=cover_image_url,
            content=content,
            output_filename="final_ebook.pdf"
        )
        pdf_result = pdf_tool.run()
        
        return pdf_result

    def response_validator(self, message):
        return message

if __name__ == "__main__":
    agent = EbookGenerationAgent()
    pdf_path = agent.create_ebook(
        topic="The Future of AI",
        chapters=3,
        sections_per_chapter=2,
        paragraphs_per_section=3,
        writing_style="formal",
        tone="inspirational"
    )
    print(f"Ebook generated and saved to: {pdf_path}")
