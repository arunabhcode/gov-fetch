import os
from uagents import Bureau

from config_loader import EnvLoader
from scrape import ScraperAgent, ScrapedData
from preprocessor import PreprocessorAgent, ProcessedData
from rag import QandAAgent, QAResult
from mail import MailAgent


if not EnvLoader.load_and_check():
    print("Error: Failed to load environment variables.")
    exit(1)

# Create agents first to get their addresses
preprocessor_agent = PreprocessorAgent(
    name="preprocessor",
    seed=os.getenv("PREPROCESSOR_SEED"),
    qna_address="",  # Will be set after QnA agent is created
)

qna_agent = QandAAgent(
    name="qna",
    seed=os.getenv("QNA_SEED"),
    mail_address="",  # Will be set after Mail agent is created
    keyword=os.getenv("SEARCH_KEYWORD"),
    ollama_model=os.getenv("OLLAMA_MODEL"),
)

mail_agent = MailAgent(
    name="mail",
    seed=os.getenv("MAIL_SEED"),
    recipients=os.getenv("RECIPIENT_EMAILS").split(","),
    mailgun_api_key=os.getenv("MAILGUN_API_KEY"),
    mailgun_domain=os.getenv("MAILGUN_DOMAIN"),
)

# Now set the addresses
preprocessor_agent._qna_address = qna_agent.address
qna_agent._mail_address = mail_agent.address

scraper_agent = ScraperAgent(
    name="scraper",
    seed=os.getenv("SCRAPER_SEED"),
    target_url=os.getenv("TARGET_URL"),
    preprocessor_address=preprocessor_agent.address,
)

print("Setting up Bureau...")
bureau = Bureau()
bureau.add(scraper_agent)
bureau.add(preprocessor_agent)
bureau.add(qna_agent)
bureau.add(mail_agent)

print("Agents added to Bureau:")
print(f"- Scraper: {scraper_agent.address}")
print(f"- Preprocessor: {preprocessor_agent.address}")
print(f"- QnA: {qna_agent.address}")
print(f"- Mail: {mail_agent.address}")

print("Starting Bureau...")
bureau.run()
