# Voice Assistant API Documentation

This repository contains a Voice Assistant API that provides speech-to-text (STT) and text-to-speech (TTS) capabilities, along with natural language processing for retail queries.

## Table of Contents
- [Setup](#setup)
- [Running the API](#running-the-api)
- [API Endpoints](#api-endpoints)

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
   - Edit `.env` and add your Vanna.ai API key:
     ```
     VANNA_API_KEY=your_api_key_here
     ```
   You can obtain your API key from the Vanna.ai dashboard.

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
