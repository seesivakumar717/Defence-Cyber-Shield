# 🛡️ Defence Cyber Shield

### AI-Powered Military Email Phishing Detection & Incident Management Portal

**Defence Cyber Shield** is a cybersecurity web application designed to help military/defence personnel analyze suspicious email screenshots, detect phishing indicators, assign a risk score, and automatically create incidents for high-risk messages.

The system is built as an academic/demo project using **Flask, SQLite, OpenCV, Tesseract OCR, and a custom rule-based phishing detection engine**.

---

## 🎯 Project Objective

The main objective is to provide a simple workflow for handling suspicious emails:

```text
Suspicious Email
      ↓
Take Screenshot
      ↓
Upload Screenshot
      ↓
OCR Text Extraction
      ↓
Phishing Detection
      ↓
Risk Score (0–100)
      ↓
Low / Medium / High
      ↓
High Risk → Automatic Incident
      ↓
Administrator Dashboard
```

This approach allows users to upload an email screenshot instead of manually copying the email content.

---

## ✨ Features

### 👤 Soldier/User Features
- User registration with multiple accounts supported
- Optional Army ID
- Secure password hashing
- Soldier login/logout
- Soldier dashboard
- Upload suspicious email screenshots
- OCR-based text extraction
- Automated phishing analysis
- Risk score from 0–100
- Scan result details
- Scan history
- User profile

### 🛡️ Administrator Features
- Single administrator account
- Separate administrator login
- Administrator dashboard
- View reported high-risk incidents
- Incident details
- Incident status management
- Delete/close incidents
- View registered soldiers
- Analytics and risk statistics
- Reports dashboard

### 🔍 OCR Processing
The application uses:
- **Tesseract OCR**
- **pytesseract**
- **OpenCV**
- Image preprocessing
- Grayscale conversion
- Denoising
- Adaptive thresholding
- Image upscaling for clearer text recognition

### 🧠 Phishing Detection
The project uses a **custom rule-based detection engine** rather than an external AI API.

The engine checks for indicators such as:

- Urgency and pressure language
- Account verification requests
- Password/credential harvesting
- Financial lures
- Military-sensitive keywords
- Suspicious attachments
- Suspicious URLs
- URL shorteners
- Raw IP addresses in links
- Unusual/high-risk domains
- Suspicious sender patterns
- Excessive capitalization
- Excessive punctuation

---

## 📊 Risk Scoring

| Risk Score | Level | System Behavior |
|---|---|---|
| **0–30** | 🟢 Low | Advice is shown to the user |
| **31–60** | 🟡 Medium | Warning and verification advice are shown |
| **61–100** | 🔴 High | An incident is automatically created and shown on the administrator dashboard |

The final score is calculated from the phishing indicators detected in the extracted text.

---

## 🛠️ Technology Stack

| Component | Technology |
|---|---|
| Backend | Python / Flask |
| Database | SQLite |
| Database Access | Raw `sqlite3` |
| OCR | Tesseract OCR + pytesseract |
| Image Processing | OpenCV |
| Security | Werkzeug password hashing |
| CSRF Protection | Flask-WTF |
| Frontend | HTML5, CSS3, Jinja2 |
| JavaScript | Vanilla JavaScript |
| Charts | Chart.js |
| Styling | Custom dark cyber/military UI |

---

## 📁 Project Structure

```text
defence-cyber-shield/
│
├── app.py                    # Main Flask application
├── models.py                 # SQLite database functions
├── init_db.py                # Database initialization
├── ocr.py                    # OCR and image preprocessing
├── phishing_detector.py      # Rule-based phishing detection engine
├── requirements.txt          # Python dependencies
├── .gitignore                # Git ignored files
├── README.md                 # Project documentation
│
├── templates/
│   ├── base.html
│   ├── dashboard_base.html
│   ├── index.html
│   ├── login.html
│   ├── register.html
│   ├── soldier_dashboard.html
│   ├── result.html
│   ├── history.html
│   ├── profile.html
│   ├── admin_dashboard.html
│   ├── incidents.html
│   ├── users.html
│   ├── analytics.html
│   ├── reports.html
│   ├── admin_login.html
│   └── partials/
│       └── flash.html
│
├── static/
│   ├── css/
│   │   └── style.css
│   └── js/
│       ├── main.js
│       └── charts.js
│
└── uploads/
    └── .gitkeep
```

---

## 💻 Requirements

- Python **3.10+**
- Tesseract OCR
- Git (for source control/deployment)

### Python Packages

The required packages are listed in:

```text
requirements.txt
```

Main dependencies include:

- Flask
- Flask-WTF
- Werkzeug
- Pillow
- OpenCV
- pytesseract

---

## 🚀 Local Installation

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/defence-cyber-shield.git
cd defence-cyber-shield
```

### 2. Create a virtual environment

#### Windows

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

If PowerShell blocks activation:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\venv\Scripts\Activate.ps1
```

#### Linux / macOS

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Install Tesseract OCR

#### Windows

