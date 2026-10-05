"""SQLAlchemy ORM models: Users, Profiles, Activity logs, Anomaly events, Risk scores, Alerts."""
from datetime import datetime
from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String(64), unique=True)
    role = Column(String(64))

class Profile(Base):  # the stored Digital Twin baseline (JSON)
    __tablename__ = "behavioral_profiles"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    data = Column(Text)
    trained_at = Column(DateTime, default=datetime.now)

class Activity(Base):
    __tablename__ = "activities"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    ts = Column(DateTime, index=True)
    hour = Column(Float)
    device = Column(String(64))
    location = Column(String(64))
    session_min = Column(Float)
    actions = Column(Integer)
    downloads_mb = Column(Float)
    label = Column(String(16))  # normal | history | live | sim

class AnomalyEvent(Base):
    __tablename__ = "anomaly_events"
    id = Column(Integer, primary_key=True)
    activity_id = Column(Integer, ForeignKey("activities.id"))
    anomaly_score = Column(Float)  # 0-100 from Isolation Forest
    ts = Column(DateTime)

class RiskScore(Base):
    __tablename__ = "risk_scores"
    id = Column(Integer, primary_key=True)
    activity_id = Column(Integer, ForeignKey("activities.id"))
    score = Column(Float)
    level = Column(String(16))
    ts = Column(DateTime)

class Alert(Base):
    __tablename__ = "alerts"
    id = Column(Integer, primary_key=True)
    activity_id = Column(Integer, ForeignKey("activities.id"))
    severity = Column(String(16))
    title = Column(String(128))
    message = Column(Text)
    score = Column(Float)
    status = Column(String(16), default="OPEN")
    ts = Column(DateTime)
