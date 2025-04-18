import hashlib
from typing import Optional
import pandas as pd
import psycopg2

def connect():
    try:
        conn = psycopg2.connect(
            dbname="project",
            user="postgres",
            password="1234",
            host="localhost",
            port="5432"
        )
        # Create a cursor and execute a simple test query
        cursor = conn.cursor()
        print("Connected to the database successfully!")
        return conn, cursor
    except Exception as e:
        print("Error connecting to the database:", e)
        return None, None

def create_tables():
    conn, cursor = connect()
    if conn is None or cursor is None:
        print("Connection failed, table not created.")
        return

    create_sql_statements = [
        # users table, stores all users and their hashed passwords
        """CREATE TABLE IF NOT EXISTS users (
                email VARCHAR(255) PRIMARY KEY,
                password VARCHAR(255) NOT NULL
        );""",

        # address table stores addresses referenced by buyers and sellers
        """CREATE TABLE IF NOT EXISTS address (
                address_id VARCHAR(255) PRIMARY KEY,
                zipcode VARCHAR(10),
                street_num VARCHAR(10),
                street_name VARCHAR(255)
        );""",

        # zipcode_info table stores the city and state of a zipcode area
        """CREATE TABLE IF NOT EXISTS zipcode_info (
                zipcode VARCHAR(10) PRIMARY KEY,
                city VARCHAR(255),
                state VARCHAR(255)
        );""",

        # helpdesk table stores all the helpdesk staffs and their positions
        """CREATE TABLE IF NOT EXISTS helpdesk (
                email VARCHAR(255) PRIMARY KEY,
                position VARCHAR(100)
        );""",

        # buyer table, a subset of users
        """CREATE TABLE IF NOT EXISTS buyer (
                email VARCHAR(255) PRIMARY KEY,
                business_name VARCHAR(255),
                buyer_address_id VARCHAR(255),
                FOREIGN KEY (email) REFERENCES users(email),
                FOREIGN KEY (buyer_address_id) REFERENCES address(address_id)
        );""",

        # sellers table, a subset of users that sell
        """CREATE TABLE IF NOT EXISTS sellers (
                email VARCHAR(255) PRIMARY KEY,
                business_name VARCHAR(255),
                business_address_id VARCHAR(255),
                bank_routing_number VARCHAR(50),
                bank_account_number VARCHAR(50),
                balance NUMERIC(10,2),
                FOREIGN KEY (email) REFERENCES users(email),
                FOREIGN KEY (business_address_id) REFERENCES address(address_id)
        );""",

        # credit_cards table, credit cards stored in the system
        """CREATE TABLE IF NOT EXISTS credit_cards (
                credit_card_num VARCHAR(20) PRIMARY KEY,
                card_type VARCHAR(50),
                expire_month INTEGER,
                expire_year INTEGER,
                security_code VARCHAR(10),
                owner_email VARCHAR(255),
                FOREIGN KEY (owner_email) REFERENCES buyer(email)
        );""",

        # requests table stores all info regarding a helpdesk request
        """CREATE TABLE IF NOT EXISTS requests (
                request_id INTEGER PRIMARY KEY,
                sender_email VARCHAR(255) NOT NULL,
                helpdesk_staff_email VARCHAR(255),
                request_type VARCHAR(100),
                request_desc TEXT,
                request_status INTEGER,
                FOREIGN KEY (sender_email) REFERENCES users(email)
        );""",

        # categories table stores the links between a category and its parent category in the category hierarchy
        """CREATE TABLE IF NOT EXISTS categories (
                parent_category VARCHAR(255) NOT NULL,
                category_name VARCHAR(255) NOT NULL,
                PRIMARY KEY (parent_category, category_name)
        );""",

        # product listings table, records useful information about a listed product published by a seller
        """CREATE TABLE IF NOT EXISTS product_listings (
                seller_email VARCHAR(255) NOT NULL,
                listing_id INTEGER NOT NULL,
                category VARCHAR(255),
                product_title VARCHAR(255),
                product_name VARCHAR(255),
                product_description TEXT,
                quantity INTEGER,
                product_price NUMERIC(10,2),
                status INTEGER,
                PRIMARY KEY (seller_email, listing_id),
                FOREIGN KEY (seller_email) REFERENCES sellers(email)
        );""",

        # orders table stores orders placed
        """CREATE TABLE IF NOT EXISTS orders (
                order_id INTEGER PRIMARY KEY,
                seller_email VARCHAR(255) NOT NULL,
                listing_id INTEGER NOT NULL,
                buyer_email VARCHAR(255) NOT NULL,
                date DATE,
                quantity INTEGER,
                payment NUMERIC(10,2),
                FOREIGN KEY (seller_email, listing_id) REFERENCES product_listings(seller_email, listing_id),
                FOREIGN KEY (buyer_email) REFERENCES buyer(email)
        );""",

        # reviews table stores the reviews on products and their sellers of orders
        """CREATE TABLE IF NOT EXISTS reviews (
                order_id INTEGER PRIMARY KEY,
                review_desc TEXT,
                rating VARCHAR(50),
                FOREIGN KEY (order_id) REFERENCES orders(order_id)
        );"""
    ]

    for sql in create_sql_statements:
        try:
            cursor.execute(sql)
            conn.commit()
        except Exception as e:
            print("Error executing SQL:", e)

    print("All tables created successfully.")
    cursor.close()
    conn.close()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# next part imports and reads the CSV file and hashes the password
