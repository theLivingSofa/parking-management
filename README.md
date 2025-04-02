# QR Code Parking Management System

A web-based application for managing parking lot occupancy using QR codes for vehicle check-in and check-out, built with FastAPI and PostgreSQL.

## Overview

This system allows for registering vehicle owners and their vehicles, generating unique QR codes for each vehicle. Users can then scan these QR codes via a web interface to check vehicles in (specifying the spot number) and check them out. The system calculates parking duration and fees upon check-out and provides a real-time view of parking spot availability.

## Features

* **Owner Registration:** Register vehicle owners with their name and unique phone number.
* **Vehicle Registration:** Register vehicles with a license plate, link them to an owner via phone number, and automatically generate a unique QR code (saved as a PNG image).
* **QR Code Generation:** Creates and saves unique QR code PNG images for each registered vehicle in the `qrcodes/` directory.
* **Spot Status Display:** Shows a real-time grid view of all parking spots, indicating availability and displaying occupant details (license plate, owner name/phone, entry time) if occupied.
* **QR Code Check-In:** Scan a registered vehicle's QR code using the device camera via the web interface, then manually enter the parking spot number to check the vehicle in.
* **QR Code Check-Out:** Scan a registered vehicle's QR code to check the vehicle out. The system automatically calculates the duration parked and the corresponding fee based on a configured rate.
* **Simple Web Interface:** Basic HTML/CSS/JavaScript frontend for interacting with the system.

## Technologies Used

* **Backend:**
    * Python 3.7+
    * FastAPI (ASGI Web Framework)
    * SQLAlchemy (ORM for database interaction)
    * PostgreSQL (Relational Database)
    * Pydantic (Data validation and serialization)
    * Uvicorn (ASGI Server)
    * `python-dotenv` (Environment variable management)
    * `qrcode[pil]` (QR code generation)
    * `pytz` (Timezone handling)
* **Frontend:**
    * HTML5
    * CSS3
    * JavaScript (Vanilla JS with Fetch API)
    * `html5-qrcode` (JavaScript library for QR code scanning via browser)
* **Database:**
    * PostgreSQL

## Project Structure

<img width="576" alt="image" src="https://github.com/user-attachments/assets/b31c1343-4295-4220-ad26-99773fc00197" />


## Setup and Installation

1.  **Clone the Repository:**
    ```bash
    git clone https://github.com/theLivingSofa/parking-management.git
    cd parking-management
    ```

2.  **Prerequisites:**
    * Install Python 3.7 or higher.
    * Install PostgreSQL and ensure the server is running.

3.  **Create Directories:**
    * Manually create the directory for storing QR codes:
        ```bash
        mkdir qrcodes
        ```

4.  **Set Up Virtual Environment (Recommended):**
    ```bash
    python -m venv venv
    # Activate it:
    # Windows: venv\Scripts\activate
    # macOS/Linux: source venv/bin/activate
    ```

5.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

6.  **Set Up PostgreSQL Database:**
    * Connect to PostgreSQL (e.g., using `psql`).
    * Create the database specified in your `.env` file (if it doesn't exist):
        ```sql
        CREATE DATABASE your_db_name;
        ```

7.  **Configure Environment Variables:**
    * Create a `.env` file in the project root directory by copying/renaming from a template if provided, or create it manually.
    * Edit the `.env` file and set your actual `DATABASE_URL` and `PARKING_RATE_PER_HOUR`. Example content:
        ```dotenv
        DATABASE_URL=postgresql://YOUR_DB_USER:YOUR_DB_PASSWORD@YOUR_DB_HOST:YOUR_DB_PORT/YOUR_DB_NAME
        PARKING_RATE_PER_HOUR=20.00
        ```

8.  **Create Database Tables:**
    * Make sure your virtual environment is activated and you are in the project root directory.
    * Run the database script (this uses the models defined in `app/models.py` [cite: uploaded:Parking Mgmt/backend/models.py]):
        ```bash
        python -m app.database
        ```
    * Alternatively, use the manual SQL commands provided in previous steps.

9.  **Add Initial Parking Spots:**
    * You need to populate the `parking_spots` table before you can check vehicles in. Connect to your database and run `INSERT` commands:
        ```sql
        -- Connect first: \c your_db_name
        INSERT INTO parking_spots (spot_number) VALUES
        ('A01'), ('A02'), ('A03'), ('B01'), ('B02'), ('B03')
        ON CONFLICT (spot_number) DO NOTHING;
        -- Add all your desired spots
        ```

10. **(Optional) Host QR Library Locally:**
    * Download `html5-qrcode.min.js` (e.g., from unpkg orcdnjs) and place it in the `static/` folder.
    * Ensure the `<script>` tag in `templates/index.html` points to `/static/html5-qrcode.min.js` [cite: uploaded:Parking Mgmt/frontend/index.html].

## Running the Application

**Run using Uvicorn (Standard Method):**
1.  Make sure you are in the project root directory and your virtual environment is activated.
2.  Start the Uvicorn server:
    ```bash
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
    ```
3.  Open your web browser and navigate to `http://127.0.0.1:8000`.

**Run using Clickable Scripts (Alternative):**
* For MacOS
1. Modify the code in the file named `start_parking_app.sh` in your project root directory and set the venv path to the venv you created.
2. Make the script executable (run this *once* in your terminal from the project root):
        ```bash
        chmod +x start_parking_app.sh
        ```
3. Run the script from the terminal (`./start_parking_app.sh`) or by double-clicking it in Finder.
4. Open your web browser and navigate to `http://127.0.0.1:8000`.

* For Windows
1. Modify the code in the file named `start_parking_app.bat` in your project root directory and set the venv path to the venv you created.
2. Run the script by double-clicking the `start_parking_app.bat` file.
3. Open your web browser and navigate to `http://127.0.0.1:8000`.


## Usage Workflow

1.  **Register Owners:** Use the "Register New Owner" section to add owners by name and unique phone number.
2.  **Register Vehicles:** Use the "Register New Vehicle" section, providing the license plate and the phone number of a previously registered owner. A QR code will be generated and displayed for download.
3.  **Check-In:** Click "Scan QR for Check-In", scan the vehicle's QR code using your camera. Enter the assigned parking spot number when prompted and click "Confirm Check-In".
4.  **Check-Out:** Click "Scan QR for Check-Out", scan the vehicle's QR code. Click "Confirm Check-Out". The system calculates the fee and marks the spot as available.
5.  **View Status:** The "Parking Lot Status" section updates automatically after check-ins and check-outs, showing availability and occupant details.

## API Endpoints (Brief)

* `POST /api/owners`: Register a new owner.
* `POST /api/register`: Register a new vehicle and get its QR code.
* `GET /api/spots`: Get the status of all parking spots.
* `POST /api/checkin`: Check a vehicle in.
* `POST /api/checkout`: Check a vehicle out.
* `GET /`: Serves the frontend HTML.
* `GET /static/...`: Serves static CSS/JS files.
* `GET /qrcodes/...`: Serves generated QR code PNG images.

## Future Enhancements (Ideas)

* User authentication for operators.
* Different rates based on time or spot type.
* Parking spot reservations.
* Admin interface for managing spots/owners/vehicles.
* Database migrations using Alembic.
* More robust error handling and UI feedback.
* Reporting features.
