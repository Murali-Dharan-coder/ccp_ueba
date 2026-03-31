from sqlalchemy import Column, Integer, String, Float, DateTime
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    name = Column(String)
    department = Column(String)
    hashed_password = Column(String)
    anomaly_score = Column(Float, default=0.0)
    critical_level = Column(String, default="Low")
    login_attempts = Column(Integer, default=0)
    status = Column(String, default="Active")
    lock_reason = Column(String, nullable=True)

class AnomalyRecord(Base):
    __tablename__ = "anomalies"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer)
    type = Column(String)
    description = Column(String)
    timestamp = Column(DateTime)
    features_json = Column(String)
