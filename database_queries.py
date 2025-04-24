# imports
import hashlib
from typing import Optional
import pandas as pd
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT


#establish connection with database (and create one if it doesn't exist)
def connect():
    try:
        # Try to connect to the target 'project' database
        conn = psycopg2.connect(
            dbname="project",
            user="postgres",
            password="password",  #Replace with your actual password
            host="localhost",
            port="5432"
        )
        cursor = conn.cursor()
        print("Connected to 'project' database.")
        return conn, cursor
    except psycopg2.OperationalError as e:
        if "does not exist" in str(e):
            print("'project' database not found. Creating it...")
            try:
                # Connect to default 'postgres' database to create 'project'
                default_conn = psycopg2.connect(
                    dbname="postgres",
                    user="postgres",
                    password="password",
                    host="localhost",
                    port="5432"
                )
                default_conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
                default_cursor = default_conn.cursor()
                default_cursor.execute("CREATE DATABASE project;")
                default_cursor.close()
                default_conn.close()
                print("Database 'project' created successfully.")
                # Retry connecting to the new database
                conn = psycopg2.connect(
                    dbname="project",
                    user="postgres",
                    password="password",
                    host="localhost",
                    port="5432"
                )
                cursor = conn.cursor()
                print("Connected to 'project' database.")
                return conn, cursor
            except Exception as create_err:
                print("Failed to create database:", create_err)
                return None, None
        else:
            print("Error connecting to database:", e)
            return None, None

# create initial tables 
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

# hash the password
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


# imports and reads the CSV file and hashes the password
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


# populate all tables in correct order to ensure no foreign key violations
def populate_all_tables():
    populate_zipcode_info()
    populate_users()
    populate_helpdesk()
    populate_requests()
    populate_buyers()
    populate_credit_cards()
    populate_address()
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


def add_user_to_database(email: str, password: str):
    conn, cursor = connect()
    if conn is None or cursor is None:
        print("Connection failed, could not add user.")
        return False

    # hash the incoming password
    hashed = hash_password(password)

    # try to insert; do nothing if the email already exists
    insert_sql = """
         INSERT INTO users (email, password)
         VALUES (%s, %s)
         ON CONFLICT (email) DO NOTHING
     """
    try:
        cursor.execute(insert_sql, (email, hashed))
        conn.commit()

        if cursor.rowcount == 0:
            # no row was inserted → user already exists
            print(f"User with email {email!r} already exists. Please log in instead")
            return False

        print(f"New user {email!r} added successfully.")
        return True

    except Exception as e:
        print("Error adding new user:", e)
        conn.rollback()
        return False

    finally:
        cursor.close()
        conn.close()


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
    conn, cursor = connect()
    if conn is None or cursor is None:
        return []
    # Map "All" to "Root" to match the database structure
    if parent_category == "All":
        query = "SELECT category_name FROM categories WHERE parent_category = %s"
        cursor.execute(query, ("Root",))
    else:
        query = "SELECT category_name FROM categories WHERE parent_category = %s"
        cursor.execute(query, (parent_category,))
    results = cursor.fetchall()
    cursor.close()
    conn.close()
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


# fetches all listings for a given seller
def get_listings_by_seller(seller_email: str) -> list:
    conn, cursor = connect()
    if not conn:
        return []
    query = """
         SELECT listing_id, category, product_title, product_name, product_description,
                quantity, product_price, status
           FROM product_listings
          WHERE seller_email = %s
          ORDER BY listing_id
     """
    cursor.execute(query, (seller_email,))
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    # return list of listings
    return rows


# inserts a new product listing for the given seller
def insert_product_listing(
        seller_email: str,
        category: str,
        product_title: str,
        product_name: str,
        product_description: str,
        quantity: int,
        product_price: float
) -> bool:
    conn, cursor = connect()
    if not conn:
        return False
    # determine the next listing_id for this seller
    cursor.execute(
        "SELECT COALESCE(MAX(listing_id), 0) FROM product_listings WHERE seller_email = %s",
        (seller_email,)
    )
    next_id = cursor.fetchone()[0] + 1  # increment from max or start at 1
    status = 1  # default status: active
    insert_sql = """
         INSERT INTO product_listings
             (seller_email, listing_id, category, product_title, product_name,
              product_description, quantity, product_price, status)
         VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
     """
    try:
        # execute insert with all fields
        cursor.execute(insert_sql, (
            seller_email,
            next_id,
            category,
            product_title,
            product_name,
            product_description,
            quantity,
            product_price,
            status
        ))
        conn.commit()
        return True
    except Exception:
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()


