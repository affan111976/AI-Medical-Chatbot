import re
import os
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, date
import logging

logger = logging.getLogger(__name__)

class ValidationError(Exception):
    """Custom exception for validation errors"""
    pass

class UserValidator:
    """Validator for user-related data"""
    
    @staticmethod
    def validate_username(username: str) -> Tuple[bool, str]:
        """
        Validate username format and requirements
        
        Args:
            username: Username to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not username:
            return False, "Username is required"
        
        if len(username) < 3:
            return False, "Username must be at least 3 characters long"
        
        if len(username) > 50:
            return False, "Username must be less than 50 characters"
        
        # Allow alphanumeric, underscore, and hyphen
        if not re.match("^[a-zA-Z0-9_-]+$", username):
            return False, "Username can only contain letters, numbers, underscore, and hyphen"
        
        # Must start with a letter
        if not username[0].isalpha():
            return False, "Username must start with a letter"
        
        return True, ""
    
    @staticmethod
    def validate_email(email: str) -> Tuple[bool, str]:
        """
        Validate email format
        
        Args:
            email: Email to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not email:
            return False, "Email is required"
        
        # Basic email regex pattern
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        
        if not re.match(email_pattern, email):
            return False, "Invalid email format"
        
        if len(email) > 255:
            return False, "Email must be less than 255 characters"
        
        # Check for common invalid patterns
        invalid_patterns = [
            r'\.{2,}',  # Multiple consecutive dots
            r'^\.', # Starting with dot
            r'\.$', # Ending with dot
        ]
        
        for pattern in invalid_patterns:
            if re.search(pattern, email):
                return False, "Invalid email format"
        
        return True, ""
    
    @staticmethod
    def validate_password(password: str) -> Tuple[bool, str]:
        """
        Validate password strength
        
        Args:
            password: Password to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not password:
            return False, "Password is required"
        
        min_length = int(os.getenv("PASSWORD_MIN_LENGTH", "8"))
        
        if len(password) < min_length:
            return False, f"Password must be at least {min_length} characters long"
        
        if len(password) > 128:
            return False, "Password must be less than 128 characters"
        
        # Check for required character types
        has_upper = bool(re.search(r'[A-Z]', password))
        has_lower = bool(re.search(r'[a-z]', password))
        has_digit = bool(re.search(r'\d', password))
        has_special = bool(re.search(r'[!@#$%^&*(),.?":{}|<>]', password))
        
        missing_types = []
        if not has_upper:
            missing_types.append("uppercase letter")
        if not has_lower:
            missing_types.append("lowercase letter")
        if not has_digit:
            missing_types.append("digit")
        if not has_special:
            missing_types.append("special character")
        
        if len(missing_types) > 1:  # Allow missing one type for flexibility
            return False, f"Password must contain at least three of: {', '.join(['uppercase letter', 'lowercase letter', 'digit', 'special character'])}"
        
        # Check for common weak passwords
        weak_passwords = [
            "password", "123456", "password123", "admin", "user",
            "qwerty", "abc123", "letmein", "welcome", "monkey"
        ]
        
        if password.lower() in weak_passwords:
            return False, "Password is too common. Please choose a stronger password"
        
        return True, ""
    
    @staticmethod
    def validate_name(name: str, field_name: str = "Name") -> Tuple[bool, str]:
        """
        Validate person name
        
        Args:
            name: Name to validate
            field_name: Field name for error messages
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not name:
            return True, ""  # Names are optional in many cases
        
        if len(name) > 100:
            return False, f"{field_name} must be less than 100 characters"
        
        # Allow letters, spaces, hyphens, apostrophes
        if not re.match("^[a-zA-Z\s\-']+$", name):
            return False, f"{field_name} can only contain letters, spaces, hyphens, and apostrophes"
        
        # Check for reasonable length and format
        if len(name.strip()) < 1:
            return False, f"{field_name} cannot be empty"
        
        return True, ""
    
    @staticmethod
    def validate_phone_number(phone: str) -> Tuple[bool, str]:
        """
        Validate phone number format
        
        Args:
            phone: Phone number to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not phone:
            return True, ""  # Phone is optional
        
        # Remove common formatting characters
        cleaned_phone = re.sub(r'[\s\-\(\)\.]+', '', phone)
        
        # Check if it contains only digits and + (for international)
        if not re.match(r'^\+?[\d]+$', cleaned_phone):
            return False, "Phone number can only contain digits, spaces, hyphens, parentheses, and + for international numbers"
        
        # Check length (7-15 digits is reasonable for most phone numbers)
        digit_count = len(re.sub(r'[^\d]', '', cleaned_phone))
        if digit_count < 7 or digit_count > 15:
            return False, "Phone number must contain 7-15 digits"
        
        return True, ""

class MedicalDataValidator:
    """Validator for medical-related data"""
    
    @staticmethod
    def validate_medical_condition(condition: str) -> Tuple[bool, str]:
        """
        Validate medical condition entry
        
        Args:
            condition: Medical condition to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not condition:
            return False, "Medical condition cannot be empty"
        
        if len(condition) > 200:
            return False, "Medical condition description must be less than 200 characters"
        
        # Allow letters, numbers, spaces, and common medical punctuation
        if not re.match(r'^[a-zA-Z0-9\s\-\(\)\.,\']+$', condition):
            return False, "Medical condition contains invalid characters"
        
        # Check for potential HTML/script injection
        suspicious_patterns = [
            r'<script', r'javascript:', r'<iframe', r'<object',
            r'on\w+\s*=', r'<embed', r'<link'
        ]
        
        for pattern in suspicious_patterns:
            if re.search(pattern, condition, re.IGNORECASE):
                return False, "Invalid characters detected in medical condition"
        
        return True, ""
    
    @staticmethod
    def validate_medication(medication: str) -> Tuple[bool, str]:
        """
        Validate medication entry
        
        Args:
            medication: Medication to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not medication:
            return False, "Medication cannot be empty"
        
        if len(medication) > 150:
            return False, "Medication name must be less than 150 characters"
        
        # Allow letters, numbers, spaces, and common medication punctuation
        if not re.match(r'^[a-zA-Z0-9\s\-\(\)\.,/]+$', medication):
            return False, "Medication name contains invalid characters"
        
        return True, ""
    
    @staticmethod
    def validate_allergy(allergy: str) -> Tuple[bool, str]:
        """
        Validate allergy entry
        
        Args:
            allergy: Allergy to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not allergy:
            return False, "Allergy cannot be empty"
        
        if len(allergy) > 100:
            return False, "Allergy description must be less than 100 characters"
        
        # Allow letters, numbers, spaces, and basic punctuation
        if not re.match(r'^[a-zA-Z0-9\s\-\(\)\.,\']+$', allergy):
            return False, "Allergy description contains invalid characters"
        
        return True, ""
    
    @staticmethod
    def validate_date_of_birth(dob_str: str) -> Tuple[bool, str]:
        """
        Validate date of birth
        
        Args:
            dob_str: Date of birth string (YYYY-MM-DD format)
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not dob_str:
            return True, ""  # DOB is optional
        
        try:
            dob = datetime.strptime(dob_str, "%Y-%m-%d").date()
        except ValueError:
            return False, "Date of birth must be in YYYY-MM-DD format"
        
        # Check if date is reasonable (not in future, not too old)
        today = date.today()
        if dob > today:
            return False, "Date of birth cannot be in the future"
        
        age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        if age > 150:
            return False, "Invalid date of birth (age would be over 150 years)"
        
        return True, ""

class ChatValidator:
    """Validator for chat-related data"""
    
    @staticmethod
    def validate_message(message: str) -> Tuple[bool, str]:
        """
        Validate chat message
        
        Args:
            message: Chat message to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not message or not message.strip():
            return False, "Message cannot be empty"
        
        if len(message) > 5000:
            return False, "Message must be less than 5000 characters"
        
        # Check for potential security issues
        suspicious_patterns = [
            r'<script', r'javascript:', r'<iframe', r'<object',
            r'on\w+\s*=', r'<embed', r'<link', r'<style'
        ]
        
        for pattern in suspicious_patterns:
            if re.search(pattern, message, re.IGNORECASE):
                return False, "Message contains potentially harmful content"
        
        return True, ""
    
    @staticmethod
    def validate_session_name(session_name: str) -> Tuple[bool, str]:
        """
        Validate chat session name
        
        Args:
            session_name: Session name to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not session_name:
            return False, "Session name cannot be empty"
        
        if len(session_name) > 100:
            return False, "Session name must be less than 100 characters"
        
        # Allow letters, numbers, spaces, and safe punctuation
        if not re.match(r'^[a-zA-Z0-9\s\-_\(\)\.,]+$', session_name):
            return False, "Session name contains invalid characters"
        
        return True, ""
    
    @staticmethod
    def validate_rating(rating: int) -> Tuple[bool, str]:
        """
        Validate rating value
        
        Args:
            rating: Rating to validate (1-5)
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not isinstance(rating, int):
            return False, "Rating must be an integer"
        
        if rating < 1 or rating > 5:
            return False, "Rating must be between 1 and 5"
        
        return True, ""

