# src/summarizer/summarizer.py

import os
import requests
import streamlit as st
from pypdf import PdfReader
import time

# The model we'll use from the Hugging Face Hub
API_URL = "https://api-inference.huggingface.co/models/facebook/bart-large-cnn"

@st.cache_data
def get_huggingface_summary(text: str) -> str:
    """
    Sends text to the Hugging Face Inference API and returns a summary.
    """
    if not text:
        return "No text provided to summarize."

    hf_token = os.environ.get("HF_TOKEN")
    if not hf_token:
        return "ERROR: Hugging Face API token (HF_TOKEN) not found in environment."

    headers = {"Authorization": f"Bearer {hf_token}"}
    
    # Hugging Face API can be sensitive to very long inputs, so we truncate if necessary
    max_input_length = 1024 
    inputs = text[:max_input_length]

    payload = {
        "inputs": inputs,
        "parameters": {"min_length": 50, "max_length": 250}
    }

    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=60)
        
        # Handle API response
        if response.status_code == 200:
            summary = response.json()
            return summary[0]['summary_text']
        elif response.status_code == 503 and "is currently loading" in response.text:
            # Model is loading, wait and retry
            st.info("Model is loading on the server, please wait...")
            time.sleep(20) # Wait 20 seconds
            response = requests.post(API_URL, headers=headers, json=payload, timeout=60)
            if response.status_code == 200:
                summary = response.json()
                return summary[0]['summary_text']
            else:
                 return f"Error after retry: {response.status_code} - {response.text}"
        else:
            return f"Error: {response.status_code} - {response.text}"

    except Exception as e:
        error_message = f"Failed to get summary from Hugging Face API: {e}"
        print(error_message)
        return error_message

def extract_text_from_pdf(pdf_file) -> str:
    """
    Extracts text content from an uploaded PDF file.
    """
    try:
        pdf_reader = PdfReader(pdf_file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text()
        return text
    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
        return "Could not read the PDF file. It might be corrupted or image-based."