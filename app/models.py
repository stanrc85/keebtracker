from sqlalchemy import Column, String, Integer, Boolean, Date, DateTime, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from .database import Base
import enum
from datetime import datetime

class SwitchType(enum.Enum):
    Linear = "Linear"
    Tactile = "Tactile"
    Clicky = "Clicky"
    Silent = "Silent"

class KeycapMaterial(enum.Enum):
    ABS = "ABS"
    PBT = "PBT"

class BuildStatus(enum.Enum):
    Active = "Active"
    Display = "Display"
    Disassembled = "Disassembled"

class MediaType(enum.Enum):
    image = "image"
    audio_soundtest = "audio_soundtest"

class Case(Base):
    __tablename__ = "cases"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    color = Column(String)
    material = Column(String)
    acquired_date = Column(Date)

class PCB(Base):
    __tablename__ = "pcbs"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    firmware = Column(String)

class Switch(Base):
    __tablename__ = "switches"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    type = Column(Enum(SwitchType), nullable=False)
    lubed = Column(Boolean, default=False)
    filmed = Column(Boolean, default=False)
    quantity = Column(Integer, default=0)

class Keycap(Base):
    __tablename__ = "keycaps"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    profile = Column(String)
    material = Column(Enum(KeycapMaterial), nullable=False)

class Build(Base):
    __tablename__ = "builds"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    case_id = Column(String, ForeignKey("cases.id"))
    pcb_id = Column(String, ForeignKey("pcbs.id"))
    switch_id = Column(String, ForeignKey("switches.id"))
    keycap_id = Column(String, ForeignKey("keycaps.id"))
    status = Column(Enum(BuildStatus), default=BuildStatus.Active)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    case = relationship("Case")
    pcb = relationship("PCB")
    switch = relationship("Switch")
    keycap = relationship("Keycap")
    revisions = relationship("BuildRevision", back_populates="build")
    media = relationship("Media", back_populates="build")

class BuildRevision(Base):
    __tablename__ = "build_revisions"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    build_id = Column(String, ForeignKey("builds.id"))
    changed_component_type = Column(String, nullable=False)
    old_component_id = Column(String)
    new_component_id = Column(String)
    changed_at = Column(DateTime, default=datetime.utcnow)

    build = relationship("Build", back_populates="revisions")

class Media(Base):
    __tablename__ = "media"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    build_id = Column(String, ForeignKey("builds.id"))
    media_type = Column(Enum(MediaType), nullable=False)
    file_path = Column(String, nullable=False)
    uploaded_at = Column(DateTime, default=datetime.utcnow)

    build = relationship("Build", back_populates="media")