def read_and_hash_password():
    users_df = pd.read_csv('Users.csv')
    print("CSV file read successfully.")
    # hash the passwords from the passwords category
    users_df['password'] = users_df['password'].apply(lambda x: hash_password(x))
    return users_df

# function to populate users table
def populate_users():
    conn, cursor = connect()
    if conn is None or cursor is None:
        print("Connection failed, could not populate users table.")
        return
    # call function to read hashed passwords into table
    users_df = read_and_hash_password()
    # sql insert statement with conflict handling
    insert_sql = "INSERT INTO users (email, password) VALUES (%s, %s) ON CONFLICT DO NOTHING"
    try:
        # insert all rows from dataframe into users table
        cursor.executemany(insert_sql, users_df.values.tolist())
        conn.commit()
        print("Users data imported successfully.")
    except Exception as e:
        print("Error inserting users data:", e)
    cursor.close()
    conn.close()

# function to populate helpdesk table
def populate_helpdesk():
    conn, cursor = connect()
    if conn is None or cursor is None:
        print("Connection failed, could not populate helpdesk table.")
        return
    # read helpdesk.csv into a pandas dataframe
    helpdesk_df = pd.read_csv('Helpdesk.csv')
    print("Helpdesk CSV read successfully.")
    # sql insert statement with conflict handling
    insert_sql = "INSERT INTO helpdesk (email, position) VALUES (%s, %s) ON CONFLICT DO NOTHING"
    try:
        # insert all rows from dataframe into helpdesk table
        cursor.executemany(insert_sql, helpdesk_df.values.tolist())
        conn.commit()
        print("Helpdesk data imported successfully.")
    except Exception as e:
        print("Error inserting helpdesk data:", e)
    cursor.close()
    conn.close()

# function to populate requests table
def populate_requests():
    conn, cursor = connect()
    if conn is None or cursor is None:
        print("connection failed, could not populate requests table.")
        return
    # read requests.csv into a pandas dataframe
    requests_df = pd.read_csv('Requests.csv')
    print("requests csv read successfully")
    # sql insert statement with conflict handling
    insert_sql = """INSERT INTO requests 
        (request_id, sender_email, helpdesk_staff_email, request_type, request_desc, request_status)
        VALUES (%s, %s, %s, %s, %s, %s) ON CONFLICT DO NOTHING"""
    try:
        # insert all rows from dataframe into requests table
        cursor.executemany(insert_sql, requests_df.values.tolist())
        conn.commit()
        print("requests data imported successfully.")
    except Exception as e:
        print("error inserting requests data:", e)
    cursor.close()
    conn.close()

