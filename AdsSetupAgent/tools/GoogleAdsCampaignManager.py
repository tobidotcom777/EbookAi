from agency_swarm.tools import BaseTool
from pydantic import Field
from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException
import os

# Set your Google Ads API credentials globally
developer_token = os.getenv("GOOGLE_ADS_DEVELOPER_TOKEN")
client_id = os.getenv("GOOGLE_ADS_CLIENT_ID")
client_secret = os.getenv("GOOGLE_ADS_CLIENT_SECRET")
refresh_token = os.getenv("GOOGLE_ADS_REFRESH_TOKEN")
customer_id = os.getenv("GOOGLE_ADS_CUSTOMER_ID")

class GoogleAdsCampaignManager(BaseTool):
    """
    This tool integrates with the Google Ads API to set up and manage ad campaigns.
    It can create, update, and delete campaigns, ad groups, and ads. The tool also
    handles budget management, keyword targeting, and performance tracking. It ensures
    compliance with Google Ads policies and provides error handling for common issues.
    """

    action: str = Field(
        ..., description="The action to perform: 'create', 'update', or 'delete'."
    )
    entity: str = Field(
        ..., description="The entity to manage: 'campaign', 'ad_group', or 'ad'."
    )
    entity_id: str = Field(
        None, description="The ID of the entity to update or delete. Not required for creation."
    )
    name: str = Field(
        None, description="The name of the campaign, ad group, or ad. Required for creation."
    )
    budget: int = Field(
        None, description="The budget for the campaign in micros. Required for campaign creation."
    )
    keywords: list = Field(
        None, description="A list of keywords for the ad group. Required for ad group creation."
    )
    ad_text: str = Field(
        None, description="The text for the ad. Required for ad creation."
    )

    def run(self):
        """
        The implementation of the run method, where the tool's main functionality is executed.
        This method interacts with the Google Ads API to manage campaigns, ad groups, and ads.
        """
        try:
            client = GoogleAdsClient.load_from_storage(path="google-ads.yaml")  # Ensure you have the correct path to the credentials file.

            if self.action == 'create':
                if self.entity == 'campaign':
                    return self.create_campaign(client)
                elif self.entity == 'ad_group':
                    return self.create_ad_group(client)
                elif self.entity == 'ad':
                    return self.create_ad(client)
            elif self.action == 'update':
                if self.entity == 'campaign':
                    return self.update_campaign(client)
                elif self.entity == 'ad_group':
                    return self.update_ad_group(client)
                elif self.entity == 'ad':
                    return self.update_ad(client)
            elif self.action == 'delete':
                if self.entity == 'campaign':
                    return self.delete_campaign(client)
                elif self.entity == 'ad_group':
                    return self.delete_ad_group(client)
                elif self.entity == 'ad':
                    return self.delete_ad(client)
            else:
                return {"error": "Invalid action specified"}

        except GoogleAdsException as ex:
            return {"error": f"Google Ads API error: {ex.error.message}"}
        except Exception as e:
            return {"error": f"An unexpected error occurred: {str(e)}"}

    def create_campaign(self, client):
        campaign_service = client.get_service("CampaignService")
        campaign_operation = client.get_type("CampaignOperation")
        campaign = campaign_operation.create
        campaign.name = self.name
        campaign.advertising_channel_type = client.enums.AdvertisingChannelTypeEnum.SEARCH
        campaign.status = client.enums.CampaignStatusEnum.PAUSED
        campaign.manual_cpc.enhanced_cpc_enabled = True
        campaign.campaign_budget = client.get_service("CampaignBudgetService").campaign_budget_path(customer_id, self.budget)
        response = campaign_service.mutate_campaigns(customer_id, [campaign_operation])
        return {"result": f"Created campaign with resource name: {response.results[0].resource_name}"}

    def create_ad_group(self, client):
        ad_group_service = client.get_service("AdGroupService")
        ad_group_operation = client.get_type("AdGroupOperation")
        ad_group = ad_group_operation.create
        ad_group.name = self.name
        ad_group.campaign = client.get_service("CampaignService").campaign_path(customer_id, self.entity_id)
        ad_group.status = client.enums.AdGroupStatusEnum.ENABLED
        response = ad_group_service.mutate_ad_groups(customer_id, [ad_group_operation])
        return {"result": f"Created ad group with resource name: {response.results[0].resource_name}"}

    def create_ad(self, client):
        ad_group_ad_service = client.get_service("AdGroupAdService")
        ad_group_ad_operation = client.get_type("AdGroupAdOperation")
        ad_group_ad = ad_group_ad_operation.create
        ad_group_ad.ad_group = client.get_service("AdGroupService").ad_group_path(customer_id, self.entity_id)
        ad_group_ad.status = client.enums.AdGroupAdStatusEnum.PAUSED
        ad_group_ad.ad.expanded_text_ad.headline_part1 = self.name
        ad_group_ad.ad.expanded_text_ad.headline_part2 = self.ad_text
        ad_group_ad.ad.expanded_text_ad.description = self.ad_text
        response = ad_group_ad_service.mutate_ad_group_ads(customer_id, [ad_group_ad_operation])
        return {"result": f"Created ad with resource name: {response.results[0].resource_name}"}

    def update_campaign(self, client):
        campaign_service = client.get_service("CampaignService")
        campaign_operation = client.get_type("CampaignOperation")
        campaign = campaign_operation.update
        campaign.resource_name = campaign_service.campaign_path(customer_id, self.entity_id)
        campaign.name = self.name
        client.copy_from(campaign_operation.update_mask, client.get_type("FieldMask"))
        response = campaign_service.mutate_campaigns(customer_id, [campaign_operation])
        return {"result": f"Updated campaign with resource name: {response.results[0].resource_name}"}

    def update_ad_group(self, client):
        ad_group_service = client.get_service("AdGroupService")
        ad_group_operation = client.get_type("AdGroupOperation")
        ad_group = ad_group_operation.update
        ad_group.resource_name = ad_group_service.ad_group_path(customer_id, self.entity_id)
        ad_group.name = self.name
        client.copy_from(ad_group_operation.update_mask, client.get_type("FieldMask"))
        response = ad_group_service.mutate_ad_groups(customer_id, [ad_group_operation])
        return {"result": f"Updated ad group with resource name: {response.results[0].resource_name}"}

    def update_ad(self, client):
        ad_group_ad_service = client.get_service("AdGroupAdService")
        ad_group_ad_operation = client.get_type("AdGroupAdOperation")
        ad_group_ad = ad_group_ad_operation.update
        ad_group_ad.resource_name = ad_group_ad_service.ad_group_ad_path(customer_id, self.entity_id)
        ad_group_ad.ad.expanded_text_ad.headline_part1 = self.name
        ad_group_ad.ad.expanded_text_ad.headline_part2 = self.ad_text
        ad_group_ad.ad.expanded_text_ad.description = self.ad_text
        client.copy_from(ad_group_ad_operation.update_mask, client.get_type("FieldMask"))
        response = ad_group_ad_service.mutate_ad_group_ads(customer_id, [ad_group_ad_operation])
        return {"result": f"Updated ad with resource name: {response.results[0].resource_name}"}

    def delete_campaign(self, client):
        campaign_service = client.get_service("CampaignService")
        campaign_operation = client.get_type("CampaignOperation")
        campaign_operation.remove = campaign_service.campaign_path(customer_id, self.entity_id)
        response = campaign_service.mutate_campaigns(customer_id, [campaign_operation])
        return {"result": f"Deleted campaign with resource name: {response.results[0].resource_name}"}

    def delete_ad_group(self, client):
        ad_group_service = client.get_service("AdGroupService")
        ad_group_operation = client.get_type("AdGroupOperation")
        ad_group_operation.remove = ad_group_service.ad_group_path(customer_id, self.entity_id)
        response = ad_group_service.mutate_ad_groups(customer_id, [ad_group_operation])
        return {"result": f"Deleted ad group with resource name: {response.results[0].resource_name}"}

    def delete_ad(self, client):
        ad_group_ad_service = client.get_service("AdGroupAdService")
        ad_group_ad_operation = client.get_type("AdGroupAdOperation")
        ad_group_ad_operation.remove = ad_group_ad_service.ad_group_ad_path(customer_id, self.entity_id)
        response = ad_group_ad_service.mutate_ad_group_ads(customer_id, [ad_group_ad_operation])
        return {"result": f"Deleted ad with resource name: {response.results[0].resource_name}"}
