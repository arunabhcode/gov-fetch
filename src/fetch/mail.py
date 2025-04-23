from uagents import Agent, Context, Model
import os
import requests
import datetime

# Import the disable model from controller
from controller import DisableTrigger


# Define the message model for Q&A results (from QandAAgent)
class QAResult(Model):
    prompt: str
    answer: str


# Define the Mail Agent
class MailAgent(Agent):
    def __init__(
        self,
        name: str,
        seed: str,
        recipients: list[str],
        mailgun_api_key: str,
        mailgun_domain: str,
        controller_address: str,
    ):
        super().__init__(name=name, seed=seed)
        self._recipients = recipients
        self._mailgun_api_key = mailgun_api_key
        self._mailgun_domain = mailgun_domain
        self._controller_address = controller_address
        self._mailgun_url = (
            f"https://api.mailgun.net/v3/{self._mailgun_domain}/messages"
        )
        self.on_message(model=QAResult)(self.handle_qa_result)

    async def handle_qa_result(self, ctx: Context, sender: str, msg: QAResult):
        ctx.logger.info(f"Received Q&A result from {sender}. Preparing email.")

        # Format Subject
        now = datetime.datetime.now()
        subject = f"Visa Bulletin Update - {now.strftime('%B %Y')}"

        # Format Body (simple example, can be enhanced with HTML)
        body = f"""Hello,

Here is the latest update based on the Visa Bulletin query:

--- Prompt ---
{msg.prompt}

--- Answer ---
{msg.answer}

Regards,
GovFetch Agent
"""

        # Send email via Mailgun
        try:
            response = requests.post(
                self._mailgun_url,
                auth=("api", self._mailgun_api_key),
                data={
                    "from": f"GovFetch Agent <mailgun@{self._mailgun_domain}>",
                    "to": self._recipients,  # Send to the list of recipients
                    "subject": subject,
                    "text": body,
                },
                timeout=30,
            )
            response.raise_for_status()  # Raise an exception for bad status codes
            ctx.logger.info(
                f"Successfully sent email to {len(self._recipients)} recipients via Mailgun."
            )
            # Send disable signal to Controller Agent
            await self.send_disable_signal(ctx)
        except requests.exceptions.RequestException as e:
            ctx.logger.error(f"Mailgun API error: {e}")
            if e.response is not None:
                ctx.logger.error(f"Mailgun response: {e.response.text}")
        except Exception as e:
            ctx.logger.error(f"Error sending email: {e}")

    async def send_disable_signal(self, ctx: Context):
        """Sends the DisableTrigger message to the controller agent."""
        if not self._controller_address:
            ctx.logger.warning(
                "Controller address not set, cannot send disable signal."
            )
            return
        try:
            await ctx.send(self._controller_address, DisableTrigger(disable=True))
            ctx.logger.info(
                f"Sent DisableTrigger to controller {self._controller_address}"
            )
        except Exception as e:
            ctx.logger.error(
                f"Failed to send DisableTrigger to controller {self._controller_address}: {e}"
            )


# Example Usage (if run directly, replace with actual setup in main.py)
if __name__ == "__main__":
    MAIL_SEED = os.getenv("MAIL_SEED", "mail_secret_phrase")
    MAILGUN_API_KEY = os.getenv("MAILGUN_API_KEY")
    MAILGUN_DOMAIN = os.getenv("MAILGUN_DOMAIN")
    RECIPIENT_EMAILS = os.getenv("RECIPIENT_EMAILS", "test@example.com").split(
        ","
    )  # Comma-separated list

    if not MAILGUN_API_KEY or not MAILGUN_DOMAIN:
        print(
            "Error: MAILGUN_API_KEY and MAILGUN_DOMAIN environment variables must be set."
        )
        exit(1)

    agent = MailAgent(
        name="mail_agent",
        seed=MAIL_SEED,
        recipients=RECIPIENT_EMAILS,
        mailgun_api_key=MAILGUN_API_KEY,
        mailgun_domain=MAILGUN_DOMAIN,
        controller_address="agent_controller_address...",  # Example placeholder
    )

    # Expose the agent's endpoint for the QandAAgent
    print(f"Mail Agent Address: {agent.address}")

    agent.run()
