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

### 1. Downloading Code
Clone the repository to your local machine using the following command:

```bash
git clone https://github.com/daxpatel2/NittanyBusinessSimulation/
```
Then, navigate to the project folder using:
``` bash
cd NittanyBusinessSimulation
```

### 2. Environment Setup
Install the required Python packages by running:
```bash 
pip install flask psycopg2-binary pandas
```
### 3. Database Credentials 
Open the Python file containing the database connection logic (e.g., `database_queries.py`) and update the `connect()` function with your PostgreSQL credentials. Make sure:

(1) PostgreSQL is running.

(2) The credentials (dbname, user, password, host, port) match your local or remote PostgreSQL server settings.

If you do not already have PostgreSQL downloaded and setup, download it [here](https://www.postgresql.org/download/). Once downloaded, set up an account, then proceed with the above steps.

#### If using Windows
If you are on Windows, you may run into additional PATH issues regarding PostgreSQL. If (in later steps) when you try to run the app you run into login issues, this may be the cause. Refer to [this](https://sqlbackupandftp.com/blog/setting-windows-path-for-postgres-tools/) tutorial for help.

### 4. CSV Data
Make sure that all CSV files are in the root directory of your project, if not, move them there.

## Usage

To connect to the database, create the tables, and populate the tables, run the following:

```python
from database_queries import main
main()
```

### 4. Start the flask server
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
