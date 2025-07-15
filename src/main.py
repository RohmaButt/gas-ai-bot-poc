from database.database import create_connection
from nlp.main import get_response

def main():
    conn = create_connection(r"retail.db")
    print("Welcome to the Voice Assistant for Retail!")
    
    if conn is not None:
        print("Successfully connected to the database.")
        
        while True:
            try:
                user_input = input("> ")
                if user_input.lower() == "exit":
                    break
                
                response = get_response(user_input)
                print(response)
            except EOFError:
                break
    else:
        print("Error! cannot create the database connection.")

if __name__ == '__main__':
    main()

