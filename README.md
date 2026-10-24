Smart Hostel Management System

A web-based hostel management application built with Python, Flask, SQLite, HTML, CSS, and JavaScript.

Features

- User login and registration
- Student management
- Room management and allocations
- Complaint management
- Leave request management
- Mess menu management
- Hostel payment records
- Visitor records
- Notices and analytics
- Staff and student portals

Requirements

- Python 3.10 or newer
- Flask
- SQLite
- A modern web browser

Installation

1. Open the project folder in VS Code.

2. Open the terminal in the project directory.

3. Install the dependencies:

   pip install -r requirements.txt

4. Make sure the "instance" folder exists and your database schema has been initialized.

5. Configure the required environment variables in ".env".

Run the application

Run:

python app.py

Open the following address in your browser:

http://127.0.0.1:5000/

Project structure

- "app.py" — Flask application entry point
- "config.py" — application configuration
- "database/" — database schema and seed script
- "instance/" — local SQLite database
- "models/" — data models
- "routes/" — Flask routes and blueprints
- "services/" — application service modules
- "static/" — CSS, JavaScript, and images
- "templates/" — HTML templates
- "tests/" — automated tests
- "uploads/" — uploaded complaint attachments

Development notes

This project is intended for development and testing. Before deployment, configure a secure secret key, disable debug mode, and review authentication, authorization, and file-upload security.