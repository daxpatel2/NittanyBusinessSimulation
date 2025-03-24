import pandas as pd
import psycopg2
import hashlib

from numpy.f2py.auxfuncs import throw_error


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



def create_table():
    conn, cursor = connect()
    if conn is None or cursor is None:
        print("Connection failed, table not created.")
        return

    create_table_sql = """
    CREATE TABLE IF NOT EXISTS users (
        email VARCHAR(255) PRIMARY KEY,
        password VARCHAR(255)
    );
    """

    try:
        cursor.execute(create_table_sql)
        conn.commit()
        print("Table created successfully.")
    except Exception as e:
        print("Error creating table because database connection failed: ", e)
        return None

# create_table()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# next part imports and reads the CSV file and populates the database tables
def read_and_hash_password():
    users_df = pd.read_csv('Users.csv')
    # print(users_df)

    #has the passwords from the passwords category
    users_df['password'] = users_df['password'].apply(lambda x: hash_password(x))

    return users_df

def populate_table() -> None:
    conn, cursor = connect()
    if conn is None or cursor is None:
        print("Connection failed, could not populate table.")
        return

    users_df = read_and_hash_password()

    insert_into_table = "INSERT INTO users (email, password) VALUES (%s, %s)"

    try:
        cursor.executemany(insert_into_table, users_df.values.tolist())
        conn.commit()
        print("Data imported successfully into the table")
    except Exception as e:
        print("Error creating table because database connection failed: ", e)
        return None


def fetch_user_data(email: str, password: str) -> bool | None:
    conn, cursor = connect()
    if conn is None or cursor is None:
        print("Connection failed, could not fetch user data.")
        return

    #fetch the data from the database with that user, check the password by hashing the newone and comparing it to the one in the db
    fetch_user_data_sql = "SELECT * FROM users WHERE email = %s"
    cursor.execute(fetch_user_data_sql, (email,))
    user_data = cursor.fetchone()

    if not user_data:
        print("Username not found in the database.")
        return None

    hashed_password = hash_password(password)

    if hashed_password != user_data[1]:
        print("Incorrect password.")
        return False

    return True