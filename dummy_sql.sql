-- Suppliers Table (no foreign keys, can be created first)
CREATE TABLE suppliers (
    supplier_id INT NOT NULL IDENTITY(1,1) PRIMARY KEY,
    company_name NVARCHAR(100) NOT NULL,
    contact_name NVARCHAR(50),
    email NVARCHAR(60),
    phone NVARCHAR(15),
    address NVARCHAR(MAX),
    city NVARCHAR(30),
    country NVARCHAR(30)
);

-- Customers Table (no foreign keys, can be created early)
CREATE TABLE customers (
    customer_id INT NOT NULL IDENTITY(1,1) PRIMARY KEY,
    first_name NVARCHAR(30) NOT NULL,
    last_name NVARCHAR(30) NOT NULL,
    email NVARCHAR(60) UNIQUE,
    phone NVARCHAR(15),
    address NVARCHAR(MAX),
    city NVARCHAR(30),
    country NVARCHAR(30),
    registration_date DATE DEFAULT GETDATE(),
    credit_limit DECIMAL(10,2) DEFAULT 5000.00
);

-- Employees Table (self-referencing foreign key and references departments later)
CREATE TABLE employees (
    emp_id INT NOT NULL IDENTITY(1,1) PRIMARY KEY,
    first_name NVARCHAR(30) NOT NULL,
    last_name NVARCHAR(30) NOT NULL,
    email NVARCHAR(60) NOT NULL UNIQUE,
    phone NVARCHAR(15),
    hire_date DATE NOT NULL,
    job_title NVARCHAR(50),
    salary DECIMAL(10,2),
    dept_id INT,
    manager_id INT,
    status NVARCHAR(20) DEFAULT 'Active' CHECK (status IN ('Active', 'Inactive', 'On Leave')),
    CONSTRAINT FK_employees_employees FOREIGN KEY (manager_id) REFERENCES employees(emp_id)
);

-- Departments Table (references employees)
CREATE TABLE departments (
    dept_id INT NOT NULL IDENTITY(1,1) PRIMARY KEY,
    dept_name NVARCHAR(50) NOT NULL,
    location NVARCHAR(50),
    manager_id INT,
    budget DECIMAL(12,2),
    created_date DATE DEFAULT GETDATE(),
    CONSTRAINT FK_departments_employees FOREIGN KEY (manager_id) REFERENCES employees(emp_id)
);

-- Add foreign key to employees for dept_id after departments is created
ALTER TABLE employees
ADD CONSTRAINT FK_employees_departments FOREIGN KEY (dept_id) REFERENCES departments(dept_id);

-- Products Table (references suppliers)
CREATE TABLE products (
    product_id INT NOT NULL IDENTITY(1,1) PRIMARY KEY,
    product_name NVARCHAR(100) NOT NULL,
    category NVARCHAR(50),
    price DECIMAL(8,2) NOT NULL,
    stock_quantity INT DEFAULT 0,
    supplier_id INT,
    description NVARCHAR(MAX),
    created_date DATETIME DEFAULT GETDATE(),
    CONSTRAINT FK_products_suppliers FOREIGN KEY (supplier_id) REFERENCES suppliers(supplier_id)
);

-- Orders Table (references customers)
CREATE TABLE orders (
    order_id INT NOT NULL IDENTITY(1,1) PRIMARY KEY,
    customer_id INT NOT NULL,
    order_date DATE NOT NULL,
    total_amount DECIMAL(10,2),
    status NVARCHAR(20) DEFAULT 'Pending' CHECK (status IN ('Pending', 'Processing', 'Shipped', 'Delivered', 'Cancelled')),
    shipping_address NVARCHAR(MAX),
    CONSTRAINT FK_orders_customers FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

-- Order_Items Table (references orders and products)
CREATE TABLE order_items (
    item_id INT NOT NULL IDENTITY(1,1) PRIMARY KEY,
    order_id INT NOT NULL,
    product_id INT NOT NULL,
    quantity INT NOT NULL,
    unit_price DECIMAL(8,2) NOT NULL,
    total_price AS (quantity * unit_price) PERSISTED,
    CONSTRAINT FK_order_items_orders FOREIGN KEY (order_id) REFERENCES orders(order_id),
    CONSTRAINT FK_order_items_products FOREIGN KEY (product_id) REFERENCES products(product_id)
);

INSERT INTO suppliers (company_name, contact_name, email, phone, city, country) VALUES
('TechCorp Solutions', 'Jane Doe', 'jane@techcorp.com', '555-1001', 'New York', 'USA'),
('Global Electronics', 'Tom Lee', 'tom@globalelec.com', '555-1002', 'Chicago', 'USA');

INSERT INTO customers (first_name, last_name, email, phone, address, city, country, credit_limit) VALUES
('Alice', 'Cooper', 'alice.cooper@email.com', '555-2001', '100 Main St', 'New York', 'USA', 10000.00),
('Bob', 'Martinez', 'bob.martinez@email.com', '555-2002', '200 Oak Ave', 'Chicago', 'USA', 7500.00);

INSERT INTO employees (first_name, last_name, email, phone, hire_date, job_title, salary, status) VALUES
('John', 'Smith', 'john.smith@company.com', '555-0101', '2020-01-15', 'IT Manager', 85000.00, 'Active'),
('Sarah', 'Johnson', 'sarah.johnson@company.com', '555-0102', '2021-03-22', 'Software Developer', 75000.00, 'Inactive'),
('Mike', 'Brown', 'mike.brown@company.com', '555-0103', '2019-07-10', 'HR Director', 90000.00, 'Active');

INSERT INTO departments (dept_name, location, manager_id, budget) VALUES
('Information Technology', 'New York', 1, 500000.00),
('Human Resources', 'Chicago', 3, 200000.00),
('Sales', 'Los Angeles', NULL, 750000.00);

UPDATE employees SET dept_id = 1 WHERE emp_id = 1;
UPDATE employees SET dept_id = 1 WHERE emp_id = 2;
UPDATE employees SET dept_id = 2 WHERE emp_id = 3;

INSERT INTO products (product_name, category, price, stock_quantity, supplier_id) VALUES
('Laptop', 'Electronics', 999.99, 50, 1),
('Smartphone', 'Electronics', 499.99, 100, 1);

INSERT INTO orders (customer_id, order_date, total_amount, status, shipping_address) VALUES
(1, '2024-02-10', 599.98, 'Pending', '100 Main St, New York, USA');

INSERT INTO order_items (order_id, product_id, quantity, unit_price) VALUES
(1, 1, 1, 999.99);
