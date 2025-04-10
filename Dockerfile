FROM python:3.13-alpine

# Set the working directory
WORKDIR /app

# Install Poetry
RUN pip install --no-cache-dir poetry

# Copy dependency files first (to optimize caching)
COPY pyproject.toml poetry.lock /app/

# Install dependencies
RUN poetry config virtualenvs.create false \
	&& poetry install --no-root --no-interaction --no-ansi

# Copy the entire project
COPY . /app

# Expose FastAPI default port
EXPOSE 8000

# Set Python path to include src/
ENV PYTHONPATH="/app/src/web_server"

# Run the FastAPI application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
