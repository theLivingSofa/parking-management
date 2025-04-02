# app/crud.py

from sqlalchemy.orm import Session, joinedload, contains_eager, selectinload
from sqlalchemy import select, update, and_, func
from decimal import Decimal, ROUND_UP
import datetime
import pytz
from fastapi import HTTPException, status

from app import models, schemas, config
from app.qr_code import generate_qr_code

# --- Owner CRUD ---
def get_owner_by_phone(db: Session, phone_number: str) -> models.Owner | None:
    """Finds an owner by phone number."""
    # Consider normalizing phone numbers (e.g., remove spaces, dashes) before query/storage
    normalized_phone = phone_number.strip()
    if not normalized_phone: return None
    return db.query(models.Owner).filter(models.Owner.phone_number == normalized_phone).first()

def create_owner(db: Session, owner_data: schemas.OwnerCreate) -> models.Owner:
    """Creates a new owner, ensuring phone number is unique."""
    normalized_phone = owner_data.phone_number.strip()
    if not normalized_phone:
         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Phone number cannot be empty.")
    if not owner_data.name.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Owner name cannot be empty.")

    existing_owner = get_owner_by_phone(db, normalized_phone)
    if existing_owner:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Owner with phone number '{normalized_phone}' already exists."
        )
    owner = models.Owner(name=owner_data.name.strip(), phone_number=normalized_phone)
    db.add(owner)
    # Commit should happen in endpoint
    return owner

def get_or_create_owner_by_phone(db: Session, name: str, phone_number: str) -> models.Owner:
    """Gets owner by phone number or creates them if they don't exist."""
    normalized_phone = phone_number.strip()
    if not normalized_phone:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Owner phone number cannot be empty.")

    owner = get_owner_by_phone(db, normalized_phone)
    if not owner:
        # If owner doesn't exist by phone, create them
        # Ensure name is provided, maybe default if needed, but better to require it
        normalized_name = name.strip()
        if not normalized_name:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Owner name required when creating owner via vehicle registration.")

        owner = models.Owner(name=normalized_name, phone_number=normalized_phone)
        db.add(owner)
        db.flush() # Need owner ID before creating vehicle
        print(f"Created new owner: {owner.name} ({owner.phone_number})")
    return owner

# --- Vehicle CRUD ---
def get_vehicle_by_plate(db: Session, license_plate: str) -> models.Vehicle | None:
    normalized_plate = license_plate.strip().upper()
    return db.query(models.Vehicle).filter(func.upper(models.Vehicle.license_plate) == normalized_plate).first()

def get_vehicle_by_qrcode(db: Session, qr_code: str) -> models.Vehicle | None:
    # Eager load owner when fetching vehicle
    return db.query(models.Vehicle).options(joinedload(models.Vehicle.owner)).filter(models.Vehicle.qr_code == qr_code).first()

def register_vehicle(db: Session, vehicle_data: schemas.VehicleCreate) -> tuple[models.Vehicle | None, str | None]:
    """Registers a new vehicle, linking via owner's phone number."""
    normalized_plate = vehicle_data.license_plate.strip().upper()
    owner_phone = vehicle_data.owner_phone_number.strip() # Use phone number from schema

    if not normalized_plate: raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="License plate empty.")
    if not owner_phone: raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Owner phone number empty.")

    existing_vehicle = get_vehicle_by_plate(db, normalized_plate)
    if existing_vehicle: raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Vehicle '{normalized_plate}' already registered.")

    # Find owner by phone. We need a name if creating the owner here.
    # For now, let's assume owner MUST be registered first via the separate owner endpoint.
    owner = get_owner_by_phone(db, owner_phone)
    if not owner:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Owner with phone number '{owner_phone}' not found. Please register owner first.")

    # Proceed with QR generation and vehicle creation
    qr_data, qr_file_path = generate_qr_code(normalized_plate)
    if not qr_data or not qr_file_path: raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to generate QR code.")
    existing_qr = get_vehicle_by_qrcode(db, qr_data)
    if existing_qr: raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Generated QR code collision.")

    new_vehicle = models.Vehicle(
        license_plate=normalized_plate,
        qr_code=qr_data,
        owner_id=owner.id # Use the found owner's ID
    )
    db.add(new_vehicle)
    # Flush to potentially populate relationship before returning
    db.flush()
    # Manually set relationship if needed before commit/refresh in endpoint
    new_vehicle.owner = owner

    return new_vehicle, qr_file_path


