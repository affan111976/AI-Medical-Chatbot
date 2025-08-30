from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String(100), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    
    # Personal Information (encrypted)
    first_name = Column(Text, nullable=True)  # Encrypted
    last_name = Column(Text, nullable=True)   # Encrypted
    date_of_birth = Column(Text, nullable=True)  # Encrypted
    phone_number = Column(Text, nullable=True)   # Encrypted
    
    # Preferences
    language_preference = Column(String(10), default="en")
    accessibility_font_size = Column(String(20), default="medium")
    accessibility_high_contrast = Column(Boolean, default=False)
    accessibility_screen_reader = Column(Boolean, default=False)
    
    # Medical Background (encrypted)
    medical_conditions = Column(Text, nullable=True)  # JSON string, encrypted
    medications = Column(Text, nullable=True)         # JSON string, encrypted
    allergies = Column(Text, nullable=True)           # JSON string, encrypted
    emergency_contact = Column(Text, nullable=True)   # JSON string, encrypted
    
    # Account Info
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    last_login = Column(DateTime, nullable=True)
    
    # Privacy settings
    data_sharing_consent = Column(Boolean, default=False)
    marketing_consent = Column(Boolean, default=False)
    
    # Relationships
    chat_sessions = relationship("ChatSession", back_populates="user", cascade="all, delete-orphan")
    user_feedback = relationship("UserFeedback", back_populates="user", cascade="all, delete-orphan")

class ChatSession(Base):
    __tablename__ = "chat_sessions"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    
    # Session metadata
    session_name = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_bookmarked = Column(Boolean, default=False)
    session_summary = Column(Text, nullable=True)
    
    # Session settings
    language_used = Column(String(10), default="en")
    
    # Privacy and sharing
    is_shared = Column(Boolean, default=False)
    shared_with_provider = Column(String(255), nullable=True)  # Email of healthcare provider
    
    # Relationships
    user = relationship("User", back_populates="chat_sessions")
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")

class ChatMessage(Base):
    __tablename__ = "chat_messages"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String(36), ForeignKey("chat_sessions.id"), nullable=False)
    
    # Message content (encrypted)
    user_message = Column(Text, nullable=True)      # Encrypted
    bot_response = Column(Text, nullable=True)      # Encrypted
    source_documents = Column(Text, nullable=True)  # JSON string, encrypted
    
    # Message metadata
    timestamp = Column(DateTime, default=datetime.utcnow)
    response_time = Column(Float, nullable=True)  # Response time in seconds
    confidence_score = Column(Float, nullable=True)  # AI confidence score
    
    # User interaction
    is_bookmarked = Column(Boolean, default=False)
    user_rating = Column(Integer, nullable=True)  # 1-5 rating
    user_notes = Column(Text, nullable=True)      # User's personal notes
    
    # Medical context
    medical_specialty = Column(String(100), nullable=True)
    urgency_level = Column(String(20), nullable=True)  # low, medium, high, emergency
    
    # Relationships
    session = relationship("ChatSession", back_populates="messages")

class UserFeedback(Base):
    __tablename__ = "user_feedback"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    message_id = Column(String(36), ForeignKey("chat_messages.id"), nullable=True)
    
    # Feedback content
    feedback_type = Column(String(50), nullable=False)  # rating, bug_report, feature_request, etc.
    rating = Column(Integer, nullable=True)  # 1-5 stars
    feedback_text = Column(Text, nullable=True)
    
    # Categorization
    category = Column(String(100), nullable=True)  # accuracy, response_time, user_experience, etc.
    severity = Column(String(20), nullable=True)   # low, medium, high, critical
    
    # Status tracking
    status = Column(String(20), default="open")  # open, in_progress, resolved, closed
    admin_response = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="user_feedback")

class MedicalProfile(Base):
    __tablename__ = "medical_profiles"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    
    # Medical history (all encrypted)
    chronic_conditions = Column(Text, nullable=True)  # JSON array
    past_surgeries = Column(Text, nullable=True)      # JSON array
    family_history = Column(Text, nullable=True)      # JSON array
    lifestyle_factors = Column(Text, nullable=True)   # JSON object
    
    # Current health status
    current_symptoms = Column(Text, nullable=True)
    pain_level = Column(Integer, nullable=True)  # 1-10 scale
    mobility_level = Column(String(50), nullable=True)
    
    # Preferences for personalization
    preferred_medical_terminology = Column(String(20), default="simple")  # simple, technical
    communication_style = Column(String(20), default="empathetic")  # direct, empathetic, detailed
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class SessionExport(Base):
    __tablename__ = "session_exports"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    session_id = Column(String(36), ForeignKey("chat_sessions.id"), nullable=False)
    
    # Export details
    export_type = Column(String(20), nullable=False)  # pdf, json, txt
    file_path = Column(String(500), nullable=True)
    file_size = Column(Integer, nullable=True)
    
    # Export settings
    include_sources = Column(Boolean, default=True)
    include_timestamps = Column(Boolean, default=True)
    include_ratings = Column(Boolean, default=False)
    
    # Status and metadata
    export_status = Column(String(20), default="pending")  # pending, completed, failed
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)  # For temporary exports
    
    # Privacy and sharing
    shared_with = Column(String(255), nullable=True)  # Email of recipient
    access_code = Column(String(50), nullable=True)   # For secure sharing