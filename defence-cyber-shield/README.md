# Defence Cyber Shield

AI-Powered Military Email Phishing Detection & Incident Management Portal.

Soldiers upload a screenshot of a suspicious email instead of forwarding it.
The portal runs OCR on the image, scores it with a rule-based phishing
detection engine, and — for High risk emails — automatically opens a cyber
incident that shows up on the Administrator's SOC dashboard.

## Tech stack

- **Backend:** Flask (Python), SQLite (raw `sqlite3`, no ORM)
- **OCR:** Tesseract OCR + OpenCV preprocessing + Pillow
- **AI Engine:** Custom rule-based phishing scoring engine (no external API)
- **Frontend:** HTML5, CSS3 (custom dark cyber/military design system),
  Bootstrap 5, vanilla JavaScript, Chart.js
- **Security:** password hashing (Werkzeug), server-side sessions,
  CSRF protection (Flask-WTF), upload validation, secure file serving

## Requirements

- Python 3.10+
- Tesseract OCR installed on the host system and available on `PATH`
  - Ubuntu/Debian: `sudo apt-get install tesseract-ocr`
  - macOS: `brew install tesseract`
  - Windows: install from https://github.com/UB-Mannheim/tesseract/wiki
    and make sure `tesseract.exe` is on your `PATH`

## Setup

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

pip install -r requirements.txt

python init_db.py               # creates database.db
python app.py                   # starts the dev server on :5000
```

Open http://127.0.0.1:5000 in your browser.

## First run

1. The landing page will show a **Register** button. Only ONE soldier
   account can ever be created — after registration completes, the
   registration page is permanently disabled (tracked in the `system`
   table; delete `database.db` and re-run `init_db.py` to reset).
2. Sign in as that soldier to upload screenshots and view your scan
   history.
3. Sign in as the Administrator using the toggle on the login page:
   - **Username:** `admin`
   - **Password:** `Army@123`
   - These are hardcoded in `app.py` (`ADMIN_USERNAME` /
     `ADMIN_PASSWORD_HASH`) and never appear on the registration form.

## How scoring works

`phishing_detector.py` inspects the OCR-extracted email text for:

- Urgency / pressure language ("act now", "final notice"...)
- Credential-harvesting phrases ("verify your account", "reset your
  password"...)
- Financial lures ("wire transfer", "gift card"...)
- Military-sensitive terms ("classified", "deployment schedule"...)
- Malicious attachment patterns (`.exe`, "enable macros"...)
- Suspicious links (URL shorteners, raw IPs, high-risk TLDs)
- Sender reputation (high-risk TLDs vs. genuine `.mil`/`.gov` senders)

Scores are combined into a 0–100 risk score:

| Score  | Level  | Behavior                                              |
|--------|--------|--------------------------------------------------------|
| 0–30   | Low    | Advice shown only                                      |
| 31–60  | Medium | Warning + advice shown, no incident created             |
| 61–100 | High   | Incident auto-created and routed to the admin dashboard |

## Project structure

```
project/
├── app.py                 # Flask routes, auth, upload handling
├── init_db.py              # DB bootstrap script
├── models.py                # SQLite data access layer
├── phishing_detector.py     # Rule-based AI scoring engine
├── ocr.py                    # OpenCV + Tesseract text extraction
├── requirements.txt
├── templates/                # Jinja2 templates
│   ├── base.html / dashboard_base.html
│   ├── index.html, login.html, register.html
│   ├── soldier_dashboard.html, result.html, history.html, profile.html
│   ├── admin_dashboard.html, incidents.html, users.html,
│   │   analytics.html, reports.html
│   └── partials/flash.html
├── static/
│   ├── css/style.css        # Design system (dark cyber/military theme)
│   └── js/main.js, charts.js
└── uploads/                  # Uploaded screenshots (created at runtime)
```

## Notes

- `app.config["SECRET_KEY"]` is generated randomly at process start by
  default. Set the `DCS_SECRET_KEY` environment variable to pin it
  across restarts (recommended once you move beyond local testing).
- Max upload size is 8 MB; only PNG/JPG/JPEG/WEBP are accepted.
- This is a demonstration / training portal. Before any real deployment,
  put it behind HTTPS, run it with a production WSGI server (gunicorn/
  waitress), and change the hardcoded admin password.
