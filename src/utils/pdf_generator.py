import os
from datetime import datetime
from typing import List, Dict, Any, Optional
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
import io
import base64
import logging

logger = logging.getLogger(__name__)

class PDFGenerator:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._create_custom_styles()
    
    def _create_custom_styles(self):
        """Create custom styles for the medical chatbot PDF"""
        # Title style
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.darkblue
        ))
        
        # Header style
        self.styles.add(ParagraphStyle(
            name='CustomHeader',
            parent=self.styles['Heading2'],
            fontSize=14,
            spaceAfter=12,
            spaceBefore=20,
            textColor=colors.darkblue
        ))
        
        # User message style
        self.styles.add(ParagraphStyle(
            name='UserMessage',
            parent=self.styles['Normal'],
            fontSize=11,
            spaceAfter=6,
            leftIndent=20,
            textColor=colors.darkblue,
            backColor=colors.lightblue,
            borderColor=colors.blue,
            borderWidth=1,
            borderPadding=8
        ))
        
        # Bot response style
        self.styles.add(ParagraphStyle(
            name='BotResponse',
            parent=self.styles['Normal'],
            fontSize=11,
            spaceAfter=12,
            leftIndent=20,
            textColor=colors.darkgreen,
            backColor=colors.lightgreen,
            borderColor=colors.green,
            borderWidth=1,
            borderPadding=8
        ))
        
        # Metadata style
        self.styles.add(ParagraphStyle(
            name='Metadata',
            parent=self.styles['Normal'],
            fontSize=9,
            textColor=colors.grey,
            alignment=TA_RIGHT
        ))
        
        # Warning style
        self.styles.add(ParagraphStyle(
            name='Warning',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.red,
            backColor=colors.lightyellow,
            borderColor=colors.orange,
            borderWidth=1,
            borderPadding=10,
            spaceAfter=20
        ))
    
    def generate_chat_session_pdf(self, user_data: Dict[str, Any], session_data: Dict[str, Any], 
                                 messages: List[Dict[str, Any]], include_sources: bool = True,
                                 include_timestamps: bool = True, include_ratings: bool = False) -> bytes:
        """Generate PDF for a chat session"""
        
        # Create PDF buffer
        buffer = io.BytesIO()
        
        # Create document
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18
        )
        
        # Build content
        content = []
        
        # Title
        content.append(Paragraph("AI Medical Chatbot - Conversation Report", self.styles['CustomTitle']))
        content.append(Spacer(1, 20))
        
        # Medical disclaimer
        disclaimer_text = """
        <b>⚠️ MEDICAL DISCLAIMER:</b> This document contains AI-generated responses for informational 
        purposes only and should not replace professional medical advice, diagnosis, or treatment. 
        Always consult with qualified healthcare professionals for medical concerns.
        """
        content.append(Paragraph(disclaimer_text, self.styles['Warning']))
        
        # Session information
        content.append(Paragraph("Session Information", self.styles['CustomHeader']))
        
        session_info = [
            ['Session Name:', session_data.get('session_name', 'Unnamed Session')],
            ['User:', user_data.get('username', 'Anonymous')],
            ['Session Date:', session_data.get('created_at', datetime.now()).strftime('%Y-%m-%d %H:%M:%S')],
            ['Total Messages:', str(len(messages))],
            ['Report Generated:', datetime.now().strftime('%Y-%m-%d %H:%M:%S')]
        ]
        
        session_table = Table(session_info, colWidths=[2*inch, 4*inch])
        session_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        
        content.append(session_table)
        content.append(Spacer(1, 20))
        
        # Conversation
        content.append(Paragraph("Conversation", self.styles['CustomHeader']))
        
        for i, message in enumerate(messages):
            # Message number
            content.append(Paragraph(f"Message {i+1}", self.styles['Heading3']))
            
            # Timestamp
            if include_timestamps and message.get('timestamp'):
                timestamp_text = f"Time: {message['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}"
                content.append(Paragraph(timestamp_text, self.styles['Metadata']))
            
            # User message
            if message.get('user_message'):
                content.append(Paragraph("👤 <b>Your Question:</b>", self.styles['Normal']))
                user_msg = message['user_message'].replace('\n', '<br/>')
                content.append(Paragraph(user_msg, self.styles['UserMessage']))
            
            # Bot response
            if message.get('bot_response'):
                content.append(Paragraph("🤖 <b>AI Response:</b>", self.styles['Normal']))
                bot_msg = message['bot_response'].replace('\n', '<br/>')
                content.append(Paragraph(bot_msg, self.styles['BotResponse']))
            
            # Rating
            if include_ratings and message.get('user_rating'):
                rating_text = f"Your Rating: {'⭐' * message['user_rating']} ({message['user_rating']}/5)"
                content.append(Paragraph(rating_text, self.styles['Metadata']))
            
            # Confidence score
            if message.get('confidence_score'):
                confidence_text = f"AI Confidence: {message['confidence_score']:.2%}"
                content.append(Paragraph(confidence_text, self.styles['Metadata']))
            
            # Source documents
            if include_sources and message.get('source_documents'):
                content.append(Paragraph("📚 <b>Source Documents:</b>", self.styles['Normal']))
                for j, source in enumerate(message['source_documents'][:3]):  # Limit to 3 sources
                    source_text = f"Source {j+1}: {source.get('content', '')[:200]}..."
                    content.append(Paragraph(source_text, self.styles['Normal']))
            
            content.append(Spacer(1, 15))
            
            # Page break every 3 messages to avoid clutter
            if (i + 1) % 3 == 0 and i < len(messages) - 1:
                content.append(PageBreak())
        
        # Footer information
        content.append(PageBreak())
        content.append(Paragraph("Export Information", self.styles['CustomHeader']))
        
        export_info = [
            ['Export Type:', 'PDF Report'],
            ['Includes Source Documents:', 'Yes' if include_sources else 'No'],
            ['Includes Timestamps:', 'Yes' if include_timestamps else 'No'],
            ['Includes Ratings:', 'Yes' if include_ratings else 'No'],
            ['Generated by:', 'AI Medical Chatbot System'],
            ['Export Date:', datetime.now().strftime('%Y-%m-%d %H:%M:%S')]
        ]
        
        export_table = Table(export_info, colWidths=[2*inch, 4*inch])
        export_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        
        content.append(export_table)
        
        # Privacy notice
        privacy_text = """
        <b>Privacy Notice:</b> This document may contain sensitive medical information. 
        Please handle with appropriate care and dispose of securely when no longer needed.
        Do not share this document without proper authorization.
        """
        content.append(Spacer(1, 20))
        content.append(Paragraph(privacy_text, self.styles['Warning']))
        
        # Build PDF
        doc.build(content)
        
        # Get PDF bytes
        pdf_bytes = buffer.getvalue()
        buffer.close()
        
        return pdf_bytes
    
    def generate_user_summary_pdf(self, user_data: Dict[str, Any], 
                                 sessions_summary: List[Dict[str, Any]]) -> bytes:
        """Generate a user activity summary PDF"""
        
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        content = []
        
        # Title
        content.append(Paragraph("Medical Chatbot - User Activity Summary", self.styles['CustomTitle']))
        content.append(Spacer(1, 20))
        
        # User information
        content.append(Paragraph("User Profile", self.styles['CustomHeader']))
        
        user_info = [
            ['Username:', user_data.get('username', 'Anonymous')],
            ['Account Created:', user_data.get('created_at', datetime.now()).strftime('%Y-%m-%d')],
            ['Last Login:', user_data.get('last_login', 'Never').strftime('%Y-%m-%d %H:%M') if user_data.get('last_login') else 'Never'],
            ['Total Sessions:', str(len(sessions_summary))],
            ['Language Preference:', user_data.get('language_preference', 'English')]
        ]
        
        user_table = Table(user_info, colWidths=[2*inch, 4*inch])
        user_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        
        content.append(user_table)
        content.append(Spacer(1, 20))
        
        # Sessions summary
        content.append(Paragraph("Session History", self.styles['CustomHeader']))
        
        if sessions_summary:
            session_data = [['Session Name', 'Date', 'Messages', 'Bookmarked']]
            for session in sessions_summary:
                session_data.append([
                    session.get('session_name', 'Unnamed'),
                    session.get('created_at', datetime.now()).strftime('%Y-%m-%d'),
                    str(session.get('message_count', 0)),
                    'Yes' if session.get('is_bookmarked') else 'No'
                ])
            
            sessions_table = Table(session_data, colWidths=[2.5*inch, 1.5*inch, 1*inch, 1*inch])
            sessions_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            content.append(sessions_table)
        else:
            content.append(Paragraph("No sessions found.", self.styles['Normal']))
        
        doc.build(content)
        pdf_bytes = buffer.getvalue()
        buffer.close()
        
        return pdf_bytes
    
    def save_pdf_to_file(self, pdf_bytes: bytes, filename: str, directory: str = "exports") -> str:
        """Save PDF bytes to file and return the file path"""
        try:
            # Create directory if it doesn't exist
            os.makedirs(directory, exist_ok=True)
            
            # Create unique filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_filename = f"{timestamp}_{filename}.pdf"
            file_path = os.path.join(directory, safe_filename)
            
            # Write PDF to file
            with open(file_path, 'wb') as f:
                f.write(pdf_bytes)
            
            logger.info(f"PDF saved to {file_path}")
            return file_path
            
        except Exception as e:
            logger.error(f"Error saving PDF: {e}")
            raise
    
    def pdf_to_base64(self, pdf_bytes: bytes) -> str:
        """Convert PDF bytes to base64 string for download"""
        return base64.b64encode(pdf_bytes).decode()

# Global PDF generator instance
pdf_generator = PDFGenerator()

def generate_session_pdf(user_data: Dict[str, Any], session_data: Dict[str, Any], 
                        messages: List[Dict[str, Any]], **kwargs) -> bytes:
    """Convenience function to generate session PDF"""
    return pdf_generator.generate_chat_session_pdf(user_data, session_data, messages, **kwargs)

def generate_user_summary_pdf(user_data: Dict[str, Any], sessions_summary: List[Dict[str, Any]]) -> bytes:
    """Convenience function to generate user summary PDF"""
    return pdf_generator.generate_user_summary_pdf(user_data, sessions_summary)