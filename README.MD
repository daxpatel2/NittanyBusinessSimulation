# NittanyBusiness Login System

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
- [Code Explanation](#code-explanation)

## Overview

The system reads user data from a CSV file (`Users.csv`), hashes each password using SHA256, and stores the data in a PostgreSQL database. A Flask web server then serves a login page where users enter their credentials. The login logic fetches the stored record, compares the hashed password, and returns a message that is displayed in a dialog popup on the page.

## Features

- **Database Connection:** Connects to PostgreSQL using psycopg2.
- **Table Creation:** Automatically creates a `users` table if it does not already exist.
- **Data Import:** Reads and processes a CSV file, hashing passwords before insertion.
- **User Login:** Verifies user credentials against the stored data.
- **Responsive HTML Login Page:** A clean, simple interface with a built-in HTML dialog for user feedback.

## Prerequisites

- **Python 3.8+**
- **PostgreSQL** (ensure it is installed and running)
- Required Python packages:
  - `psycopg2` (or `psycopg2-binary`)
  - `Flask`
  - `pandas`
- A CSV file named `Users.csv` with at least two columns: `email` and `password`.
