import json
import hashlib
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc
from .models import User, ChatSession, ChatMessage, UserFeedback, MedicalProfile, SessionExport
from .database import get_db_session
from ..utils.encryption import encrypt_data, decrypt_data
import logging

logger = logging.getLogger(__name__)

class UserManager:
    def __init__(self):
        pass
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password using SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    @staticmethod
    def verify_password(password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        return hashlib.sha256(password.encode()).hexdigest() == hashed_password
    
    def _user_to_dict(self, user: User) -> Dict[str, Any]:
        """Convert SQLAlchemy User object to dictionary to avoid session issues"""
        if not user:
            return None
            
        return {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'date_of_birth': user.date_of_birth,
            'phone_number': user.phone_number,
            'language_preference': user.language_preference,
            'accessibility_font_size': user.accessibility_font_size,
            'accessibility_high_contrast': user.accessibility_high_contrast,
            'accessibility_screen_reader': user.accessibility_screen_reader,
            'medical_conditions': user.medical_conditions,
            'medications': user.medications,
            'allergies': user.allergies,
            'emergency_contact': user.emergency_contact,
            'created_at': user.created_at,
            'updated_at': user.updated_at,
            'is_active': user.is_active,
            'last_login': user.last_login,
            'data_sharing_consent': user.data_sharing_consent,
            'marketing_consent': user.marketing_consent
        }
    
    def create_user(self, username: str, email: str, password: str, 
                   first_name: str = None, last_name: str = None) -> Optional[Dict[str, Any]]:
        """Create a new user and return user dictionary"""
        try:
            with get_db_session() as session:
                # Check if user already exists
                existing_user = session.query(User).filter(
                    or_(User.username == username, User.email == email)
                ).first()
                
                if existing_user:
                    logger.warning(f"User with username {username} or email {email} already exists")
                    return None
                
                # Create new user
                new_user = User(
                    username=username,
                    email=email,
                    password_hash=self.hash_password(password),
                    first_name=encrypt_data(first_name) if first_name else None,
                    last_name=encrypt_data(last_name) if last_name else None
                )
                
                session.add(new_user)
                session.flush()  # Get the user ID
                
                # Create medical profile
                medical_profile = MedicalProfile(user_id=new_user.id)
                session.add(medical_profile)
                
                # Convert to dictionary before session closes
                user_dict = self._user_to_dict(new_user)
                
                logger.info(f"User {username} created successfully")
                return user_dict
                
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            return None
    
    def authenticate_user(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticate user and update last login - returns user dictionary"""
        try:
            with get_db_session() as session:
                user = session.query(User).filter(
                    and_(
                        or_(User.username == username, User.email == username),
                        User.is_active == True
                    )
                ).first()
                
                if user and self.verify_password(password, user.password_hash):
                    user.last_login = datetime.utcnow()
                    
                    # Convert to dictionary before session closes
                    user_dict = self._user_to_dict(user)
                    
                    logger.info(f"User {username} authenticated successfully")
                    return user_dict
                
                logger.warning(f"Authentication failed for user {username}")
                return None
                
        except Exception as e:
            logger.error(f"Error authenticating user: {e}")
            return None
    
    def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID - returns user dictionary"""
        try:
            with get_db_session() as session:
                user = session.query(User).filter(User.id == user_id).first()
                if user:
                    return self._user_to_dict(user)
                return None
        except Exception as e:
            logger.error(f"Error getting user by ID: {e}")
            return None
    
    def update_user_preferences(self, user_id: str, preferences: Dict[str, Any]) -> bool:
        """Update user preferences"""
        try:
            with get_db_session() as session:
                user = session.query(User).filter(User.id == user_id).first()
                if not user:
                    return False
                
                # Update preferences
                if 'language_preference' in preferences:
                    user.language_preference = preferences['language_preference']
                if 'accessibility_font_size' in preferences:
                    user.accessibility_font_size = preferences['accessibility_font_size']
                if 'accessibility_high_contrast' in preferences:
                    user.accessibility_high_contrast = preferences['accessibility_high_contrast']
                if 'accessibility_screen_reader' in preferences:
                    user.accessibility_screen_reader = preferences['accessibility_screen_reader']
                
                user.updated_at = datetime.utcnow()
                logger.info(f"Preferences updated for user {user_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error updating user preferences: {e}")
            return False
    
    def update_medical_profile(self, user_id: str, medical_data: Dict[str, Any]) -> bool:
        """Update user's medical profile"""
        try:
            with get_db_session() as session:
                user = session.query(User).filter(User.id == user_id).first()
                if not user:
                    return False
                
                # Update encrypted medical data
                if 'medical_conditions' in medical_data:
                    user.medical_conditions = encrypt_data(json.dumps(medical_data['medical_conditions']))
                if 'medications' in medical_data:
                    user.medications = encrypt_data(json.dumps(medical_data['medications']))
                if 'allergies' in medical_data:
                    user.allergies = encrypt_data(json.dumps(medical_data['allergies']))
                if 'emergency_contact' in medical_data:
                    user.emergency_contact = encrypt_data(json.dumps(medical_data['emergency_contact']))
                
                user.updated_at = datetime.utcnow()
                logger.info(f"Medical profile updated for user {user_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error updating medical profile: {e}")
            return False
    
    def get_user_medical_data(self, user_id: str) -> Dict[str, Any]:
        """Get decrypted medical data for personalization"""
        try:
            with get_db_session() as session:
                user = session.query(User).filter(User.id == user_id).first()
                if not user:
                    return {}
                
                medical_data = {}
                
                if user.medical_conditions:
                    try:
                        medical_data['medical_conditions'] = json.loads(decrypt_data(user.medical_conditions))
                    except Exception as e:
                        logger.warning(f"Could not decrypt medical conditions: {e}")
                        medical_data['medical_conditions'] = []
                        
                if user.medications:
                    try:
                        medical_data['medications'] = json.loads(decrypt_data(user.medications))
                    except Exception as e:
                        logger.warning(f"Could not decrypt medications: {e}")
                        medical_data['medications'] = []
                        
                if user.allergies:
                    try:
                        medical_data['allergies'] = json.loads(decrypt_data(user.allergies))
                    except Exception as e:
                        logger.warning(f"Could not decrypt allergies: {e}")
                        medical_data['allergies'] = []
                
                return medical_data
                
        except Exception as e:
            logger.error(f"Error getting user medical data: {e}")
            return {}

class SessionManager:
    def __init__(self):
        pass
    
    def _session_to_dict(self, session_obj: ChatSession) -> Dict[str, Any]:
        """Convert SQLAlchemy Session object to dictionary"""
        if not session_obj:
            return None
            
        return {
            'id': session_obj.id,
            'user_id': session_obj.user_id,
            'session_name': session_obj.session_name,
            'created_at': session_obj.created_at,
            'updated_at': session_obj.updated_at,
            'is_bookmarked': session_obj.is_bookmarked,
            'session_summary': session_obj.session_summary,
            'language_used': session_obj.language_used,
            'is_shared': session_obj.is_shared,
            'shared_with_provider': session_obj.shared_with_provider
        }
    
    def create_session(self, user_id: str, session_name: str = None) -> Optional[Dict[str, Any]]:
        """Create a new chat session"""
        try:
            with get_db_session() as session:
                new_session = ChatSession(
                    user_id=user_id,
                    session_name=session_name or f"Chat {datetime.now().strftime('%Y-%m-%d %H:%M')}"
                )
                session.add(new_session)
                session.flush()
                
                # Convert to dictionary before session closes
                session_dict = self._session_to_dict(new_session)
                
                logger.info(f"New chat session created for user {user_id}")
                return session_dict
                
        except Exception as e:
            logger.error(f"Error creating chat session: {e}")
            return None
    
    def get_user_sessions(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get user's chat sessions as dictionaries"""
        try:
            with get_db_session() as session:
                sessions = session.query(ChatSession).filter(
                    ChatSession.user_id == user_id
                ).order_by(desc(ChatSession.updated_at)).limit(limit).all()
                
                # Convert all sessions to dictionaries
                session_dicts = []
                for s in sessions:
                    session_dict = self._session_to_dict(s)
                    if session_dict:
                        session_dicts.append(session_dict)
                
                return session_dicts
                
        except Exception as e:
            logger.error(f"Error getting user sessions: {e}")
            return []
    
    def save_message(self, session_id: str, user_message: str, bot_response: str, 
                    source_documents: List[Any] = None, response_time: float = None,
                    confidence_score: float = None) -> Optional[str]:
        """Save a chat message and return message ID"""
        try:
            with get_db_session() as session:
                # Encrypt message content
                encrypted_user_msg = encrypt_data(user_message)
                encrypted_bot_response = encrypt_data(bot_response)
                encrypted_sources = encrypt_data(json.dumps([
                    {"content": doc.page_content, "metadata": doc.metadata} 
                    for doc in source_documents
                ])) if source_documents else None
                
                new_message = ChatMessage(
                    session_id=session_id,
                    user_message=encrypted_user_msg,
                    bot_response=encrypted_bot_response,
                    source_documents=encrypted_sources,
                    response_time=response_time,
                    confidence_score=confidence_score
                )
                
                session.add(new_message)
                session.flush()
                
                # Get message ID before session closes
                message_id = new_message.id
                
                # Update session timestamp
                chat_session = session.query(ChatSession).filter(
                    ChatSession.id == session_id
                ).first()
                if chat_session:
                    chat_session.updated_at = datetime.utcnow()
                
                logger.info(f"Message saved for session {session_id}")
                return message_id
                
        except Exception as e:
            logger.error(f"Error saving message: {e}")
            return None
    
    def get_session_messages(self, session_id: str) -> List[Dict[str, Any]]:
        """Get decrypted messages for a session"""
        try:
            with get_db_session() as session:
                messages = session.query(ChatMessage).filter(
                    ChatMessage.session_id == session_id
                ).order_by(ChatMessage.timestamp).all()
                
                decrypted_messages = []
                for msg in messages:
                    try:
                        decrypted_msg = {
                            'id': msg.id,
                            'user_message': decrypt_data(msg.user_message) if msg.user_message else None,
                            'bot_response': decrypt_data(msg.bot_response) if msg.bot_response else None,
                            'timestamp': msg.timestamp,
                            'is_bookmarked': msg.is_bookmarked,
                            'user_rating': msg.user_rating,
                            'confidence_score': msg.confidence_score
                        }
                        
                        if msg.source_documents:
                            try:
                                decrypted_msg['source_documents'] = json.loads(decrypt_data(msg.source_documents))
                            except Exception as e:
                                logger.warning(f"Could not decrypt source documents: {e}")
                                decrypted_msg['source_documents'] = []
                        
                        decrypted_messages.append(decrypted_msg)
                    except Exception as e:
                        logger.warning(f"Could not decrypt message {msg.id}: {e}")
                        continue
                
                return decrypted_messages
                
        except Exception as e:
            logger.error(f"Error getting session messages: {e}")
            return []
    
    def bookmark_message(self, message_id: str, user_id: str) -> bool:
        """Bookmark/unbookmark a message"""
        try:
            with get_db_session() as session:
                message = session.query(ChatMessage).join(ChatSession).filter(
                    and_(
                        ChatMessage.id == message_id,
                        ChatSession.user_id == user_id
                    )
                ).first()
                
                if message:
                    message.is_bookmarked = not message.is_bookmarked
                    logger.info(f"Message {message_id} bookmark status changed")
                    return True
                
                return False
                
        except Exception as e:
            logger.error(f"Error bookmarking message: {e}")
            return False

    # CODE TO ADD to SessionManager class in user_manager.py

    def delete_session(self, session_id: str, user_id: str) -> bool:
        """Delete a chat session and its messages if the user is the owner"""
        try:
            with get_db_session() as session:
                # Find the session, ensuring it belongs to the requesting user
                session_to_delete = session.query(ChatSession).filter(
                    and_(
                        ChatSession.id == session_id,
                        ChatSession.user_id == user_id
                    )
                ).first()
                
                if session_to_delete:
                    # Delete the session. Associated messages will be deleted automatically
                    # due to the 'cascade="all, delete-orphan"' setting in the model.
                    session.delete(session_to_delete)
                    logger.info(f"Session {session_id} deleted successfully by user {user_id}")
                    return True
                else:
                    # The session either doesn't exist or doesn't belong to the user
                    logger.warning(f"User {user_id} failed to delete session {session_id}: Not found or not owner")
                    return False
                    
        except Exception as e:
            logger.error(f"Error deleting session {session_id}: {e}")
            return False
    
    def rate_message(self, message_id: str, user_id: str, rating: int) -> bool:
        """Rate a bot response (1-5 stars)"""
        try:
            with get_db_session() as session:
                message = session.query(ChatMessage).join(ChatSession).filter(
                    and_(
                        ChatMessage.id == message_id,
                        ChatSession.user_id == user_id
                    )
                ).first()
                
                if message and 1 <= rating <= 5:
                    message.user_rating = rating
                    logger.info(f"Message {message_id} rated {rating} stars")
                    return True
                
                return False
                
        except Exception as e:
            logger.error(f"Error rating message: {e}")
            return False

class FeedbackManager:
    def __init__(self):
        pass
    
    def submit_feedback(self, user_id: str, feedback_type: str, feedback_text: str,
                       rating: int = None, category: str = None, 
                       message_id: str = None) -> bool:
        """Submit user feedback"""
        try:
            with get_db_session() as session:
                feedback = UserFeedback(
                    user_id=user_id,
                    message_id=message_id,
                    feedback_type=feedback_type,
                    rating=rating,
                    feedback_text=feedback_text,
                    category=category
                )
                
                session.add(feedback)
                logger.info(f"Feedback submitted by user {user_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error submitting feedback: {e}")
            return False
    
    def get_user_feedback(self, user_id: str) -> List[UserFeedback]:
        """Get user's feedback history"""
        try:
            with get_db_session() as session:
                return session.query(UserFeedback).filter(
                    UserFeedback.user_id == user_id
                ).order_by(desc(UserFeedback.created_at)).all()
                
        except Exception as e:
            logger.error(f"Error getting user feedback: {e}")
            return []