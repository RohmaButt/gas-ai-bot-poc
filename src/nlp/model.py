import requests
import os

def text_to_sql_api(text, schema):
    """Calls the Text2SQL.ai API to convert text to SQL."""
    api_key = os.environ.get("TEXT2SQL_API_KEY")
    if not api_key:
        print("Warning: TEXT2SQL_API_KEY environment variable not set. Using mock response.")
        if "customers" in text:
            return "SELECT * FROM customers"
        elif "products" in text:
            return "SELECT * FROM products"
        else:
            return None

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    data = {
        "question": text,
        "schema": schema,
    }

    response = requests.post("https://api.text2sql.ai/v1/sql", headers=headers, json=data)

    if response.status_code == 200:
        return response.json()["sql"]
    else:
        return None

def text_to_sql(text):
    """Converts natural language text to an SQL query."""
    # In the future, this will use a proper NLP model.
    # For now, we'll use a simple keyword-based approach.
    if "customers" in text:
        return "SELECT * FROM customers"
    elif "products" in text:
        return "SELECT * FROM products"
    else:
        return None