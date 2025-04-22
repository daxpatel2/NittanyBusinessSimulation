# NittanyBusiness Simulation

This project implements a user login system as part of the Phase 2 Progress Review for CMPSC431W Database Management Systems. It demonstrates how to:

- Connect to a PostgreSQL database using Python (psycopg2)
- Create a table and import data from a CSV file (with securely hashed passwords)
- Build a simple Flask web application that verifies user credentials
- Display login feedback using an HTML dialog

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Configuration](#configuration)
- [Usage](#usage)

## Overview

The system reads user data from a CSV file (`Users.csv`), hashes each password using SHA256, and stores the data in a PostgreSQL database. A Flask web server then serves a login page where users enter their credentials. The login logic fetches the stored record, compares the hashed password, and returns a message that is displayed in a dialog popup on the page.

## Features

- **Database Connection:** Connects to PostgreSQL using psycopg2.
- **Table Creation:** Automatically creates a `users` table if it does not already exist.
- **Data Import:** Reads and processes a CSV file, hashing passwords before insertion.
- **User Login:** Verifies user credentials against the stored data.
- **Responsive HTML Login Page:** A clean, simple interface with a built-in HTML dialog for user feedback.


## Configuration
Before running the applicaiton, ensure all steps below are completed.

### 1. Environment Setup
Install the required Python packages by running:
```bash 
pip install flask psycopg2-binary
```
### 2. Database Connection 
Open the Python file containing the database connection logic (e.g., `database_queries.py`) and update the `connect()` function with your PostgreSQL credentials:

(1) Make sure PostgreSQL is running.

(2) The credentials (dbname, user, password, host, port) match your local or remote PostgreSQL server settings.

### 3. CSV Data
Make sure the Users.csv file is in the root directory of your project, if not, move it there. 
Verify that:

(1) The CSV file contains at least two columns: email and password.

(2) The columns are correctly named exactly as 'email' and 'password' (case-sensitive).

## Usage

Follow these steps to run the application and test the login system:

### 1. Create the Users Table
Before inserting any data, ensure the `users` table exists in your PostgreSQL database. Run the `create_table()` function once to create it.

### 2. Populate the Users Table
After creating the table, load user data from the `Users.csv` file. This file should contain user emails and plain-text passwords. The system will automatically hash the passwords using SHA-256 before inserting them into the database.

```python
from database_queries import populate_table
populate_table()
```
If there is an issue, make sure the Users.csv file is in the same directory and follows the correct format (email,password) as mentioned above.

### 3. Start the flask server
To launch the login interface, run the Flask application by executing the following command in your terminal from the project’s root directory:

```bash
python app.py
```

The webpage should be available at:
```cpp
http://127.0.0.1:5000/
```

If you run into any issues:
(1) Go back through the confirguration and usage steps.
(2) Ensure no other service is using port 5000.
(3) Make sure you are in the same directory as 'app.py'.

## END
