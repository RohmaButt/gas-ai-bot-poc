from nlp.vanna_module import setup_vanna, text_to_sql_vanna
from database.database import create_connection
from common.utils import format_results

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