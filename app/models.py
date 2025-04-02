# app/models.py

from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, ForeignKey, Numeric
)
from sqlalchemy.orm import relationship
import datetime
import pytz

from app.database import Base

# --- MODIFIED Owner Model ---
class Owner(Base):
    """Represents a vehicle owner with name and phone."""
    __tablename__ = "owners"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False) # Name is still required
    # Phone number is now the unique business key for linking
    phone_number = Column(String(20), unique=True, index=True, nullable=False)

    vehicles = relationship("Vehicle", back_populates="owner", passive_deletes=True)

    def __repr__(self):
        return f"<Owner(name='{self.name}', phone='{self.phone_number}')>"


class Vehicle(Base):
    """Represents a vehicle, linked to an owner via owner_id."""
    __tablename__ = "vehicles"

    id = Column(Integer, primary_key=True, index=True)
    license_plate = Column(String(20), unique=True, nullable=False, index=True)
    qr_code = Column(String, unique=True, nullable=False, index=True)

    # Keep owner_id as the foreign key, but we'll find the owner via phone number first
    owner_id = Column(Integer, ForeignKey("owners.id", ondelete="SET NULL"), nullable=True)
    owner = relationship("Owner", back_populates="vehicles")

    parking_records = relationship("ParkingRecord", back_populates="vehicle", cascade="all, delete-orphan")

    def __repr__(self):
        owner_info = f", owner_id={self.owner_id}" if self.owner_id else ""
        return f"<Vehicle(license_plate='{self.license_plate}'{owner_info})>"


# --- ParkingSpot and ParkingRecord remain unchanged ---
class ParkingSpot(Base):
    """Represents a single parking spot."""
    __tablename__ = "parking_spots"
    id = Column(Integer, primary_key=True, index=True)
    spot_number = Column(String(10), unique=True, nullable=False, index=True)
    is_occupied = Column(Boolean, default=False, nullable=False)
    parking_records = relationship("ParkingRecord", back_populates="spot")

    def __repr__(self):
        status = "Occupied" if self.is_occupied else "Available"
        return f"<ParkingSpot(spot_number='{self.spot_number}', status='{status}')>"

class ParkingRecord(Base):
    """Represents a single instance of a vehicle parking in a spot."""
    __tablename__ = "parking_records"
    id = Column(Integer, primary_key=True, index=True)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id"), nullable=False)
    spot_id = Column(Integer, ForeignKey("parking_spots.id"), nullable=False)
    entry_time = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.datetime.now(pytz.utc))
    exit_time = Column(DateTime(timezone=True), nullable=True)
    fee = Column(Numeric(10, 2), nullable=True)
    vehicle = relationship("Vehicle", back_populates="parking_records")
    spot = relationship("ParkingSpot", back_populates="parking_records")

    def __repr__(self):
        exit_status = f", exited={self.exit_time}" if self.exit_time else ", active"
        return f"<ParkingRecord(id={self.id}, vehicle_id={self.vehicle_id}, spot_id={self.spot_id}, entry={self.entry_time}{exit_status})>"