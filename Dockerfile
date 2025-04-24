# Use the official Python 3.12 slim image as a base
FROM python:3.12-slim

# You need to install build-essential and git to install txtai[pipeline]
RUN apt-get update && apt-get install -y locate build-essential git && rm -rf /var/lib/apt/lists/*

# Set the working directory in the container
WORKDIR /app

# Install uv, the package installer
RUN pip install uv

# Copy the pyproject.toml file first to leverage Docker layer caching
COPY pyproject.toml uv.lock /app/

# Install dependencies only (not the project itself)
RUN uv sync --frozen --no-install-project --no-dev

# Copy the rest of the code (including fetch)
COPY . /app

# Install the project itself (fetch)
RUN uv sync --frozen --no-dev

# Ensure the virtual environment is on the PATH
ENV PATH="/app/.venv/bin:$PATH"

# Define the command to run the application
CMD ["uv", "run", "python", "-m", "fetch.main"] 