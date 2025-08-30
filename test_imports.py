print("Attempting to import pipeline from transformers...")
try:
    from transformers import pipeline
    print("✅ Successfully imported pipeline.")
except Exception as e:
    print("❌ FAILED to import pipeline.")
    print(f"Error: {e}")