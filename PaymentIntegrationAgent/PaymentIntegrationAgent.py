from agency_swarm.agents import Agent


class PaymentIntegrationAgent(Agent):
    def __init__(self):
        super().__init__(
            name="PaymentIntegrationAgent",
            description="The PaymentIntegrationAgent is responsible for securely integrating the Stripe API to handle payment processing and ensure seamless ebook delivery within the EbookAutomationAgency.",
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
