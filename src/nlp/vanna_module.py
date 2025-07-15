import vanna as vnn
from vanna.remote import VannaDefault

def setup_vanna(database_path="retail.db"):
    """
    Initializes and trains Vanna.ai with a local SQLite database.
    
    Args:
        database_path (str): Path to the SQLite database file (default: 'retail.db')
    
    Returns:
        VannaDefault: Initialized Vanna object
    """
    try:
        # Initialize Vanna and connect to SQLite
        api_key = vnn.get_api_key('codewithdark90@gmail.com')
        vanna_instance = VannaDefault(model="chinook", api_key=api_key)
        vanna_instance.connect_to_sqlite(database_path)

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