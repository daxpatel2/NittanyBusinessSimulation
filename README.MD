# NittanyBusiness Simulation

This project implements a full user account and product management system as part of the Phase 2 Progress Review for CMPSC431W: Database Management Systems. It demonstrates how to:

- Connect to and create a PostgreSQL database using Python (`psycopg2`)
- Build a Flask web application with multiple user roles (buyers, sellers, helpdesk staff)
- Securely handle user account creation and login
- Manage products, purchasing, and reviews for buyers and sellers

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Configuration](#configuration)
- [Usage](#usage)
- [Troubleshooting](#troubleshooting)

## Overview

The system reads user data from a CSV file (`Users.csv`), hashes each password using SHA-256, and stores the data in a PostgreSQL database.  
A Flask web server then serves multiple interfaces, allowing users to log in, create accounts, buy and review products, and manage product listings based on their roles.

Helpdesk staff can log in, although their functionality is still under development.

## Features

- **Database Management:**  
  - Connects to PostgreSQL and creates a new database (if it does not already exist).
  - Automatically creates and populates necessary tables.

- **User Management:**  
  - Secure login system using hashed passwords.
  - Ability for users to create new accounts, with information securely added to the database.

- **Buyer Functionality:**  
  - Search for available products.
  - Purchase products.
  - Leave reviews on products.

- **Seller Functionality:**  
  - Manage existing product listings.
  - Add new products to the platform.

- **Helpdesk Functionality (In Progress):**  
  - Helpdesk users can log in, but their full functionality is currently being implemented.

- **Responsive Web Interface:**  
  - Clean and simple login page using HTML dialogs for feedback.

## Configuration

Before running the application, complete the following steps:

### 1. Download the Code

Clone the repository:

```bash
git clone https://github.com/daxpatel2/NittanyBusinessSimulation/
cd NittanyBusinessSimulation
```
## 2. Set Up the Environment

Install the required Python packages:

```bash
pip install flask psycopg2-binary pandas
```
## 3. Configure Database Credentials

Open `database_queries.py` and update the `connect()` function with your PostgreSQL credentials:

- Ensure PostgreSQL is running.
- Update `dbname`, `user`, `password`, `host`, and `port` to match your local or remote server settings.

> **Note:**  
> If PostgreSQL is not installed, download it [here](https://www.postgresql.org/download/), create an account, and set it up before proceeding.

### Windows Users

If you encounter issues connecting to PostgreSQL (such as login errors), it may be due to missing PATH environment settings.  
Refer to [this guide](https://sqlbackupandftp.com/blog/setting-windows-path-for-postgres-tools/) for assistance.


## 4. CSV Data

Ensure that all CSV files (e.g., `Users.csv`) are located in the project’s root directory.

# Usage

## 1. Populate the Database

To connect to the database, create the necessary tables, and import CSV data, run:

```bash
python database_queries.py
```
## 2. Start the Flask Server
Launch the Flask app:
```bash
python app.py
```
The login and user interface will be available at:
```text
http://127.0.0.1:5000/
```
From there:
- New users can register for an account.

- Buyers can browse products, make purchases, and leave reviews.

- Sellers can add and manage product listings.

- Helpdesk staff can log in (future features coming soon).

# Troubleshooting
If you encounter any issues:

- Review the (Configuration)[#configuration] and (Usage)[#usage] sections.

- Make sure PostgreSQL is running and your credentials are correct.

- Confirm no other service is using port 5000.

- Ensure you are in the correct directory (NittanyBusinessSimulation) when running scripts.

