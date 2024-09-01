from agency_swarm.agents import Agent  # Import the Agent class
from agency_swarm.tools import BaseTool
from pydantic import Field
import requests
import os

class EbookCoverGenerator(BaseTool):
    """
    This tool generates an ebook cover image using a prompt.
    It fetches the generated image and saves it locally under a specified directory.
    """
    
    prompt: str = Field(
        ..., description="A text description of the desired ebook cover image."
    )
    output_directory: str = Field(
        "EbookAutomationAgency/EbookGenerationAgent/files", description="Directory to save the generated cover image."
    )
    
    def run(self):
        """
        Generates an ebook cover image based on the provided prompt and saves it locally.
        """
        # Simulate image generation (replace this part with actual API call to generate an image)
        api_url = "https://api.example.com/v1/images/generate"  # Placeholder API URL
        headers = {
            "Authorization": "Bearer YOUR_API_KEY",  # Replace with your actual API key
            "Content-Type": "application/json"
        }
        data = {
            "prompt": self.prompt,
            "n": 1,
            "size": "1024x1024"
        }

        # Example of how to call an image generation API (DALL-E or similar)
        response = requests.post(api_url, headers=headers, json=data)

        if response.status_code == 200:
            image_url = response.json().get("data", [])[0].get("url")
            image_response = requests.get(image_url)
            if image_response.status_code == 200:
                # Ensure the output directory exists
                os.makedirs(self.output_directory, exist_ok=True)

                # Define the path to save the image
                image_path = os.path.join(self.output_directory, "cover_image.jpg")
                
                # Save the image locally
                with open(image_path, "wb") as img_file:
                    img_file.write(image_response.content)
                
                return f"Cover image generated and saved to: {image_path}"
            else:
                return f"Failed to download the generated image: {image_response.status_code} - {image_response.text}"
        else:
            return f"Failed to generate ebook cover: {response.status_code} - {response.text}"

class EbookCoverGenerationAgent(Agent):
    def __init__(self, **kwargs):
        super().__init__(
            name="EbookCoverGenerationAgent",
            description="This agent generates ebook covers based on a text prompt.",
            instructions="./instructions.md",
            files_folder="./files",
            schemas_folder="./schemas",
            tools=[EbookCoverGenerator],
            tools_folder="./tools",
            **kwargs
        )

    def response_validator(self, message):
        return message
