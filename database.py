"""
Database models and connection module for email verification system.
"""
import os
import logging
from datetime import datetime

import sqlalchemy
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL")

# Create engine and base
engine = sqlalchemy.create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Models
class EmailVerificationService(Base):
    __tablename__ = "email_verification_services"
    
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, index=True)
    name = sqlalchemy.Column(sqlalchemy.String(50), unique=True, nullable=False)
    api_key = sqlalchemy.Column(sqlalchemy.String(255))
    base_url = sqlalchemy.Column(sqlalchemy.String(255))
    is_active = sqlalchemy.Column(sqlalchemy.Boolean, default=True)
    created_at = sqlalchemy.Column(sqlalchemy.DateTime, default=datetime.utcnow)
    updated_at = sqlalchemy.Column(sqlalchemy.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<EmailVerificationService(name='{self.name}', is_active={self.is_active})>"

class EmailVerification(Base):
    __tablename__ = "email_verification"
    
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, index=True)
    email = sqlalchemy.Column(sqlalchemy.String(255), nullable=False, index=True)
    is_valid = sqlalchemy.Column(sqlalchemy.Boolean)
    score = sqlalchemy.Column(sqlalchemy.Float)
    provider = sqlalchemy.Column(sqlalchemy.String(50), nullable=False)
    verification_date = sqlalchemy.Column(sqlalchemy.DateTime, default=datetime.utcnow)
    details = sqlalchemy.Column(JSONB)
    
    def __repr__(self):
        return f"<EmailVerification(email='{self.email}', is_valid={self.is_valid}, provider='{self.provider}')>"
    
    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'is_valid': self.is_valid,
            'score': self.score,
            'provider': self.provider,
            'verification_date': self.verification_date.isoformat() if self.verification_date else None,
            'details': self.details
        }

class EmailList(Base):
    __tablename__ = "email_lists"
    
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, index=True)
    name = sqlalchemy.Column(sqlalchemy.String(100), nullable=False)
    description = sqlalchemy.Column(sqlalchemy.Text)
    created_at = sqlalchemy.Column(sqlalchemy.DateTime, default=datetime.utcnow)
    updated_at = sqlalchemy.Column(sqlalchemy.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    entries = relationship("EmailListEntry", back_populates="email_list", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<EmailList(name='{self.name}')>"

class EmailListEntry(Base):
    __tablename__ = "email_list_entries"
    
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, index=True)
    list_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("email_lists.id", ondelete="CASCADE"))
    email = sqlalchemy.Column(sqlalchemy.String(255), nullable=False, index=True)
    first_name = sqlalchemy.Column(sqlalchemy.String(100))
    last_name = sqlalchemy.Column(sqlalchemy.String(100))
    company = sqlalchemy.Column(sqlalchemy.String(100))
    position = sqlalchemy.Column(sqlalchemy.String(100))
    added_at = sqlalchemy.Column(sqlalchemy.DateTime, default=datetime.utcnow)
    
    email_list = relationship("EmailList", back_populates="entries")
    
    def __repr__(self):
        return f"<EmailListEntry(email='{self.email}')>"

# Database functions
def get_db():
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Initialize the database."""
    try:
        # Create all tables
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully.")
    except Exception as e:
        logger.error(f"Error creating database tables: {str(e)}")

def add_default_services():
    """Add default verification services to the database."""
    try:
        # Check if services already exist
        db = next(get_db())
        existing_services = db.query(EmailVerificationService).all()
        
        if existing_services:
            logger.info("Default services already exist.")
            db.close()
            return
        
        # Default services configuration
        default_services = [
            {
                "name": "zerobounce",
                "base_url": "https://api.zerobounce.net/v2",
                "is_active": True
            },
            {
                "name": "mailboxlayer",
                "base_url": "https://api.mailboxlayer.com",
                "is_active": True
            },
            {
                "name": "neutrinoapi",
                "base_url": "https://neutrinoapi.net/email-validate",
                "is_active": True
            },
            {
                "name": "spokeo",
                "base_url": "https://api.spokeo.com",
                "is_active": True
            },
            {
                "name": "hunter",
                "base_url": "https://api.hunter.io/v2",
                "is_active": True
            }
        ]
        
        # Add default services
        for service_data in default_services:
            service = EmailVerificationService(**service_data)
            db.add(service)
        
        db.commit()
        logger.info("Default services added to database.")
        db.close()
    except Exception as e:
        logger.error(f"Error adding default services: {str(e)}")