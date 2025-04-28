from uagents import Agent, Context
import os
import ollama  # Make sure ollama library is installed

from fetch.custom_types import ProcessedData, QAResult


# Define the Q&A Agent
class QandAAgent(Agent):
    def __init__(
        self,
        name: str,
        seed: str,
        mail_address: str,
        keyword: str,
        ollama_model: str = "qwen2.5:32b",
    ):
        super().__init__(name=name, seed=seed)
        self._mail_address = mail_address
        self._keyword = keyword
        self._ollama_model = ollama_model
        self._search_keyword = os.getenv("SEARCH_KEYWORD")
        self._keyword_to_prompt_dict = {
            "f1": f"What are the two dates for family based f1 visa for {os.getenv("COUNTRY_NAME")}?",
            "f2a": f"What are the two dates for family based f2a visa for {os.getenv("COUNTRY_NAME")}?",
            "f2b": f"What are the two dates for family based f2b visa for {os.getenv("COUNTRY_NAME")}?",
            "f3": f"What are the two dates for family based f3 visa for {os.getenv("COUNTRY_NAME")}?",
            "f4": f"What are the two dates for family based f4 visa for {os.getenv("COUNTRY_NAME")}?",
            "eb1": f"What are the two dates for employment based 1st preference visa for {os.getenv("COUNTRY_NAME")}?",
            "eb2": f"What are the two dates for employment based 2nd preference visa for {os.getenv("COUNTRY_NAME")}?",
            "eb3": f"What are the two dates for employment based 3rd preference visa for {os.getenv("COUNTRY_NAME")}?",
        }
        if self._search_keyword not in self._keyword_to_prompt_dict:
            raise ValueError(
                f"Invalid search keyword '{self._search_keyword}'. Must be one of {list(self._keyword_to_prompt_dict.keys())}"
            )
        if not os.getenv("OLLAMA_HOST"):
            self._ollama_host = ollama.Client(host="http://ollama-cpu:11434")
        else:
            self._ollama_host = ollama.Client(host=os.getenv("OLLAMA_HOST"))
        # Check if Ollama server is running (optional but good practice)
        try:
            self._ollama_host.list()
        except Exception as e:
            print(f"Ollama server might not be running or reachable: {e}")
        self.on_message(model=ProcessedData, replies=None)(self.handle_processed_data)

    async def handle_processed_data(
        self, ctx: Context, sender: str, msg: ProcessedData
    ):
        ctx.logger.info(
            f"Received {len(msg.chunks)} chunks from {sender}. Performing Q&A."
        )

        # Step 1: Filter chunks by keyword
        filtered_chunks = self.filter_chunks_by_keyword(msg.chunks, self._keyword)
        if not filtered_chunks:
            ctx.logger.warning(
                f"No chunks found containing keyword '{self._keyword}'. Cannot generate prompt."
            )
            return  # Or send an error message?
        for chunk in filtered_chunks:
            print(chunk)
        # Step 2: Generate the prompt
        # Note: generate_prompt from paragraph_chunk.py has a hardcoded question.
        # Consider making the question dynamic or part of the agent's configuration.
        try:
            prompt = self.generate_prompt(filtered_chunks)
            ctx.logger.info("Generated prompt based on filtered chunks.")
        except Exception as e:
            ctx.logger.error(f"Error generating prompt: {e}")
            return

        # Step 3: Call Ollama for the answer
        try:
            ctx.logger.info(f"Querying Ollama model '{self._ollama_model}'...")
            response = self._ollama_host.chat(
                model=self._ollama_model,
                messages=[{"role": "user", "content": prompt}],
                # Options from paragraph_chunk.py, make configurable if needed
                options={"num_ctx": 8192, "temperature": 0.0},
            )
            answer = response["message"]["content"]
            ctx.logger.info("Received answer from Ollama.")
        except Exception as e:
            ctx.logger.error(f"Error querying Ollama: {e}")
            answer = f"Error: Could not get answer from Ollama. {e}"  # Send error back
        ctx.logger.info(f"Answer: {answer}")
        # Step 4: Send Prompt and Answer to Mail Agent
        await ctx.send(self._mail_address, QAResult(prompt=prompt, answer=answer))
        ctx.logger.info(f"Sent Q&A result to {self._mail_address}")

    def filter_chunks_by_keyword(self, chunks: list[str], keyword: str) -> list[str]:
        """Filters a list of text chunks, returning only those containing the keyword (case-insensitive)."""
        matching_chunks = []
        keyword_lower = keyword.lower()
        for chunk in chunks:
            if keyword_lower in chunk.lower():
                matching_chunks.append(chunk)
        return matching_chunks

    # combine chunks into a single string
    def combine_chunks(self, chunks: list[str]) -> str:
        return " ".join(chunks)

    def generate_prompt(self, chunks: list[str]) -> str:
        combined_chunks = self.combine_chunks(chunks)
        prompt = f"""You are a helpful assistant that can answer questions using the following markdown text with dates from two provided tables with information about country and visa type, THE FIRST TABLE IS FOR FINAL ACTION DATES AND THE SECOND TABLE IS FOR DATES OF FILING:
{combined_chunks}

{self._keyword_to_prompt_dict.get(self._search_keyword)}"""
        return prompt


# Example Usage (if run directly, replace with actual setup in main.py)
if __name__ == "__main__":
    QNA_SEED = os.getenv("QNA_SEED", "qna_secret_phrase")
    MAIL_ADDRESS = "agent1..."  # Replace with actual Mail agent address
    SEARCH_KEYWORD = "2nd"  # Example keyword

    agent = QandAAgent(
        name="qna_agent",
        seed=QNA_SEED,
        mail_address=MAIL_ADDRESS,
        keyword=SEARCH_KEYWORD,
    )
    # Expose the agent's endpoint for the PreprocessorAgent
    print(f"QnA Agent Address: {agent.address}")

    agent.run()
