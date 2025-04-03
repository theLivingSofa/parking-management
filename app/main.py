# app/main.py

import os
from fastapi import FastAPI, Depends, HTTPException, Request, status
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Dict # Import Dict

from app import crud, models, schemas, database, config

# --- App, Middleware, Static Files, Templates (Unchanged) ---
app = FastAPI(title="QR Vehicle Status System")
origins = ["*"]
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount(config.QR_CODE_URL_PATH, StaticFiles(directory=config.QR_CODE_DIR), name="qrcodes")
templates = Jinja2Templates(directory="templates")

# --- Database Initialization (Unchanged) ---
@app.on_event("startup")
def on_startup(): # Keep startup event as before
    try:
        from sqlalchemy import inspect
        inspector = inspect(database.engine)
        if not inspector.has_table("vehicles"): print("DB tables not found, creating..."); database.create_db_tables()
        else: print("DB tables already exist.")
    except Exception as e: print(f"DB check/creation error: {e}")

# --- API Endpoints ---

# Owner Registration (Unchanged)
@app.post("/api/owners", response_model=schemas.Owner, status_code=status.HTTP_201_CREATED)
async def register_new_owner(owner_data: schemas.OwnerCreate, db: Session = Depends(database.get_db)):
    try: owner = crud.create_owner(db=db, owner_data=owner_data); db.commit(); db.refresh(owner); return owner
    except HTTPException as http_exc: db.rollback(); raise http_exc
    except Exception as e: db.rollback(); print(f"Error owner reg: {e}"); raise HTTPException(status_code=500)

# Vehicle Registration (Unchanged)
@app.post("/api/register", response_model=schemas.VehicleRegistrationResponse, status_code=status.HTTP_201_CREATED)
async def register_new_vehicle(vehicle_data: schemas.VehicleCreate, db: Session = Depends(database.get_db)):
    try:
        vehicle, qr_path = crud.register_vehicle(db=db, vehicle_data=vehicle_data); db.commit(); db.refresh(vehicle)
        # Ensure owner relationship is loaded for response if needed (crud should handle via flush)
        # if not vehicle.owner: db.refresh(vehicle.owner) # Might not be needed
    except HTTPException as http_exc: db.rollback(); raise http_exc
    except Exception as e: db.rollback(); print(f"Error vehicle reg: {e}"); raise HTTPException(status_code=500)
    relative_qr_url = f"{config.QR_CODE_URL_PATH}/{os.path.basename(qr_path)}"
    response_vehicle_schema = schemas.Vehicle.model_validate(vehicle)
    return schemas.VehicleRegistrationResponse(vehicle=response_vehicle_schema, qr_code_path=relative_qr_url, message=f"Vehicle '{vehicle.license_plate}' registered for owner phone '{vehicle_data.owner_phone_number}'.")

# --- Spots Endpoint REMOVED ---
# @app.get("/api/spots", ...) removed

# --- NEW: Vehicle Status Endpoint ---
@app.post("/api/vehicle-status", response_model=schemas.VehicleStatusResponse)
async def get_vehicle_status(
    # Use a simple schema for the request body
    request_data: schemas.CheckOutRequest, # Reusing CheckOutRequest as it just needs qr_code
    db: Session = Depends(database.get_db)
):
    """Gets the current status (checked-in/out) and details of a vehicle by QR code."""
    try:
        status_details = crud.get_vehicle_status_by_qrcode(db=db, qr_code=request_data.qr_code)
        # Directly return the dict which should match the Pydantic model
        return status_details
    except HTTPException as http_exc:
        raise http_exc # Re-raise HTTP exceptions from CRUD
    except Exception as e:
        print(f"Error getting vehicle status: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal error getting vehicle status.")


# --- MODIFIED: Check-in Endpoint ---
@app.post("/api/checkin", response_model=schemas.VehicleStatusResponse)
async def check_in_vehicle(
    # Request now only contains qr_code
    check_in_data: schemas.CheckInRequest,
    db: Session = Depends(database.get_db)
):
    """Checks a vehicle IN using QR code."""
    vehicle = crud.get_vehicle_by_qrcode(db, qr_code=check_in_data.qr_code) # Loads owner
    if not vehicle: raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Vehicle with QR code not found.")

    active_record = crud.get_active_record_by_vehicle_id(db, vehicle_id=vehicle.id)
    if active_record: raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Vehicle {vehicle.license_plate} is already checked in.")

    # --- Spot lookup/check REMOVED ---

    try:
        record = crud.checkin_vehicle(db=db, vehicle_id=vehicle.id) # No spot_id needed
        db.commit(); db.refresh(record)
        db.refresh(record.vehicle);
        if record.vehicle: db.refresh(record.vehicle.owner) # Ensure owner loaded
    except Exception as e:
        db.rollback(); print(f"Error check-in commit: {e}"); raise HTTPException(status_code=500)

    owner_name = record.vehicle.owner.name if record.vehicle and record.vehicle.owner else "N/A"
    owner_phone = record.vehicle.owner.phone_number if record.vehicle and record.vehicle.owner else "N/A"

    return schemas.VehicleStatusResponse(
        message=f"Vehicle {vehicle.license_plate} checked IN successfully.",
        is_checked_in=True,
        license_plate=vehicle.license_plate,
        owner_name=owner_name,
        owner_phone_number=owner_phone,
        entry_time=record.entry_time
    )

# --- MODIFIED: Check-out Endpoint ---
@app.post("/api/checkout", response_model=schemas.VehicleStatusResponse) # Changed response model
async def check_out_vehicle(
    check_out_data: schemas.CheckOutRequest,
    db: Session = Depends(database.get_db)
):
    """Checks out a vehicle using its QR code."""
    vehicle = crud.get_vehicle_by_qrcode(db, qr_code=check_out_data.qr_code) # Loads owner
    if not vehicle: raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Vehicle with QR code not found.")

    try:
        checkout_details = crud.checkout_vehicle(db=db, vehicle_id=vehicle.id)
        if not checkout_details:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Vehicle {vehicle.license_plate} is not currently checked in.")
        db.commit()
    except HTTPException as http_exc:
         db.rollback(); raise http_exc
    except Exception as e:
        db.rollback(); print(f"Error check-out commit: {e}"); raise HTTPException(status_code=500)

    # Use the details returned from crud function
    return schemas.VehicleStatusResponse(
        message=f"Vehicle {checkout_details['license_plate']} checked OUT successfully.",
        is_checked_in=False,
        license_plate=checkout_details['license_plate'],
        owner_name=checkout_details['owner_name'],
        owner_phone_number=checkout_details['owner_phone_number'],
        entry_time=checkout_details['entry_time'],
        exit_time=checkout_details['exit_time'],
        duration_hours=checkout_details['duration_hours'],
        fee=checkout_details['fee']
    )

# --- Frontend Serving & Health Check (Unchanged) ---
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request): return templates.TemplateResponse("index.html", {"request": request})
@app.get("/health", status_code=200)
async def health_check(): return {"status": "OK"}