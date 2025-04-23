from uagents import Agent, Context, Model
import os
import re
import nltk

from custom_types import ScrapedData, ProcessedData, QAResult


# Define the Preprocessor Agent
class PreprocessorAgent(Agent):
    def __init__(self, name: str, seed: str, qna_address: str):
        super().__init__(name=name, seed=seed)
        self._qna_address = qna_address
        nltk.download("punkt")
        nltk.download("punkt_tab")
        # Register the message handler using decorator pattern
        self.on_message(model=ScrapedData, replies=None)(self.preprocess_text)

    async def preprocess_text(self, ctx: Context, sender: str, msg: ScrapedData):
        ctx.logger.info(f"Received text from {sender}. Starting preprocessing.")

        # Step 1: Format tables within the text
        try:
            formatted_text = self.format_tables_in_text(msg.text)
            ctx.logger.info("Table formatting applied.")
        except Exception as e:
            ctx.logger.error(f"Error during table formatting: {e}")
            formatted_text = msg.text  # Fallback to original text if formatting fails

        # Step 2: Chunk the text
        try:
            chunks = self.document_based_chunking(formatted_text)
            ctx.logger.info(f"Text chunked into {len(chunks)} parts.")
        except Exception as e:
            ctx.logger.error(f"Error during text chunking: {e}")
            chunks = []  # Send empty list if chunking fails

        # Step 3: Send processed chunks to Q&A Agent
        if chunks:
            await ctx.send(self._qna_address, ProcessedData(chunks=chunks))
            ctx.logger.info(f"Sent {len(chunks)} chunks to {self._qna_address}")
        else:
            ctx.logger.warning(
                "No chunks generated or chunking failed. Nothing sent to Q&A agent."
            )

    def parse_row(self, line: str) -> list[str]:
        """
        Parses a Markdown table row into a list of cell contents.
        Removes leading/trailing whitespace from the line and cells.
        Handles lines starting/ending with '|'.
        """
        # Strip leading/trailing whitespace and the outer pipes if they exist
        content = line.strip()
        if content.startswith("|"):
            content = content[1:]
        if content.endswith("|"):
            content = content[:-1]
        # Split by pipe and strip whitespace from each cell
        cells = [cell.strip() for cell in content.split("|")]
        return cells

    def is_separator_line(self, line: str) -> bool:
        """
        Checks if a line is a Markdown table separator line (e.g., |---|---| :--- |).
        It must contain pipes and hyphens, and only contain pipe, hyphen, colon, or whitespace.
        """
        line = line.strip()
        if not line.startswith("|") or not line.endswith("|"):
            return False
        # Check if all non-whitespace characters are pipe, hyphen, or colon
        allowed_chars = set(["|", "-", ":", " "])
        if not all(c in allowed_chars for c in line):
            return False
        # Check if it contains at least one hyphen (to distinguish from header/data)
        if "-" not in line:
            return False
        # Check structure: ensure segments between pipes are valid separators
        parts = [part.strip() for part in line.strip("|").split("|")]
        if not parts:
            return False
        for part in parts:
            if not part:  # Skip empty parts resulting from ||
                continue
            # Must contain at least one hyphen
            if "-" not in part:
                return False
            # Can start/end with colon, but otherwise only hyphens
            valid_part = True
            if part.startswith(":"):
                part = part[1:]
            if part.endswith(":"):
                part = part[:-1]
            if not all(c == "-" for c in part):
                valid_part = False
            if not valid_part:
                return False

        return True

    def is_table_row(self, line: str) -> bool:
        """
        Checks if a line could be a Markdown table header or data row.
        Simple check: contains a pipe '|'. More robustly, starts and ends with '|' after stripping.
        """
        stripped_line = line.strip()
        # Consider lines with at least one pipe as potential table rows
        # Exclude separator lines explicitly
        return "|" in stripped_line and not self.is_separator_line(stripped_line)

    def format_table(
        self, header_line: str, separator_line: str, data_lines: list[str]
    ) -> str:
        """
        Formats a given table (header, separator, data lines) into a nicely aligned string.
        """
        header_cells = self.parse_row(header_line)
        data_rows = [self.parse_row(line) for line in data_lines]
        num_columns = len(header_cells)

        # Ensure all data rows have the same number of columns as the header
        # Pad with empty strings if necessary
        for row in data_rows:
            while len(row) < num_columns:
                row.append("")
            # Truncate if too long (less common)
            if len(row) > num_columns:
                row = row[:num_columns]

        # Calculate maximum width for each column
        col_widths = [len(cell) for cell in header_cells]
        for row in data_rows:
            for i, cell in enumerate(row):
                if i < num_columns:  # Ensure index is within bounds
                    col_widths[i] = max(col_widths[i], len(cell))

        # Use separator alignment hints (optional, default left)
        # Basic separator generation: at least 3 dashes
        separator_parts = []
        for i in range(num_columns):
            # Make separator dashes match column width
            # Ensure minimum length of 3 dashes for GFM
            width = max(3, col_widths[i])
            col_widths[i] = width  # Update col_widths to include min separator width
            separator_parts.append("-" * width)

        formatted_separator = "| " + " | ".join(separator_parts) + " |"

        # Format header
        formatted_header_cells = []
        for i, cell in enumerate(header_cells):
            formatted_header_cells.append(cell.ljust(col_widths[i]))
        formatted_header = "| " + " | ".join(formatted_header_cells) + " |"

        # Format data rows
        formatted_data_rows = []
        for row in data_rows:
            formatted_cells = []
            for i, cell in enumerate(row):
                if i < num_columns:
                    formatted_cells.append(cell.ljust(col_widths[i]))
            formatted_data_rows.append("| " + " | ".join(formatted_cells) + " |")

        # Combine all parts
        return "\n".join([formatted_header, formatted_separator] + formatted_data_rows)

    def format_tables_in_text(self, text: str) -> str:
        """Applies Markdown table formatting logic directly to a string."""
        lines = text.splitlines()
        output_lines = []
        i = 0
        while i < len(lines):
            line = lines[
                i
            ]  # Keep original line ending if needed, but splitlines removes them

            # Look ahead to detect table start (header + separator)
            if (
                i + 1 < len(lines)
                and self.is_table_row(line)  # Current line looks like a header/data row
                and self.is_separator_line(lines[i + 1])  # Next line is a separator
            ):
                header_line = line
                separator_line = lines[i + 1]
                data_lines = []
                table_block_line_count = 2  # Header + Separator

                # Consume separator line index
                current_table_index = i + 2

                # Gather data rows
                while current_table_index < len(lines):
                    data_line_candidate = lines[current_table_index]
                    if self.is_table_row(data_line_candidate):
                        data_lines.append(data_line_candidate)
                        table_block_line_count += 1
                        current_table_index += 1
                    else:
                        break  # End of table detected

                # Format the collected table
                try:
                    formatted_table = self.format_table(
                        header_line, separator_line, data_lines
                    )
                    output_lines.append(
                        formatted_table
                    )  # Append formatted table as a single block
                except Exception as e:
                    # If formatting fails, append original lines to avoid data loss
                    print(
                        f"Warning: Failed to format table starting near line {i+1}. Keeping original. Error: {e}"
                    )
                    output_lines.append(header_line)
                    output_lines.append(separator_line)
                    output_lines.extend(data_lines)

                # Move index past the processed table block
                i += table_block_line_count

            else:
                # Not a table start, just append the line
                output_lines.append(line)
                i += 1

        # Join lines back together
        return "\n".join(output_lines)

    def document_based_chunking(self, text: str) -> list[str]:
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


# Example Usage (if run directly, replace with actual setup in main.py)
if __name__ == "__main__":
    PREPROCESSOR_SEED = os.getenv("PREPROCESSOR_SEED", "preprocessor_secret_phrase")
    QNA_ADDRESS = "agent1..."  # Replace with actual QnA agent address

    agent = PreprocessorAgent(
        name="preprocessor_agent", seed=PREPROCESSOR_SEED, qna_address=QNA_ADDRESS
    )
    # Expose the agent's endpoint for the ScraperAgent
    # In a real setup, this address needs to be shared (e.g., via AgentVerse)
    print(f"Preprocessor Agent Address: {agent.address}")

    agent.run()