# --- Parking Spot CRUD ---
def get_spot_by_number(db: Session, spot_number: str) -> models.ParkingSpot | None:
    return db.query(models.ParkingSpot).filter(models.ParkingSpot.spot_number == spot_number).first()
def update_spot_status(db: Session, spot_id: int, is_occupied: bool) -> bool:
    result = db.execute(update(models.ParkingSpot).where(models.ParkingSpot.id == spot_id).values(is_occupied=is_occupied))
    return result.rowcount > 0
def get_all_spots_with_status(db: Session) -> list[schemas.ParkingSpotStatus]:
    """Gets all spots with occupant and owner details if occupied."""
    stmt = (
        select(
            models.ParkingSpot.id, models.ParkingSpot.spot_number, models.ParkingSpot.is_occupied,
            models.Vehicle.license_plate, models.ParkingRecord.entry_time,
            models.Owner.name.label("owner_name"), models.Owner.phone_number.label("owner_phone_number") # Select owner details
        )
        .select_from(models.ParkingSpot)
        .outerjoin(models.ParkingRecord, and_(models.ParkingSpot.id == models.ParkingRecord.spot_id, models.ParkingRecord.exit_time == None))
        .outerjoin(models.Vehicle, models.ParkingRecord.vehicle_id == models.Vehicle.id)
        .outerjoin(models.Owner, models.Vehicle.owner_id == models.Owner.id) # Join vehicle to owner
        .order_by(models.ParkingSpot.spot_number)
    )
    results = db.execute(stmt).all()
    spots_data = [
        schemas.ParkingSpotStatus(
            id=row.id, spot_number=row.spot_number, is_occupied=row.is_occupied,
            license_plate=row.license_plate if row.is_occupied else None,
            owner_name=row.owner_name if row.is_occupied else None, # Add owner name
            owner_phone_number=row.owner_phone_number if row.is_occupied else None, # Add owner phone
            entry_time=row.entry_time if row.is_occupied else None
        ) for row in results
    ]
    return spots_data

# --- Parking Record CRUD ---
def get_active_record_by_vehicle_id(db: Session, vehicle_id: int) -> models.ParkingRecord | None:
    """Finds active record, joining spot, vehicle, and owner."""
    return db.query(models.ParkingRecord)\
             .options(
                 joinedload(models.ParkingRecord.spot),
                 joinedload(models.ParkingRecord.vehicle).joinedload(models.Vehicle.owner) # Load vehicle->owner
             )\
             .filter(models.ParkingRecord.vehicle_id == vehicle_id, models.ParkingRecord.exit_time == None).first()

def checkin_vehicle(db: Session, vehicle_id: int, spot_id: int) -> models.ParkingRecord:
    """Creates parking record, marks spot occupied."""
    entry_time = datetime.datetime.now(pytz.utc)
    db_record = models.ParkingRecord(vehicle_id=vehicle_id, spot_id=spot_id, entry_time=entry_time)
    db.add(db_record)
    update_spot_status(db=db, spot_id=spot_id, is_occupied=True)
    return db_record

def checkout_vehicle(db: Session, vehicle_id: int) -> dict | None:
    """Finds active record, calculates fee, updates record/spot. Includes owner details."""
    record = get_active_record_by_vehicle_id(db, vehicle_id) # Uses function that loads owner
    if not record: return None

    exit_time = datetime.datetime.now(pytz.utc)
    entry_time_aware = record.entry_time.astimezone(pytz.utc) if record.entry_time.tzinfo else pytz.utc.localize(record.entry_time)
    duration = exit_time - entry_time_aware
    duration_hours = Decimal(duration.total_seconds()) / Decimal(3600)
    hours_charged = duration_hours.quantize(Decimal('1'), rounding=ROUND_UP)
    fee = (hours_charged * config.PARKING_RATE_PER_HOUR).quantize(Decimal("0.01"))

    record.exit_time = exit_time
    record.fee = fee
    update_spot_status(db=db, spot_id=record.spot_id, is_occupied=False)

    owner_name_str = record.vehicle.owner.name if record.vehicle and record.vehicle.owner else "N/A"
    owner_phone_str = record.vehicle.owner.phone_number if record.vehicle and record.vehicle.owner else "N/A"

    return {
        "license_plate": record.vehicle.license_plate if record.vehicle else "N/A",
        "owner_name": owner_name_str, # Include owner name
        "owner_phone_number": owner_phone_str, # Include owner phone
        "spot_number": record.spot.spot_number if record.spot else "N/A",
        "entry_time": record.entry_time,
        "exit_time": exit_time,
        "duration_hours": float(duration_hours.quantize(Decimal("0.001"))),
        "fee": float(fee)
    }