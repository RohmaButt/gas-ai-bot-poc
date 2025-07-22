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

### API Endpoint

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
  "question": "Find total sales by product category for the last month"
}
```

Example Response:
```json
{
  "status": "success",
  "sql_query": "SELECT TOP 10 e.first_name, e.last_name, e.job_title, d.dept_name, e.salary FROM employees e INNER JOIN departments d ON e.dept_id = d.dept_id WHERE d.dept_name = 'IT' AND e.status = 'Active' ORDER BY e.salary DESC",
  "raw_result": [
    {
      "first_name": "John",
      "last_name": "Doe",
      "job_title": "IT Manager",
      "dept_name": "IT",
      "salary": 95000.00
    }
  ],
  "natural_language_response": "Found 1 employee(s) in the IT department:\n1. John Doe, IT Manager, Salary: $95,000.00",
  "tables_used": ["employees", "departments"]
}
```

Error Response Example:
```json
{
  "detail": "GROQ_API_KEY environment variable not found. Please add it to your .env file."
}
```

## Environment Variables

The following environment variables are required:

### API Configuration
- `GROQ_API_KEY`: Your Groq API key (required)
- `GROQ_MODEL`: The Groq model to use (default: mixtral-8x7b-32768)

### Database Configuration
- `DB_SERVER`: SQL Server hostname
- `DB_NAME`: Database name
- `DB_USER`: Database username
- `DB_PASSWORD`: Database password
- `DB_DRIVER`: SQL Server driver (default: "ODBC Driver 17 for SQL Server")
- `SQL_ROW_LIMIT`: Maximum number of rows to return (default: 10)

See `.env.example` for a template.

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
