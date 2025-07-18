from typing import List, Dict, Any, Optional
from langchain_experimental.sql import SQLDatabaseChain
from langchain_community.utilities import SQLDatabase
from langchain_groq import ChatGroq
from langchain.prompts.prompt import PromptTemplate
from langchain.chains.llm import LLMChain
import os
import json
import sqlite3
from dotenv import load_dotenv

# Load environment variables
load_dotenv(override=True)

class SQLAgent:
    def __init__(self, db_path: str = "retail.db"):
        """
        Initialize the SQL Agent with database connection and LLM.
        
        Args:
            db_path (str): Path to SQLite database
        """
        # Store database path
        self.db_path = db_path
        # Initialize database connection
        self.db = SQLDatabase.from_uri(f"sqlite:///{db_path}")
        
        # Initialize LLM with proper API key handling
        api_key = os.getenv('GROQ_API_KEY')
        if not api_key:
            raise ValueError("GROQ_API_KEY not found in environment variables")
            
        model_name = os.getenv("GROQ_MODEL", "mixtral-8x7b-32768")
        
        self.llm = ChatGroq(
            temperature=0,
            api_key=api_key,  # Use the actual API key from environment
            model=model_name
        )
        
        # Initialize database chain with proper configuration
        self.db_chain = SQLDatabaseChain.from_llm(
            llm=self.llm,
            db=self.db,
            verbose=True,
            return_intermediate_steps=True,
            top_k=10
        )

    def get_table_info(self) -> str:
        """Get information about the database schema."""
        return self.db.get_table_info()

    def test_connection(self) -> bool:
        """Test database connection and show table info."""
        try:
            table_info = self.get_table_info()
            print("Database connection successful!")
            print("Available tables and schema:")
            print(table_info)
            return True
        except Exception as e:
            print(f"Database connection failed: {e}")
            return False

    def _extract_tables_used(self, query: str) -> List[str]:
        """
        Extract table names used in the SQL query.
        
        Args:
            query (str): SQL query
            
        Returns:
            List[str]: List of table names used in the query
        """
        if not query or query == "No query generated":
            return []
            
        query_lower = query.lower()
        tables = []
        keywords = ["from ", "join ", "update ", "insert into ", "delete from "]
        
        for keyword in keywords:
            if keyword in query_lower:
                parts = query_lower.split(keyword)
                for part in parts[1:]:
                    words = part.split()
                    if words:
                        table = words[0].strip('();,')
                        if table and table not in tables and not table.startswith('('):
                            tables.append(table)
        
        return tables

    def _parse_sqlite_result(self, raw_result: Any, sql_query: str) -> List[Dict[str, Any]]:
        """
        Parse SQLite query results into a list of dictionaries.
        
        Args:
            raw_result (Any): Raw result from SQLite query
            sql_query (str): The executed SQL query
            
        Returns:
            List[Dict[str, Any]]: Parsed results as list of dictionaries
        """
        try:
            if not raw_result:
                return []
                
            # If result is already a list of dicts, return it
            if isinstance(raw_result, list) and all(isinstance(row, dict) for row in raw_result):
                return raw_result
            
            # Handle raw tuple/list results from SQLite
            if isinstance(raw_result, (list, tuple)) and len(raw_result) > 0:
                # Get column names from the SQL query or connect to DB
                columns = []
                
                # Try to extract column names from the SELECT statement
                if sql_query and "SELECT" in sql_query.upper():
                    try:
                        # Simple extraction - look for column names after SELECT
                        select_part = sql_query.upper().split("SELECT")[1].split("FROM")[0].strip()
                        if select_part and select_part != "*":
                            # Extract column names (simple case)
                            columns = [col.strip() for col in select_part.split(",")]
                            # Clean up column names (remove table prefixes, etc.)
                            columns = [col.split(".")[-1] for col in columns]
                    except:
                        pass
                
                # If we couldn't extract from SQL, try connecting to DB
                if not columns:
                    try:
                        conn = sqlite3.connect(self.db_path)
                        cursor = conn.cursor()
                        cursor.execute(sql_query)
                        columns = [desc[0] for desc in cursor.description] if cursor.description else []
                        cursor.close()
                        conn.close()
                    except:
                        # Fallback to generic column names
                        if raw_result and isinstance(raw_result[0], (list, tuple)):
                            columns = [f"col_{i}" for i in range(len(raw_result[0]))]
                        else:
                            columns = ["value"]
                
                # Convert rows to dictionaries
                result = []
                for row in raw_result:
                    if isinstance(row, (list, tuple)):
                        if len(columns) == len(row):
                            row_dict = dict(zip(columns, row))
                        else:
                            # Fallback if columns don't match
                            row_dict = {f"col_{i}": val for i, val in enumerate(row)}
                        result.append(row_dict)
                    else:
                        # Single value
                        result.append({"value": row})
                
                return result
            
            # Handle string results
            if isinstance(raw_result, str):
                try:
                    # Try to parse as JSON
                    result = json.loads(raw_result)
                    if isinstance(result, list):
                        return result
                except json.JSONDecodeError:
                    pass
                
                # Return as single string value
                return [{"value": raw_result}]
            
            # Handle single values
            if raw_result:
                return [{"value": raw_result}]
            
            return []
            
        except Exception as e:
            print(f"Error parsing result: {e}")
            return []

    def _generate_natural_language_response(self, question: str, sql_query: str, 
                                           query_result: List[Dict[str, Any]], status: str) -> str:
        """
        Generate a natural language response based on the query results.
        
        Args:
            question (str): Original question
            sql_query (str): Generated SQL query
            query_result (List[Dict[str, Any]]): Parsed query results
            status (str): Query execution status
            
        Returns:
            str: Natural language response
        """
        try:
            if status == "error":
                return f"I encountered an error while processing your question: '{question}'. Please try rephrasing your question."
            
            if not query_result:
                return f"I couldn't find any results for your question: '{question}'. The query executed successfully but returned no data."
            
            # Generate response based on data
            response = f"I found {len(query_result)} result(s) for your question:\n\n"
            
            for i, row in enumerate(query_result, 1):
                item_details = []
                for key, value in row.items():
                    if value is not None:
                        item_details.append(f"{key}: {value}")
                response += f"{i}. {', '.join(item_details)}\n"
            
            return response
                
        except Exception as e:
            return f"I found some results for your question about '{question}', but had trouble formatting them. Raw data available in the response."

    def query(self, question: str, top_k: int = 10) -> Dict[str, Any]:
        """
        Process a natural language question and return JSON results.
        
        Args:
            question (str): Natural language question
            top_k (int): Maximum number of results to return
            
        Returns:
            Dict[str, Any]: JSON formatted response
        """
        try:
            print(f"\nProcessing question: {question}")
            
            # Update the chain's top_k
            self.db_chain.top_k = top_k
            
            # Execute the chain - use just the question string
            result = self.db_chain.invoke(question)
            
            # Extract the SQL query from intermediate steps
            sql_query = "No query generated"
            raw_result = []
            
            if "intermediate_steps" in result and result["intermediate_steps"]:
                intermediate_steps = result["intermediate_steps"]
                if isinstance(intermediate_steps, list) and len(intermediate_steps) >= 2:
                    # First step is usually the SQL query
                    sql_step = intermediate_steps[0]
                    # Second step is usually the result
                    result_step = intermediate_steps[1]
                    
                    # Extract SQL query
                    if isinstance(sql_step, str):
                        sql_query = sql_step
                    elif hasattr(sql_step, 'content'):
                        sql_query = sql_step.content
                    else:
                        sql_query = str(sql_step)
                    
                    # Clean up SQL query
                    sql_query = sql_query.replace("SQLQuery:", "").replace("```sql", "").replace("```", "").strip()
                    
                    # Extract result data
                    if isinstance(result_step, (list, tuple)):
                        raw_result = result_step
                    elif isinstance(result_step, str) and result_step.startswith("SQLResult:"):
                        # Parse the result string
                        result_str = result_step.replace("SQLResult:", "").strip()
                        try:
                            # Try to evaluate the string as Python literal
                            import ast
                            raw_result = ast.literal_eval(result_str)
                        except:
                            raw_result = []
                    else:
                        raw_result = []
            
            # If we still don't have results, try to get them from the main result
            if not raw_result:
                chain_result = result.get("result", "No results found")
                if isinstance(chain_result, str) and "SQLResult:" in chain_result:
                    # Extract the result portion
                    result_part = chain_result.split("SQLResult:")[1].split("Answer:")[0].strip()
                    try:
                        import ast
                        raw_result = ast.literal_eval(result_part)
                    except:
                        raw_result = []
            
            # Parse the results into dictionaries
            parsed_result = self._parse_sqlite_result(raw_result, sql_query)
            
            # Determine status
            status = "success" if sql_query != "No query generated" and sql_query else "error"
            
            # Generate natural language response
            natural_response = self._generate_natural_language_response(
                question, sql_query, parsed_result, status
            )
            
            return {
                "status": status,
                "sql_query": sql_query,
                "raw_result": parsed_result,
                "natural_language_response": natural_response,
                "tables_used": self._extract_tables_used(sql_query),
                "question": question
            }
            
        except Exception as e:
            error_msg = str(e)
            print(f"Error processing query: {error_msg}")
            return {
                "status": "error",
                "sql_query": "",
                "raw_result": [],
                "natural_language_response": f"I encountered an error while processing your question: '{question}'. Error: {error_msg}",
                "tables_used": [],
                "question": question,
                "error_details": error_msg
            }

    def query_json(self, question: str, top_k: int = 10) -> str:
        """
        Process a natural language question and return JSON string.
        
        Args:
            question (str): Natural language question
            top_k (int): Maximum number of results to return
            
        Returns:
            str: JSON formatted string response
        """
        result = self.query(question, top_k)
        return json.dumps(result, indent=2, ensure_ascii=False)

    def execute_raw_sql(self, sql_query: str) -> Dict[str, Any]:
        """
        Execute a raw SQL query directly and return JSON response.
        
        Args:
            sql_query (str): SQL query to execute
            
        Returns:
            Dict[str, Any]: JSON Query results
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(sql_query)
            raw_result = cursor.fetchall()
            parsed_result = self._parse_sqlite_result(raw_result, sql_query)
            cursor.close()
            conn.close()
            
            natural_response = self._generate_natural_language_response(
                f"Direct SQL execution: {sql_query}", sql_query, parsed_result, "success"
            )
            
            return {
                "status": "success",
                "sql_query": sql_query,
                "raw_result": parsed_result,
                "natural_language_response": natural_response,
                "tables_used": self._extract_tables_used(sql_query),
                "question": f"Direct SQL execution: {sql_query}"
            }
        except Exception as e:
            return {
                "status": "error",
                "sql_query": sql_query,
                "raw_result": [],
                "natural_language_response": f"Error executing SQL query: {str(e)}",
                "tables_used": [],
                "question": f"Direct SQL execution: {sql_query}",
                "error_details": str(e)
            }
