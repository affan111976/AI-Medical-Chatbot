#!/usr/bin/env python3
"""
Script to create all necessary __init__.py files for the project structure
"""

import os

def create_init_files():
    """Create __init__.py files in all necessary directories"""
    
    directories = [
        "src",
        "src/database",
        "src/utils",
        "src/chatbot"
    ]
    
    for directory in directories:
        # Create directory if it doesn't exist
        os.makedirs(directory, exist_ok=True)
        
        # Create __init__.py file
        init_file_path = os.path.join(directory, "__init__.py")
        
        if not os.path.exists(init_file_path):
            with open(init_file_path, "w") as f:
                if directory == "src":
                    f.write('"""AI Medical Chatbot - Source Code Package"""\n\n')
                elif directory == "src/database":
                    f.write('"""Database management and models"""\n\n')
                elif directory == "src/utils":
                    f.write('"""Utility functions and helpers"""\n\n')
                elif directory == "src/chatbot":
                    f.write('"""Chatbot core functionality"""\n\n')
                else:
                    f.write("")
            
            print(f"✅ Created {init_file_path}")
        else:
            print(f"📄 {init_file_path} already exists")

def create_env_template():
    """Create .env template file"""
    env_template = """# AI Medical Chatbot Environment Variables

# Database Configuration
DATABASE_URL=sqlite:///medical_chatbot.db
# For PostgreSQL: DATABASE_URL=postgresql://username:password@localhost/dbname

# Mistral AI API Configuration
MISTRALI_API_KEY=your_mistral_api_key_here

# Encryption Configuration (Generate secure keys in production)
ENCRYPTION_KEY=
ENCRYPTION_PASSWORD=secure_medical_chatbot_password_2024
ENCRYPTION_SALT=medical_chatbot_salt_2024

# Logging Level
LOG_LEVEL=INFO

# Application Settings
DEBUG=False
APP_NAME=AI Medical Chatbot
APP_VERSION=1.0.0

# Session Configuration
SESSION_TIMEOUT=3600  # 1 hour in seconds

# File Upload Settings
MAX_FILE_SIZE=10485760  # 10MB in bytes
ALLOWED_FILE_TYPES=pdf,txt,docx

# Export Settings
EXPORT_DIRECTORY=exports
TEMP_DIRECTORY=temp

# Security Settings
PASSWORD_MIN_LENGTH=8
SESSION_SECURITY_KEY=your_session_security_key_here
"""
    
    if not os.path.exists(".env"):
        with open(".env", "w") as f:
            f.write(env_template)
        print("✅ Created .env template file")
        print("⚠️  Please update the .env file with your actual API keys and configuration")
    else:
        print("📄 .env file already exists")

def create_gitignore():
    """Create .gitignore file"""
    gitignore_content = """# Environment variables
.env
.env.local
.env.production

# Database files
*.db
*.sqlite
*.sqlite3

# Python cache
__pycache__/
*.py[cod]
*$py.class
*.so

# Distribution / packaging
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual environments
venv/
env/
ENV/
.venv/

# IDE files
.vscode/
.idea/
*.swp
*.swo
*~

# Logs
*.log
logs/

# Temporary files
tmp/
temp/
*.tmp

# Exports and uploads
exports/
uploads/

# Vector store data
vectorstore/

# OS generated files
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db

# Streamlit
.streamlit/

# Jupyter Notebook
.ipynb_checkpoints

# PyTorch models
*.pt
*.pth

# HuggingFace cache
.cache/
"""
    
    if not os.path.exists(".gitignore"):
        with open(".gitignore", "w") as f:
            f.write(gitignore_content)
        print("✅ Created .gitignore file")
    else:
        print("📄 .gitignore file already exists")

