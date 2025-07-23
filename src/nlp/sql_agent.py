from typing import List, Dict, Any, Optional
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
            temperature=0,  # Reduced temperature for more consistent results
            api_key=api_key,
            model=model_name,
            max_tokens=1500,  # Increased for better responses
            timeout=60
        )
        
        self.default_row_limit = int(os.getenv('SQL_ROW_LIMIT', '10'))
        
        # Store actual schema with relationships
        self.actual_schema = {}
        self.table_relationships = {}
        self._load_complete_schema()
        
        # Improved prompt template
        self.custom_prompt = PromptTemplate(
            input_variables=["input", "table_info", "relationships", "sample_data", "default_row_limit"],
            template="""You are an expert SQL Server database developer. Generate a SQL query based on the schema, relationships, and sample data provided.

DATABASE SCHEMA:
{table_info}

TABLE RELATIONSHIPS:
{relationships}

SAMPLE DATA (for reference):
{sample_data}

User Question: {input}

CRITICAL REQUIREMENTS:
1. Use EXACTLY the table and column names as shown in the schema (case-sensitive)
2. Always include "TOP {default_row_limit}" in SELECT queries with proper spacing
3. DO NOT use square brackets [] around names
4. Use the relationships shown above for JOINs - do not assume relationships that aren't listed
5. Only use tables and columns that exist in the schema
6. Return ONLY the SQL query without explanations or markdown
7. If no valid query is possible, return "NO_VALID_QUERY_POSSIBLE"
8. Use proper SQL Server syntax (GETDATE(), etc.)
9. For customer searches, use BCUSTOM table (CUSTNO, FNAME, SNAME, etc.)
10. For payments/invoices, use DSAMASTER table (AMOUNT, PAYED, SADATE, etc.)
11. For areas/cities, use area table if it exists
12. Use table aliases for better readability when joining tables
13. When searching for text values, consider using LIKE with wildcards if exact matches might fail
14. Check the sample data to understand actual data formats and values

COMMON PATTERNS:
- BCUSTOM.CUSTNO links to other tables via CUSTNO
- COMPNO appears in most tables as a company identifier
- Most tables have COMPNO as part of composite keys
- Phone numbers are in TEL1, TEL2, TELM columns in BCUSTOM
- Customer names are in FNAME, SNAME in BCUSTOM
- Payment info is in DSAMASTER (AMOUNT, PAYED columns)

QUERY VALIDATION CHECKLIST:
- All table names exist in schema? 
- All column names exist in their tables?
- JOIN conditions use actual relationships or common key columns?
- TOP clause included for SELECT queries?
- No square brackets used?
- Consider if data might be empty and query is still valid?

SQL Query:"""
        )
        
        self.db_chain = SQLDatabaseChain.from_llm(
            llm=self.llm,
            db=self.db,
            verbose=False,
            return_intermediate_steps=True,
            prompt=self.custom_prompt
        )
    
    def _load_complete_schema(self):
        """Load complete database schema including relationships."""
        try:
            conn = pyodbc.connect(self.connection_string)
            cursor = conn.cursor()
            
            # Get all tables with their columns
            cursor.execute("""
                SELECT 
                    t.TABLE_NAME,
                    c.COLUMN_NAME,
                    c.DATA_TYPE,
                    c.IS_NULLABLE,
                    c.COLUMN_DEFAULT,
                    CASE WHEN pk.COLUMN_NAME IS NOT NULL THEN 'YES' ELSE 'NO' END as IS_PRIMARY_KEY
                FROM INFORMATION_SCHEMA.TABLES t
                LEFT JOIN INFORMATION_SCHEMA.COLUMNS c ON t.TABLE_NAME = c.TABLE_NAME
                LEFT JOIN (
                    SELECT ku.TABLE_NAME, ku.COLUMN_NAME
                    FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS tc
                    JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE ku ON tc.CONSTRAINT_NAME = ku.CONSTRAINT_NAME
                    WHERE tc.CONSTRAINT_TYPE = 'PRIMARY KEY'
                ) pk ON c.TABLE_NAME = pk.TABLE_NAME AND c.COLUMN_NAME = pk.COLUMN_NAME
                WHERE t.TABLE_TYPE = 'BASE TABLE'
                ORDER BY t.TABLE_NAME, c.ORDINAL_POSITION
            """)
            
            schema_data = cursor.fetchall()
            
            # Organize schema data
            current_table = None
            for row in schema_data:
                table_name, col_name, data_type, is_nullable, default_val, is_pk = row
                
                if table_name != current_table:
                    current_table = table_name
                    self.actual_schema[table_name.upper()] = {
                        'original_name': table_name,
                        'columns': {}
                    }
                
                if col_name:  # Skip if column is None
                    self.actual_schema[table_name.upper()]['columns'][col_name.upper()] = {
                        'original_name': col_name,
                        'data_type': data_type,
                        'is_nullable': is_nullable,
                        'is_primary_key': is_pk == 'YES',
                        'default': default_val
                    }
            
            # Get foreign key relationships
            cursor.execute("""
                SELECT 
                    fk.TABLE_NAME as FK_TABLE,
                    fk.COLUMN_NAME as FK_COLUMN,
                    pk.TABLE_NAME as PK_TABLE,
                    pk.COLUMN_NAME as PK_COLUMN,
                    fk.CONSTRAINT_NAME
                FROM INFORMATION_SCHEMA.REFERENTIAL_CONSTRAINTS rc
                JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE fk ON rc.CONSTRAINT_NAME = fk.CONSTRAINT_NAME
                JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE pk ON rc.UNIQUE_CONSTRAINT_NAME = pk.CONSTRAINT_NAME
                ORDER BY fk.TABLE_NAME, fk.COLUMN_NAME
            """)
            
            relationships = cursor.fetchall()
            for fk_table, fk_col, pk_table, pk_col, constraint_name in relationships:
                if fk_table.upper() not in self.table_relationships:
                    self.table_relationships[fk_table.upper()] = []
                
                self.table_relationships[fk_table.upper()].append({
                    'fk_column': fk_col,
                    'references_table': pk_table,
                    'references_column': pk_col,
                    'constraint_name': constraint_name
                })
            
            # If no formal FK relationships found, infer common relationships based on column names
            if not self.table_relationships:
                self._infer_relationships()
            
            cursor.close()
            conn.close()
            
            print(f"Loaded schema for {len(self.actual_schema)} tables with {len(self.table_relationships)} relationship sets")
            
        except Exception as e:
            print(f"Warning: Could not load complete schema: {e}")
            self.actual_schema = {}
            self.table_relationships = {}

    def _infer_relationships(self):
        """Infer likely relationships based on common column naming patterns."""
        print("No formal FK relationships found. Inferring relationships based on column patterns...")
        
        # Common relationship patterns in your database
        inferred_relationships = {
            'BCUSTOM': [
                # Customers are referenced by CUSTNO in other tables
                {'pattern': 'CUSTNO', 'description': 'Customer reference'}
            ],
            'COMMON_KEYS': [
                # Company number appears in most tables
                {'pattern': 'COMPNO', 'description': 'Company reference'},
                # Department references
                {'pattern': 'DPID', 'description': 'Department reference'},
                # Area/location references  
                {'pattern': 'ZIPCODE', 'description': 'Area/ZIP code reference'}
            ]
        }
        
        # Find tables with common key patterns
        for table_key, table_data in self.actual_schema.items():
            table_name = table_data['original_name']
            columns = [col_data['original_name'] for col_data in table_data['columns'].values()]
            
            relationships = []
            
            # Check for customer references
            if 'CUSTNO' in [c.upper() for c in columns] and table_name != 'BCUSTOM':
                relationships.append({
                    'fk_column': 'CUSTNO',
                    'references_table': 'BCUSTOM', 
                    'references_column': 'CUSTNO',
                    'constraint_name': f'INFERRED_{table_name}_CUSTNO'
                })
            
            # Check for company references
            if 'COMPNO' in [c.upper() for c in columns]:
                relationships.append({
                    'fk_column': 'COMPNO',
                    'references_table': 'COMPANIES',
                    'references_column': 'COMPNO', 
                    'constraint_name': f'INFERRED_{table_name}_COMPNO'
                })
            
            # Check for area/zipcode references
            if 'ZIPCODE' in [c.upper() for c in columns] and table_name != 'area':
                if 'AREA' in [t['original_name'].upper() for t in self.actual_schema.values()]:
                    relationships.append({
                        'fk_column': 'ZIPCODE',
                        'references_table': 'area',
                        'references_column': 'zipcode',
                        'constraint_name': f'INFERRED_{table_name}_ZIPCODE'
                    })
            
            if relationships:
                self.table_relationships[table_key] = relationships

    def get_enhanced_table_info(self, limit_tables: int = None) -> str:
        """Get enhanced table information including column details and constraints."""
        try:
            if not self.actual_schema:
                self._load_complete_schema()
            
            schema_info = []
            tables_included = 0
            
            for table_key, table_data in self.actual_schema.items():
                if limit_tables and tables_included >= limit_tables:
                    schema_info.append("... (schema truncated)")
                    break
                
                table_name = table_data['original_name']
                schema_info.append(f"\nTable: {table_name}")
                schema_info.append("-" * (len(table_name) + 7))
                
                if table_data['columns']:
                    for col_key, col_data in table_data['columns'].items():
                        col_name = col_data['original_name']
                        data_type = col_data['data_type']
                        is_pk = " (PK)" if col_data.get('is_primary_key') else ""
                        nullable = " NOT NULL" if col_data.get('is_nullable') == 'NO' else ""
                        schema_info.append(f"  {col_name}: {data_type}{is_pk}{nullable}")
                else:
                    schema_info.append("  -- No columns found")
                
                tables_included += 1
            
            return "\n".join(schema_info)
            
        except Exception as e:
            return f"Error getting enhanced table info: {str(e)}"

    def get_relationship_info(self) -> str:
        """Get foreign key relationship information."""
        if not self.table_relationships:
            return "No foreign key relationships found."
        
        rel_info = []
        for table, relationships in self.table_relationships.items():
            table_original = self.actual_schema.get(table, {}).get('original_name', table)
            rel_info.append(f"\n{table_original} relationships:")
            for rel in relationships:
                if 'INFERRED' in rel['constraint_name']:
                    rel_info.append(f"  {table_original}.{rel['fk_column']} -> {rel['references_table']}.{rel['references_column']} (inferred)")
                else:
                    rel_info.append(f"  {table_original}.{rel['fk_column']} -> {rel['references_table']}.{rel['references_column']}")
        
        return "\n".join(rel_info) if rel_info else "No relationships defined."

    def _get_sample_data_info(self, table_name: str, limit: int = 5) -> str:
        """Get sample data from a table to help with query generation."""
        try:
            conn = pyodbc.connect(self.connection_string)
            cursor = conn.cursor()
            
            # Get sample data
            cursor.execute(f"SELECT TOP {limit} * FROM {table_name}")
            rows = cursor.fetchall()
            columns = [column[0] for column in cursor.description] if cursor.description else []
            
            if not rows:
                cursor.close()
                conn.close()
                return f"Table {table_name} appears to be empty."
            
            # Get row count
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            total_rows = cursor.fetchone()[0]
            
            cursor.close()
            conn.close()
            
            sample_info = f"\nSample data from {table_name} (showing {len(rows)} of {total_rows} rows):"
            
            # Show sample values for key columns
            key_columns = ['CUSTNO', 'FNAME', 'SNAME', 'CITY', 'TEL1', 'TEL2', 'TELM', 'AMOUNT', 'PAYED', 'COMPNO']
            shown_columns = [col for col in columns if col.upper() in [k.upper() for k in key_columns]][:6]
            
            if not shown_columns:
                shown_columns = columns[:4]  # Show first 4 columns if no key columns
            
            for i, row in enumerate(rows):
                row_data = []
                for j, col in enumerate(shown_columns):
                    if j < len(row):
                        value = str(row[j])[:20] if row[j] is not None else 'NULL'
                        row_data.append(f"{col}: {value}")
                sample_info += f"\n  Row {i+1}: {', '.join(row_data)}"
            
            return sample_info
            
        except Exception as e:
            return f"Could not get sample data from {table_name}: {str(e)}"

    def test_connection(self) -> bool:
        """Test database connection and show enhanced schema info."""
        try:
            table_info = self.get_enhanced_table_info(limit_tables=5)
            relationship_info = self.get_relationship_info()
            
            print("Database connection successful!")
            print("Available tables and schema (limited):")
            print(table_info)
            print("\nTable Relationships:")
            print(relationship_info)
            
            # Show sample data for key tables
            print("\nSample Data Preview:")
            key_tables = ['BCUSTOM', 'DSAMASTER']
            for table_name in key_tables:
                if table_name.upper() in self.actual_schema:
                    print(self._get_sample_data_info(table_name, 2))
            
            return True
        except Exception as e:
            print(f"Database connection failed: {e}")
            return False

    def _normalize_identifier(self, identifier: str) -> str:
        """Normalize table/column identifiers for comparison."""
        return identifier.upper().strip()

    def _validate_query_against_schema(self, query: str) -> tuple[bool, str, List[str]]:
        """Enhanced query validation against actual database schema."""
        if not query or len(query.strip()) < 10:
            return False, "Query is empty or too short", []
            
        if query.strip() == "NO_VALID_QUERY_POSSIBLE":
            return False, "LLM indicated no valid query possible", []
        
        query_upper = query.upper().strip()
        suggestions = []
        
        # Check TOP clause formatting
        if re.search(r'\bTOP\d+\b', query_upper):
            return False, "TOP clause missing space (use 'TOP 10' not 'TOP10')", []

        # Extract and validate table references
        table_pattern = r'(?:FROM|JOIN)\s+(\w+)(?:\s+(?:AS\s+)?(\w+))?'
        table_matches = re.findall(table_pattern, query_upper)
        
        # Build alias mapping
        alias_map = {}
        referenced_tables = []
        
        for table, alias in table_matches:
            table_norm = self._normalize_identifier(table)
            referenced_tables.append(table_norm)
            
            # Map both table name and alias (if exists) to normalized table name
            alias_map[table_norm] = table_norm
            if alias:
                alias_norm = self._normalize_identifier(alias)
                alias_map[alias_norm] = table_norm

        # Validate all referenced tables exist
        available_tables = set(self.actual_schema.keys())
        invalid_tables = [t for t in set(referenced_tables) if t not in available_tables]
        
        if invalid_tables:
            available_names = [self.actual_schema[t]['original_name'] for t in available_tables]
            error_msg = f"Invalid table(s): {', '.join(invalid_tables)}. Available: {', '.join(available_names)}"
            
            # Suggest similar table names
            for invalid_table in invalid_tables:
                similar = [name for name in available_names if invalid_table.lower() in name.lower() or name.lower() in invalid_table.lower()]
                if similar:
                    suggestions.append(f"Did you mean '{similar[0]}' instead of '{invalid_table}'?")
            
            return False, error_msg, suggestions

        # Validate column references
        column_pattern = r'(\w+)\.(\w+)'
        column_matches = re.findall(column_pattern, query_upper)
        
        invalid_columns = []
        for table_or_alias, column in column_matches:
            table_or_alias_norm = self._normalize_identifier(table_or_alias)
            column_norm = self._normalize_identifier(column)
            
            # Resolve table name from alias
            actual_table = alias_map.get(table_or_alias_norm)
            if actual_table and actual_table in self.actual_schema:
                table_columns = self.actual_schema[actual_table]['columns']
                if column_norm not in table_columns:
                    original_table_name = self.actual_schema[actual_table]['original_name']
                    invalid_columns.append(f"{original_table_name}.{column}")
                    
                    # Suggest similar columns
                    available_cols = [col_data['original_name'] for col_data in table_columns.values()]
                    similar_cols = [col for col in available_cols if column.lower() in col.lower() or col.lower() in column.lower()]
                    if similar_cols:
                        suggestions.append(f"Did you mean '{original_table_name}.{similar_cols[0]}'?")
                    else:
                        suggestions.append(f"Available columns in {original_table_name}: {', '.join(available_cols[:5])}{'...' if len(available_cols) > 5 else ''}")

        if invalid_columns:
            return False, f"Invalid column(s): {', '.join(invalid_columns)}", suggestions

        # Basic syntax validation
        if not re.search(r'^\s*SELECT\s+', query_upper):
            if not any(query_upper.strip().startswith(cmd) for cmd in ['INSERT', 'UPDATE', 'DELETE']):
                return False, "Query must start with SELECT, INSERT, UPDATE, or DELETE", []

        return True, "", suggestions

    def _clean_and_validate_sql_query(self, raw_query: str) -> str:
        """Clean SQL query and ensure proper formatting."""
        if not raw_query:
            return ""
        
        # Remove markdown and common prefixes
        query = raw_query.replace("```sql", "").replace("```", "").strip()
        
        prefixes = [
            "SQLQuery:", "SQL Query:", "Query:", "Here's the SQL query:",
            "The SQL query is:", "Here is the query:", "Generated query:"
        ]
        for prefix in prefixes:
            if query.lower().startswith(prefix.lower()):
                query = query[len(prefix):].strip()
        
        # Remove explanatory text
        lines = query.split('\n')
        sql_lines = []
        for line in lines:
            line = line.strip()
            if line and not any(skip in line.lower() for skip in ['here is', 'this query', 'explanation:', 'note:', 'the above']):
                sql_lines.append(line)
        
        query = '\n'.join(sql_lines).rstrip('; \n\r\t')
        
        # Remove square brackets and fix spacing
        query = query.replace('[', '').replace(']', '')
        query = re.sub(r'\bTOP(\d+)\b', r'TOP \1', query, flags=re.IGNORECASE)
        
        return query

    def _execute_sql_directly(self, sql_query: str) -> tuple[List[Dict[str, Any]], str]:
        """Execute SQL query with enhanced error handling."""
        try:
            conn = pyodbc.connect(self.connection_string)
            cursor = conn.cursor()
            
            # Ensure TOP clause for SELECT queries
            query_upper = sql_query.upper().strip()
            if query_upper.startswith('SELECT') and 'TOP' not in query_upper[:50]:
                parts = sql_query.split(' ', 1)
                if len(parts) > 1:
                    sql_query = f"{parts[0]} TOP {self.default_row_limit} {parts[1]}"
            
            print(f"Executing SQL: {sql_query}")
            cursor.execute(sql_query)
            
            columns = [column[0] for column in cursor.description] if cursor.description else []
            rows = cursor.fetchall()
            
            results = []
            for row in rows:
                row_dict = {}
                for i, value in enumerate(row):
                    col_name = columns[i] if i < len(columns) else f"col_{i}"
                    row_dict[col_name] = value
                results.append(row_dict)
            
            cursor.close()
            conn.close()
            return results, ""
            
        except Exception as e:
            error_msg = str(e)
            print(f"SQL execution error: {error_msg}")
            return [], error_msg

    def _format_natural_language_response(self, results: List[Dict[str, Any]], question: str) -> str:
        """Format query results as natural language using LLM."""
        if not results:
            return self._format_no_results_response(question)
        
        try:
            # Prepare data for LLM formatting
            results_json = json.dumps(results, indent=2, default=str)
            
            # Create prompt for natural language formatting
            format_prompt = f"""You are a helpful assistant that converts database query results into natural, conversational responses.

User's Question: "{question}"

Query Results (JSON format):
{results_json}

Instructions:
1. Convert the results into a natural, conversational response
2. Make it sound human and friendly
3. Use appropriate formatting (bullets, numbers, etc.) when helpful
4. Highlight key information that answers the user's question
5. If there are multiple results, organize them clearly
6. Use proper grammar and natural language flow
7. Keep technical database column names minimal - translate them to user-friendly terms when possible
8. For customer data: CUSTNO = Customer ID, FNAME = First Name, SNAME = Last Name, TEL1/TEL2/TELM = Phone Numbers
9. For financial data: AMOUNT = Amount, PAYED = Amount Paid, SADATE = Sale Date, SANO = Sale Number
10. If amounts are involved, format them as currency when appropriate

Respond in a natural, helpful tone as if you're directly answering the user's question."""

            response = self.llm.invoke(format_prompt)
            formatted_response = response.content if hasattr(response, 'content') else str(response)
            
            return formatted_response.strip()
            
        except Exception as e:
            print(f"Error formatting with LLM: {e}")
            # Fallback to basic formatting if LLM fails
            return self._basic_format_response(results, question)
    
    def _format_no_results_response(self, question: str) -> str:
        """Format no results response using LLM for more intelligent suggestions."""
        try:
            no_results_prompt = f"""You are a helpful database assistant. A user asked a question and the SQL query executed successfully, but returned no results.

User's Question: "{question}"

The database contains tables for:
- Customers (BCUSTOM): customer information, names, phone numbers, addresses
- Sales/Payments (DSAMASTER): transaction records, amounts, payment status
- Areas (area): location/address information
- And many other business tables

Your task is to create a helpful response that:
1. Acknowledges that no results were found
2. Suggests possible reasons why (be specific to their question)
3. Provides alternative search suggestions
4. Maintains a helpful, encouraging tone
5. Keep it concise (2-3 sentences)

Common reasons for no results:
- Exact name/phone number doesn't exist in database
- Spelling variations or different formats
- Data might be stored differently than expected
- No matching records for the specific criteria

Create a natural, helpful response that guides the user on what to try next."""

            response = self.llm.invoke(no_results_prompt)
            formatted_response = response.content if hasattr(response, 'content') else str(response)
            
            return formatted_response.strip()
            
        except Exception as e:
            print(f"Error formatting no results with LLM: {e}")
            return f"No results found for: '{question}'. The query executed successfully but no matching records were found. Try using different search terms or check if the data exists in the database."
    
    def _basic_format_response(self, results: List[Dict[str, Any]], question: str) -> str:
        """Fallback basic formatting method."""
        response_text = f"Found {len(results)} result(s) for '{question}':\n\n"
        
        for i, row in enumerate(results, 1):
            formatted_items = []
            for key, value in row.items():
                if value is not None:
                    # Format different data types appropriately
                    if isinstance(value, (int, float)):
                        formatted_value = str(value)
                    elif len(str(value)) > 50:
                        formatted_value = str(value)[:47] + "..."
                    else:
                        formatted_value = str(value)
                    formatted_items.append(f"{key}: {formatted_value}")
            
            response_text += f"{i}. {' | '.join(formatted_items)}\n"
        
        return response_text

    def query(self, question: str, top_k: int = None) -> Dict[str, Any]:
        """Process natural language question with enhanced error handling."""
        top_k = top_k if top_k is not None else self.default_row_limit
        
        try:
            # Get enhanced schema information
            table_info = self.get_enhanced_table_info()
            relationship_info = self.get_relationship_info()
            
            # Get sample data for key tables to help with query generation
            sample_data = ""
            key_tables = ['BCUSTOM', 'DSAMASTER', 'area']
            for table_name in key_tables:
                if table_name.upper() in self.actual_schema:
                    sample_data += self._get_sample_data_info(table_name, 3)
            
            # Generate SQL using improved prompt
            prompt = self.custom_prompt.format(
                input=question,
                table_info=table_info,
                relationships=relationship_info,
                sample_data=sample_data if sample_data else "No sample data available.",
                default_row_limit=top_k
            )
            
            print(f"Generating SQL for: {question}")
            response = self.llm.invoke(prompt)
            raw_query = response.content if hasattr(response, 'content') else str(response)
            print(f"Raw LLM response: {raw_query}")
            
            # Clean and validate the query
            sql_query = self._clean_and_validate_sql_query(raw_query)
            print(f"Cleaned SQL query: {sql_query}")
            
            # Validate against schema
            is_valid, error_msg, suggestions = self._validate_query_against_schema(sql_query)
            if not is_valid:
                print(f"Schema validation failed: {error_msg}")
                return {
                    "status": "error",
                    "sql_query": sql_query,
                    "raw_result": [],
                    "natural_language_response": self._create_helpful_error_message(question, error_msg, suggestions),
                    "tables_used": [],
                    "question": question,
                    "error_details": error_msg,
                    "suggestions": suggestions
                }
            
            # Execute the query
            results, execution_error = self._execute_sql_directly(sql_query)
            
            if execution_error:
                return {
                    "status": "error",
                    "sql_query": sql_query,
                    "raw_result": [],
                    "natural_language_response": f"Query validation passed but execution failed: {execution_error}",
                    "tables_used": [],
                    "question": question,
                    "error_details": execution_error
                }
            
            # Limit results
            if len(results) > top_k:
                results = results[:top_k]
            
            # Format response
            response_text = self._format_natural_language_response(results, question)
            
            return {
                "status": "success",
                "sql_query": sql_query,
                "raw_result": results,
                "natural_language_response": response_text,
                "tables_used": self._extract_tables_from_query(sql_query),
                "question": question
            }
            
        except Exception as e:
            error_msg = str(e)
            print(f"Unexpected error: {error_msg}")
            return {
                "status": "error",
                "sql_query": "",
                "raw_result": [],
                "natural_language_response": f"Unexpected error processing '{question}': {error_msg}",
                "tables_used": [],
                "question": question,
                "error_details": error_msg
            }

    def _extract_tables_from_query(self, query: str) -> List[str]:
        """Extract table names from SQL query."""
        if not query:
            return []
        
        query_upper = query.upper()
        table_pattern = r'(?:FROM|JOIN)\s+(\w+)'
        matches = re.findall(table_pattern, query_upper)
        return list(set(matches))

    def _create_helpful_error_message(self, question: str, error_msg: str, suggestions: List[str]) -> str:
        """Create helpful error message with suggestions using LLM."""
        try:
            # Create prompt for natural error message formatting
            error_prompt = f"""You are a helpful database assistant. A user asked a question but there was an issue with generating or executing the SQL query.

User's Question: "{question}"
Technical Error: {error_msg}
Suggestions: {', '.join(suggestions) if suggestions else 'None'}

Your task is to create a friendly, helpful response that:
1. Acknowledges the user's question
2. Explains what went wrong in simple terms (avoid technical jargon)
3. Provides actionable suggestions if available
4. Encourages the user to try again with different wording
5. Maintains a helpful, apologetic tone

Available tables in the database include: BCUSTOM (customers), DSAMASTER (sales/payments), area (locations), and many others.

Common issues:
- Table or column names don't exist
- No data matches the search criteria
- Query syntax problems

Create a natural, conversational response (2-4 sentences) that helps the user understand what to do next."""

            response = self.llm.invoke(error_prompt)
            formatted_error = response.content if hasattr(response, 'content') else str(response)
            
            return formatted_error.strip()
            
        except Exception as e:
            print(f"Error formatting error message with LLM: {e}")
            # Fallback to basic error formatting
            return self._basic_error_format(question, error_msg, suggestions)
    
    def _basic_error_format(self, question: str, error_msg: str, suggestions: List[str]) -> str:
        """Fallback basic error formatting method."""
        base_msg = f"I couldn't process your question: '{question}'\n\nReason: {error_msg}"
        
        if suggestions:
            base_msg += f"\n\nSuggestions:\n• " + "\n• ".join(suggestions)
        
        # Add general help
        if "Invalid table" in error_msg:
            available_tables = [self.actual_schema[t]['original_name'] for t in self.actual_schema.keys()]
            base_msg += f"\n\nAvailable tables: {', '.join(available_tables[:10])}{'...' if len(available_tables) > 10 else ''}"
        
        base_msg += f"\n\nPlease rephrase your question using the correct table and column names."
        return base_msg

    def query_json(self, question: str, top_k: int = 3) -> str:
        """Process question and return JSON string response."""
        result = self.query(question, top_k=top_k)
        return json.dumps(result, indent=2, ensure_ascii=False, default=str)

    def execute_raw_sql(self, sql_query: str) -> Dict[str, Any]:
        """Execute raw SQL query with validation."""
        try:
            is_valid, error_msg, suggestions = self._validate_query_against_schema(sql_query)
            if not is_valid:
                return {
                    "status": "error",
                    "sql_query": sql_query,
                    "raw_result": [],
                    "natural_language_response": self._create_helpful_error_message(f"Direct SQL: {sql_query}", error_msg, suggestions),
                    "tables_used": [],
                    "question": f"Direct SQL execution: {sql_query}",
                    "error_details": error_msg,
                    "suggestions": suggestions
                }
            
            results, execution_error = self._execute_sql_directly(sql_query)
            
            if execution_error:
                return {
                    "status": "error",
                    "sql_query": sql_query,
                    "raw_result": [],
                    "natural_language_response": f"SQL execution failed: {execution_error}",
                    "tables_used": [],
                    "question": f"Direct SQL execution: {sql_query}",
                    "error_details": execution_error
                }
            
            response_text = self._format_natural_language_response(results, f"Direct SQL: {sql_query}")
            
            return {
                "status": "success",
                "sql_query": sql_query,
                "raw_result": results,
                "natural_language_response": response_text,
                "tables_used": self._extract_tables_from_query(sql_query),
                "question": f"Direct SQL execution: {sql_query}"
            }
            
        except Exception as e:
            return {
                "status": "error",
                "sql_query": sql_query,
                "raw_result": [],
                "natural_language_response": f"Unexpected error during SQL execution: {str(e)}",
                "tables_used": [],
                "question": f"Direct SQL execution: {sql_query}",
                "error_details": str(e)
            }

if __name__ == "__main__":
    try:
        agent = SQLAgent()
        if agent.test_connection():
            print("\n" + "="*50)
            print("Testing natural language queries...")
            
            test_queries = [
               "How do sales volumes respond to price changes?",
                "How many new customers were acquired each month?",
                "Which customers have unpaid invoices or outstanding amounts?",
            ]
            
            for query in test_queries:
                print(f"\nExecuting query: {query}")
                result = agent.query_json(query)
                print("\nResult:")
                print(result)
                print("="*50)
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()