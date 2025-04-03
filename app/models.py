# app/models.py

from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, ForeignKey, Numeric
)
from sqlalchemy.orm import relationship
import datetime
import pytz

from app.database import Base

class Owner(Base):
    """Represents a vehicle owner with name and phone."""
    __tablename__ = "owners"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    phone_number = Column(String(20), unique=True, index=True, nullable=False)
    vehicles = relationship("Vehicle", back_populates="owner", passive_deletes=True)

    def __repr__(self):
        return f"<Owner(name='{self.name}', phone='{self.phone_number}')>"

class Vehicle(Base):
    """Represents a vehicle registered in the system, linked to an owner."""
    __tablename__ = "vehicles"
    id = Column(Integer, primary_key=True, index=True)
    license_plate = Column(String(20), unique=True, nullable=False, index=True)
    qr_code = Column(String, unique=True, nullable=False, index=True)
    owner_id = Column(Integer, ForeignKey("owners.id", ondelete="SET NULL"), nullable=True)
    owner = relationship("Owner", back_populates="vehicles")
    # Relationship to parking records (history)
    parking_records = relationship("ParkingRecord", back_populates="vehicle", cascade="all, delete-orphan")

    def __repr__(self):
        owner_info = f", owner_id={self.owner_id}" if self.owner_id else ""
        return f"<Vehicle(license_plate='{self.license_plate}'{owner_info})>"

# --- ParkingSpot model is REMOVED ---

class ParkingRecord(Base):
    """Represents a check-in/out time interval for a vehicle."""
    __tablename__ = "parking_records"

    id = Column(Integer, primary_key=True, index=True)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id"), nullable=False)
    # --- spot_id and spot relationship REMOVED ---
    entry_time = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.datetime.now(pytz.utc))
    exit_time = Column(DateTime(timezone=True), nullable=True) # Null indicates currently checked-in
    fee = Column(Numeric(10, 2), nullable=True)

    vehicle = relationship("Vehicle", back_populates="parking_records")
    # --- spot relationship REMOVED ---

    def __repr__(self):
        status = "Active" if self.exit_time is None else f"Completed ({self.exit_time})"
        return f"<ParkingRecord(id={self.id}, vehicle_id={self.vehicle_id}, entry={self.entry_time}, status='{status}')>"