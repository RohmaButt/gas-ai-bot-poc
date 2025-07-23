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

1. Set up environment variables:
   - Copy `.env.example` to `.env`:
     ```bash
     cp .env.example .env
     ```

   - Edit `.env` with your configuration:
     ```
     # Database Configuration
     DB_SERVER=your_server
     DB_NAME=your_database
     DB_USER=your_username
     DB_PASSWORD=your_password
     DB_DRIVER=ODBC Driver 17 for SQL Server
     
     # LLM Configuration
      GROQ_API_KEY=your_groq_api_key
      GROQ_MODEL=meta-llama/llama-4-scout-17b-16e-instruct  # used this model Long Context
     ```

   - The `.env.example` file is provided as a template. Do **not** commit your real `.env` file to version control.

## Running the API

1. Start the FastAPI server:
```bash
uvicorn src.main:app --reload
```

The API will be available at `http://localhost:8000`

## API Endpoints for `/languages`

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

### 2. API Endpoint for `/speech-to-text`
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

### 3. API Endpoint for `/text-to-speech`
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
```

## Text-to-SQL Component

The SQL Agent component provides natural language to SQL query conversion for a retail database system.

### Database Schema

The system works with the following tables:

1. **Departments**
   - Fields: dept_id (PK), dept_name, location, manager_id, budget
   - Contains: IT, HR, Sales, Marketing, Finance, Operations departments

2. **Employees**
   - Fields: emp_id (PK), first_name, last_name, email, phone, hire_date, job_title, salary, dept_id (FK), manager_id, status
   - Status values: 'Active', 'Inactive', 'On Leave'

3. **Customers**
   - Fields: customer_id (PK), first_name, last_name, email, phone, address, city, country, registration_date, credit_limit

4. **Orders**
   - Fields: order_id (PK), customer_id (FK), order_date, total_amount, status
   - Status values: 'Pending', 'Processing', 'Shipped', 'Delivered', 'Cancelled'

5. **Order Items**
   - Fields: item_id (PK), order_id (FK), product_id (FK), quantity, unit_price, total_price

6. **Products**
   - Fields: product_id (PK), product_name, category, price, stock_quantity, supplier_id (FK), description
   - Categories: Electronics, Furniture

7. **Suppliers**
   - Fields: supplier_id (PK), company_name, contact_name, email, phone, address, city, country

### API Endpoint for `/text-to-sql`

```http
POST /text-to-sql
```

Parameters:
- `question` (string, required): Natural language question to convert to SQL

Example Requests:

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

Example Response:
```json
Result:
{
  "status": "success",
  "sql_query": "SELECT TOP 3\nYEAR(c.registration_date) AS Year,\nMONTH(c.registration_date) AS Month,\nCOUNT(c.customer_id) AS NewCustomers\nFROM\ncustomers c\nGROUP BY\nYEAR(c.registration_date),\nMONTH(c.registration_date)\nORDER BY\nYear,\nMonth",
  "raw_result": [
    {
      "Year": 2025,
      "Month": 7,
      "NewCustomers": 2
    }
  ],
  "natural_language_response": "Based on the data, here's the information on new customers acquired each month:\n\nIn July 2025, **2 new customers** were acquired.\n\nThat's the only data available for now. If you're looking for information on previous months or a longer period, please let me know and I can try to provide that for you! \n\nIf you have any other questions or need further assistance, feel free to ask!",
  "tables_used": [
    "CUSTOMERS"
  ],
  "question": "How many new customers were acquired each month?"
}
```

### SQL Agent Features

The SQL Agent includes several advanced features:

1. **Schema Validation**
   - Automatic table and column validation
   - Relationship verification
   - SQL syntax checking

2. **Query Generation**
   - Support for complex JOINs
   - Automatic TOP clause inclusion
   - Proper SQL Server syntax
   - Date and aggregation functions

3. **Error Handling**
   - Detailed error messages
   - Invalid query detection
   - Schema mismatch reporting

4. **Result Processing**
   - Natural language response formatting
   - Result size limiting
   - Proper data type handling

