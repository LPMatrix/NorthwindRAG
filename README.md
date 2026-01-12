# Northwind Database RAG System

This project implements a Retrieval-Augmented Generation (RAG) system that allows users to query a Northwind MySQL database using natural language. It uses **Ollama** for embeddings and text generation, and **ChromaDB** for storing and retrieving schema context.

## Features

- **Schema Extraction**: Automatically extracts table schemas and foreign keys from the MySQL database.
- **Vector Search**: Stores schema information in ChromaDB for efficient retrieval based on user queries.
- **Text-to-SQL**: Generates valid MySQL queries from natural language questions using LLMs.
- **Natural Language Answers**: Explains query results in plain English.

## Prerequisites

- Python 3.8+
- MySQL Server (with the Northwind database installed)
- [Ollama](https://ollama.com/) running locally

### Required Ollama Models
You need to pull the following models:
```bash
ollama pull nomic-embed-text
ollama pull llama3.2
```

## Installation

1. Clone the repository (if applicable) or navigate to the project directory.

2. Install the required Python packages:
   ```bash
   pip install -r requirements.txt
   ```

3. Ensure your MySQL server is running and the Northwind database is accessible. Create a `.env` file in the project root with your database credentials:
   ```bash
   DB_HOST=localhost
   DB_USER=root
   DB_PASSWORD=your_password
   DB_NAME=northwind
   ```

## Usage

### 1. Extract Schema
Run this script first to index the database schema into ChromaDB.
```bash
python extract_schema.py
```

### 2. Query the Database
Start the interactive query interface:
```bash
python query_db.py
```
You can now ask questions like:
- "What products are out of stock?"
- "Who are the top 5 customers by order volume?"
- "List all employees in London."

## Project Structure

- `extract_schema.py`: Connects to MySQL, extracts schema details, generates embeddings, and stores them in ChromaDB.
- `query_db.py`: The main application that handles user input, retrieves context, generates SQL, executes it, and formats the response.
- `chroma_db_northwind/`: Directory where ChromaDB stores the vector index (generated after running extraction).