# function to populate buyer table
def populate_buyers():
    conn, cursor = connect()
    if conn is None or cursor is None:
        print("connection failed, could not populate buyers table.")
        return
    # read buyers.csv into dataframe
    buyers_df = pd.read_csv('Buyers.csv')
    print("buyers csv read successfully.")
    # sql insert statement for buyer table
    insert_sql = "INSERT INTO buyer (email, business_name, buyer_address_id) VALUES (%s, %s, %s) ON CONFLICT DO NOTHING"
    try:
        # insert all buyer records
        cursor.executemany(insert_sql, buyers_df.values.tolist())
        conn.commit()
        print("buyers data imported successfully.")
    except Exception as e:
        print("error inserting buyers data:", e)
    cursor.close()
    conn.close()

# function to populate credit_cards table
def populate_credit_cards():
    conn, cursor = connect()
    if conn is None or cursor is None:
        print("connection failed, could not populate credit_cards table.")
        return
    # read credit_cards.csv into dataframe
    cc_df = pd.read_csv('Credit_cards.csv')
    print("credit cards csv read successfully.")
    # sql insert statement for credit_cards table
    insert_sql = """INSERT INTO credit_cards 
        (credit_card_num, card_type, expire_month, expire_year, security_code, owner_email)
        VALUES (%s, %s, %s, %s, %s, %s) ON CONFLICT DO NOTHING"""
    try:
        # insert all credit card records
        cursor.executemany(insert_sql, cc_df.values.tolist())
        conn.commit()
        print("credit cards data imported successfully.")
    except Exception as e:
        print("error inserting credit cards data:", e)
    cursor.close()
    conn.close()

# function to populate address table
def populate_address():
    conn, cursor = connect()
    if conn is None or cursor is None:
        print("connection failed, could not populate address table.")
        return
    # read address.csv into dataframe
    address_df = pd.read_csv('Address.csv')
    print("address csv read successfully.")
    # sql insert statement for address table
    insert_sql = "INSERT INTO address (address_id, zipcode, street_num, street_name) VALUES (%s, %s, %s, %s) ON CONFLICT DO NOTHING"
    try:
        # insert all address records
        cursor.executemany(insert_sql, address_df.values.tolist())
        conn.commit()
        print("address data imported successfully.")
    except Exception as e:
        print("error inserting address data:", e)
    cursor.close()
    conn.close()

# function to populate zipcode_info table
def populate_zipcode_info():
    conn, cursor = connect()
    if conn is None or cursor is None:
        print("connection failed, could not populate zipcode_info table.")
        return
    # read zipcode_info.csv into dataframe
    zipcode_df = pd.read_csv('Zipcode_Info.csv')
    print("zipcode info csv read successfully.")
    # sql insert statement for zipcode_info table
    insert_sql = "INSERT INTO zipcode_info (zipcode, city, state) VALUES (%s, %s, %s) ON CONFLICT DO NOTHING"
    try:
        # insert all zipcode records
        cursor.executemany(insert_sql, zipcode_df.values.tolist())
        conn.commit()
        print("zipcode info data imported successfully.")
    except Exception as e:
        print("error inserting zipcode info data:", e)
    cursor.close()
    conn.close()

# function to populate sellers table
def populate_sellers():
    conn, cursor = connect()
    if conn is None or cursor is None:
        print("connection failed, could not populate sellers table.")
        return
    # read sellers.csv into dataframe
    sellers_df = pd.read_csv('Sellers.csv')
    print("sellers csv read successfully.")
    # sql insert statement for sellers table
    insert_sql = """INSERT INTO sellers 
        (email, business_name, business_address_id, bank_routing_number, bank_account_number, balance)
        VALUES (%s, %s, %s, %s, %s, %s) ON CONFLICT DO NOTHING"""
    try:
        # insert all seller records
        cursor.executemany(insert_sql, sellers_df.values.tolist())
        conn.commit()
        print("sellers data imported successfully.")
    except Exception as e:
        print("error inserting sellers data:", e)
    cursor.close()
    conn.close()

