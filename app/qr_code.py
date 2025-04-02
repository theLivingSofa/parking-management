# app/qr_code.py

import qrcode
import uuid
import os

# Import config to get the directory path
from app import config

def generate_qr_code(license_plate: str) -> tuple[str, str]:
    """
    Generates QR code data and saves it as a PNG image.

    Args:
        license_plate: The license plate number.

    Returns:
        A tuple containing:
            - qr_data (str): The unique string embedded in the QR code.
            - qr_file_path (str): The relative file path where the PNG was saved.
            Returns (None, None) if license_plate is empty.
    """
    if not license_plate:
        return None, None

    # Create a unique identifier combined with the license plate for the QR data
    # Using a simpler unique part here, ensure it meets uniqueness needs
    unique_id = str(uuid.uuid4())[:8]
    # Make QR data simple, could just be the unique ID or a combo
    # Let's use the combo for potential lookup later, ensure filename safety
    safe_plate = "".join(filter(str.isalnum, license_plate)).upper()
    qr_data = f"{safe_plate}-{unique_id}" # Data stored in QR

    # Ensure the target directory exists
    save_dir = config.QR_CODE_DIR
    os.makedirs(save_dir, exist_ok=True)

    # Generate file path - use qr_data as filename (ensure it's filename-safe)
    qr_file_name = f"{qr_data}.png"
    qr_file_path = os.path.join(save_dir, qr_file_name)

    try:
        # Create and save the QR code image
        qr_img = qrcode.make(qr_data)
        qr_img.save(qr_file_path)

        print(f"Generated QR Code for {license_plate}: data='{qr_data}', path='{qr_file_path}'")
        # Return the data and the relative path for storage/reference
        return qr_data, qr_file_path

    except Exception as e:
        print(f"Error generating QR code for {license_plate}: {e}")
        return None, None