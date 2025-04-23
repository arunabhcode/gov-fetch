import requests
import os
from uagents import Agent, Context
from txtai.pipeline import Textractor

from custom_types import ScrapedData, TriggerScrape


# Define the Scraper Agent
class ScraperAgent(Agent):
    def __init__(self, name: str, seed: str, preprocessor_address: str):
        super().__init__(name=name, seed=seed)
        self._preprocessor_address = preprocessor_address
        # Initialize Textractor (assuming default settings)
        self._textractor = Textractor()
        self.on_message(model=TriggerScrape, replies=None)(self.handle_trigger)

    async def handle_trigger(self, ctx: Context, sender: str, msg: TriggerScrape):
        if msg.trigger:
            ctx.logger.info(
                f"Received trigger signal from {sender}. Starting fetch and extract."
            )
            await self.fetch_and_extract(msg.url, ctx)  # Call the existing logic
        else:
            ctx.logger.warning(
                f"Received non-true trigger signal from {sender}. Ignoring."
            )

    # This method is now called by handle_trigger, not by an interval
    async def fetch_and_extract(self, url: str, ctx: Context):
        ctx.logger.info(f"Fetching content from {url}")
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()  # Raise an exception for bad status codes
            # ctx.logger.info(f"Response: {response.text}")
            extracted_text = self._textractor(response.text)

            if extracted_text:
                ctx.logger.info("Successfully extracted text.")
                # Send the extracted text to the Preprocessor Agent
                await ctx.send(
                    self._preprocessor_address, ScrapedData(text=extracted_text)
                )
                ctx.logger.info(f"Sent extracted text to {self._preprocessor_address}")
            else:
                ctx.logger.warning("No text extracted.")

        except requests.exceptions.RequestException as e:
            ctx.logger.error(f"Error fetching URL {self._target_url}: {e}")
        except Exception as e:
            ctx.logger.error(f"Error during text extraction: {e}")


# Example Usage (if run directly, replace with actual setup in main.py)
if __name__ == "__main__":
    SCRAPER_SEED = os.getenv("SCRAPER_SEED", "scraper_secret_phrase")
    PREPROCESSOR_ADDRESS = "agent1..."  # Replace with actual preprocessor agent address

    agent = ScraperAgent(
        name="scraper_agent",
        seed=SCRAPER_SEED,
        target_url="https://travel.state.gov/content/travel/en/legal/visa-law0/visa-bulletin/2025/visa-bulletin-for-may-2025.html",  # Example URL
        preprocessor_address=PREPROCESSOR_ADDRESS,
    )
    agent.run()
