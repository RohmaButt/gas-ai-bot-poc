
import sqlite3

def setup_database():
    conn = sqlite3.connect('retail.db')
    c = conn.cursor()

    # Drop existing tables if they exist
    c.executescript('''
        DROP TABLE IF EXISTS order_items;
        DROP TABLE IF EXISTS orders;
        DROP TABLE IF EXISTS products;
        DROP TABLE IF EXISTS customers;
    ''')

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

    # Insert customers
    customers = [
        ('John Doe', 'john.doe@example.com'),
        ('Jane Smith', 'jane.smith@example.com'),
        ('Alice Johnson', 'alice.j@example.com'),
        ('Bob Wilson', 'bob.wilson@example.com'),
        ('Emma Brown', 'emma.b@example.com')
    ]
    c.executemany("INSERT INTO customers (name, email) VALUES (?, ?)", customers)

    # Insert products
    products = [
        ('Gaming Laptop', 1499.99),
        ('Business Laptop', 1299.99),
        ('Wireless Mouse', 29.99),
        ('Mechanical Keyboard', 89.99),
        ('Gaming Monitor', 299.99),
        ('Wireless Headphones', 159.99),
        ('USB-C Dock', 79.99),
        ('Webcam HD', 49.99)
    ]
    c.executemany("INSERT INTO products (name, price) VALUES (?, ?)", products)

    # Insert orders
    from datetime import datetime, timedelta
    
    # Create some orders over the last week
    base_date = datetime.now() - timedelta(days=7)
    orders = [
        (1, (base_date + timedelta(days=0)).strftime('%Y-%m-%d')),  # John Doe's order
        (1, (base_date + timedelta(days=1)).strftime('%Y-%m-%d')),  # John Doe's second order
        (2, (base_date + timedelta(days=2)).strftime('%Y-%m-%d')),  # Jane's order
        (3, (base_date + timedelta(days=3)).strftime('%Y-%m-%d')),  # Alice's order
        (4, (base_date + timedelta(days=4)).strftime('%Y-%m-%d')),  # Bob's order
        (5, (base_date + timedelta(days=5)).strftime('%Y-%m-%d')),  # Emma's order
    ]
    c.executemany("INSERT INTO orders (customer_id, order_date) VALUES (?, ?)", orders)

    # Insert order items
    order_items = [
        (1, 1, 2),     # John's first order: Business Laptop
        (1, 3, 1),     # John's first order: Wireless Mouse
        (1, 4, 1),     # John's first order: Mechanical Keyboard
        (2, 1, 1),     # John's second order: Gaming Laptop
        (2, 5, 1),     # John's second order: Gaming Monitor
        (3, 2, 1),     # Jane's order: Business Laptop
        (3, 6, 1),     # Jane's order: Wireless Headphones
        (4, 7, 2),     # Alice's order: Two USB-C Docks
        (5, 8, 1),     # Bob's order: Webcam
        (6, 3, 1),     # Emma's order: Wireless Mouse
    ]
    c.executemany("INSERT INTO order_items (order_id, product_id, quantity) VALUES (?, ?, ?)", order_items)

    conn.commit()
    conn.close()
    
    print("Database setup completed with test data!")
    print("- 5 customers created")
    print("- 8 products added")
    print("- 6 orders created")
    print("- 10 order items inserted")

if __name__ == '__main__':
    setup_database()
