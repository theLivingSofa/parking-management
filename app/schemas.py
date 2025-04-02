# app/schemas.py

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
import datetime
from decimal import Decimal

# --- Owner Schemas ---
class OwnerBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    # Add phone number, maybe add validation later (e.g., regex)
    phone_number: str = Field(..., description="Owner's unique phone number")

class OwnerCreate(OwnerBase):
    pass

class Owner(OwnerBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


# --- Vehicle Schemas ---
class VehicleBase(BaseModel):
    license_plate: str = Field(..., description="Vehicle license plate")

class VehicleCreate(VehicleBase):
    """Schema for request data when registering a vehicle."""
    # Use phone number to find/link owner
    owner_phone_number: str = Field(..., description="Phone number of the registered owner")

class Vehicle(VehicleBase):
    """Schema for representing a Vehicle in API responses."""
    id: int
    qr_code: str
    # Embed owner object in the response
    owner: Optional[Owner] = None
    model_config = ConfigDict(from_attributes=True)

class VehicleRegistrationResponse(BaseModel):
    """Response after registering a vehicle."""
    message: str
    vehicle: Vehicle # Embed the full vehicle details
    qr_code_path: str

# --- Parking Spot Schemas ---
class ParkingSpotBase(BaseModel):
    spot_number: str
class ParkingSpot(ParkingSpotBase):
    id: int
    is_occupied: bool
    model_config = ConfigDict(from_attributes=True)
class ParkingSpotStatus(ParkingSpot):
    # Include owner details if spot is occupied
    owner_name: Optional[str] = None
    owner_phone_number: Optional[str] = None # Added phone number
    license_plate: Optional[str] = None
    entry_time: Optional[datetime.datetime] = None
    model_config = ConfigDict(from_attributes=True)


# --- Check-in / Check-out Schemas ---
class CheckInRequest(BaseModel):
    qr_code: str
    spot_number: str
class CheckOutRequest(BaseModel):
    qr_code: str
class CheckInOutResponse(BaseModel):
    message: str
    license_plate: Optional[str] = None
    owner_name: Optional[str] = None
    owner_phone_number: Optional[str] = None # Added phone number
    spot_number: Optional[str] = None
    entry_time: Optional[datetime.datetime] = None
class CheckOutDetailsResponse(CheckInOutResponse):
    exit_time: datetime.datetime
    duration_hours: float
    fee: float