import requests

# from bs4 import BeautifulSoup
from txtai.pipeline import Textractor
from uagents import Agent, Context, Model, Protocol
import os


# Define the message model for scraped text
class ScrapedData(Model):
    text: str


# Define the protocol for scraping
scrape_proto = Protocol("Scrape")


# Define the Scraper Agent
class ScraperAgent(Agent):
    def __init__(
        self, name: str, seed: str, target_url: str, preprocessor_address: str
    ):
        super().__init__(name=name, seed=seed)
        self._target_url = target_url
        self._preprocessor_address = preprocessor_address
        # Initialize Textractor (assuming default settings)
        self._textractor = Textractor()

    @scrape_proto.on_interval(period=3600.0)  # Run once per hour, adjust as needed
    async def fetch_and_extract(self, ctx: Context):
        ctx.logger.info(f"Fetching content from {self._target_url}")
        try:
            response = requests.get(self._target_url, timeout=30)
            response.raise_for_status()  # Raise an exception for bad status codes

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
        target_url="https://travel.state.gov/content/travel/en/legal/visa-law0/visa-bulletin.html",  # Example URL
        preprocessor_address=PREPROCESSOR_ADDRESS,
    )
    agent.run()
