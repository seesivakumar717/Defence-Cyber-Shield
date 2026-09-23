"""
models.py
---------
SQLite data access layer for Defence Cyber Shield.

Uses raw sqlite3 (no ORM) so the project has zero extra runtime
dependencies beyond what's declared in requirements.txt.
"""

import sqlite3
import os
import secrets
from datetime import datetime, timezone
from werkzeug.security import generate_password_hash

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "database.db")


def get_connection():
    """Return a new SQLite connection with row access by column name."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def has_admin():
    """Check whether an administrator account already exists in the users table."""
    conn = get_connection()
    row = conn.execute("SELECT COUNT(*) AS c FROM users WHERE role = 'admin'").fetchone()
    conn.close()
    return bool(row and row["c"] > 0)


def init_db():
    """Create all tables if they do not already exist."""
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            army_id TEXT NOT NULL UNIQUE,
            email TEXT NOT NULL UNIQUE,
            username TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'soldier',
            created_at TEXT NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS incidents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            soldier_id INTEGER NOT NULL,
            risk_score INTEGER NOT NULL,
            risk_level TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Pending',
            ocr_text TEXT,
            recommendation TEXT,
            indicators TEXT,
            uploaded_image TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY (soldier_id) REFERENCES users (id) ON DELETE CASCADE
        )
    """)

    # Every analysis is logged here, even Low/Medium risk ones that never
    # become a formal incident. Powers History + Analytics.
    cur.execute("""
        CREATE TABLE IF NOT EXISTS scans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            soldier_id INTEGER NOT NULL,
            risk_score INTEGER NOT NULL,
            risk_level TEXT NOT NULL,
            ocr_text TEXT,
            recommendation TEXT,
            indicators TEXT,
            uploaded_image TEXT,
            incident_id INTEGER,
            created_at TEXT NOT NULL,
            FOREIGN KEY (soldier_id) REFERENCES users (id) ON DELETE CASCADE
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS system (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            registration_completed INTEGER NOT NULL DEFAULT 0
        )
    """)

    cur.execute("SELECT COUNT(*) AS c FROM system")
    if cur.fetchone()["c"] == 0:
        cur.execute("INSERT INTO system (registration_completed) VALUES (0)")

    conn.commit()
    conn.close()


# ----------------------------------------------------------------------
# System / registration gate
# ----------------------------------------------------------------------

def is_registration_completed():
    conn = get_connection()
    row = conn.execute("SELECT registration_completed FROM system LIMIT 1").fetchone()
    conn.close()
    return bool(row and row["registration_completed"])


def mark_registration_completed():
    conn = get_connection()
    conn.execute("UPDATE system SET registration_completed = 1")
    conn.commit()
    conn.close()


# ----------------------------------------------------------------------
# Users
# ----------------------------------------------------------------------
# Users
# ----------------------------------------------------------------------

def generate_unique_army_id():
    """Generate a unique internal Army ID for new user accounts."""
    conn = get_connection()
    while True:
        army_id = f"USER-{secrets.token_hex(5).upper()}"
        row = conn.execute("SELECT id FROM users WHERE army_id = ?", (army_id,)).fetchone()
        if not row:
            conn.close()
            return army_id


def create_user(name, army_id, email, username, password_hash, role='soldier'):
    conn = get_connection()
    conn.execute(
        """INSERT INTO users (name, army_id, email, username, password_hash, role, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (name, army_id, email.lower(), username.lower(), password_hash, role, datetime.now(timezone.utc).isoformat()),
    )
    conn.commit()
    conn.close()


def create_soldier(name, army_id, email, username, password_hash):
    create_user(name, army_id, email, username, password_hash, role='soldier')


def create_admin(name, army_id, email, username, password_hash):
    create_user(name, army_id, email, username, password_hash, role='admin')


def get_user_by_army_id(army_id):
    conn = get_connection()
    row = conn.execute("SELECT * FROM users WHERE UPPER(army_id) = UPPER(?)", (army_id.strip(),)).fetchone()
    conn.close()
    return row


def get_user_by_username(username, role=None):
    conn = get_connection()
    if role:
        row = conn.execute(
            "SELECT * FROM users WHERE LOWER(username) = LOWER(?) AND role = ?", (username.strip(), role)
        ).fetchone()
    else:
        row = conn.execute("SELECT * FROM users WHERE LOWER(username) = LOWER(?)", (username.strip(),)).fetchone()
    conn.close()
    return row


def get_user_by_email(email):
    conn = get_connection()
    row = conn.execute("SELECT * FROM users WHERE LOWER(email) = LOWER(?)", (email.strip(),)).fetchone()
    conn.close()
    return row


def get_user_by_login(identifier, role=None):
    conn = get_connection()
    identifier = identifier.strip()
    if role:
        row = conn.execute(
            "SELECT * FROM users WHERE (LOWER(username) = LOWER(?) OR LOWER(email) = LOWER(?)) AND role = ?",
            (identifier, identifier, role),
        ).fetchone()
    else:
        row = conn.execute(
            "SELECT * FROM users WHERE (LOWER(username) = LOWER(?) OR LOWER(email) = LOWER(?))",
            (identifier, identifier),
        ).fetchone()
    conn.close()
    return row


def get_user_by_id(user_id):
    conn = get_connection()
    row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    return row


def get_all_soldiers():
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM users WHERE role = 'soldier' ORDER BY created_at DESC"
    ).fetchall()
    conn.close()
    return rows


def count_soldiers():
    conn = get_connection()
    row = conn.execute("SELECT COUNT(*) AS c FROM users WHERE role = 'soldier'").fetchone()
    conn.close()
    return row["c"]


# ----------------------------------------------------------------------
# Scans (every analysis, regardless of risk level)
# ----------------------------------------------------------------------

def create_scan(soldier_id, risk_score, risk_level, ocr_text, recommendation,
                 indicators, uploaded_image, incident_id=None):
    conn = get_connection()
    cur = conn.execute(
        """INSERT INTO scans
           (soldier_id, risk_score, risk_level, ocr_text, recommendation,
            indicators, uploaded_image, incident_id, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (soldier_id, risk_score, risk_level, ocr_text, recommendation,
         indicators, uploaded_image, incident_id, datetime.now(timezone.utc).isoformat()),
    )
    conn.commit()
    scan_id = cur.lastrowid
    conn.close()
    return scan_id


def get_scans_for_soldier(soldier_id):
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM scans WHERE soldier_id = ? ORDER BY created_at DESC", (soldier_id,)
    ).fetchall()
    conn.close()
    return rows


