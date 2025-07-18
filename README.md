# Voice Assistant API Documentation

This repository contains a Voice Assistant API that provides speech-to-text (STT) and text-to-speech (TTS) capabilities, along with natural language processing for retail queries.

## Table of Contents
- [Setup](#setup)
- [Running the API](#running-the-api)
- [API Endpoints](#api-endpoints)
- [Text-to-SQL Endpoint](#text-to-sql-endpoint)
- [Environment Variables](#environment-variables)

## Setup

### Prerequisites
- Python 3.8 or higher
- Virtual environment (recommended)
- SQLite database (included)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/RohmaButt/gas-ai-bot-poc.git
cd gas-ai-bot-poc
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
# Windows
.\venv\Scripts\activate
# Unix/MacOS
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
   - Copy `.env.example` to `.env`:
     ```bash
     cp .env.example .env
     ```

   - Edit `.env` and add your Groq API key:
     ```
     GROQ_API_KEY=your_groq_api_key_here
     GROQ_MODEL=mixtral-8x7b-32768
     ```
   You can obtain your API key from the Groq dashboard.

   - The `.env.example` file is provided as a template. Do **not** commit your real `.env` file to version control.

## Running the API

1. Start the FastAPI server:
```bash
uvicorn src.main:app --reload
```

The API will be available at `http://localhost:8000`

## API Endpoints

### 1. Get Supported Languages
Get a list of all supported languages for speech recognition.

```http
GET /languages
```

Response:
```json
{
    "languages": [
        {
            "code": "en-US",
            "name": "English (US)"
        },
        {
            "code": "es-ES",
            "name": "Spanish"
        },
        // ... more languages
    ]
}
```

### 2. Speech to Text
Convert speech from an audio file to text.

```http
POST /speech-to-text
```

Parameters:
- `audio_file`: The audio file to transcribe (multipart/form-data)
- `language`: Language code (optional, defaults to "auto")

Response:
```json
{
    "text": "Transcribed text here",
    "language_code": "en-US",
    "language_name": "English (US)"
}
```

### 3. Text to Speech
Convert text to speech.
```http
POST /text-to-speech
```

Parameters:
- `text`: The text to convert to speech
- `lang`: Language code (optional, defaults to "en")

Response:
```json
{
    "audio_file": "URL to the generated audio file"
}

## Text-to-SQL Endpoint

Convert a natural language question into a SQL query and get results from the retail database.

```http
POST /text-to-sql
```

Parameters (query or JSON body):
- `question` (string, required): The natural language question to convert to SQL
- `top_k` (integer, optional): Maximum number of results to return (default: 10)

Example Request:
```json
{
  "question": "Show me all products with price over $100",
  "top_k": 5
}
```

Example Response:
```json
{
  "status": "success",
  "sql_query": "SELECT id, name, price FROM products WHERE price > 100 ORDER BY price DESC LIMIT 5",
  "raw_result": [
    {"id": 1, "name": "Gaming Laptop", "price": 1499.99},
    {"id": 2, "name": "Business Laptop", "price": 1299.99}
  ],
  "natural_language_response": "I found 2 products with prices over $100:\n\n1. Gaming Laptop - $1,499.99\n2. Business Laptop - $1,299.99",
  "tables_used": ["products"],
  "question": "Show me all products with price over $100"
}
```

Error Response Example:
```json
{
  "detail": "GROQ_API_KEY environment variable not found. Please add it to your .env file."
}

## Environment Variables

The following environment variables are required:

- `GROQ_API_KEY`: Your Groq API key (required)
- `GROQ_MODEL`: The Groq model to use (default: mixtral-8x7b-32768)

See `.env.example` for a template.

```http
POST /text-to-speech
```

Parameters:
- `text`: The text to convert to speech
- `lang`: Language code (optional, defaults to "en")

Response:
- Audio file (WAV format)

## Error Handling

The API returns standard HTTP status codes:

- 200: Success
- 400: Bad Request (invalid parameters)
- 500: Server Error

Error responses include a detail message:
```json
{
    "detail": "Error message here"
}
```

## Notes for Frontend Integration

1. **Audio Format Support**:
   - The API accepts WAV, MP3, and OGG formats
   - For best results, use WAV format with PCM encoding

2. **File Size Limits**:
   - Maximum file size: 10MB
   - Maximum audio duration: 1 minute

3. **CORS**:
   - The API has CORS enabled for frontend integration
   - Default allowed origins: all (`*`)

4. **Real-time Processing**:
   - Speech recognition typically takes 2-5 seconds
   - Text-to-speech conversion is usually under 1 second
