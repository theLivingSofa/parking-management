# app/main.py

import os
from fastapi import FastAPI, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from typing import List
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi import FastAPI, Depends, HTTPException, Request, status
from fastapi.staticfiles import StaticFiles


from app import crud, models, schemas, database, config
# ... keep app setup, middleware, static files, templates, startup event ...
app = FastAPI(title="Owner Phone Parking Management System")
origins = ["*"]
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount(config.QR_CODE_URL_PATH, StaticFiles(directory=config.QR_CODE_DIR), name="qrcodes")
templates = Jinja2Templates(directory="templates")
@app.on_event("startup")
def on_startup(): # Keep startup event as before
    try:
        from sqlalchemy import inspect
        inspector = inspect(database.engine)
        if not inspector.has_table("vehicles"): print("Database tables not found, attempting creation..."); database.create_db_tables()
        else: print("Database tables already exist.")
    except Exception as e: print(f"Error during startup table check/creation: {e}")

# --- API Endpoints ---

# MODIFIED: Owner Registration Endpoint
@app.post("/api/owners", response_model=schemas.Owner, status_code=status.HTTP_201_CREATED)
async def register_new_owner(
    # Use schema with name and phone
    owner_data: schemas.OwnerCreate,
    db: Session = Depends(database.get_db)
):
    """Registers a new owner with name and phone number."""
    try:
        owner = crud.create_owner(db=db, owner_data=owner_data)
        db.commit()
        db.refresh(owner)
        return owner
    except HTTPException as http_exc:
        db.rollback(); raise http_exc
    except Exception as e:
        db.rollback(); print(f"Error registering owner: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal error registering owner.")

# MODIFIED: Vehicle Registration Endpoint
@app.post("/api/register", response_model=schemas.VehicleRegistrationResponse, status_code=status.HTTP_201_CREATED)
async def register_new_vehicle(
    # Use schema with license plate and owner phone number
    vehicle_data: schemas.VehicleCreate,
    db: Session = Depends(database.get_db)
):
    """Registers a new vehicle, associates via owner's phone number, generates QR code."""
    try:
        # CRUD function now handles owner lookup/creation by phone
        vehicle, qr_path = crud.register_vehicle(db=db, vehicle_data=vehicle_data)
        db.commit()
        db.refresh(vehicle)
        # Ensure relationship is loaded for response schema population
        if not vehicle.owner: # If owner was newly created and relationship not auto-populated
             db.refresh(vehicle.owner) # Explicitly refresh (might need owner object from crud)
             # A cleaner way might be to return the full owner object from crud register_vehicle
             # For now, assume SQLAlchemy handles it or fetch separately if needed.
             # Let's rely on Pydantic's from_attributes for now.

    except HTTPException as http_exc:
        db.rollback(); raise http_exc
    except Exception as e:
        db.rollback(); print(f"Error during registration: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal error during vehicle registration.")

    relative_qr_url = f"{config.QR_CODE_URL_PATH}/{os.path.basename(qr_path)}"

    # Use Pydantic's validation/serialization which handles nested models
    response_vehicle_schema = schemas.Vehicle.model_validate(vehicle)

    return schemas.VehicleRegistrationResponse(
        vehicle=response_vehicle_schema,
        qr_code_path=relative_qr_url,
        message=f"Vehicle '{vehicle.license_plate}' registered successfully for owner with phone '{vehicle_data.owner_phone_number}'."
    )


@app.get("/api/spots", response_model=List[schemas.ParkingSpotStatus])
async def get_parking_spots(db: Session = Depends(database.get_db)):
    """Retrieves spot status, including owner details if occupied."""
    spots = crud.get_all_spots_with_status(db=db)
    return spots


@app.post("/api/checkin", response_model=schemas.CheckInOutResponse)
async def check_in_vehicle(
    check_in_data: schemas.CheckInRequest,
    db: Session = Depends(database.get_db)
):
    """Checks a vehicle in using QR code and assigned spot number."""
    vehicle = crud.get_vehicle_by_qrcode(db, qr_code=check_in_data.qr_code) # Loads owner too now
    if not vehicle: raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Vehicle with scanned QR code not found.")

    active_record = crud.get_active_record_by_vehicle_id(db, vehicle_id=vehicle.id)
    if active_record:
        spot_num = active_record.spot.spot_number if active_record.spot else 'unknown'
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Vehicle {vehicle.license_plate} is already parked in spot {spot_num}.")

    spot = crud.get_spot_by_number(db, spot_number=check_in_data.spot_number)
    if not spot: raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Parking spot '{check_in_data.spot_number}' not found.")
    if spot.is_occupied: raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Parking spot '{check_in_data.spot_number}' is already occupied.")

    try:
        record = crud.checkin_vehicle(db=db, vehicle_id=vehicle.id, spot_id=spot.id)
        db.commit(); db.refresh(record)
        # Refresh related objects needed for response
        db.refresh(record.vehicle);
        if record.vehicle: db.refresh(record.vehicle.owner) # Ensure owner is loaded
        db.refresh(record.spot)
    except Exception as e:
        db.rollback(); print(f"Error during check-in DB commit: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error during check-in.")

    owner_name_str = record.vehicle.owner.name if record.vehicle and record.vehicle.owner else "N/A"
    owner_phone_str = record.vehicle.owner.phone_number if record.vehicle and record.vehicle.owner else "N/A"

    return schemas.CheckInOutResponse(
        message=f"Vehicle {vehicle.license_plate} (Owner: {owner_name_str}) checked into spot {spot.spot_number}",
        license_plate=vehicle.license_plate,
        owner_name=owner_name_str,
        owner_phone_number=owner_phone_str,
        spot_number=spot.spot_number,
        entry_time=record.entry_time
    )

@app.post("/api/checkout", response_model=schemas.CheckOutDetailsResponse)
async def check_out_vehicle(
    check_out_data: schemas.CheckOutRequest,
    db: Session = Depends(database.get_db)
):
    """Checks out a vehicle using its QR code."""
    vehicle = crud.get_vehicle_by_qrcode(db, qr_code=check_out_data.qr_code) # Loads owner too
    if not vehicle: raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Vehicle with scanned QR code not found.")

    try:
        checkout_details = crud.checkout_vehicle(db=db, vehicle_id=vehicle.id)
        if not checkout_details:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Vehicle {vehicle.license_plate} is not currently checked in."
            )
        db.commit()
    except HTTPException as http_exc:
         db.rollback(); raise http_exc
    except Exception as e:
        db.rollback(); print(f"Error during check-out DB commit/logic: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error during check-out.")

    owner_name = checkout_details.get("owner_name", "N/A") # Get owner name from details dict

    return schemas.CheckOutDetailsResponse(
        message=f"Vehicle {checkout_details['license_plate']} (Owner: {owner_name}) checked out from spot {checkout_details['spot_number']}.",
        **checkout_details
    )


# --- Frontend Serving Route & Health Check (Keep as before) ---
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request): return templates.TemplateResponse("index.html", {"request": request})
@app.get("/health", status_code=200)
async def health_check(): return {"status": "OK"}