# src/intent_classifier/classifier.py

from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline
import streamlit as st

@st.cache_resource
def load_intent_model():
    """Loads the fine-tuned intent classification model and tokenizer."""
    model_path = "models/intent_classifier/"
    tokenizer = AutoTokenizer.from_pretrained(model_path)
    model = AutoModelForSequenceClassification.from_pretrained(model_path)
    # Use a pipeline for easy prediction
    classifier_pipeline = pipeline("text-classification", model=model, tokenizer=tokenizer)
    return classifier_pipeline

class IntentClassifier:
    def __init__(self):
        self.pipeline = load_intent_model()

    def predict(self, query: str) -> str:
        """Predicts the intent of a user query."""
        if not query:
            return "unknown"
        try:
            prediction = self.pipeline(query)
            # The pipeline returns a list of dictionaries, e.g., [{'label': 'symptom_inquiry', 'score': 0.99}]
            return prediction[0]['label']
        except Exception as e:
            print(f"Error during intent prediction: {e}")
            return "unknown"

# Create a single instance to be used by the app
intent_classifier = IntentClassifier()