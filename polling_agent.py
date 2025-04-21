import requests
import hashlib
from uagents import Agent, Context, Model
from uagents.setup import fund_agent_if_low
from bs4 import BeautifulSoup
import datetime
from nltk.tokenize import sent_tokenize, word_tokenize
import nltk
from nltk.corpus import stopwords
import re
from docling_core.transforms.chunker.hybrid_chunker import HybridChunker
from docling_core.types.doc import DoclingDocument
from docling_core.types.doc.labels import DocItemLabel
from html import unescape

AGENT_SEED = "visa_bulletin_polling_agent_seed" # Replace with a secure seed phrase if needed
# AGENT_ADDRESS = "agent1q2..." # Replace with actual agent address after running once or from fetch.ai wallet

POLL_INTERVAL_SECONDS = 5 # Poll every hour
JINA_READER = "https://r.jina.ai/"
# TARGET_URL = JINA_READER + "https://en.wikipedia.org/wiki/Miss_Meyers"
TARGET_URL = JINA_READER + "https://travel.state.gov/content/travel/en/legal/visa-law0/visa-bulletin/2025/visa-bulletin-for-may-2025.html"




def extract_chunk_metadata(chunk):
    """Extract essential metadata from a chunk"""
    metadata = {
        "text": chunk.text,
        "headings": [],
        "page_info": None,
        "content_type": None
    }
        
    if hasattr(chunk, 'meta'):
        # Extract headings
        if hasattr(chunk.meta, 'headings') and chunk.meta.headings:
            metadata["headings"] = chunk.meta.headings
        
        # Extract page information and content type
        if hasattr(chunk.meta, 'doc_items'):
            for item in chunk.meta.doc_items:
                if hasattr(item, 'label'):
                    metadata["content_type"] = str(item.label)
                
                if hasattr(item, 'prov') and item.prov:
                    for prov in item.prov:
                        if hasattr(prov, 'page_no'):
                            metadata["page_info"] = prov.page_no
    
    return metadata

def process_document(text):
    """Process document and create searchable index with metadata"""
    
    # Extract a base name from the URL or use a default
    doc_name = TARGET_URL.split('/')[-1] if TARGET_URL else "processed_document"
    if not doc_name:
        doc_name = "processed_document"
        
    doc = DoclingDocument(name=doc_name)
    doc.add_text(DocItemLabel.TEXT, text.encode('unicode_escape').decode('unicode_escape'))

    # Create chunks using hybrid chunker
    # chunker = HybridChunker()
    chunker = HybridChunker(tokenizer="jinaai/jina-embeddings-v3")
    chunks = list(chunker.chunk(doc))
    
    # Process chunks and extract metadata
    print("\nProcessing chunks and extracting metadata:")
    processed_chunks = []
    for i, chunk in enumerate(chunks):
        # metadata = extract_chunk_metadata(chunk)
        # processed_chunks.append(metadata)
        # print(f"Processed Chunk {i} Metadata:", metadata) # Print processed metadata
        print(chunk)
        print("--------------------------------")
    # exit() # Removed exit
    return processed_chunks

# Define a simple model for messages (optional for this basic poller)
class StatusUpdate(Model):
    url: str
    status_code: int
    content_hash: str | None

# Create the agent
agent = Agent(
    name="visa_bulletin_poller",
    port=8000,
    seed=AGENT_SEED,
    endpoint=["http://127.0.0.1:8000/submit"],
)

# Store the last known hash of the content
last_content_hash = None

@agent.on_interval(period=POLL_INTERVAL_SECONDS)
async def poll_visa_bulletin(ctx: Context):
    global last_content_hash
    ctx.logger.info(f"Polling URL: {TARGET_URL}")
    try:
        response = requests.get(TARGET_URL, timeout=30) # Added timeout
        response.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)

        ctx.logger.info(f"Successfully fetched URL. Status: {response.status_code}")
        fetched_text = response.text
        ctx.logger.info(f"Fetched text length: {len(fetched_text)}")
        # write to file
        with open("fetched_text.txt", "w") as f:
            f.write(fetched_text)
        exit()
        # Uncomment the next line if you want to see the full text (can be very long!)
        # print("Fetched Text:\n", fetched_text)

        ctx.logger.info("Processing document content with Docling...")
        processed_chunks = process_document(fetched_text)
        ctx.logger.info(f"Docling processing complete. Found {len(processed_chunks)} chunks.")
        # exit() # Removed exit

        # Calculate hash based on the *original* content for change detection
        current_content_hash = hashlib.sha256(response.content).hexdigest()
        status_update = StatusUpdate(
            url=TARGET_URL,
            status_code=response.status_code,
            content_hash=current_content_hash
        )

        ctx.logger.info(f"URL Status: {status_update.status_code}, Content Hash: {current_content_hash}")

        if last_content_hash is None:
            ctx.logger.info("First poll, storing content hash.")
            # TODO: Store or process initial chunks
            last_content_hash = current_content_hash
        elif last_content_hash != current_content_hash:
            ctx.logger.info(f"Content changed! New hash: {current_content_hash}")
            # TODO: Add logic here to handle the change using processed_chunks
            last_content_hash = current_content_hash
        else:
            ctx.logger.info("Content unchanged.")

    except requests.exceptions.RequestException as e:
        ctx.logger.error(f"Error polling URL {TARGET_URL}: {e}")
        # Optionally send an error status or retry logic
    except Exception as e:
        ctx.logger.error(f"An unexpected error occurred: {e}")


if __name__ == "__main__":
    print(f"Agent address: {agent.address}") # Print agent address
    agent.run()