def create_readme():
    """Create README.md file"""
    readme_content = """# AI Medical Chatbot

A sophisticated medical chatbot with user management, personalization, and session persistence features.

## Features

### 🔐 User Management & Authentication
- Secure user registration and login
- Encrypted storage of personal and medical data
- User preferences and accessibility settings

### 👤 Personalization
- Medical history tracking for personalized responses
- Language preferences and communication styles
- Accessibility features (font size, high contrast, screen reader support)

### 💬 Advanced Chat Features
- Persistent chat sessions across logins
- Message bookmarking and rating
- Source document citations
- Confidence scoring for AI responses

### 📄 Export & Sharing
- Export chat sessions as PDF reports
- User activity summary reports
- Secure sharing with healthcare providers

### 🔒 Security & Privacy
- End-to-end encryption for sensitive data
- HIPAA-compliant data handling
- Secure session management
- Data retention policies

## Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd ai-medical-chatbot
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\\Scripts\\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**
   - Copy `.env.example` to `.env`
   - Add your API keys and configuration

5. **Initialize the project structure:**
   ```bash
   python create_init_files.py
   ```

6. **Prepare your medical documents:**
   - Place PDF files in the `data/` directory
   - Run the document processing script:
     ```bash
     python src/chatbot/memory_LLM.py
     ```

7. **Run the application:**
   ```bash
   streamlit run frontend_enhanced.py
   ```

## Project Structure

```
AI_MEDICAL_CHATBOT/
├── data/                          # PDF medical documents
├── vectorstore/                   # FAISS vector database
├── src/
│   ├── database/
│   │   ├── models.py             # Database models
│   │   ├── database.py           # Database connection
│   │   └── user_manager.py       # User management logic
│   ├── utils/
│   │   ├── pdf_generator.py      # PDF export functionality
│   │   ├── encryption.py         # Data encryption utilities
│   │   └── validators.py         # Input validation
│   └── chatbot/
│       ├── memory_LLM.py         # Document processing
│       └── memory_with_LLM.py    # Core chatbot logic
├── frontend_enhanced.py           # Enhanced Streamlit app
├── requirements.txt
├── .env                          # Environment variables
└── README.md
```

## Usage

### For Users
1. **Register/Login:** Create an account or log in to existing account
2. **Set Preferences:** Configure language, accessibility, and medical information
3. **Start Chatting:** Ask medical questions and get personalized responses
4. **Manage Sessions:** View history, bookmark important messages, export conversations

### For Administrators
1. **Database Management:** Monitor user activity and feedback
2. **Content Updates:** Add new medical documents to the knowledge base
3. **System Monitoring:** Track performance and user engagement

## Configuration

### Environment Variables
- `MISTRALI_API_KEY`: Your Mistral AI API key
- `DATABASE_URL`: Database connection string
- `ENCRYPTION_KEY`: Encryption key for sensitive data
- `LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR)

### Database Configuration
The system supports SQLite (default) and PostgreSQL. Configure via `DATABASE_URL`.

### Security Settings
- Password requirements
- Session timeout
- File upload restrictions
- Data retention policies

## API Documentation

### User Management
- `UserManager`: Handle user registration, authentication, preferences
- `SessionManager`: Manage chat sessions and messages
- `FeedbackManager`: Collect and process user feedback

### Data Processing
- `PDFGenerator`: Export functionality for sessions and user data
- `EncryptionManager`: Secure data encryption/decryption

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## Security Considerations

- All sensitive data is encrypted at rest
- Secure password hashing
- Session management with timeouts
- Input validation and sanitization
- Regular security audits recommended

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:
- Create an issue in the repository
- Contact the development team
- Check the documentation wiki

## Disclaimer

This AI chatbot is for informational purposes only and should not replace professional medical advice, diagnosis, or treatment. Always consult with qualified healthcare professionals for medical concerns.
"""
    
    if not os.path.exists("README.md"):
        with open("README.md", "w", encoding="utf-8") as f:
            f.write(readme_content)
        print("✅ Created README.md file")
    else:
        print("📄 README.md file already exists")

if __name__ == "__main__":
    print("🚀 Setting up AI Medical Chatbot project structure...")
    print()
    
    create_init_files()
    print()
    
    create_env_template()
    print()
    
    create_gitignore()
    print()
    
    create_readme()
    print()
    
    print("✅ Project setup complete!")
    print()
    print("Next steps:")
    print("1. Update the .env file with your API keys")
    print("2. Install dependencies: pip install -r requirements.txt")
    print("3. Place your medical PDFs in the data/ directory")
    print("4. Run: python src/chatbot/memory_LLM.py")
    print("5. Start the app: streamlit run frontend_enhanced.py")