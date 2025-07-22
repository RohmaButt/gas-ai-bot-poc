from typing import List, Dict, Any
from langchain_experimental.sql import SQLDatabaseChain
from langchain_community.utilities import SQLDatabase
from langchain_groq import ChatGroq
from langchain.prompts.prompt import PromptTemplate
import os
import json
import pyodbc
from urllib.parse import quote_plus
from dotenv import load_dotenv
import re

# Load environment variables
load_dotenv(override=True)

class SQLAgent:
    def __init__(self, connection_string: str = None):
        """
        Initialize the SQL Agent with database connection and LLM.
        
        Args:
            connection_string (str): SQL Server connection string. If None, uses environment variables.
        """
        if not connection_string:
            server = os.getenv('DB_SERVER', 'localhost')
            database = os.getenv('DB_NAME', 'dummy_test_db')
            username = os.getenv('DB_USER')
            password = os.getenv('DB_PASSWORD')
            driver = os.getenv('DB_DRIVER', 'ODBC Driver 17 for SQL Server')
            
            if not all([server, database, username, password]):
                raise ValueError("Database credentials not found in environment variables")
            
            params = {
                'DRIVER': driver,
                'SERVER': server,
                'DATABASE': database,
                'UID': username,
                'PWD': password,
                'Trusted_Connection': 'no',
                'Encrypt': 'yes',
                'TrustServerCertificate': 'yes'
            }
            connection_string = ';'.join([f'{k}={v}' for k, v in params.items()])
        
        self.connection_string = connection_string
        connection_uri = f"mssql+pyodbc:///?odbc_connect={quote_plus(connection_string)}"
        
        try:
            self.db = SQLDatabase.from_uri(connection_uri)
        except Exception as e:
            raise ValueError(f"Failed to connect to database: {str(e)}")
        
        api_key = os.getenv('GROQ_API_KEY')
        if not api_key:
            raise ValueError("GROQ_API_KEY not found in environment variables")
            
        model_name = os.getenv("GROQ_MODEL", "mixtral-8x7b-32768")
        
        self.llm = ChatGroq(
            temperature=0.1,
            api_key=api_key,
            model=model_name,
            max_tokens=1000,
            timeout=60
        )
        
        self.default_row_limit = int(os.getenv('SQL_ROW_LIMIT', '10'))
        
        self.custom_prompt = PromptTemplate(
            input_variables=["input", "table_info", "dialect", "default_row_limit"],
            template="""You are an expert SQL Server database developer. Generate a SQL query based on the following schema and question.

            Database Schema:
            {table_info}

            User Question: {input}

            CRITICAL REQUIREMENTS:
            1. Use ONLY tables and columns from the provided schema.
            2. Always include TOP {default_row_limit} in SELECT queries.
            3. Do NOT use square brackets [] around table or column names; use plain identifiers (e.g., employees.first_name).
            4. Use appropriate JOINs based on schema relationships.
            5. Return ONLY the SQL query - no explanations, markdown, or extra text.
            6. Use appropriate WHERE clauses for filtering.
            7. If the question cannot be answered with the schema, return "NO_VALID_QUERY_POSSIBLE".
            8. Use SQL Server specific functions (e.g., GETDATE(), DATEADD()).
            9. Ensure the query is syntactically correct and executable.

            SQL Query:
            """
        )
        
        self.db_chain = SQLDatabaseChain.from_llm(
            llm=self.llm,
            db=self.db,
            verbose=False,
            return_intermediate_steps=True,
            prompt=self.custom_prompt
        )
    
    def get_table_info(self, limit_tables: int = None) -> str:
        """
        Get optimized information about the database schema.
        """
        try:
            full_table_info = self.db.get_table_info()
            if limit_tables:
                lines = full_table_info.split('\n')
                limited_info = []
                tables_included = 0
                for line in lines:
                    if line.strip().startswith('CREATE TABLE'):
                        tables_included += 1
                        if tables_included > limit_tables:
                            limited_info.append("... (schema truncated)")
                            break
                    limited_info.append(line)
                return '\n'.join(limited_info)
            return full_table_info
        except Exception as e:
            return f"Error getting table info: {str(e)}"

    def test_connection(self) -> bool:
        """Test database connection and show limited table info."""
        try:
            table_info = self.get_table_info(limit_tables=7)
            print("Database connection successful!")
            print("Available tables and schema (limited):")
            print(table_info)
            return True
        except Exception as e:
            print(f"Database connection failed: {e}")
            return False

    def _extract_tables_and_columns(self, query: str) -> tuple[List[str], List[tuple[str, str]]]:
        """Extract table and column names used in the SQL query."""
        if not query or query == "NO_VALID_QUERY_POSSIBLE":
            return [], []
            
        query_lower = query.lower()
        tables = []
        columns = []
        
        table_patterns = [r'from\s+(\w+)', r'join\s+(\w+)']
        for pattern in table_patterns:
            matches = re.findall(pattern, query_lower)
            tables.extend([t for t in matches if t not in tables])
        
        column_pattern = r'(\w+)\.(\w+)'
        matches = re.findall(column_pattern, query_lower)
        columns.extend([(table, col) for table, col in matches if (table, col) not in columns])
        
        return tables, columns

    def _extract_alias_mapping(self, query: str) -> dict[str, str]:
        """Extract alias mappings from the SQL query (e.g., 'employees e' -> {'e': 'employees'})."""
        query_lower = query.lower()
        alias_mapping = {}
        pattern = r'(from|join)\s+(\w+)(?:\s+(\w+))?'
        matches = re.finditer(pattern, query_lower)
        for match in matches:
            _, table, alias = match.groups()
            if alias:
                alias_mapping[alias] = table
            else:
                alias_mapping[table] = table
        return alias_mapping

    def _is_valid_sql_query(self, query: str) -> tuple[bool, str]:
        """Check if the query is valid and matches available schema."""
        if not query or len(query.strip()) < 10:
            return False, "Query is empty or too short"
            
        if query.strip() == "NO_VALID_QUERY_POSSIBLE":
            return False, "LLM indicated no valid query possible"
            
        query_lower = query.lower().strip()
        
        schema_info = self.get_table_info()
        available_tables = set()
        available_columns = {}
        
        current_table = None
        for line in schema_info.split('\n'):
            line = line.strip()
            if line.startswith('CREATE TABLE'):
                table_match = re.search(r'CREATE TABLE \[?(\w+)\]?', line, re.IGNORECASE)
                if table_match:
                    current_table = table_match.group(1).lower()
                    available_tables.add(current_table)
                    available_columns[current_table] = []
            elif current_table and not line.startswith('CONSTRAINT') and line and not line.startswith(')'):
                column_name = line.split()[0].lower()
                available_columns[current_table].append(column_name)

        alias_mapping = self._extract_alias_mapping(query)
        referenced_tables = list(set(alias_mapping.values()))

        invalid_tables = [t for t in referenced_tables if t not in available_tables]
        if invalid_tables:
            return False, f"Query references invalid tables: {', '.join(invalid_tables)}"

        column_pattern = r'(\w+)\.(\w+)'
        referenced_columns = re.findall(column_pattern, query_lower)
        invalid_columns = []

        for alias, col in referenced_columns:
            if alias in alias_mapping:
                actual_table = alias_mapping[alias]
                if actual_table in available_columns and col.lower() in available_columns[actual_table]:
                    continue
                else:
                    invalid_columns.append(f"{alias}.{col}")
            else:
                invalid_columns.append(f"{alias}.{col} (undefined alias)")

        if invalid_columns:
            return False, f"Query references invalid columns: {', '.join(invalid_columns)}"

        # Improved structural validation
        select_patterns = [r'^\s*select\s+top', r'^\s*select\s+distinct\s+top', r'^\s*select\s+', r'^\s*select\s+\*']
        other_patterns = [r'^\s*insert\s+into', r'^\s*update\s+', r'^\s*delete\s+from']
        has_valid_start = any(re.match(pattern, query_lower, re.IGNORECASE) for pattern in select_patterns + other_patterns)
        
        # Use regex to reliably detect FROM clause
        has_from = bool(re.search(r'\s+from\s+\w+', query_lower, re.IGNORECASE)) or query_lower.startswith(('insert', 'update', 'delete'))
        is_reasonable_length = 10 <= len(query.strip()) <= 1000

        # Debug logging for validation checks
        if not has_valid_start:
            print("Validation failed: Invalid query start")
        if not has_from:
            print("Validation failed: Missing FROM clause")
        if not is_reasonable_length:
            print(f"Validation failed: Invalid query length ({len(query.strip())} characters)")

        if not (has_valid_start and has_from and is_reasonable_length):
            return False, "Query has invalid structure or syntax"
            
        return True, ""

    def _clean_sql_query(self, raw_query: str) -> str:
        """Clean and extract SQL query from LLM response, removing square brackets."""
        if not raw_query:
            return ""
        
        query = raw_query.replace("```sql", "").replace("```", "").strip()
        prefixes = [
            "SQLQuery:", "SQL Query:", "Query:", "Here's the SQL query:",
            "The SQL query is:", "Here is the query:", "Generated query:"
        ]
        for prefix in prefixes:
            if query.lower().startswith(prefix.lower()):
                query = query[len(prefix):].strip()
        
        lines = query.split('\n')
        cleaned_lines = [line for line in lines if not any(indicator in line.lower() for indicator in ['here is', 'this query', 'explanation:', 'note:'])]
        query = '\n'.join(cleaned_lines).rstrip('; \n\r\t')
        
        query = query.replace('[', '').replace(']', '')
        
        return query

    def _format_natural_language_response(self, results: List[Dict[str, Any]], question: str) -> str:
        """Format query results as natural language."""
        if not results:
            return f"No results found for: '{question}'"
            
        response_text = f"Found {len(results)} result(s) for '{question}':\n"
        for i, row in enumerate(results, 1):
            row_items = [f"{key}: {str(value)[:50] + '...' if len(str(value)) > 50 else str(value)}" for key, value in row.items() if value is not None]
            response_text += f"{i}. {', '.join(row_items)}\n"
        
        return response_text

    def _execute_sql_directly(self, sql_query: str) -> List[Dict[str, Any]]:
        """Execute SQL query directly using pyodbc."""
        try:
            conn = pyodbc.connect(self.connection_string)
            cursor = conn.cursor()
            
            if sql_query.lower().strip().startswith('select') and 'top' not in sql_query.lower()[:30]:
                parts = sql_query.split(' ', 1)
                sql_query = f"{parts[0]} TOP {self.default_row_limit} {parts[1]}"
            
            cursor.execute(sql_query)
            columns = [column[0] for column in cursor.description] if cursor.description else []
            rows = cursor.fetchall()
            
            results = [{columns[i] if i < len(columns) else f"col_{i}": value for i, value in enumerate(row)} for row in rows]
            
            cursor.close()
            conn.close()
            return results
            
        except Exception as e:
            print(f"SQL execution error: {e}")
            return []

    def query(self, question: str, top_k: int = None) -> Dict[str, Any]:
        """
        Process a natural language question and return results in natural language.
        
        Args:
            question (str): The natural language question to process
            top_k (int, optional): Number of results to return. If None, uses default_row_limit
        """
        top_k = top_k if top_k is not None else self.default_row_limit
        try:
            print(f"\nProcessing question: {question}")
            table_info = self.get_table_info()
            
            prompt = self.custom_prompt.format(
                input=question,
                table_info=table_info,
                dialect="mssql",
                default_row_limit=top_k
            )
            
            response = self.llm.invoke(prompt)
            raw_query = response.content if hasattr(response, 'content') else str(response)
            print(f"Raw SQL query generated: {raw_query}")
            sql_query = self._clean_sql_query(raw_query)
            
            is_valid, error_msg = self._is_valid_sql_query(sql_query)
            if not is_valid:
                print(f"Invalid SQL generated: {sql_query}\nReason: {error_msg}")
                return {
                    "status": "error",
                    "sql_query": sql_query,
                    "raw_result": [],
                    "natural_language_response": f"Unable to generate valid SQL for: '{question}'. {error_msg}",
                    "tables_used": [],
                    "question": question,
                    "error_details": error_msg
                }
            
            print(f"Executing SQL: {sql_query}")
            results = self._execute_sql_directly(sql_query)
            if len(results) > top_k:
                results = results[:top_k]
            
            response_text = self._format_natural_language_response(results, question)
            
            return {
                "status": "success",
                "sql_query": sql_query,
                "raw_result": results,
                "natural_language_response": response_text,
                "tables_used": self._extract_tables_and_columns(sql_query)[0],
                "question": question
            }
            
        except Exception as e:
            error_msg = str(e)
            print(f"Error processing query: {error_msg}")
            return {
                "status": "error",
                "sql_query": "",
                "raw_result": [],
                "natural_language_response": f"Error processing question: '{question}'. {error_msg}",
                "tables_used": [],
                "question": question,
                "error_details": error_msg
            }

    def query_json(self, question: str, top_k: int = 3) -> str:
        """Process question and return JSON string response."""
        result = self.query(question, top_k=top_k)
        return json.dumps(result, indent=2, ensure_ascii=False, default=str)

    def execute_raw_sql(self, sql_query: str) -> Dict[str, Any]:
        """Execute a raw SQL query and return results in natural language."""
        try:
            is_valid, error_msg = self._is_valid_sql_query(sql_query)
            if not is_valid:
                return {
                    "status": "error",
                    "sql_query": sql_query,
                    "raw_result": [],
                    "natural_language_response": f"Invalid SQL: {error_msg}",
                    "tables_used": [],
                    "question": f"Direct SQL execution: {sql_query}",
                    "error_details": error_msg
                }
            
            results = self._execute_sql_directly(sql_query)
            response_text = self._format_natural_language_response(results, f"Direct SQL: {sql_query}")
            
            return {
                "status": "success",
                "sql_query": sql_query,
                "raw_result": results,
                "natural_language_response": response_text,
                "tables_used": self._extract_tables_and_columns(sql_query)[0],
                "question": f"Direct SQL execution: {sql_query}"
            }
            
        except Exception as e:
            return {
                "status": "error",
                "sql_query": sql_query,
                "raw_result": [],
                "natural_language_response": f"Error executing SQL: {str(e)}",
                "tables_used": [],
                "question": f"Direct SQL execution: {sql_query}",
                "error_details": str(e)
            }

# if __name__ == "__main__":
#     try:
#         agent = SQLAgent()
#         if agent.test_connection():
#             print("\n" + "="*50)
#             print("Testing natural language queries...")
            
#             test_queries = [
#                 "Show me all IT department employees",
#                 "Who are the highest paid employees?",
#                 "Show me orders from February 2024",
#                 "What are the best selling products?",
#                 "Show customer order history with product details"
#             ]
            
#             for query in test_queries:
#                 print(f"\nExecuting query: {query}")
#                 result = agent.query_json(query)
#                 print("\nResult:")
#                 print(result)
#                 print("="*50)
            
#     except Exception as e:
#         print(f"Error: {e}")
#         import traceback
#         traceback.print_exc()