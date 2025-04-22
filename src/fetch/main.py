import os
from uagents import Bureau

# Import Agent classes and protocols
from scrape import ScraperAgent, ScrapedData
from preprocessor import PreprocessorAgent, preprocessor_proto, ProcessedData
from rag import QandAAgent, qna_proto, QAResult
from mail import MailAgent, mail_proto

# --- Configuration --- (Load from environment variables or a config file)
SCRAPER_SEED = os.getenv("SCRAPER_SEED", "scraper_agent_secret_phrase")
PREPROCESSOR_SEED = os.getenv("PREPROCESSOR_SEED", "preprocessor_agent_secret_phrase")
QNA_SEED = os.getenv("QNA_SEED", "qna_agent_secret_phrase")
MAIL_SEED = os.getenv("MAIL_SEED", "mail_agent_secret_phrase")

TARGET_URL = os.getenv(
    "TARGET_URL",
    "https://travel.state.gov/content/travel/en/legal/visa-law0/visa-bulletin/2025/visa-bulletin-for-may-2025.html",
)
SEARCH_KEYWORD = os.getenv("SEARCH_KEYWORD", "f2a")  # Keyword for Q&A filtering
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:14b")  # Ollama model for RAG

MAILGUN_API_KEY = os.getenv("MAILGUN_API_KEY")
MAILGUN_DOMAIN = os.getenv("MAILGUN_DOMAIN")
RECIPIENT_EMAILS = os.getenv("RECIPIENT_EMAILS", "test@example.com").split(
    ","
)  # Comma-separated list

# if not MAILGUN_API_KEY or not MAILGUN_DOMAIN:
#     print(
#         "Error: MAILGUN_API_KEY and MAILGUN_DOMAIN environment variables must be set."
#     )
#     exit(1)
# if not RECIPIENT_EMAILS or not RECIPIENT_EMAILS[0]:
#     print(
#         "Warning: RECIPIENT_EMAILS environment variable is not set or empty. Mail agent will not send emails."
#     )
# Optionally exit(1) if emails are mandatory

# --- Agent Instantiation ---

# Create agents first to get their addresses
preprocessor_agent = PreprocessorAgent(
    name="preprocessor",
    seed=PREPROCESSOR_SEED,
    qna_address="",  # Will be set after QnA agent is created
)

qna_agent = QandAAgent(
    name="qna",
    seed=QNA_SEED,
    mail_address="",  # Will be set after Mail agent is created
    keyword=SEARCH_KEYWORD,
    ollama_model=OLLAMA_MODEL,
)

mail_agent = MailAgent(
    name="mail",
    seed=MAIL_SEED,
    recipients=RECIPIENT_EMAILS,
    mailgun_api_key=MAILGUN_API_KEY,
    mailgun_domain=MAILGUN_DOMAIN,
)

# Now set the addresses
preprocessor_agent._qna_address = qna_agent.address
qna_agent._mail_address = mail_agent.address

scraper_agent = ScraperAgent(
    name="scraper",
    seed=SCRAPER_SEED,
    target_url=TARGET_URL,
    preprocessor_address=preprocessor_agent.address,
)

# --- Include Protocols ---
# Ensure agents know about the protocols they interact with

preprocessor_agent.include(preprocessor_proto, publish_manifest=True)

qna_agent.include(qna_proto, publish_manifest=True)
# preprocessor_agent.include(preprocessor_proto)  # Knows structure of incoming messages
# qna_agent.include(mail_proto)  # Knows how to talk to mail

# mail_agent.include(mail_proto, publish_manifest=True)
# qna_agent.include(qna_proto)  # Knows structure of incoming messages

# --- Bureau Setup ---
print("Setting up Bureau...")
bureau = Bureau()
bureau.add(scraper_agent)
bureau.add(preprocessor_agent)
bureau.add(qna_agent)
# bureau.add(mail_agent)

print("Agents added to Bureau:")
print(f"- Scraper: {scraper_agent.address}")
# print(f"- Preprocessor: {preprocessor_agent.address}")
# print(f"- QnA: {qna_agent.address}")
# print(f"- Mail: {mail_agent.address}")

# --- Run Bureau ---
if __name__ == "__main__":
    print("Starting Bureau...")
    bureau.run()
