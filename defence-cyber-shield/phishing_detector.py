"""
phishing_detector.py
---------------------
Custom rule-based phishing scoring engine. No external AI API required.

The engine inspects OCR-extracted email text and returns a risk score
(0-100), a risk level (Low / Medium / High), a human-readable
recommendation, and the list of specific indicators that were triggered
(used for transparency in the UI and incident reports).
"""

import re

# ----------------------------------------------------------------------
# Signal dictionaries. Each entry maps a matched signal -> point value.
# ----------------------------------------------------------------------

URGENCY_WORDS = {
    "urgent": 8, "immediately": 8, "act now": 10, "asap": 6,
    "final notice": 9, "last warning": 9, "expire": 7, "expires today": 10,
    "within 24 hours": 9, "response required": 6, "time sensitive": 6,
    "failure to comply": 10, "immediate action": 9,
}

CREDENTIAL_WORDS = {
    "verify your account": 12, "verify account": 12, "confirm your password": 14,
    "password": 8, "reset your password": 12, "update your credentials": 12,
    "login credentials": 10, "click here to verify": 12, "suspended": 9,
    "account suspended": 12, "unusual activity": 8, "security alert": 6,
}

FINANCIAL_WORDS = {
    "bank": 7, "bank account": 9, "wire transfer": 12, "payment details": 9,
    "invoice": 5, "salary": 6, "tax refund": 8, "credit card": 9,
    "billing information": 8, "gift card": 10,
}

MILITARY_SENSITIVE_WORDS = {
    "classified": 14, "top secret": 15, "military": 6, "confidential": 10,
    "deployment schedule": 14, "operation order": 13, "chain of command": 8,
    "personnel file": 10, "clearance": 8, "command directive": 10,
}

ATTACHMENT_WORDS = {
    "attachment": 5, "attached file": 6, "open the attached": 9,
    "download attachment": 9, "enable macros": 14, "enable content": 12,
    ".exe": 15, ".scr": 15, ".zip": 6, ".js": 8,
}

SUSPICIOUS_LINK_PATTERNS = [
    (re.compile(r"bit\.ly", re.I), "bit.ly shortened link", 12),
    (re.compile(r"tinyurl", re.I), "TinyURL shortened link", 12),
    (re.compile(r"goo\.gl", re.I), "goo.gl shortened link", 10),
    (re.compile(r"t\.co/", re.I), "t.co shortened link", 8),
    (re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"), "raw IP address used as link", 15),
    (re.compile(r"https?://[^\s]*@"), "credential-embedded URL", 15),
    (re.compile(r"[a-z0-9.-]+\.(?:xyz|top|club|zip|country|gq|tk|men)\b", re.I),
     "high-risk / unusual top-level domain", 10),
]

TRUSTED_MIL_DOMAIN_PATTERN = re.compile(r"@[\w.-]*\.(?:mil|gov|nic\.in)\b", re.I)

SUSPICIOUS_SENDER_PATTERNS = [
    (re.compile(r"@.*\.(?:xyz|top|club|zip|country|gq|tk|men)\b", re.I),
     "sender domain uses a high-risk TLD", 12),
    (re.compile(r"noreply.*@.*\.(?:com|net|info)", re.I),
     "generic no-reply sender on a public domain", 4),
    (re.compile(r"support@|admin@|security@|helpdesk@", re.I),
     "generic role-based sender address", 3),
]


def _scan_dictionary(text_lower, dictionary):
    hits = []
    score = 0
    for phrase, points in dictionary.items():
        if phrase in text_lower:
            hits.append(phrase)
            score += points
    return score, hits


def _scan_links(text):
    hits = []
    score = 0
    for pattern, label, points in SUSPICIOUS_LINK_PATTERNS:
        if pattern.search(text):
            hits.append(label)
            score += points
    return score, hits


def _scan_sender(text):
    hits = []
    score = 0
    for pattern, label, points in SUSPICIOUS_SENDER_PATTERNS:
        if pattern.search(text):
            hits.append(label)
            score += points

    # Reward legitimate-looking military / government sender domains
    # (anchored to an actual @...mil / @...gov / @...nic.in address, not
    # just the substring appearing anywhere in the email body).
    if TRUSTED_MIL_DOMAIN_PATTERN.search(text):
        score -= 10
        hits.append("sender domain matches a trusted .mil/.gov pattern (risk reduced)")

    return score, hits


def analyze_text(ocr_text):
    """
    Analyze OCR-extracted email text and return a dict:
        {
            "score": int (0-100),
            "level": "Low" | "Medium" | "High",
            "recommendation": str,
            "indicators": [str, ...],
        }
    """
    if not ocr_text or not ocr_text.strip():
        return {
            "score": 20,
            "level": "Low",
            "recommendation": (
                "No readable text could be extracted from the screenshot. "
                "Upload a clearer image if you believe this email is suspicious."
            ),
            "indicators": ["OCR could not extract meaningful text from the image"],
        }

    text_lower = ocr_text.lower()
    total_score = 0
    indicators = []

    for dictionary, category in [
        (URGENCY_WORDS, "Urgency"),
        (CREDENTIAL_WORDS, "Credential harvesting"),
        (FINANCIAL_WORDS, "Financial lure"),
        (MILITARY_SENSITIVE_WORDS, "Military-sensitive content"),
        (ATTACHMENT_WORDS, "Malicious attachment pattern"),
    ]:
        score, hits = _scan_dictionary(text_lower, dictionary)
        total_score += score
        indicators.extend(f"{category}: '{h}'" for h in hits)

    link_score, link_hits = _scan_links(ocr_text)
    total_score += link_score
    indicators.extend(f"Suspicious link: {h}" for h in link_hits)

    sender_score, sender_hits = _scan_sender(ocr_text)
    total_score += sender_score
    indicators.extend(f"Sender reputation: {h}" for h in sender_hits)

    
    
    if ocr_text.count("!") >= 3:
        total_score += 4
        indicators.append("Excessive punctuation / urgency formatting")

    caps_words = re.findall(r"\b[A-Z]{4,}\b", ocr_text)
    if len(caps_words) >= 3:
        total_score += 4
        indicators.append("Excessive use of capital letters")

    score = max(0, min(100, total_score))

    if score <= 30:
        level = "Low"
        recommendation = "This email appears safe. Continue exercising caution."
    elif score <= 60:
        level = "Medium"
        recommendation = (
            "This email contains suspicious characteristics. "
            "Verify sender before responding."
        )
    else:
        level = "High"
        recommendation = (
            "This email exhibits strong phishing indicators. "
            "This incident has been automatically reported to Defence CERT. "
            "Do not click links, open attachments, or reply."
        )

    if not indicators:
        indicators.append("No known phishing indicators detected in extracted text")

    return {
        "score": score,
        "level": level,
        "recommendation": recommendation,
        "indicators": indicators,
    }
