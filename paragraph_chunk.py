import sys
import logging
import nltk
import re
import ollama

nltk.download('punkt')

def document_based_chunking(text):
    paragraphs = re.split(r'\n\s*\n', text)
    chunks = []
    
    for paragraph in paragraphs:
        sentences = nltk.sent_tokenize(paragraph)
        current_chunk = ""
        
        for sentence in sentences:
            if len(current_chunk) + len(sentence) <= 100:
                current_chunk += sentence + " "
            else:
                chunks.append(current_chunk.strip())
                current_chunk = sentence + " "
        
        if current_chunk:
            chunks.append(current_chunk.strip())
    
    return chunks

def filter_chunks_by_keyword(chunks: list[str], keyword: str) -> list[str]:
    """Filters a list of text chunks, returning only those containing the keyword (case-insensitive)."""
    matching_chunks = []
    keyword_lower = keyword.lower()
    for chunk in chunks:
        if keyword_lower in chunk.lower():
            matching_chunks.append(chunk)
    if not matching_chunks:
        logging.warning(f"No chunks found containing the keyword: '{keyword}'")
    else:
        logging.info(f"Found {len(matching_chunks)} chunks containing the keyword: '{keyword}'")
    return matching_chunks

# combine chunks into a single string
def combine_chunks(chunks: list[str]) -> str:
    return " ".join(chunks)

def generate_prompt(chunks: list[str]) -> str:
    combined_chunks = combine_chunks(chunks)
    prompt = f"""
    You are a helpful assistant that can answer questions about the following text that extracts dates from the two tables with information about country and visa type from the bulletin, the first table is for final action date and the second table is for date of filing:
    {combined_chunks}

    What are the two dates for the india f2a visa?
    """
    return prompt

if __name__ == "__main__":
    input_file = "fetched_text.txt" # Hardcoded filename as requested
    search_keyword = "f2a" # Example keyword - change as needed
    
    logging.info(f"Processing file: {input_file}")
    try:
        with open(input_file, "r", encoding='utf-8') as f:
            text = f.read()
        logging.info("Successfully read file.")
    except FileNotFoundError:
        logging.error(f"Error: Input file '{input_file}' not found.")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Error reading file: {e}")
        sys.exit(1)

    logging.info("Starting chunking process...")
    all_chunks = document_based_chunking(text)
    logging.info(f"Generated {len(all_chunks)} chunks in total.")

    logging.info(f"Filtering chunks by keyword: '{search_keyword}'")
    filtered_chunks = filter_chunks_by_keyword(all_chunks, search_keyword)
    # combined_chunks = combine_chunks(filtered_chunks)
    prompt = generate_prompt(all_chunks)
    # print(prompt)
    response = ollama.chat(model="qwen2.5:7b", messages=[{"role": "user", "content": prompt}], options={"num_ctx": 8192, "temperature": 0.0})
    print(response)