class FileValidator:
    """Validator for file uploads and exports"""
    
    @staticmethod
    def validate_file_upload(file_content: bytes, filename: str) -> Tuple[bool, str]:
        """
        Validate uploaded file
        
        Args:
            file_content: File content as bytes
            filename: Name of the file
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not file_content:
            return False, "File content is empty"
        
        max_size = int(os.getenv("MAX_FILE_SIZE", "10485760"))  # 10MB default
        if len(file_content) > max_size:
            return False, f"File size exceeds maximum allowed size of {max_size / 1024 / 1024:.1f}MB"
        
        # Validate filename
        if not filename:
            return False, "Filename is required"
        
        if len(filename) > 255:
            return False, "Filename is too long"
        
        # Check file extension
        allowed_types = os.getenv("ALLOWED_FILE_TYPES", "pdf,txt,docx").split(",")
        file_extension = filename.split(".")[-1].lower() if "." in filename else ""
        
        if file_extension not in allowed_types:
            return False, f"File type not allowed. Allowed types: {', '.join(allowed_types)}"
        
        # Basic content validation
        if file_extension == "pdf" and not file_content.startswith(b'%PDF'):
            return False, "Invalid PDF file format"
        
        return True, ""
    
    @staticmethod
    def validate_export_settings(settings: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Validate export settings
        
        Args:
            settings: Export settings dictionary
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        required_fields = ["export_type", "include_sources", "include_timestamps"]
        
        for field in required_fields:
            if field not in settings:
                return False, f"Missing required field: {field}"
        
        valid_export_types = ["pdf", "json", "txt"]
        if settings["export_type"] not in valid_export_types:
            return False, f"Invalid export type. Must be one of: {', '.join(valid_export_types)}"
        
        # Validate boolean fields
        boolean_fields = ["include_sources", "include_timestamps", "include_ratings"]
        for field in boolean_fields:
            if field in settings and not isinstance(settings[field], bool):
                return False, f"{field} must be a boolean value"
        
        return True, ""

class SecurityValidator:
    """Security-related validators"""
    
    @staticmethod
    def validate_sql_injection(input_string: str) -> Tuple[bool, str]:
        """
        Check for potential SQL injection attempts
        
        Args:
            input_string: String to validate
            
        Returns:
            Tuple of (is_safe, error_message)
        """
        if not input_string:
            return True, ""
        
        # Common SQL injection patterns
        dangerous_patterns = [
            r'(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION)\b)',
            r'(\b(OR|AND)\s+\d+\s*=\s*\d+)',
            r'(\'|\"|`|;|--|\*|\/\*|\*\/)',
            r'(\bxp_\w+)',
            r'(\bsp_\w+)',
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, input_string, re.IGNORECASE):
                return False, "Input contains potentially harmful content"
        
        return True, ""
    
    @staticmethod
    def validate_xss_attempt(input_string: str) -> Tuple[bool, str]:
        """
        Check for potential XSS attempts
        
        Args:
            input_string: String to validate
            
        Returns:
            Tuple of (is_safe, error_message)
        """
        if not input_string:
            return True, ""
        
        # Common XSS patterns
        xss_patterns = [
            r'<\s*script\b[^<]*(?:(?!<\/\s*script\s*>)<[^<]*)*<\/\s*script\s*>',
            r'javascript\s*:',
            r'on\w+\s*=',
            r'<\s*iframe\b',
            r'<\s*object\b',
            r'<\s*embed\b',
            r'<\s*link\b',
            r'<\s*meta\b',
            r'<\s*style\b',
        ]
        
        for pattern in xss_patterns:
            if re.search(pattern, input_string, re.IGNORECASE):
                return False, "Input contains potentially harmful content"
        
        return True, ""

class CompositeValidator:
    """Main validator class that combines all validators"""
    
    def __init__(self):
        self.user_validator = UserValidator()
        self.medical_validator = MedicalDataValidator()
        self.chat_validator = ChatValidator()
        self.file_validator = FileValidator()
        self.security_validator = SecurityValidator()
    
    def validate_user_registration(self, user_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate complete user registration data
        
        Args:
            user_data: Dictionary containing user registration data
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        # Required fields validation
        username = user_data.get("username", "")
        email = user_data.get("email", "")
        password = user_data.get("password", "")
        
        # Validate username
        is_valid, error = self.user_validator.validate_username(username)
        if not is_valid:
            errors.append(f"Username: {error}")
        
        # Security check for username
        is_safe, error = self.security_validator.validate_sql_injection(username)
        if not is_safe:
            errors.append(f"Username: {error}")
        
        # Validate email
        is_valid, error = self.user_validator.validate_email(email)
        if not is_valid:
            errors.append(f"Email: {error}")
        
        # Validate password
        is_valid, error = self.user_validator.validate_password(password)
        if not is_valid:
            errors.append(f"Password: {error}")
        
        # Optional fields validation
        first_name = user_data.get("first_name", "")
        if first_name:
            is_valid, error = self.user_validator.validate_name(first_name, "First name")
            if not is_valid:
                errors.append(f"First name: {error}")
        
        last_name = user_data.get("last_name", "")
        if last_name:
            is_valid, error = self.user_validator.validate_name(last_name, "Last name")
            if not is_valid:
                errors.append(f"Last name: {error}")
        
        phone = user_data.get("phone", "")
        if phone:
            is_valid, error = self.user_validator.validate_phone_number(phone)
            if not is_valid:
                errors.append(f"Phone: {error}")
        
        return len(errors) == 0, errors
    
    def validate_medical_profile(self, medical_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate medical profile data
        
        Args:
            medical_data: Dictionary containing medical profile data
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        # Validate conditions
        conditions = medical_data.get("medical_conditions", [])
        if isinstance(conditions, list):
            for condition in conditions:
                is_valid, error = self.medical_validator.validate_medical_condition(condition)
                if not is_valid:
                    errors.append(f"Medical condition '{condition}': {error}")
        
        # Validate medications
        medications = medical_data.get("medications", [])
        if isinstance(medications, list):
            for medication in medications:
                is_valid, error = self.medical_validator.validate_medication(medication)
                if not is_valid:
                    errors.append(f"Medication '{medication}': {error}")
        
        # Validate allergies
        allergies = medical_data.get("allergies", [])
        if isinstance(allergies, list):
            for allergy in allergies:
                is_valid, error = self.medical_validator.validate_allergy(allergy)
                if not is_valid:
                    errors.append(f"Allergy '{allergy}': {error}")
        
        return len(errors) == 0, errors
    
    def validate_chat_input(self, message: str, session_name: str = None) -> Tuple[bool, List[str]]:
        """
        Validate chat input
        
        Args:
            message: Chat message
            session_name: Optional session name
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        # Validate message
        is_valid, error = self.chat_validator.validate_message(message)
        if not is_valid:
            errors.append(f"Message: {error}")
        
        # Security checks
        is_safe, error = self.security_validator.validate_sql_injection(message)
        if not is_safe:
            errors.append(f"Message: {error}")
        
        is_safe, error = self.security_validator.validate_xss_attempt(message)
        if not is_safe:
            errors.append(f"Message: {error}")
        
        # Validate session name if provided
        if session_name:
            is_valid, error = self.chat_validator.validate_session_name(session_name)
            if not is_valid:
                errors.append(f"Session name: {error}")
        
        return len(errors) == 0, errors

# Global validator instance
validator = CompositeValidator()

# Convenience functions
def validate_user_data(user_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Validate user registration data"""
    return validator.validate_user_registration(user_data)

def validate_medical_data(medical_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Validate medical profile data"""
    return validator.validate_medical_profile(medical_data)

def validate_chat_message(message: str, session_name: str = None) -> Tuple[bool, List[str]]:
    """Validate chat input"""
    return validator.validate_chat_input(message, session_name)

def is_safe_input(input_string: str) -> bool:
    """Quick security check for input string"""
    sql_safe, _ = SecurityValidator.validate_sql_injection(input_string)
    xss_safe, _ = SecurityValidator.validate_xss_attempt(input_string)
    return sql_safe and xss_safe