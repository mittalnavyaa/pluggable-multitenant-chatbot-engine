# apps/central-hub-backend/src/analytics/lead_detection/heuristics.py

import re

# Dominant Intent Classifications Key Mappings
INTENT_PATTERNS = {
    "PRICING": [
        r"\bprice\b", r"\bpricing\b", r"\bcost\b", r"\bsubscription\b", 
        r"\bplan\b", r"\bbilling\b", r"\bquote\b", r"\bbuy\b", r"\blicensing\b"
    ],
    "DEMO_REQUEST": [
        r"\bdemo\b", r"\bschedule\b", r"\bcall\b", r"\benterprise\b", 
        r"\bmeeting\b", r"\bpresentation\b", r"\bwalkthrough\b"
    ],
    "TECHNICAL_SUPPORT": [
        r"\berror\b", r"\bdebug\b", r"\bbug\b", r"\bbroken\b", 
        r"\bfail\b", r"\btrouble\b", r"\bissue\b", r"\bexception\b"
    ],
    "DOCUMENTATION": [
        r"\bdocs\b", r"\bdocumentation\b", r"\bguide\b", r"\bapi reference\b", 
        r"\breadme\b", r"\bhow to install\b"
    ],
    "GREETINGS": [
        r"\bhi\b", r"\bhello\b", r"\bhey\b", r"\bgreetings\b", r"\bhowdy\b"
    ],
    "SMALL_TALK": [
        r"\bhow are you\b", r"\bweather\b", r"\bjoke\b", r"\bwhat is your name\b"
    ]
}

# Commercial Buying Signal Indicators
BUYING_SIGNALS = {
    "Pricing": [r"\bprice\b", r"\bpricing\b", r"\bcost\b", r"\bpricing tier\b", r"\bquote\b", r"\bdiscount\b", r"\bbudget\b"],
    "Enterprise Info": [r"\benterprise\b", r"\benterprise plan\b", r"\bcorporate\b", r"\bvolume license\b", r"\bcustom agreement\b"],
    "Demo Scheduling": [r"\bdemo\b", r"\bschedule call\b", r"\bsales representative\b", r"\bcontact sales\b"],
    "Trial & Sign-up": [r"\btrial\b", r"\bfree test\b", r"\bevaluation account\b", r"\bsign up\b"]
}

# Urgency Indicators
URGENCY_SIGNALS = [
    r"\btoday\b", r"\bimmediately\b", r"\bthis week\b", r"\bdeadline\b", 
    r"\blimited seats\b", r"\bregister now\b", r"\basap\b", r"\burgent\b"
]

# Safeguards to protect against false positives
FALSE_POSITIVE_PATTERNS = [
    # Stack traces / code logs
    r"traceback \(most recent call last\)",
    r"stack trace",
    r"unhandled exception",
    r"nullpointerexception",
    r"syntaxerror",
    
    # Generic shell commands
    r"npm install",
    r"pip install",
    r"docker run",
    r"git clone",
    
    # Non-commercial support queries
    r"forgot password",
    r"reset my account",
    r"login issue",
    r"cookie consent",
    
    # Chatbot metadata queries
    r"what can you do",
    r"write a python script",
    r"summarize this text"
]

# Contact extraction regexes
EMAIL_REGEX = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
PHONE_REGEX = re.compile(r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b")
