import streamlit as st
import os
from datetime import datetime
import time
import base64
import json
from typing import Dict, Any, List
import logging
from dotenv import load_dotenv
load_dotenv()

# Import your existing modules
from langchain_huggingface.llms import HuggingFaceEndpoint
from langchain_core.prompts import PromptTemplate
from langchain.chains import RetrievalQA
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_mistralai import ChatMistralAI
from dotenv import load_dotenv

# Import new modules
from src.database.database import db_manager, init_database
from src.database.user_manager import UserManager, SessionManager, FeedbackManager
from src.utils.pdf_generator import generate_session_pdf, generate_user_summary_pdf
from src.utils.encryption import encrypt_data, decrypt_data
# Add this with your other imports
from src.intent_classifier.classifier import intent_classifier
from src.summarizer.summarizer import get_huggingface_summary
# from src.summarizer.summarizer import Summarizer, extract_text_from_pdf

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="AI Medical Chatbot",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize managers
user_manager = UserManager()
session_manager = SessionManager()
feedback_manager = FeedbackManager()

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        color: #2E86AB;
        text-align: center;
        margin-bottom: 2rem;
        font-weight: bold;
    }
    
    .chat-message {
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    
    .user-message {
        background-color: #E3F2FD;
        border-left: 4px solid #2196F3;
    }
    
    .bot-message {
        background-color: #F1F8E9;
        border-left: 4px solid #4CAF50;
    }
    
    .warning-box {
        background-color: #FFF3E0;
        border: 1px solid #FF9800;
        border-radius: 5px;
        padding: 1rem;
        margin: 1rem 0;
    }
    
    .source-doc {
        background-color: #F5F5F5;
        border-radius: 5px;
        padding: 0.5rem;
        margin: 0.5rem 0;
        font-size: 0.8rem;
    }
</style>
""", unsafe_allow_html=True)

def create_download_link(file_content: bytes, filename: str, text: str):
    """Create a download link for files"""
    b64 = base64.b64encode(file_content).decode()
    href = f'<a href="data:application/pdf;base64,{b64}" download="{filename}">{text}</a>'
    return href

@st.cache_resource
def initialize_chatbot():
    """Initialize the chatbot with cached resources"""
    try:
        # Initialize the LLM
        llm = ChatMistralAI(
            model="mistral-large-latest",
            temperature=0,
            max_retries=2,
            api_key=os.environ.get("MISTRALI_API_KEY"),
        )
        
        # Custom prompt template
        CUSTOM_PROMPT_TEMPLATE = """
        Use the pieces of information provided in the context to answer user's question.
        If you dont know the answer, just say that you dont know, dont try to make up an answer. 
        Dont provide anything out of the given context. Always be professional and empathetic in medical contexts.

        Context: {context}
        Question: {question}

        Start the answer directly. No small talk please.
        """
        
        def set_custom_prompt(custom_prompt_template):
            prompt = PromptTemplate(template=custom_prompt_template, input_variables=["context", "question"])
            return prompt
        
        # Load Database
        DB_FAISS_PATH = "vectorstore/db_faiss"
        embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
        db = FAISS.load_local(DB_FAISS_PATH, embedding_model, allow_dangerous_deserialization=True)
        
        # Create QA chain
        qa_chain = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=db.as_retriever(search_kwargs={'k': 3}),
            return_source_documents=True,
            chain_type_kwargs={'prompt': set_custom_prompt(CUSTOM_PROMPT_TEMPLATE)}
        )
        
        return qa_chain
        
    except Exception as e:
        st.error(f"Error initializing chatbot: {str(e)}")
        return None

def get_response(qa_chain, query):
    """Get response from the chatbot"""
    try:
        with st.spinner("Processing your query..."):
            response = qa_chain.invoke({'query': query})
            return response["result"], response["source_documents"]
    except Exception as e:
        st.error(f"Error getting response: {str(e)}")
        return None, None

def login_page():
    """Display login page"""
    st.markdown('<h1 class="main-header">🏥 AI Medical Chatbot - Login</h1>', unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["Login", "Register"])
    
    with tab1:
        st.subheader("Login to Your Account")
        
        with st.form("login_form"):
            username = st.text_input("Username or Email")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login")
            
            if submitted:
                if username and password:
                    try:
                        user_data = user_manager.authenticate_user(username, password)
                        
                        if user_data:
                            st.session_state.user_id = user_data['id']
                            st.session_state.username = user_data['username']
                            st.session_state.logged_in = True
                            st.success("Login successful!")
                            st.rerun()
                        else:
                            st.error("Invalid username or password")
                            
                    except Exception as e:
                        st.error(f"Login error: {str(e)}")
                        logger.error(f"Login error for user {username}: {e}")
                else:
                    st.error("Please fill in all fields")

    with tab2:
        st.subheader("Create New Account")
        
        with st.form("register_form"):
            reg_username = st.text_input("Username", key="reg_username")
            reg_email = st.text_input("Email", key="reg_email")
            reg_password = st.text_input("Password", type="password", key="reg_password")
            reg_first_name = st.text_input("First Name (Optional)", key="reg_first_name")
            reg_last_name = st.text_input("Last Name (Optional)", key="reg_last_name")
            
            data_consent = st.checkbox("I consent to secure storage of my medical data for personalization")
            terms_consent = st.checkbox("I agree to the terms of service and privacy policy")
            
            reg_submitted = st.form_submit_button("Register")
            
            if reg_submitted:
                if reg_username and reg_email and reg_password and data_consent and terms_consent:
                    try:
                        user_data = user_manager.create_user(
                            username=reg_username,
                            email=reg_email,
                            password=reg_password,
                            first_name=reg_first_name or None,
                            last_name=reg_last_name or None
                        )
                        
                        if user_data:
                            st.success("Account created successfully! Please login.")
                        else:
                            st.error("Failed to create account. Username or email might already exist.")
                            
                    except Exception as e:
                        st.error(f"Registration error: {str(e)}")
                        logger.error(f"Registration error: {e}")
                else:
                    st.error("Please fill in required fields and accept terms")

def user_profile_page():
    """Display user profile and preferences"""
    st.header("👤 User Profile & Preferences")
    
    user_data = user_manager.get_user_by_id(st.session_state.user_id)
    
    if not user_data:
        st.error("User not found")
        return
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Personal Information")
        
        with st.form("profile_form"):
            first_name = ""
            last_name = ""
            
            try:
                if user_data.get('first_name'):
                    first_name = decrypt_data(user_data['first_name'])
                if user_data.get('last_name'):
                    last_name = decrypt_data(user_data['last_name'])
            except Exception as e:
                st.warning(f"Could not decrypt personal data: {e}")
            
            new_first_name = st.text_input("First Name", value=first_name)
            new_last_name = st.text_input("Last Name", value=last_name)
            
            st.subheader("Preferences")
            
            language_options = ["en", "es", "fr", "de"]
            try:
                current_lang = user_data.get('language_preference', 'en')
                lang_index = language_options.index(current_lang) if current_lang in language_options else 0
            except (ValueError, TypeError):
                lang_index = 0
                
            language = st.selectbox(
                "Language Preference", 
                language_options,
                index=lang_index
            )
            
            font_options = ["small", "medium", "large"]
            try:
                current_font = user_data.get('accessibility_font_size', 'medium')
                font_index = font_options.index(current_font) if current_font in font_options else 1
            except (ValueError, TypeError):
                font_index = 1
                
            font_size = st.selectbox(
                "Font Size",
                font_options,
                index=font_index
            )
            
            high_contrast = st.checkbox("High Contrast Mode", value=bool(user_data.get('accessibility_high_contrast', False)))
            screen_reader = st.checkbox("Screen Reader Support", value=bool(user_data.get('accessibility_screen_reader', False)))
            
            if st.form_submit_button("Update Profile"):
                try:
                    success = user_manager.update_user_preferences(st.session_state.user_id, {
                        'language_preference': language,
                        'accessibility_font_size': font_size,
                        'accessibility_high_contrast': high_contrast,
                        'accessibility_screen_reader': screen_reader
                    })
                    
                    if success:
                        st.success("Profile updated successfully!")
                        st.rerun()
                    else:
                        st.error("Failed to update profile")
                        
                except Exception as e:
                    st.error(f"Error updating profile: {e}")
        
        # Medical Profile section
        st.subheader("Medical Information")
        st.info("This information helps personalize your experience. All data is encrypted and secure.")
        
        try:
            medical_data = user_manager.get_user_medical_data(st.session_state.user_id)
            if medical_data is None:
                medical_data = {}
        except Exception as e:
            st.warning(f"Could not load medical data: {e}")
            medical_data = {}
        
        with st.form("medical_form"):
            conditions = st.text_area(
                "Medical Conditions (one per line)",
                value="\n".join(medical_data.get('medical_conditions', []))
            )
            
            medications = st.text_area(
                "Current Medications (one per line)",
                value="\n".join(medical_data.get('medications', []))
            )
            
            allergies = st.text_area(
                "Known Allergies (one per line)",
                value="\n".join(medical_data.get('allergies', []))
            )
            
            emergency_contact = st.text_input(
                "Emergency Contact",
                value=medical_data.get('emergency_contact', {}).get('name', '') if medical_data.get('emergency_contact') else ''
            )
            
            emergency_phone = st.text_input(
                "Emergency Contact Phone",
                value=medical_data.get('emergency_contact', {}).get('phone', '') if medical_data.get('emergency_contact') else ''
            )
            
            if st.form_submit_button("Update Medical Information"):
                try:
                    medical_update = {
                        'medical_conditions': [c.strip() for c in conditions.split('\n') if c.strip()],
                        'medications': [m.strip() for m in medications.split('\n') if m.strip()],
                        'allergies': [a.strip() for a in allergies.split('\n') if a.strip()],
                        'emergency_contact': {
                            'name': emergency_contact,
                            'phone': emergency_phone
                        } if emergency_contact else {}
                    }
                    
                    success = user_manager.update_medical_profile(st.session_state.user_id, medical_update)
                    
                    if success:
                        st.success("Medical information updated successfully!")
                        st.rerun()
                    else:
                        st.error("Failed to update medical information")
                        
                except Exception as e:
                    st.error(f"Error updating medical information: {e}")
    
    with col2:
        st.subheader("Account Statistics")
        
        try:
            sessions = session_manager.get_user_sessions(st.session_state.user_id)
            st.metric("Total Sessions", len(sessions))
            
            try:
                if user_data.get('created_at'):
                    if isinstance(user_data['created_at'], str):
                        st.metric("Account Created", user_data['created_at'])
                    else:
                        st.metric("Account Created", user_data['created_at'].strftime('%Y-%m-%d'))
            except Exception:
                st.metric("Account Created", "Unknown")
            
            try:
                if user_data.get('last_login'):
                    if isinstance(user_data['last_login'], str):
                        st.metric("Last Login", user_data['last_login'])
                    else:
                        st.metric("Last Login", user_data['last_login'].strftime('%Y-%m-%d %H:%M'))
            except Exception:
                pass
                
        except Exception as e:
            st.error(f"Could not load sessions: {e}")
            st.metric("Total Sessions", "Error")
        
        st.subheader("Data Export")
        
        if st.button("📄 Export All Data as PDF"):
            try:
                sessions_summary = []
                sessions = session_manager.get_user_sessions(st.session_state.user_id)
                
                for session_data in sessions:
                    try:
                        sessions_summary.append({
                            'session_name': session_data.get('session_name', 'Unnamed Session'),
                            'created_at': session_data.get('created_at'),
                            'message_count': 0,
                            'is_bookmarked': session_data.get('is_bookmarked', False)
                        })
                    except Exception as e:
                        st.warning(f"Could not process session: {e}")
                        continue
                
                user_data_for_pdf = {
                    'username': user_data.get('username', 'Unknown'),
                    'created_at': user_data.get('created_at'),
                    'last_login': user_data.get('last_login'),
                    'language_preference': user_data.get('language_preference', 'en')
                }
                
                pdf_bytes = generate_user_summary_pdf(user_data_for_pdf, sessions_summary)
                
                st.download_button(
                    label="📥 Download User Summary PDF",
                    data=pdf_bytes,
                    file_name=f"user_summary_{user_data.get('username', 'user')}_{datetime.now().strftime('%Y%m%d')}.pdf",
                    mime="application/pdf"
                )
                
            except Exception as e:
                st.error(f"Error generating PDF: {e}")

def session_history_page():
    """Display session history and management"""
    st.header("📚 Chat Session History")
    
    try:
        sessions = session_manager.get_user_sessions(st.session_state.user_id, limit=100)
    except Exception as e:
        st.error(f"Could not load sessions: {e}")
        return
    
    if not sessions:
        st.info("No chat sessions found. Start a new conversation to create your first session!")
        return
    
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        search_term = st.text_input("🔍 Search sessions", placeholder="Search by session name...")
    
    with col2:
        show_bookmarked = st.checkbox("Show only bookmarked")
    
    with col3:
        sort_by = st.selectbox("Sort by", ["Most Recent", "Oldest", "Name"])
    
    filtered_sessions = sessions
    
    if search_term:
        filtered_sessions = [s for s in sessions if search_term.lower() in s.get('session_name', '').lower()]
    
    if show_bookmarked:
        filtered_sessions = [s for s in filtered_sessions if s.get('is_bookmarked', False)]
    
    try:
        if sort_by == "Most Recent":
            filtered_sessions.sort(
                key=lambda x: x.get('updated_at') or x.get('created_at') or datetime.min, 
                reverse=True
            )
        elif sort_by == "Oldest":
            filtered_sessions.sort(
                key=lambda x: x.get('updated_at') or x.get('created_at') or datetime.min
            )
        elif sort_by == "Name":
            filtered_sessions.sort(key=lambda x: x.get('session_name', ''))
    except Exception as e:
        st.warning(f"Could not sort sessions: {e}")
    
    for session_data in filtered_sessions:
        try:
            with st.container():
                col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
                
                with col1:
                    bookmark_icon = "⭐" if session_data.get('is_bookmarked', False) else "☆"
                    session_name = session_data.get('session_name', 'Unnamed Session')
                    created_at = session_data.get('created_at', 'Unknown')
                    
                    if hasattr(created_at, 'strftime'):
                        created_str = created_at.strftime('%Y-%m-%d %H:%M')
                    else:
                        created_str = str(created_at)
                    
                    try:
                        messages = session_manager.get_session_messages(session_data.get('id'))
                        messages_count = len(messages)
                    except Exception:
                        messages_count = 0
                    
                    st.markdown(f"""
                    <div class="session-item">
                        <h4>{bookmark_icon} {session_name}</h4>
                        <p>Created: {created_str}</p>
                        <p>Messages: {messages_count}</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    session_id = session_data.get('id')
                    if st.button("💬 Open", key=f"open_{session_id}"):
                        st.session_state.selected_session_id = session_id
                        st.session_state.page = "chat"
                        # FIXED: Clear current messages when switching sessions
                        if 'messages' in st.session_state:
                            del st.session_state.messages
                        st.rerun()
                
                with col3:
                    if st.button("📄 Export", key=f"export_{session_id}"):
                        try:
                            messages = session_manager.get_session_messages(session_id)
                            user_data = user_manager.get_user_by_id(st.session_state.user_id)
                            
                            user_data_for_pdf = {
                                'username': user_data.get('username', 'Unknown') if user_data else 'Unknown',
                                'created_at': user_data.get('created_at') if user_data else None
                            }
                            
                            session_data_for_pdf = {
                                'session_name': session_data.get('session_name', 'Unnamed Session'),
                                'created_at': session_data.get('created_at')
                            }
                            
                            pdf_bytes = generate_session_pdf(
                                user_data_for_pdf, session_data_for_pdf, messages,
                                include_sources=True,
                                include_timestamps=True,
                                include_ratings=True
                            )
                            
                            st.download_button(
                                label="📥 Download PDF",
                                data=pdf_bytes,
                                file_name=f"session_{session_data.get('session_name', 'session')}_{datetime.now().strftime('%Y%m%d')}.pdf",
                                mime="application/pdf",
                                key=f"download_{session_id}"
                            )
                            
                        except Exception as e:
                            st.error(f"Error exporting session: {e}")
                
                with col4:
                    # FIXED: Add proper session deletion functionality
                    if st.button("🗑️ Delete", key=f"delete_{session_id}"):
                        st.session_state[f"confirm_delete_{session_id}"] = True
                    
                    # Show confirmation if delete was clicked
                    # Replace the old block with this new code in frontend_enhanced.py

                    if st.button("⚠️ Confirm Delete", key=f"confirm_delete_btn_{session_id}"):
                        try:
        # Call the new delete_session method from the session manager
                            success = session_manager.delete_session(session_id, st.session_state.user_id)
        
                            if success:
                                st.success("Session deleted successfully!")
                            else:
                                st.error("Failed to delete session. It may have already been removed.")
        
        # Reset the confirmation state to hide the confirmation button
                            st.session_state[f"confirm_delete_{session_id}"] = False
        
        # Rerun the script to refresh the session list in the UI
                            st.rerun()
        
                        except Exception as e:
                            st.error(f"Error deleting session: {e}")
                            
        except Exception as e:
            st.error(f"Error displaying session: {e}")
            continue

def chat_interface():
    """Main chat interface for interacting with the chatbot"""
    # Initialize chatbot
    qa_chain = initialize_chatbot()

    if qa_chain is None:
        st.error("Failed to initialize the chatbot. Please check your configuration.")
        return

    # --- START OF MAJOR FIXES ---

    # 1. LOAD EXISTING MESSAGES OR INITIALIZE A NEW CHAT
    # Check if a session is selected and if messages for it have not been loaded yet.
    if 'selected_session_id' not in st.session_state:
        st.session_state.selected_session_id = None
        
    if 'messages' not in st.session_state or not st.session_state.messages:
        if st.session_state.selected_session_id:
            # A session is selected, so load its messages from the database.
            try:
                # Get messages from the database
                db_messages = session_manager.get_session_messages(st.session_state.selected_session_id)
                
                # Format messages for display in the UI
                st.session_state.messages = []
                for msg in db_messages:
                    if msg.get('user_message'):
                        st.session_state.messages.append({"role": "user", "content": msg['user_message']})
                    if msg.get('bot_response'):
                        bot_content = msg['bot_response']
                        sources = msg.get('source_documents', [])
                        st.session_state.messages.append({
                            "role": "assistant", 
                            "content": bot_content, 
                            "sources": sources
                        })

            except Exception as e:
                st.error(f"Error loading session history: {e}")
                st.session_state.messages = []
        else:
            # No session is selected, so start with a fresh message list.
            st.session_state.messages = []

    # --- END OF MESSAGE LOADING LOGIC ---
    
    if 'sample_query' not in st.session_state:
        st.session_state.sample_query = ""

    # Main chat interface
    col1, col2 = st.columns([3, 1])

    with col1:
        # Display session name or "New Chat"
        if st.session_state.selected_session_id:
            try:
                # This could be improved by fetching the session details once
                sessions = session_manager.get_user_sessions(st.session_state.user_id)
                current_session = next((s for s in sessions if s['id'] == st.session_state.selected_session_id), None)
                session_name = current_session['session_name'] if current_session else "Chat"
                st.header(f"💬 {session_name}")
            except Exception:
                st.header("💬 Chat Interface")
        else:
            st.header("💬 New Chat")

        # Display chat history (this part remains mostly the same)
        chat_container = st.container()
        with chat_container:
            for message in st.session_state.messages:
                role = message["role"]
                content = message["content"]
                
                if role == "user":
                    st.markdown(f'<div class="chat-message user-message"><strong>👤 You:</strong><br>{content}</div>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="chat-message bot-message"><strong>🤖 Medical AI:</strong><br>{content}</div>', unsafe_allow_html=True)
                    if "sources" in message and message["sources"]:
                        with st.expander("📚 Source Documents"):
                            for i, source in enumerate(message["sources"]):
                                page_content = source.get('page_content', 'No content available.')
                                source_metadata = source.get('metadata', {}).get('source', 'Unknown')
                                st.markdown(f'<div class="source-doc"><strong>Source {i+1}:</strong><br>{page_content[:200]}...<br><small>📄 {source_metadata}</small></div>', unsafe_allow_html=True)

        # Chat input
        query = st.text_input(
            "Ask your medical question:",
            value=st.session_state.sample_query,
            placeholder="e.g., What are the symptoms of diabetes?",
            key="user_input"
        )
        if st.session_state.sample_query:
            st.session_state.sample_query = ""

        col_send, col_clear = st.columns([1, 1])

        with col_send:
            if st.button("📤 Send", type="primary"):
                if query.strip():
                    # --- START OF MESSAGE SAVING LOGIC ---
                    # 1. First, classify the user's intent
                    predicted_intent = intent_classifier.predict(query)
                    st.info(f"Detected Intent: **{predicted_intent}**") # Optional: for debugging

                    # 2. Add user message to UI immediately
                    st.session_state.messages.append({"role": "user", "content": query})
                    
                    # 3. Implement Guided Dialog based on the intent
                    if predicted_intent == "personal_inquiry":
                        # For this intent, ask a clarifying question instead of calling the RAG chain
                        clarifying_message = "I understand you're asking about symptoms. To help me find the most relevant information, could you please specify the condition or illness you are concerned about?"
                        st.session_state.messages.append({"role": "assistant", "content": clarifying_message})
                        st.rerun() # Rerun to display the new messages
                        return # Stop further processing for this turn

                    # 2. CREATE A NEW SESSION IF NEEDED
                    # If no session is active, create one before saving the message.
                    if not st.session_state.selected_session_id:
                        try:
                            # Create a default session name from the first query
                            new_session_name = f"Chat about '{query[:30]}...'"
                            new_session = session_manager.create_session(st.session_state.user_id, new_session_name)
                            if new_session:
                                st.session_state.selected_session_id = new_session['id']
                            else:
                                st.error("Could not create a new chat session.")
                                return # Stop if session creation fails
                        except Exception as e:
                            st.error(f"Error creating session: {e}")
                            return
                    
                    # Get bot response
                    response, sources = get_response(qa_chain, query)

                    if response:
                        # Add bot response to UI
                        sources_for_ui = [
                            {"page_content": doc.page_content, "metadata": doc.metadata}
                            for doc in sources
                        ] if sources else []

                        # Add bot response to UI using the dictionary format.
                        bot_message = {"role": "assistant", "content": response, "sources": sources_for_ui}
                        st.session_state.messages.append(bot_message)
                        
                        # 3. SAVE THE CONVERSATION TO THE DATABASE
                        try:
                            # Pass the original 'sources' (list of Document objects) to be saved.
                            session_manager.save_message(
                                session_id=st.session_state.selected_session_id,
                                user_message=query,
                                bot_response=response,
                                source_documents=sources 
                            )
                        except Exception as e:
                            st.error(f"Failed to save message: {e}")
                    
                    # Rerun to update the display
                    st.rerun()
                    # --- END OF MESSAGE SAVING LOGIC ---

        with col_clear:
            if st.button("🗑️ Clear Chat"):
                # This button is now less critical but can clear the UI for the current session
                st.session_state.messages = []
                st.rerun()

    with col2:
        st.header("📊 Chat Statistics")
        total_messages = len(st.session_state.messages)
        user_messages = len([m for m in st.session_state.messages if m["role"] == "user"])
        bot_messages = len([m for m in st.session_state.messages if m["role"] == "assistant"])
        st.metric("Total Messages", total_messages)
        st.metric("Your Questions", user_messages)
        st.metric("AI Responses", bot_messages)
        st.markdown("---")

        # Feedback section
        st.subheader("💭 Feedback")
        
        with st.form("feedback_form"):
            feedback_type = st.selectbox(
                "Feedback Type",
                ["General", "Bug Report", "Feature Request", "Accuracy Issue"]
            )
            
            rating = st.slider("Overall Rating", 1, 5, 3)
            
            feedback_text = st.text_area("Your Feedback")
            
            if st.form_submit_button("Submit Feedback"):
                if feedback_text:
                    try:
                        success = feedback_manager.submit_feedback(
                            st.session_state.user_id,
                            feedback_type.lower().replace(" ", "_"),
                            feedback_text,
                            rating
                        )
                        
                        if success:
                            st.success("Thank you for your feedback!")
                        else:
                            st.error("Failed to submit feedback")
                    except Exception as e:
                        st.error(f"Error submitting feedback: {e}")
        
        st.markdown("---")
        # Current time display
        st.markdown(f"**🕒 Current Time:**<br>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", unsafe_allow_html=True)

def summarization_page():
    st.title("Summarizer Page Reached!")
    # In summarization_page()
    summary = get_huggingface_summary(extracted_text)


def main():
    # Header
    """Main application function"""
    # Initialize database
    if not init_database():
        st.error("Failed to initialize database. Please check your configuration.")
        return
    
    # Initialize session state
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    
    if 'page' not in st.session_state:
        st.session_state.page = "chat"
    
    # Show login page if not logged in
    if not st.session_state.logged_in:
        login_page()
        return
    
    # Show main chat interface if logged in
    st.markdown('<h1 class="main-header">🏥 AI Medical Chatbot</h1>', unsafe_allow_html=True)
    
    # Medical disclaimer
    st.markdown("""
    <div class="warning-box">
        <strong>⚠️ Medical Disclaimer:</strong> This AI chatbot is for informational purposes only and should not replace professional medical advice, diagnosis, or treatment. Always consult with qualified healthcare professionals for medical concerns.
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        
        st.header(f"👋 Welcome, {st.session_state.username}")
        
        # Navigation
        page_options = ["💬 Chat", "👤 Profile", "📚 History", "🔧 Settings", "Summarize Report"]
        page_keys = ["chat", "profile", "history", "settings", "Summarize Report"]
        
        try:
            current_index = page_keys.index(st.session_state.page)
        except ValueError:
            current_index = 0
            st.session_state.page = "chat"
        
        page = st.selectbox(
            "Navigate to:",
            page_options,
            index=current_index
        )
        
        st.session_state.page = page.split(" ")[1].lower()
        
        st.markdown("---")

        try:
            sessions = session_manager.get_user_sessions(st.session_state.user_id, limit=5)
            st.metric("Recent Sessions", len(sessions))
        except Exception as e:
            st.metric("Recent Sessions", "Error")
            st.caption(f"Could not load sessions: {e}")

        st.markdown("---")
        
        # In the sidebar, after the navigation selectbox
        if st.button("➕ New Chat"):
            # Clear the selected session and messages to start a new chat
            st.session_state.selected_session_id = None
            st.session_state.messages = []
            st.rerun()

        st.markdown("---")

        # Information
        st.header("ℹ️ About")
        st.markdown("""
        This medical chatbot uses:
        - **RAG (Retrieval-Augmented Generation)**
        - **FAISS Vector Database**
        - **Mistral AI Language Model**
        - **Medical Document Knowledge Base**
        """)
        
        st.markdown("---")
        
        # Sample questions
        st.header("💡 Sample Questions")
        sample_questions = [
            "What are the symptoms of diabetes?",
            "How is hypertension treated?",
            "What are the side effects of chemotherapy?",
            "Explain the causes of heart disease",
            "What is the treatment for pneumonia?"
        ]
        
        for question in sample_questions:
            if st.button(f"📝 {question}", key=question):
                st.session_state.sample_query = question

        st.markdown("---")

        if st.button("🚪 Logout"):
            # FIXED: Properly clear all session state on logout
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

    # Main content area
    try:
        if st.session_state.page == "chat":
            chat_interface()
        elif st.session_state.page == "profile":
            user_profile_page()
        elif st.session_state.page == "history":
            session_history_page()
        elif st.session_state.page == "Summarize Report":
            summarization_page()
        elif st.session_state.page == "settings":
            st.header("🔧 Settings")
            st.info("Additional settings will be implemented here")

    except Exception as e:
        st.error(f"Error loading page: {e}")
        logger.error(f"Page loading error: {e}")
        st.info("Please try refreshing the page or contact support if the issue persists.")
    
    
if __name__ == "__main__":
    main()