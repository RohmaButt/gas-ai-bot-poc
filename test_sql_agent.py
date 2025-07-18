"""
Simple API wrapper for the SQL Agent
This provides a clean interface for using the SQL Agent with JSON responses
"""

import json
from typing import Dict, Any
from src.nlp.sql_agent import SQLAgent

class SQLAgentAPI:
    def __init__(self, db_path: str = "retail.db"):
        """
        Initialize the SQL Agent API.
        
        Args:
            db_path (str): Path to SQLite database
        """
        self.agent = SQLAgent(db_path)
        
    def ask(self, question: str, return_json: bool = True) -> Dict[str, Any] | str:
        """
        Ask a natural language question and get a structured response.
        
        Args:
            question (str): Natural language question
            return_json (bool): Whether to return JSON string or dict
            
        Returns:
            Dict[str, Any] | str: Response as dictionary or JSON string
        """
        result = self.agent.query(question)
        
        if return_json:
            return json.dumps(result, indent=2, ensure_ascii=False)
        else:
            return result
    
    def get_response_summary(self, question: str) -> str:
        """
        Get just the natural language response for a question.
        
        Args:
            question (str): Natural language question
            
        Returns:
            str: Natural language response
        """
        result = self.agent.query(question)
        return result.get("natural_language_response", "No response generated")
    
    def get_sql_query(self, question: str) -> str:
        """
        Get just the SQL query for a question.
        
        Args:
            question (str): Natural language question
            
        Returns:
            str: Generated SQL query
        """
        result = self.agent.query(question)
        return result.get("sql_query", "No query generated")
    
    def execute_sql(self, sql_query: str, return_json: bool = True) -> Dict[str, Any] | str:
        """
        Execute raw SQL query.
        
        Args:
            sql_query (str): SQL query to execute
            return_json (bool): Whether to return JSON string or dict
            
        Returns:
            Dict[str, Any] | str: Response as dictionary or JSON string
        """
        result = self.agent.execute_raw_sql(sql_query)
        
        if return_json:
            return json.dumps(result, indent=2, ensure_ascii=False)
        else:
            return result

# Example usage
if __name__ == "__main__":
    # Initialize the API
    api = SQLAgentAPI()
    
    # Test questions
    test_questions = [
        "How many products do we have?",
        "Show me the most expensive product",
        "Which customer has made the most orders?",
        "What's the total revenue from all orders?"
    ]
    
    print("=== SQL Agent API Demo ===\n")
    
    for question in test_questions:
        print(f"Question: {question}")
        print("-" * 50)
        
        # Get full JSON response
        full_response = api.ask(question, return_json=False)
        
        # Display key information
        print(f"Status: {full_response['status']}")
        print(f"SQL Query: {full_response['sql_query']}")
        print(f"Natural Language Response: {full_response['natural_language_response']}")
        
        if full_response['status'] == 'error':
            print(f"Error: {full_response.get('error_details', 'Unknown error')}")
        
        print("\n" + "="*60 + "\n")
    
    # Demo of individual methods
    print("=== Individual Method Examples ===\n")
    
    question = "What is the average price of all products?"
    
    print(f"Question: {question}")
    print(f"Just the SQL: {api.get_sql_query(question)}")
    print(f"Just the response: {api.get_response_summary(question)}")
    
    print("\n" + "="*60 + "\n")
    