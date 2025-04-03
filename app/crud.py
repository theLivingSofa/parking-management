# app/crud.py

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select, update, and_, func
from decimal import Decimal, ROUND_UP
import datetime
import pytz
from fastapi import HTTPException, status

from app import models, schemas, config
from app.qr_code import generate_qr_code

# --- Owner CRUD (Unchanged) ---
def get_owner_by_phone(db: Session, phone_number: str) -> models.Owner | None:
    normalized_phone = phone_number.strip(); return db.query(models.Owner).filter(models.Owner.phone_number == normalized_phone).first() if normalized_phone else None
def create_owner(db: Session, owner_data: schemas.OwnerCreate) -> models.Owner:
    normalized_phone = owner_data.phone_number.strip(); normalized_name = owner_data.name.strip()
    if not normalized_phone or not normalized_name: raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Name and Phone required.")
    existing_owner = get_owner_by_phone(db, normalized_phone)
    if existing_owner: raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Owner with phone '{normalized_phone}' exists.")
    owner = models.Owner(name=normalized_name, phone_number=normalized_phone); db.add(owner); return owner

# --- Vehicle CRUD (Register unchanged, get_vehicle modified) ---
def get_vehicle_by_plate(db: Session, license_plate: str) -> models.Vehicle | None:
    normalized_plate = license_plate.strip().upper(); return db.query(models.Vehicle).filter(func.upper(models.Vehicle.license_plate) == normalized_plate).first() if normalized_plate else None
def get_vehicle_by_qrcode(db: Session, qr_code: str) -> models.Vehicle | None:
    """Gets vehicle by QR code, eager loads Owner."""
    return db.query(models.Vehicle).options(joinedload(models.Vehicle.owner)).filter(models.Vehicle.qr_code == qr_code).first()
def register_vehicle(db: Session, vehicle_data: schemas.VehicleCreate) -> tuple[models.Vehicle | None, str | None]:
    normalized_plate = vehicle_data.license_plate.strip().upper(); owner_phone = vehicle_data.owner_phone_number.strip()
    if not normalized_plate or not owner_phone: raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Plate and Owner Phone required.")
    if get_vehicle_by_plate(db, normalized_plate): raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Vehicle '{normalized_plate}' registered.")
    owner = get_owner_by_phone(db, owner_phone)
    if not owner: raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Owner with phone '{owner_phone}' not found.")
    qr_data, qr_file_path = generate_qr_code(normalized_plate)
    if not qr_data or not qr_file_path: raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="QR generation failed.")
    if get_vehicle_by_qrcode(db, qr_data): raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="QR collision.")
    new_vehicle = models.Vehicle(license_plate=normalized_plate, qr_code=qr_data, owner_id=owner.id); db.add(new_vehicle); db.flush(); new_vehicle.owner = owner; return new_vehicle, qr_file_path

# --- Parking Spot CRUD (REMOVED) ---
# get_spot_by_number, update_spot_status, get_all_spots_with_status are removed

# --- Parking Record CRUD (Modified) ---
def get_active_record_by_vehicle_id(db: Session, vehicle_id: int) -> models.ParkingRecord | None:
    """Finds the active parking record (no spot involved), joining vehicle and owner."""
    return db.query(models.ParkingRecord)\
             .options(joinedload(models.ParkingRecord.vehicle).joinedload(models.Vehicle.owner))\
             .filter(models.ParkingRecord.vehicle_id == vehicle_id, models.ParkingRecord.exit_time == None).first()

def checkin_vehicle(db: Session, vehicle_id: int) -> models.ParkingRecord:
    """Creates a parking record (no spot assignment)."""
    # Assumes caller verified vehicle isn't already checked in
    entry_time = datetime.datetime.now(pytz.utc)
    db_record = models.ParkingRecord(vehicle_id=vehicle_id, entry_time=entry_time)
    db.add(db_record)
    # NO spot status update needed
    return db_record

def checkout_vehicle(db: Session, vehicle_id: int) -> dict | None:
    """Finds active record, calculates fee, updates record."""
    record = get_active_record_by_vehicle_id(db, vehicle_id) # Loads owner via vehicle
    if not record: return None

    exit_time = datetime.datetime.now(pytz.utc)
    entry_time_aware = record.entry_time.astimezone(pytz.utc) if record.entry_time.tzinfo else pytz.utc.localize(record.entry_time)
    duration = exit_time - entry_time_aware
    duration_hours = Decimal(duration.total_seconds()) / Decimal(3600)
    hours_charged = duration_hours.quantize(Decimal('1'), rounding=ROUND_UP)
    fee = (hours_charged * config.PARKING_RATE_PER_HOUR).quantize(Decimal("0.01"))

    record.exit_time = exit_time
    record.fee = fee
    # NO spot status update needed

    owner_name_str = record.vehicle.owner.name if record.vehicle and record.vehicle.owner else "N/A"
    owner_phone_str = record.vehicle.owner.phone_number if record.vehicle and record.vehicle.owner else "N/A"

    return {
        "license_plate": record.vehicle.license_plate if record.vehicle else "N/A",
        "owner_name": owner_name_str,
        "owner_phone_number": owner_phone_str,
        "entry_time": record.entry_time,
        "exit_time": exit_time,
        "duration_hours": float(duration_hours.quantize(Decimal("0.001"))),
        "fee": float(fee)
    }

# --- NEW: Get Vehicle Status ---
def get_vehicle_status_by_qrcode(db: Session, qr_code: str) -> dict:
    """Gets vehicle details and current parking status by QR code."""
    vehicle = get_vehicle_by_qrcode(db, qr_code=qr_code) # Loads owner
    if not vehicle:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vehicle with scanned QR code not found.")

    active_record = get_active_record_by_vehicle_id(db, vehicle_id=vehicle.id)

    owner_name = vehicle.owner.name if vehicle.owner else "N/A"
    owner_phone = vehicle.owner.phone_number if vehicle.owner else "N/A"

    status_info = {
        "message": "", # Set dynamically below
        "is_checked_in": active_record is not None,
        "license_plate": vehicle.license_plate,
        "owner_name": owner_name,
        "owner_phone_number": owner_phone,
        "entry_time": active_record.entry_time if active_record else None,
        # Checkout specific fields initially null
        "exit_time": None,
        "duration_hours": None,
        "fee": None
    }

    if active_record:
        status_info["message"] = f"Vehicle {vehicle.license_plate} is currently checked IN (since {active_record.entry_time.strftime('%Y-%m-%d %H:%M:%S %Z')})."
    else:
        status_info["message"] = f"Vehicle {vehicle.license_plate} is currently checked OUT."

    return status_info