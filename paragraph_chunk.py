import sys
import logging
import nltk
import re
import ollama

nltk.download("punkt")
nltk.download("punkt_tab")


def document_based_chunking(text):
    paragraphs = re.split(r"\n\s*\n", text)
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
        logging.info(
            f"Found {len(matching_chunks)} chunks containing the keyword: '{keyword}'"
        )
    return matching_chunks


# combine chunks into a single string
def combine_chunks(chunks: list[str]) -> str:
    return " ".join(chunks)


def generate_prompt(chunks: list[str]) -> str:
    combined_chunks = combine_chunks(chunks)
    prompt = f"""
    You are a helpful assistant that can answer questions about the following markdown text that extracts dates from the two provided tables with information about country and visa type, THE FIRST TABLE IS FOR FINAL ACTION DATES AND THE SECOND TABLE IS FOR DATES OF FILING:
    {combined_chunks}

    What are the two dates for employment based 2nd preference category for india?
    """
    return prompt

    # You are a helpful assistant that can answer questions based on the following markdown formatted text:


if __name__ == "__main__":
    input_file = "visa_bulletin_formatted.md"  # Hardcoded filename as requested
    search_keyword = "2nd"  # Example keyword - change as needed

    logging.info(f"Processing file: {input_file}")
    with open(input_file, "r", encoding="utf-8") as f:
        text = f.read()

    logging.info("Starting chunking process...")
    all_chunks = document_based_chunking(text)
    logging.info(f"Generated {len(all_chunks)} chunks in total.")

    # logging.info(f"Filtering chunks by keyword: '{search_keyword}'")
    filtered_chunks = filter_chunks_by_keyword(all_chunks, search_keyword)
    # combined_chunks = combine_chunks(filtered_chunks)
    # print(combined_chunks)
    # for chunk in all_chunks:
    #     print(chunk)
    # print("-" * 100)
    prompt = generate_prompt(filtered_chunks)
    # print(prompt)
    response = ollama.chat(
        model="qwen2.5:14b",
        messages=[{"role": "user", "content": prompt}],
        options={"num_ctx": 8192, "temperature": 0.0},
    )
    print(response)