# updates an existing product listing
def update_product_listing(
        seller_email: str,
        listing_id: int,
        category: str,
        product_title: str,
        product_name: str,
        product_description: str,
        quantity: int,
        product_price: float
) -> bool:
    conn, cursor = connect()
    if not conn:
        return False
    # if quantity is zero, mark as sold (status 2) else active (1)
    status = 2 if quantity == 0 else 1
    update_sql = """
         UPDATE product_listings
            SET category = %s,
                product_title = %s,
                product_name = %s,
                product_description = %s,
                quantity = %s,
                product_price = %s,
                status = %s
          WHERE seller_email = %s
            AND listing_id    = %s
     """
    try:
        # execute update with dynamic parameters
        cursor.execute(update_sql, (
            category,
            product_title,
            product_name,
            product_description,
            quantity,
            product_price,
            status,
            seller_email,
            listing_id
        ))
        conn.commit()
        return True
    except Exception:
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()


# soft‑deletes a listing by setting its status to inactive (0)
def set_listing_status(seller_email: str, listing_id: int, status: int) -> bool:
    conn, cursor = connect()
    if not conn:
        return False
    update_sql = """
         UPDATE product_listings
            SET status = %s
          WHERE seller_email = %s
            AND listing_id    = %s
     """
    try:
        cursor.execute(update_sql, (status, seller_email, listing_id))  # update status field
        conn.commit()
        return True
    except Exception:
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()


# fetches all credit cards for a given buyer
def get_credit_cards_by_buyer(buyer_email: str) -> list:
    conn, cursor = connect()
    if not conn:
        return []
    cursor.execute(
        """
        SELECT credit_card_num, card_type, expire_month, expire_year
          FROM credit_cards
         WHERE owner_email = %s
        """,
        (buyer_email,)
    )  # execute select query
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    # return credit card list
    return rows


# inserts a new credit card for buyer, ignoring duplicates
def add_credit_card(credit_card_num: str, card_type: str,
                    expire_month: int, expire_year: int,
                    security_code: str, buyer_email: str) -> bool:
    conn, cursor = connect()
    if not conn:
        return False
    try:
        cursor.execute(
            """
            INSERT INTO credit_cards
              (credit_card_num, card_type, expire_month, expire_year, security_code, owner_email)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT DO NOTHING
            """,
            (credit_card_num, card_type, expire_month, expire_year, security_code, buyer_email)
        )  # upsert credit card
        conn.commit()  # commit insertion
        return True
    except Exception:
        conn.rollback()  # rollback on error
        return False
    finally:
        cursor.close()
        conn.close()


# inserts a new order and updates inventory, product status, and seller balance atomically
def insert_order(seller_email: str, listing_id: int,
                 buyer_email: str, quantity: int,
                 credit_card_num: str) -> bool:
    conn, cursor = connect()
    if not cursor:
        return False
    try:
        # lock the specific product row to prevent concurrent modifications
        cursor.execute(
            """
            SELECT product_price, quantity
              FROM product_listings
             WHERE seller_email=%s AND listing_id=%s
             FOR UPDATE
            """,
            (seller_email, listing_id)
        )
        row = cursor.fetchone()  # fetch price and available quantity
        if not row:
            raise Exception("listing not found")  # no such listing
        unit_price, avail = row

        # ensure requested quantity is available
        if quantity > avail:
            raise Exception("not enough inventory")
        total = unit_price * quantity  # calculate total payment

        # generate a new unique order ID
        cursor.execute("SELECT COALESCE(MAX(order_id), 0) FROM orders")
        next_order_id = cursor.fetchone()[0] + 1

        # insert the new order record
        cursor.execute(
            """
            INSERT INTO orders
              (order_id, seller_email, listing_id, buyer_email, date, quantity, payment)
            VALUES (%s, %s, %s, %s, CURRENT_DATE, %s, %s)
            """,
            (next_order_id, seller_email, listing_id, buyer_email, quantity, total)
        )

        # update product inventory and status after sale
        new_qty = avail - quantity
        new_status = 2 if new_qty == 0 else 1  # sold out? mark sold else active
        cursor.execute(
            """
            UPDATE product_listings
               SET quantity = %s,
                   status   = %s
             WHERE seller_email = %s
               AND listing_id   = %s
            """,
            (new_qty, new_status, seller_email, listing_id)
        )

        # increment seller's balance by sale amount
        cursor.execute(
            """
            UPDATE sellers
               SET balance = balance + %s
             WHERE email = %s
            """,
            (total, seller_email)
        )
        # commit entire transaction
        conn.commit()
        return True

    except Exception as e:
        print("order error:", e)  # log error details
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()


