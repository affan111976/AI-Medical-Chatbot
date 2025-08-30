# training/train_intent_model.py

import pandas as pd
from sklearn.model_selection import train_test_split
from transformers import AutoTokenizer, AutoModelForSequenceClassification, Trainer, TrainingArguments
from datasets import Dataset
import torch

# 1. Load and Prepare the Dataset
df = pd.read_csv('data/medical_df.csv') #
df = df.dropna(subset=['query', 'intent']) # Ensure no empty rows

# Create a mapping from string labels to integer IDs
unique_intents = df['intent'].unique()
intent_to_id = {intent: i for i, intent in enumerate(unique_intents)}
id_to_intent = {i: intent for i, intent in enumerate(unique_intents)}

# Add integer labels to the dataframe
df['label'] = df['intent'].map(intent_to_id)

# 2. Split Data
train_df, val_df = train_test_split(df, test_size=0.2, random_state=42, stratify=df['label'])

train_dataset = Dataset.from_pandas(train_df)
val_dataset = Dataset.from_pandas(val_df)

# 3. Load Tokenizer and Model
model_name = "distilbert-base-uncased"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSequenceClassification.from_pretrained(
    model_name,
    num_labels=len(unique_intents),
    id2label=id_to_intent,
    label2id=intent_to_id
)

# 4. Tokenize Datasets
def tokenize_function(examples):
    return tokenizer(examples['query'], padding="max_length", truncation=True)

train_dataset = train_dataset.map(tokenize_function, batched=True)
val_dataset = val_dataset.map(tokenize_function, batched=True)

# 5. Set up the Trainer
training_args = TrainingArguments(
    output_dir='./results',
    num_train_epochs=1,
    per_device_train_batch_size=16,
    per_device_eval_batch_size=16,
    warmup_steps=500,
    weight_decay=0.01,
    logging_dir='./logs',
    logging_steps=10,
    eval_strategy="epoch"
)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=train_dataset,
    eval_dataset=val_dataset,
)

# 6. Train the model
print("Starting model training...")
trainer.train()
print("Training complete.")

# 7. Save the fine-tuned model
output_model_path = "models/intent_classifier/"
print(f"Saving model to {output_model_path}")
trainer.save_model(output_model_path)
tokenizer.save_pretrained(output_model_path)
print("Model and tokenizer saved successfully.")