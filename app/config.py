# app/config.py

import os
from dotenv import load_dotenv
from decimal import Decimal, InvalidOperation

# Load environment variables from .env file
load_dotenv()

# --- Database Configuration ---
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("CRITICAL ERROR: DATABASE_URL environment variable not set!")
    # Consider raising an error or exiting in a real application

# --- Application Settings ---
DEFAULT_PARKING_RATE = Decimal("20.00")
PARKING_RATE_PER_HOUR_STR = os.getenv("PARKING_RATE_PER_HOUR")

try:
    PARKING_RATE_PER_HOUR = Decimal(PARKING_RATE_PER_HOUR_STR)
    if PARKING_RATE_PER_HOUR < 0:
        print(f"Warning: PARKING_RATE_PER_HOUR ({PARKING_RATE_PER_HOUR}) is negative. Using default.")
        PARKING_RATE_PER_HOUR = DEFAULT_PARKING_RATE
except (TypeError, InvalidOperation, ValueError):
    print(f"Warning: PARKING_RATE_PER_HOUR not found or invalid ('{PARKING_RATE_PER_HOUR_STR}'). Using default: {DEFAULT_PARKING_RATE}")
    PARKING_RATE_PER_HOUR = DEFAULT_PARKING_RATE

# --- QR Code Settings ---
# Directory to save generated QR code images (relative to project root)
QR_CODE_DIR = "qrcodes"
# Base URL path for accessing QR codes if served statically
QR_CODE_URL_PATH = "/qrcodes" # Corresponds to StaticFiles mount in main.py

# Optional: Print loaded values for verification during startup (remove in production)
# print(f"Loaded DATABASE_URL: {'Set' if DATABASE_URL else 'Not Set'}")
# print(f"Loaded PARKING_RATE_PER_HOUR: {PARKING_RATE_PER_HOUR}")
# print(f"QR Code Directory: {QR_CODE_DIR}")