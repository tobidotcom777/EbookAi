from agency_swarm.agents import Agent


class AdsSetupAgent(Agent):
    def __init__(self):
        super().__init__(
            name="AdsSetupAgent",
            description="The AdsSetupAgent is responsible for implementing Google Ads using the Google Ads API to effectively market the ebook within the EbookAutomationAgency.",
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