# function to populate categories table
def populate_categories():
    conn, cursor = connect()
    if conn is None or cursor is None:
        print("connection failed, could not populate categories table.")
        return
    # read categories.csv into dataframe
    categories_df = pd.read_csv('Categories.csv')
    print("categories csv read successfully.")
    # sql insert statement for categories table
    insert_sql = "INSERT INTO categories (parent_category, category_name) VALUES (%s, %s) ON CONFLICT DO NOTHING"
    try:
        # insert all category records
        cursor.executemany(insert_sql, categories_df.values.tolist())
        conn.commit()
        print("categories data imported successfully.")
    except Exception as e:
        print("error inserting categories data:", e)
    cursor.close()
    conn.close()

# function to populate product_listings table
def populate_product_listings():
    conn, cursor = connect()
    if conn is None or cursor is None:
        print("connection failed, could not populate product_listings table.")
        return
    # read product_listings.csv into dataframe
    listings_df = pd.read_csv('Product_Listings.csv')
    print("product listings csv read successfully.")

    # clean product_price column by removing dollar sign and converting to numeric
    if 'Product_Price' in listings_df.columns:
        listings_df['Product_Price'] = listings_df['Product_Price'].replace({'\$': ''}, regex=True).str.strip()
        listings_df['Product_Price'] = pd.to_numeric(listings_df['Product_Price'], errors='coerce')

    # sql insert statement for product_listings table
    insert_sql = """INSERT INTO product_listings 
        (seller_email, listing_id, category, product_title, product_name, product_description, quantity, product_price, status)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) ON CONFLICT DO NOTHING"""
    try:
        # insert all product listing records
        cursor.executemany(insert_sql, listings_df.values.tolist())
        conn.commit()
        print("product listings data imported successfully.")
    except Exception as e:
        print("error inserting product listings data:", e)
    cursor.close()
    conn.close()

# function to populate orders table
def populate_orders():
    conn, cursor = connect()
    if conn is None or cursor is None:
        print("connection failed, could not populate orders table.")
        return
    # read orders.csv into dataframe
    orders_df = pd.read_csv('Orders.csv')
    print("orders csv read successfully")

    # convert date column to datetime format
    if 'Date' in orders_df.columns:
        orders_df['Date'] = pd.to_datetime(orders_df['Date'], errors='coerce').dt.date

    # sql insert statement for orders table
    insert_sql = """INSERT INTO orders 
        (order_id, seller_email, listing_id, buyer_email, date, quantity, payment)
        VALUES (%s, %s, %s, %s, %s, %s, %s) ON CONFLICT DO NOTHING"""
    try:
        # insert all order records
        cursor.executemany(insert_sql, orders_df.values.tolist())
        conn.commit()
        print("orders data imported successfully.")
    except Exception as e:
        print("error inserting orders data:", e)
    cursor.close()
    conn.close()

# function to populate reviews table
def populate_reviews():
    conn, cursor = connect()
    if conn is None or cursor is None:
        print("connection failed, could not populate reviews table.")
        return
    # read reviews.csv into dataframe
    reviews_df = pd.read_csv('Reviews.csv')
    print("reviews csv read successfully.")
    # sql insert statement for reviews table
    insert_sql = "INSERT INTO reviews (order_id, review_desc, rating) VALUES (%s, %s, %s) ON CONFLICT DO NOTHING"
    try:
        # insert all review records
        cursor.executemany(insert_sql, reviews_df.values.tolist())
        conn.commit()
        print("reviews data imported successfully.")
    except Exception as e:
        print("error inserting reviews data:", e)
    cursor.close()
    conn.close()

def populate_all_tables():
    populate_users()
    populate_helpdesk()
    populate_requests()
    populate_buyers()
    populate_credit_cards()
    populate_address()
    populate_zipcode_info()
    populate_sellers()
    populate_categories()
    populate_product_listings()
    populate_orders()
    populate_reviews()

