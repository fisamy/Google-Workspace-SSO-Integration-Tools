"""
Database models and connection module for email verification system.
"""
import os
import json
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Boolean, Float, ForeignKey, DateTime, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database connection
DATABASE_URL = os.getenv('DATABASE_URL')
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Define models
class EmailVerificationService(Base):
    __tablename__ = "email_verification_services"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)
    api_key = Column(String(255))
    base_url = Column(String(255))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<EmailVerificationService(name='{self.name}', is_active={self.is_active})>"

class EmailVerification(Base):
    __tablename__ = "email_verification"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), nullable=False, index=True)
    is_valid = Column(Boolean)
    score = Column(Float)
    provider = Column(String(50), nullable=False)
    verification_date = Column(DateTime, default=datetime.utcnow)
    details = Column(JSONB)
    
    def __repr__(self):
        return f"<EmailVerification(email='{self.email}', is_valid={self.is_valid}, provider='{self.provider}')>"
    
    def to_dict(self):
        return {
            "id": self.id,
            "email": self.email,
            "is_valid": self.is_valid,
            "score": self.score,
            "provider": self.provider,
            "verification_date": self.verification_date.isoformat() if self.verification_date else None,
            "details": self.details
        }

class EmailList(Base):
    __tablename__ = "email_lists"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    entries = relationship("EmailListEntry", back_populates="email_list", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<EmailList(name='{self.name}')>"

class EmailListEntry(Base):
    __tablename__ = "email_list_entries"
    
    id = Column(Integer, primary_key=True, index=True)
    list_id = Column(Integer, ForeignKey("email_lists.id", ondelete="CASCADE"))
    email = Column(String(255), nullable=False, index=True)
    first_name = Column(String(100))
    last_name = Column(String(100))
    company = Column(String(100))
    position = Column(String(100))
    added_at = Column(DateTime, default=datetime.utcnow)
    
    email_list = relationship("EmailList", back_populates="entries")
    
    def __repr__(self):
        return f"<EmailListEntry(email='{self.email}', list_id={self.list_id})>"

# Helper functions
def get_db():
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Initialize the database."""
    Base.metadata.create_all(bind=engine)

def add_default_services():
    """Add default verification services to the database."""
    db = SessionLocal()
    
    # Check if services already exist
    existing_services = db.query(EmailVerificationService).all()
    if existing_services:
        db.close()
        return
    
    # Define default services
    default_services = [
        {
            "name": "zerobounce",
            "base_url": "https://api.zerobounce.net/v2"
        },
        {
            "name": "mailboxlayer",
            "base_url": "https://api.mailboxlayer.com"
        },
        {
            "name": "neutrinoapi",
            "base_url": "https://neutrinoapi.net/email-validate"
        },
        {
            "name": "spokeo",
            "base_url": "https://www.spokeo.com/api"
        },
        {
            "name": "hunter",
            "base_url": "https://api.hunter.io/v2"
        }
    ]
    
    # Add services
    for service in default_services:
        db_service = EmailVerificationService(**service)
        db.add(db_service)
    
    db.commit()
    db.close()

if __name__ == "__main__":
    init_db()
    add_default_services()