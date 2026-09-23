"""
init_db.py
----------
Initializes the SQLite database and required tables. Safe to re-run;
existing tables are left untouched.

Usage:
    python init_db.py
"""

import models

if __name__ == "__main__":
    models.init_db()
    print("[Defence Cyber Shield] Database initialized at:", models.DB_PATH)
    print("Registration completed:", models.is_registration_completed())
    print("Run 'python app.py' to start the portal.")
