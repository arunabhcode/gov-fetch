import sys
import re


def parse_row(line: str) -> list[str]:
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


def is_separator_line(line: str) -> bool:
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


def is_table_row(line: str) -> bool:
    """
    Checks if a line could be a Markdown table header or data row.
    Simple check: contains a pipe '|'. More robustly, starts and ends with '|' after stripping.
    """
    stripped_line = line.strip()
    # Consider lines with at least one pipe as potential table rows
    # Exclude separator lines explicitly
    return "|" in stripped_line and not is_separator_line(stripped_line)


def format_table(header_line: str, separator_line: str, data_lines: list[str]) -> str:
    """
    Formats a given table (header, separator, data lines) into a nicely aligned string.
    """
    header_cells = parse_row(header_line)
    data_rows = [parse_row(line) for line in data_lines]
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
    separator_cells = parse_row(separator_line)
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


def format_markdown_tables(input_filename: str, output_filename: str):
    """
    Reads a Markdown file, formats tables, and writes to an output file.
    """
    try:
        with open(input_filename, "r", encoding="utf-8") as infile:
            lines = infile.readlines()
    except FileNotFoundError:
        print(f"Error: Input file '{input_filename}' not found.", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error reading file '{input_filename}': {e}", file=sys.stderr)
        sys.exit(1)

    output_lines = []
    i = 0
    while i < len(lines):
        line = lines[i].rstrip("\r\n")  # Process without trailing newline initially

        # Look ahead to detect table start (header + separator)
        if (
            i + 1 < len(lines)
            and is_table_row(line)  # Current line looks like a header/data row
            and is_separator_line(lines[i + 1])
        ):  # Next line is a separator
            header_line = line
            separator_line = lines[i + 1].rstrip("\r\n")
            data_lines = []
            table_block_line_count = 2  # Header + Separator

            # Consume separator line index
            current_table_index = i + 2

            # Gather data rows
            while current_table_index < len(lines):
                data_line_candidate = lines[current_table_index].rstrip("\r\n")
                # Check if it's a valid data row for *this* table
                # It should contain '|' and not be a separator itself
                if is_table_row(data_line_candidate):
                    # Basic check: does it look like a row?
                    # More robust: check column count consistency? (maybe too complex)
                    data_lines.append(data_line_candidate)
                    table_block_line_count += 1
                    current_table_index += 1
                else:
                    # End of table detected
                    break

            # Format the collected table
            try:
                formatted_table = format_table(header_line, separator_line, data_lines)
                output_lines.append(
                    formatted_table
                )  # Append formatted table as a single block
            except Exception as e:
                # If formatting fails, append original lines to avoid data loss
                print(
                    f"Warning: Failed to format table starting line {i+1}. Keeping original. Error: {e}",
                    file=sys.stderr,
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

    # Write the output file
    try:
        with open(output_filename, "w", encoding="utf-8") as outfile:
            # Join lines with original newline characters (or default to \n)
            # This preserves original line endings if mixed, though uncommon.
            # Simpler: just use '\n'.
            outfile.write("\n".join(output_lines) + "\n")  # Add trailing newline
        print(f"Formatted Markdown written to '{output_filename}'")
    except Exception as e:
        print(f"Error writing file '{output_filename}': {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    format_markdown_tables("visa_bulletin.md", "visa_bulletin_formatted.md")
