import os
from uagents import Bureau

from config_loader import EnvLoader
from scrape import ScraperAgent, ScrapedData
from preprocessor import PreprocessorAgent, ProcessedData
from rag import QandAAgent, QAResult
from mail import MailAgent
from controller import ControllerAgent


if not EnvLoader.load_and_check():
    print("Error: Failed to load environment variables.")
    exit(1)


mail_agent = MailAgent(
    name="mail",
    seed=os.getenv("MAIL_SEED"),
    recipients=os.getenv("RECIPIENT_EMAILS").split(","),
    mailgun_api_key=os.getenv("MAILGUN_API_KEY"),
    mailgun_domain=os.getenv("MAILGUN_DOMAIN"),
    controller_address="",  # Placeholder
)

qna_agent = QandAAgent(
    name="qna",
    seed=os.getenv("QNA_SEED"),
    mail_address=mail_agent.address,
    keyword=os.getenv("SEARCH_KEYWORD"),
    ollama_model=os.getenv("OLLAMA_MODEL"),
)

# Create agents first to get their addresses
preprocessor_agent = PreprocessorAgent(
    name="preprocessor",
    seed=os.getenv("PREPROCESSOR_SEED"),
    qna_address=qna_agent.address,
)


scraper_agent = ScraperAgent(
    name="scraper",
    seed=os.getenv("SCRAPER_SEED"),
    preprocessor_address=preprocessor_agent.address,  # This is okay, preprocessor is already created
)

# Instantiate agents first
controller_agent = ControllerAgent(
    name="controller",
    seed=os.getenv("CONTROLLER_SEED"),
    scraper_address=scraper_agent.address,
)

# Now set the dependent addresses
mail_agent._controller_address = controller_agent.address

print("Setting up Bureau...")
bureau = Bureau()
bureau.add(controller_agent)
bureau.add(scraper_agent)
bureau.add(preprocessor_agent)
bureau.add(qna_agent)
bureau.add(mail_agent)

print("Agents added to Bureau:")
print(f"- Scraper: {scraper_agent.address}")
print(f"- Preprocessor: {preprocessor_agent.address}")
print(f"- QnA: {qna_agent.address}")
print(f"- Mail: {mail_agent.address}")
print(f"- Controller: {controller_agent.address}")

print("Starting Bureau...")
bureau.run()
