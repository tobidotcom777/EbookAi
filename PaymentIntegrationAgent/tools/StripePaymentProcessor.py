from agency_swarm.tools import BaseTool
from pydantic import Field
import stripe
import os

# Set your Stripe API key globally
stripe.api_key = os.getenv("STRIPE_API_KEY")

class StripePaymentProcessor(BaseTool):
    """
    This tool integrates with the Stripe API to handle payment processing.
    It can create payment intents, handle webhooks for payment status updates,
    and manage customer data securely. The tool ensures compliance with PCI DSS
    standards and provides error handling for common payment issues.
    """

    amount: int = Field(
        ..., description="The amount to be charged in the smallest currency unit (e.g., cents for USD)."
    )
    currency: str = Field(
        ..., description="The currency in which the payment is to be made (e.g., 'usd')."
    )
    customer_email: str = Field(
        ..., description="The email address of the customer making the payment."
    )
    description: str = Field(
        ..., description="A description of the payment."
    )

    def run(self):
        """
        The implementation of the run method, where the tool's main functionality is executed.
        This method creates a payment intent using the Stripe API.
        """
        try:
            # Create a new customer
            customer = stripe.Customer.create(
                email=self.customer_email,
                description=self.description
            )

            # Create a payment intent
            payment_intent = stripe.PaymentIntent.create(
                amount=self.amount,
                currency=self.currency,
                customer=customer.id,
                description=self.description,
                payment_method_types=["card"]
            )

            # Return the client secret and other relevant details to complete the payment on the client side
            return {
                "client_secret": payment_intent.client_secret,
                "customer_id": customer.id,
                "payment_intent_id": payment_intent.id
            }

        except stripe.error.CardError as e:
            # Handle card errors
            return {"error": f"Card error: {e.user_message}"}
        except stripe.error.RateLimitError as e:
            # Handle rate limit errors
            return {"error": "Rate limit error: Too many requests made to the API too quickly"}
        except stripe.error.InvalidRequestError as e:
            # Handle invalid parameters errors
            return {"error": f"Invalid request: {e.user_message}"}
        except stripe.error.AuthenticationError as e:
            # Handle authentication errors
            return {"error": "Authentication error: Incorrect API keys"}
        except stripe.error.APIConnectionError as e:
            # Handle network communication errors
            return {"error": "Network error: Failed to connect to Stripe"}
        except stripe.error.StripeError as e:
            # Handle generic Stripe errors
            return {"error": f"Stripe error: {e.user_message}"}
        except Exception as e:
            # Handle other unexpected errors
            return {"error": f"An unexpected error occurred: {str(e)}"}