def get_all_scans():
    conn = get_connection()
    rows = conn.execute(
        """SELECT scans.*, users.name AS soldier_name, users.army_id AS soldier_army_id
           FROM scans JOIN users ON scans.soldier_id = users.id
           ORDER BY scans.created_at DESC"""
    ).fetchall()
    conn.close()
    return rows


# ----------------------------------------------------------------------
# Incidents (only High risk scans become incidents)
# ----------------------------------------------------------------------

def create_incident(soldier_id, risk_score, risk_level, ocr_text, recommendation,
                     indicators, uploaded_image):
    conn = get_connection()
    cur = conn.execute(
        """INSERT INTO incidents
           (soldier_id, risk_score, risk_level, status, ocr_text, recommendation,
            indicators, uploaded_image, created_at)
           VALUES (?, ?, ?, 'Pending', ?, ?, ?, ?, ?)""",
        (soldier_id, risk_score, risk_level, ocr_text, recommendation,
         indicators, uploaded_image, datetime.now(timezone.utc).isoformat()),
    )
    conn.commit()
    incident_id = cur.lastrowid
    conn.close()
    return incident_id


def get_all_incidents():
    conn = get_connection()
    rows = conn.execute(
        """SELECT incidents.*, users.name AS soldier_name, users.army_id AS soldier_army_id
           FROM incidents JOIN users ON incidents.soldier_id = users.id
           ORDER BY incidents.created_at DESC"""
    ).fetchall()
    conn.close()
    return rows


def get_incident_by_id(incident_id):
    conn = get_connection()
    row = conn.execute(
        """SELECT incidents.*, users.name AS soldier_name, users.army_id AS soldier_army_id,
                  users.email AS soldier_email
           FROM incidents JOIN users ON incidents.soldier_id = users.id
           WHERE incidents.id = ?""",
        (incident_id,),
    ).fetchone()
    conn.close()
    return row


def update_incident_status(incident_id, status):
    conn = get_connection()
    conn.execute("UPDATE incidents SET status = ? WHERE id = ?", (status, incident_id))
    conn.commit()
    conn.close()


def delete_incident(incident_id):
    conn = get_connection()
    conn.execute("DELETE FROM incidents WHERE id = ?", (incident_id,))
    conn.commit()
    conn.close()


def get_incident_counts():
    conn = get_connection()
    rows = conn.execute(
        "SELECT status, COUNT(*) AS c FROM incidents GROUP BY status"
    ).fetchall()
    conn.close()
    counts = {"Pending": 0, "Open": 0, "Resolved": 0}
    for r in rows:
        counts[r["status"]] = r["c"]
    return counts


def get_risk_counts():
    conn = get_connection()
    rows = conn.execute(
        "SELECT risk_level, COUNT(*) AS c FROM scans GROUP BY risk_level"
    ).fetchall()
    conn.close()
    counts = {"Low": 0, "Medium": 0, "High": 0}
    for r in rows:
        counts[r["risk_level"]] = r["c"]
    return counts


def get_monthly_trend():
    conn = get_connection()
    rows = conn.execute(
        """SELECT strftime('%Y-%m', created_at) AS ym, COUNT(*) AS c
           FROM scans GROUP BY ym ORDER BY ym"""
    ).fetchall()
    conn.close()
    return [{"month": r["ym"], "count": r["c"]} for r in rows]


def total_uploads():
    conn = get_connection()
    row = conn.execute("SELECT COUNT(*) AS c FROM scans").fetchone()
    conn.close()
    return row["c"]


def get_top_threat_categories(limit=6):
    """
    Derive a 'top threat types' breakdown by counting how often each
    indicator category (the text before ':' in scans.indicators) fires
    across all scans, e.g. 'Urgency', 'Suspicious link', 'Sender reputation'.
    """
    import json as _json

    conn = get_connection()
    rows = conn.execute("SELECT indicators FROM scans WHERE indicators IS NOT NULL").fetchall()
    conn.close()

    counts = {}
    for row in rows:
        try:
            indicators = _json.loads(row["indicators"] or "[]")
        except ValueError:
            continue
        for item in indicators:
            category = item.split(":", 1)[0].strip() if ":" in item else item
            if "risk reduced" in item:
                continue
            counts[category] = counts.get(category, 0) + 1

    ranked = sorted(counts.items(), key=lambda kv: kv[1], reverse=True)[:limit]
    return [{"label": label, "count": count} for label, count in ranked]
