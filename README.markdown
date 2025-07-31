# Voice Assistant API

A FastAPI-based Voice Assistant API providing speech-to-text (STT), text-to-speech (TTS), text translation, and natural language to SQL query conversion for retail database systems.

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

## Table of Contents

- [Voice Assistant API](#voice-assistant-api)
  - [Table of Contents](#table-of-contents)
  - [Overview](#overview)
  - [Setup](#setup)
    - [Prerequisites](#prerequisites)
    - [Installation](#installation)
  - [Running the API](#running-the-api)
  - [API Endpoints](#api-endpoints)
    - [1. Get Supported Languages](#1-get-supported-languages)
    - [2. Speech-to-Text](#2-speech-to-text)
    - [3. Text-to-Speech](#3-text-to-speech)
    - [4. Translate](#4-translate)
  - [Text-to-SQL Component](#text-to-sql-component)
    - [Database Schema](#database-schema)
    - [API Endpoint for `/text-to-sql`](#api-endpoint-for-text-to-sql)
    - [SQL Agent Features](#sql-agent-features)
  - [Environment Variables](#environment-variables)

## Overview

This API enables voice interaction and data querying capabilities for retail applications. It supports:
- Speech-to-text transcription
- Text-to-speech conversion
- Text translation between languages (e.g., English to Chinese)
- Natural language to SQL query conversion for retail database analysis

The API is built with FastAPI, uses SQLite for local storage, and integrates with the `googletrans` library for translation.

## Setup

### Prerequisites
- **Python**: Version 3.8 or higher
- **Virtual Environment**: Recommended for dependency isolation
- **SQLite**: Included with the repository
- **Dependencies**: Listed in `requirements.txt`

### Installation

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/RohmaButt/gas-ai-bot-poc.git
   cd gas-ai-bot-poc
   ```

2. **Create and Activate a Virtual Environment**:
   ```bash
   python -m venv venv
   ```
   - Windows:
     ```bash
     .\venv\Scripts\activate
     ```
   - Unix/macOS:
     ```bash
     source venv/bin/activate
     ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
   Ensure `googletrans==3.1.0a0` is included for translation functionality.

4. **Configure Environment Variables**:
   - Copy the example environment file:
     ```bash
     cp .env.example .env
     ```
   - Edit `.env` with your configuration:
     ```plaintext
     # Database Configuration
     DB_SERVER=your_server
     DB_NAME=your_database
     DB_USER=your_username
     DB_PASSWORD=your_password
     DB_DRIVER=ODBC Driver 17 for SQL Server

     # LLM Configuration
     GROQ_API_KEY=your_groq_api_key
     GROQ_MODEL=meta-llama/llama-4-scout-17b-16e-instruct
     ```
   - **Note**: Do not commit the `.env` file to version control.

## Running the API

1. Start the FastAPI server:
   ```bash
   uvicorn src.main:app --reload
   ```

2. Access the API at `http://localhost:8000`.

3. Explore the interactive API documentation at `http://localhost:8000/docs`.

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/languages` | GET | Retrieve supported languages for speech recognition. |
| `/speech-to-text` | POST | Convert audio to text. |
| `/text-to-speech` | POST | Convert text to audio. |
| `/translate` | POST | Translate text between languages (e.g., English to Chinese). |

### 1. Get Supported Languages
Retrieve a list of supported languages for speech recognition.

```http
GET /languages
```

**Response**:
```json
{
    "languages": [
        {"code": "en-US", "name": "English (US)"},
        {"code": "es-ES", "name": "Spanish"},
        // ... more languages
    ]
}
```

**Error Response** (e.g., server error):
```json
{
    "detail": "Internal server error"
}
```

### 2. Speech-to-Text
Convert audio to transcribed text.

```http
POST /speech-to-text
```

**Parameters**:
- `audio_file`: Audio file (multipart/form-data, e.g., WAV, MP3)
- `language`: Language code (optional, defaults to "auto")

**Request Example**:
```bash
curl -X POST "http://localhost:8000/speech-to-text" -F "audio_file=@audio.wav" -F "language=en-US"
```

**Response**:
```json
{
    "text": "Transcribed text here",
    "language_code": "en-US",
    "language_name": "English (US)"
}
```

**Error Response** (e.g., invalid audio):
```json
{
    "detail": "Invalid audio file format"
}
```

### 3. Text-to-Speech
Convert text to audio.

```http
POST /text-to-speech
```

**Parameters**:
- `text`: Text to convert (string)
- `lang`: Language code (optional, defaults to "en")

**Request Example**:
```json
{
    "text": "Hello, welcome to the Voice Assistant!",
    "lang": "en"
}
```

**Response**:
```json
{
    "audio_file": "http://localhost:8000/audio/output.mp3"
}
```

**Error Response** (e.g., unsupported language):
```json
{
    "detail": "Language not supported"
}
```

### 4. Translate
Translate text between supported languages.

```http
POST /translate
```

**Parameters**:
- `text`: Text to translate (string, required)
- `source_lang`: Source language code (string, optional, defaults to "auto")
- `target_lang`: Target language code (string, required, e.g., "zh-cn" for Simplified Chinese)

**Request Example**:
```json
{
    "text": "Hello, how are you?",
    "source_lang": "en",
    "target_lang": "zh-cn"
}
```

**Response**:
```json
{
    "original_text": "Hello, how are you?",
    "source_lang": "en",
    "target_lang": "zh-cn",
    "translated_text": "你好，你好吗？"
}
```

**Error Response** (e.g., invalid target language):
```json
{
    "detail": "Invalid target language: zh-xxx"
}
```

## Text-to-SQL Component

The Text-to-SQL component converts natural language questions into SQL queries for a retail database.

### Database Schema

| Table | Fields | Notes |
|-------|--------|-------|
| **Departments** | `dept_id` (PK), `dept_name`, `location`, `manager_id`, `budget` | Includes IT, HR, Sales, etc. |
| **Employees** | `emp_id` (PK), `first_name`, `last_name`, `email`, `phone`, `hire_date`, `job_title`, `salary`, `dept_id` (FK), `manager_id`, `status` | Status: Active, Inactive, On Leave |
| **Customers** | `customer_id` (PK), `first_name`, `last_name`, `email`, `phone`, `address`, `city`, `country`, `registration_date`, `credit_limit` | |
| **Orders** | `order_id` (PK), `customer_id` (FK), `order_date`, `total_amount`, `status` | Status: Pending, Processing, Shipped, Delivered, Cancelled |
| **Order Items** | `item_id` (PK), `order_id` (FK), `product_id` (FK), `quantity`, `unit_price`, `total_price` | |
| **Products** | `product_id` (PK), `product_name`, `category`, `price`, `stock_quantity`, `supplier_id` (FK), `description` | Categories: Electronics, Furniture |
| **Suppliers** | `supplier_id` (PK), `company_name`, `contact_name`, `email`, `phone`, `address`, `city`, `country` | |

### API Endpoint for `/text-to-sql`

```http
POST /text-to-sql
```

**Parameters**:
- `question`: Natural language question (string, required)

**Request Examples**:
1. Employee Query:
   ```json
   {
       "question": "Show me active IT department employees sorted by salary"
   }
   ```
2. Sales Analysis:
   ```json
   {
       "question": "How many new customers were acquired each month?"
   }
   ```

**Response Example**:
```json
{
    "status": "success",
    "sql_query": "SELECT TOP 3 YEAR(c.registration_date) AS Year, MONTH(c.registration_date) AS Month, COUNT(c.customer_id) AS NewCustomers FROM customers c GROUP BY YEAR(c.registration_date), MONTH(c.registration_date) ORDER BY Year, Month",
    "raw_result": [
        {
            "Year": 2025,
            "Month": 7,
            "NewCustomers": 2
        }
    ],
    "natural_language_response": "In July 2025, 2 new customers were acquired. No data is available for other months. Let me know if you need further details!",
    "tables_used": ["CUSTOMERS"],
    "question": "How many new customers were acquired each month?"
}
```

**Error Response** (e.g., invalid question):
```json
{
    "detail": "Unable to generate valid SQL query"
}
```

### SQL Agent Features

- **Schema Validation**:
  - Validates tables and columns
  - Verifies relationships
  - Checks SQL syntax
- **Query Generation**:
  - Supports complex JOINs
  - Includes TOP clause
  - Uses SQL Server syntax
  - Handles date and aggregation functions
- **Error Handling**:
  - Provides detailed error messages
  - Detects invalid queries
  - Reports schema mismatches
- **Result Processing**:
  - Formats natural language responses
  - Limits result size
  - Handles data types correctly

## Environment Variables

Create a `.env` file based on `.env.example` with the following variables:

```plaintext
# Database Configuration
DB_SERVER=your_server
DB_NAME=your_database
DB_USER=your_username
DB_PASSWORD=your_password
DB_DRIVER=ODBC Driver 17 for SQL Server

# LLM Configuration
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=meta-llama/llama-4-scout-17b-16e-instruct
```

**Note**: Keep the `.env` file secure and exclude it from version control.
