
import sqlite3

def setup_database():
    conn = sqlite3.connect('retail.db')
    c = conn.cursor()

    # Create tables
    c.execute("""
    CREATE TABLE customers (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE
    )
    """)

    c.execute("""
    CREATE TABLE products (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        price REAL NOT NULL
    )
    """)

    c.execute("""
    CREATE TABLE orders (
        id INTEGER PRIMARY KEY,
        customer_id INTEGER NOT NULL,
        order_date TEXT NOT NULL,
        FOREIGN KEY (customer_id) REFERENCES customers (id)
    )
    """)

    c.execute("""
    CREATE TABLE order_items (
        id INTEGER PRIMARY KEY,
        order_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        quantity INTEGER NOT NULL,
        FOREIGN KEY (order_id) REFERENCES orders (id),
        FOREIGN KEY (product_id) REFERENCES products (id)
    )
    """)

    # Insert some sample data
    c.execute("INSERT INTO customers (name, email) VALUES ('John Doe', 'john.doe@example.com')")
    c.execute("INSERT INTO customers (name, email) VALUES ('Jane Smith', 'jane.smith@example.com')")

    c.execute("INSERT INTO products (name, price) VALUES ('Laptop', 1200.00)")
    c.execute("INSERT INTO products (name, price) VALUES ('Mouse', 25.00)")
    c.execute("INSERT INTO products (name, price) VALUES ('Keyboard', 75.00)")

    conn.commit()
    conn.close()

if __name__ == '__main__':
    setup_database()
