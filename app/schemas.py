# app/schemas.py

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
import datetime
from decimal import Decimal

# --- Owner Schemas (Unchanged) ---
class OwnerBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    phone_number: str = Field(..., description="Owner's unique phone number")
class OwnerCreate(OwnerBase): pass
class Owner(OwnerBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

# --- Vehicle Schemas (Unchanged structure, but used in new Status) ---
class VehicleBase(BaseModel):
    license_plate: str = Field(..., description="Vehicle license plate")
class VehicleCreate(VehicleBase):
    owner_phone_number: str = Field(..., description="Phone number of the registered owner")
class Vehicle(VehicleBase):
    id: int
    qr_code: str
    owner: Optional[Owner] = None
    model_config = ConfigDict(from_attributes=True)
class VehicleRegistrationResponse(BaseModel):
    message: str
    vehicle: Vehicle
    qr_code_path: str

# --- Parking Spot Schemas (REMOVED) ---
# ParkingSpotBase, ParkingSpot, ParkingSpotStatus are no longer needed

# --- Check-in / Check-out Schemas ---
class CheckInRequest(BaseModel):
    # Only need QR code now, spot number removed
    qr_code: str = Field(..., description="QR code data scanned from the vehicle")

class CheckOutRequest(BaseModel):
    qr_code: str = Field(..., description="QR code data scanned from the vehicle")

# --- Combined Status / CheckInOut Response Schemas ---
class VehicleStatusResponse(BaseModel):
    """Response schema for vehicle status lookup, check-in, or check-out."""
    message: str
    is_checked_in: bool
    license_plate: Optional[str] = None
    owner_name: Optional[str] = None
    owner_phone_number: Optional[str] = None
    entry_time: Optional[datetime.datetime] = None # Populated if checked in
    # Fields specific to checkout result
    exit_time: Optional[datetime.datetime] = None
    duration_hours: Optional[float] = None
    fee: Optional[float] = None
    model_config = ConfigDict(from_attributes=True) # Allow creation from dicts

# Optional: Separate schema if CheckOut response needs different structure than Status/CheckIn
# class CheckOutDetailsResponse(VehicleStatusResponse):
#     # Inherits fields, could add more if needed
#     pass