Install Tesseract OCR and make sure `tesseract.exe` is available to the application.

A common installation path is:

```text
C:\Program Files\Tesseract-OCR\tesseract.exe
```

#### Ubuntu / Debian

```bash
sudo apt update
sudo apt install tesseract-ocr
```

#### macOS

```bash
brew install tesseract
```

> Note: The current local Windows OCR configuration uses the Windows Tesseract executable path. For Linux/cloud deployment, `ocr.py` should use the Linux Tesseract executable path or system `PATH`.

### 5. Initialize the database

```bash
python init_db.py
```

### 6. Start the application

```bash
python app.py
```

Open:

```text
http://127.0.0.1:5000
```

---

## 🔐 Authentication

### Soldier/User Registration

New soldier/user accounts can be registered from the registration page.

- Multiple user accounts are supported.
- Army ID is optional.
- Usernames and email addresses must be unique.
- Passwords are stored using password hashing.

### Administrator

The administrator has a separate login.

The project is designed to maintain **one administrator account**. After an administrator account exists, the system uses the Admin Login page for administrator access.

**Administrator credentials are intentionally not documented in this README.**

---

## 📷 Screenshot Analysis Workflow

1. Sign in as a soldier/user.
2. Open the analysis section.
3. Select a suspicious email screenshot.
4. Upload the image.
5. The application saves the image temporarily.
6. OpenCV preprocesses the screenshot.
7. Tesseract extracts the text.
8. The phishing detection engine analyzes the extracted text.
9. The system generates a risk score.
10. The result page displays the detected indicators and recommendation.
11. If the result is **High Risk**, an incident is automatically created for the administrator.

### Supported Screenshot Formats

```text
PNG
JPG
JPEG
WEBP
```

Maximum upload size:

```text
8 MB
```

---

## 🧠 Detection Engine

The project does not require an external AI API.

Instead, `phishing_detector.py` uses a transparent rule-based scoring approach.

Example indicators include:

```text
"urgent"
"act now"
"verify your account"
"reset your password"
"unusual activity"
"wire transfer"
"classified"
"deployment schedule"
".exe"
"enable macros"
"bit.ly"
"tinyurl"
"raw IP address"
```

This makes the detection logic easy to demonstrate, inspect, and explain during an academic project presentation.

---

## 📋 Incident Management

When a scan reaches **High Risk (61–100)**:

```text
High-Risk Scan
      ↓
Incident Automatically Created
      ↓
Stored in SQLite
      ↓
Administrator Dashboard
      ↓
Admin Reviews Incident
      ↓
Status Can Be Updated
```

Low and Medium risk scans remain available in the user's scan/history workflow without creating a formal incident.

---

## 📈 Analytics & Reports

The administrator area provides:

- Total scans
- High/Medium/Low risk counts
- Incident statistics
- Risk trends
- Threat category information
- Registered soldier information
- Reports and analytics views

---

## 🔒 Security Controls

The project includes several basic web security controls:

- Werkzeug password hashing
- Server-side Flask sessions
- CSRF protection using Flask-WTF
- Secure filename handling
- Restricted upload extensions
- Maximum upload size
- Role-based route protection
- Controlled access to uploaded files

---

## 🗃️ Data Storage

The application currently uses SQLite:

```text
database.db
```

The database is intentionally excluded from Git through `.gitignore`.

Uploaded screenshots are also excluded from Git so that local test data is not committed to the repository.

---

## 🌐 Deployment

The project can be deployed to a cloud platform such as **Render** using a production WSGI server such as Gunicorn.

Typical commands:

```text
Build Command:
pip install -r requirements.txt

Start Command:
gunicorn app:app
```

### Important deployment considerations

Before production deployment:

- Move all secrets and credentials to environment variables.
- Use a persistent database instead of relying on local SQLite storage.
- Use persistent storage for uploaded screenshots.
- Configure Tesseract correctly for the Linux deployment environment.
- Enable HTTPS.
- Keep debug mode disabled.
- Review authentication and access controls.

---

## ⚠️ Project Status

This project is intended primarily for:

- Academic demonstration
- Cybersecurity learning
- Phishing detection prototyping
- Defence/cyber awareness demonstrations

The current phishing detection engine is **rule-based** and should not be treated as a production-grade enterprise phishing gateway without additional validation, testing, monitoring, and security review.

---

## 🔮 Future Enhancements

Possible future improvements include:

- Machine-learning phishing classification
- LLM-based email analysis
- Sender reputation APIs
- SPF/DKIM/DMARC verification
- Real-time URL reputation checks
- Attachment sandboxing
- Email client/browser integration
- Persistent cloud database
- Persistent object/file storage
- Security audit logging
- Multi-factor authentication
- Real-time administrator notifications

---

## 📜 License

This project is created for academic and educational purposes.

Add a specific open-source license here only if you decide to publish the source under one.

---

## 👨‍💻 Author

**Tharun Sivakumar**

**Project:** Defence Cyber Shield

**Purpose:** Cybersecurity / Phishing Detection / Incident Management
