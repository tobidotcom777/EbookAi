from agency_swarm.agents import Agent


class EbookCEO(Agent):
    def __init__(self):
        super().__init__(
            name="EbookCEO",
            description="The EbookCEO agent oversees the entire ebook automation process and coordinates between agents within the EbookAutomationAgency. It ensures that all tasks are aligned with the agency's goals and are executed efficiently.",
            instructions="./instructions.md",
            files_folder="./files",
            schemas_folder="./schemas",
            tools=[],
            tools_folder="./tools",
            temperature=0.3,
            max_prompt_tokens=25000,
        )
        
    def response_validator(self, message):
        return message
