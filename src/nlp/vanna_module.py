import vanna as vnn
from vanna.remote import VannaDefault
from src.database.database import create_connection
from src.nlp.utils import format_results
from src.config import VANNA_API_KEY, VANNA_MODEL, DATABASE_PATH

def setup_vanna(database_path=None):
    """
    Initializes and trains Vanna.ai with a local SQLite database.
    
    Args:
        database_path (str): Optional path to override the default database path
    
    Returns:
        VannaDefault: Initialized Vanna object
    """
    try:
        if not VANNA_API_KEY:
            raise ValueError("VANNA_API_KEY not found in environment variables")

        # Initialize Vanna and connect to SQLite
        api_key = vnn.get_api_key('codewithdark90@gmail.com', '1D4JML')
        vanna_instance = VannaDefault(model=VANNA_MODEL, api_key=api_key)
        vanna_instance.connect_to_sqlite(DATABASE_PATH)

        # Add context about the database schema
        schema_context = """
        The database contains the following tables:
        - products: Stores product information (id, name, price)
        - customers: Stores customer information (id, name, email)
        - orders: Stores order information (id, customer_id, order_date)
        - order_items: Stores order items (id, order_id, product_id, quantity)
        """
        vanna_instance.train(ddl=schema_context)

        # Train Vanna on the actual database schema
        df_ddl = vanna_instance.run_sql("""
            SELECT type, name, sql, tbl_name 
            FROM sqlite_master 
            WHERE type IN ('table', 'view') 
            AND name NOT LIKE 'sqlite_%'
        """)
        
        for ddl in df_ddl['sql']:
            if ddl:  # Skip None values
                vanna_instance.train(ddl=ddl)

        return vanna_instance

    except Exception as e:
        print(f"Error setting up Vanna: {e}")
        return None
    

def text_to_sql_vanna(vn, question):
    """
    Converts a natural language question to SQL using Vanna.ai.
    
    Args:
        vn: Initialized Vanna object
        question (str): Natural language question
    
    Returns:
        str: Generated SQL query or None if an error occurs
    """
    try:
        if vn is None:
            raise ValueError("Vanna is not initialized")
        
        # Provide context for common queries
        if "list" in question.lower() and "product" in question.lower():
            return "SELECT * FROM products"
        if "price" in question.lower() and "product" in question.lower():
            product_name = question.lower().split("price of ")[-1].strip('.')
            return f"SELECT name, price FROM products WHERE lower(name) LIKE lower('%{product_name}%')"
            
        return vn.generate_sql(question)
    except Exception as e:
        print(f"Error generating SQL: {e}")
        return None


def get_response(user_input):
    """Gets a response from the database based on user input."""
    vn = setup_vanna()
    sql_query = text_to_sql_vanna(vn, user_input)

    if sql_query:
        conn = create_connection(r"retail.db")
        if conn:
            cursor = conn.cursor()
            cursor.execute(sql_query)
            results = cursor.fetchall()
            formatted = format_results(cursor, results)
            conn.close()
            return formatted
            
        return "I'm sorry, I don't understand."
    