# fetches user data based on email and verifies the given password against the stored hash
def fetch_user_data(email: str, password: str) -> Optional[bool]:
    conn, cursor = connect()
    if conn is None or cursor is None:
        print("Connection failed, could not fetch user data.")
        return None

    # fetch the data from the database with that user, check the password by hashing the newone and comparing it to the one in the db
    fetch_user_data_sql = "SELECT * FROM users WHERE email = %s"
    cursor.execute(fetch_user_data_sql, (email,))
    user_data = cursor.fetchone()

    if not user_data:
        print("Username not found in the database.")
        return None

    hashed_password = hash_password(password)

    # compare input hashed password with stored hashed password
    if hashed_password != user_data[1]:
        print("Incorrect password.")
        return False

    return True

# this function returns the role of a user based on their email by checking the helpdesk, buyer, and sellers tables in order
def get_user_role(email: str) -> str:
    conn, cursor = connect()
    if conn is None or cursor is None:
        return None
    role = None
    # check if the email is in the helpdesk table
    cursor.execute("SELECT email FROM helpdesk WHERE email = %s", (email,))
    if cursor.fetchone():
        role = "helpdesk"
    else:
        # check if the email is in the buyer table
        cursor.execute("SELECT email FROM buyer WHERE email = %s", (email,))
        if cursor.fetchone():
            role = "buyer"
        else:
            # check if the email is in the sellers table
            cursor.execute("SELECT email FROM sellers WHERE email = %s", (email,))
            if cursor.fetchone():
                role = "seller"
    cursor.close()
    conn.close()
    return role

# this function retrieves subcategories from the database for a given parent category
def get_subcategories(parent_category: str) -> list:
    conn, cursor = connect()  # connect to the database
    if conn is None or cursor is None:
        return []  # if connection fails, return an empty list

    # if the parent category is "All", attempt to get top-level categories defined in the categories table
    if parent_category == "All":
        query = "SELECT category_name FROM categories WHERE parent_category = %s"
        cursor.execute(query, ("All",))
        results = cursor.fetchall()  # fetch all matching rows
        # fallback: if no top-level categories were defined in the categories table,
        # retrieve distinct categories from the product_listings table that are non-null and non-empty
        if not results:
            query = "SELECT DISTINCT category FROM product_listings WHERE category IS NOT NULL AND category <> ''"
            cursor.execute(query)
            results = cursor.fetchall()
    else:
        # if the parent is a specific category, query the categories table for its subcategories
        query = "SELECT category_name FROM categories WHERE parent_category = %s"
        cursor.execute(query, (parent_category,))
        results = cursor.fetchall()  # fetch all matching rows

    cursor.close()
    conn.close()
    # process the fetched rows and return a simple list of subcategory names
    return [row[0] for row in results]

# this function retrieves products from the database based on a given category
def get_products_by_category(category: str) -> list:
    conn, cursor = connect()  # connect to the database
    if conn is None or cursor is None:
        return []  # if connection fails, return an empty list

    # SQL query to retrieve product details from product_listings matching the provided category
    query = """SELECT seller_email, listing_id, product_title, product_name, 
                      product_description, quantity, product_price, status 
               FROM product_listings 
               WHERE category = %s"""
    cursor.execute(query, (category,))
    results = cursor.fetchall()  # fetch all matching product records
    cursor.close()
    conn.close()
    # return the list of products as tuples
    return results

# this function retrieves the full details of a specific product listing given seller email and listing id
def get_product_details(seller_email: str, listing_id: int) -> tuple:
    conn, cursor = connect()  # connect to the database
    if conn is None or cursor is None:
        return None  # if connection fails, return None

    # SQL query to get the full details of one product listing that matches the seller email and listing id
    query = """SELECT seller_email, listing_id, category, product_title, product_name, 
                      product_description, quantity, product_price, status 
               FROM product_listings 
               WHERE seller_email = %s AND listing_id = %s"""
    cursor.execute(query, (seller_email, listing_id))
    result = cursor.fetchone()  # fetch the product details as a single record (tuple)
    cursor.close()
    conn.close()
    # return the product details tuple (or None if not found)
    return result

if __name__ == '__main__':
    create_tables()
    populate_all_tables()