# fetches all orders for a given buyer, sorted by most recent date
def get_orders_by_buyer(buyer_email: str) -> list:
    conn, cursor = connect()
    if not conn:
        return []
    cursor.execute(
        """
        SELECT order_id, date, seller_email, listing_id, quantity, payment
          FROM orders
         WHERE buyer_email = %s
         ORDER BY date DESC
        """,
        (buyer_email,)
    )  # execute select sorted by date
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    # return list of orders
    return rows


# inserts or updates a review for a given order

def insert_review(order_id: int, review_desc: str, rating: int) -> bool:
    """insert or update a review for a given order"""
    conn, cursor = connect()  # open DB connection
    if not conn:
        return False  # abort if connection fails
    # upsert review record on order_id conflict
    sql = """
         INSERT INTO reviews (order_id, review_desc, rating)
         VALUES (%s, %s, %s)
         ON CONFLICT (order_id) DO UPDATE
           SET review_desc = EXCLUDED.review_desc,
               rating      = EXCLUDED.rating
     """
    try:
        cursor.execute(sql, (order_id, review_desc, rating))  # execute upsert
        conn.commit()  # commit transaction
        return True
    except Exception as e:
        print("insert_review error:", e)  # log any error
        conn.rollback()  # rollback on failure
        return False
    finally:
        cursor.close()  # close cursor
        conn.close()  # close connection

# calculates the average rating for a seller across all reviews
def get_seller_average_rating(seller_email: str) -> Optional[float]:
    conn, cursor = connect()  # open DB connection
    if conn is None or cursor is None:
        return None  # abort if connection fails
    # compute average rating, cast review_desc to integer since columns are swapped
    sql = """
         SELECT AVG(r.rating::integer)::numeric(10,2)
           FROM reviews r
           JOIN orders o ON r.order_id = o.order_id
          WHERE o.seller_email = %s
     """
    cursor.execute(sql, (seller_email,))  # execute average query
    result = cursor.fetchone()[0]  # fetch result
    cursor.close()  # close cursor
    conn.close()  # close connection
    return float(result) if result is not None else None  # return average or None


def search_products(
        keywords=None,
        min_price=None,
        max_price=None,
        sort_by="relevance",
        category=None):
    conn, cursor = connect()
    if conn is None or cursor is None:
        return []

    # Start building the query
    query = """
        SELECT p.seller_email, p.listing_id, p.category, p.product_title, 
               p.product_name, p.product_description, p.quantity, p.product_price, p.status,
               s.business_name as seller_name
        FROM product_listings p
        JOIN sellers s ON p.seller_email = s.email
        WHERE p.status = 1
    """

    params = []

    # Add category filter if provided and not "All"
    if category and category != "All":
        query += " AND p.category = %s"
        params.append(category)

    # Add keyword search if provided
    if keywords and keywords.strip():
        # Split keywords into individual terms
        keyword_terms = keywords.strip().split()
        keyword_conditions = []

        for term in keyword_terms:
            # Create ILIKE condition for each searchable field
            # ILIKE is used for case-insensitive matching
            term_with_wildcards = f"%{term}%"
            keyword_conditions.append("""
                (p.product_title ILIKE %s OR 
                 p.product_name ILIKE %s OR 
                 p.product_description ILIKE %s OR 
                 p.category ILIKE %s OR 
                 s.business_name ILIKE %s)
            """)
            # Add the parameter 5 times for each field in the condition
            params.extend([term_with_wildcards] * 5)

        # Join all keyword conditions with OR
        if keyword_conditions:
            query += " AND (" + " OR ".join(keyword_conditions) + ")"

    # Add price range filters if provided
    if min_price is not None:
        query += " AND p.product_price >= %s"
        params.append(min_price)

    if max_price is not None:
        query += " AND p.product_price <= %s"
        params.append(max_price)

    # Add sorting
    if sort_by == "price_low_high":
        query += " ORDER BY p.product_price ASC"
    elif sort_by == "price_high_low":
        query += " ORDER BY p.product_price DESC"
    else:  # Default to relevance
        # For relevance sorting, if keywords are provided, we can use a relevance score
        # Otherwise, just sort by listing_id
        if keywords and keywords.strip():
            # This is a simple relevance implementation
            # In a real system, you might use more sophisticated scoring
            query += " ORDER BY p.listing_id DESC"
        else:
            query += " ORDER BY p.listing_id DESC"

    try:
        cursor.execute(query, params)
        results = cursor.fetchall()
        return results
    except Exception as e:
        print(f"Error searching products: {e}")
        return []
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    create_tables()
