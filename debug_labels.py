"""Quick debug script to check model label mapping."""
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification

model_name = "hamzab/roberta-fake-news-classification"
cache_dir = "blog/predictor/models"

print("Loading model...")
tokenizer = AutoTokenizer.from_pretrained(model_name, cache_dir=cache_dir)
model = AutoModelForSequenceClassification.from_pretrained(model_name, cache_dir=cache_dir)
model.eval()

print(f"\nModel config id2label: {model.config.id2label}")
print(f"Model config label2id: {model.config.label2id}")
print(f"Number of labels: {model.config.num_labels}")

# Test with clearly REAL news
real_text = "India vs Pakistan T20 World Cup Boycott Row Highlights: The Pakistan cricket team were allowed to take the field against India in their T20 World Cup 2026 match on February 15, with the Pakistan government confirming the decision via a statement on Monday. This came after a series of negotiations between the Pakistan Cricket Board (PCB) and the International Cricket Council (ICC)."

# Test with clearly FAKE news 
fake_text = "BREAKING: Scientists discover miracle cure that Big Pharma has been hiding! Doctors HATE this one simple trick! Click here before they delete this!"

for label, text in [("REAL article", real_text), ("FAKE article", fake_text)]:
    inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=256, padding="max_length")
    
    with torch.no_grad():
        outputs = model(**inputs)
    
    logits = outputs.logits
    probs = torch.nn.functional.softmax(logits, dim=-1)
    
    print(f"\n{'='*50}")
    print(f"Testing: {label}")
    print(f"Text: {text[:80]}...")
    print(f"Raw logits: {logits.tolist()}")
    print(f"Probabilities: {probs.tolist()}")
    print(f"  Label 0 prob: {float(probs[0][0]):.4f}")
    print(f"  Label 1 prob: {float(probs[0][1]):.4f}")
    print(f"  Predicted label index: {torch.argmax(probs, dim=-1).item()}")
    print(f"  id2label mapping: {model.config.id2label}")
