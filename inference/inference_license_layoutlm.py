import os
import json
from PIL import Image
from transformers import LayoutLMv3Processor, LayoutLMv3ForTokenClassification
from pytesseract import pytesseract
import torch
import re

# Load the model and processor
model_dir = '/Users/suchit/Desktop/NER/model'
model = LayoutLMv3ForTokenClassification.from_pretrained(model_dir)
processor = LayoutLMv3Processor.from_pretrained("microsoft/layoutlmv3-base", apply_ocr=False)

# Define label mappings
id2label = {
    0: "irrelevant text",
    1: "driving license number",
    2: "name",
    3: "date of birth",
    4: "citizenship no",
    5: "contact no",
    6: "date of issue",
    7: "date of expiry"
}

def extract_license_info(image_path, device="cpu"):
    image = Image.open(image_path).convert("RGB")
    
    # Perform OCR
    ocr_results = pytesseract.image_to_data(image, config='--psm 3', output_type=pytesseract.Output.DICT)
    
    words = []
    boxes = []
    for i in range(len(ocr_results["text"])):
        if ocr_results["text"][i].strip():  # Ignore empty text
            x, y, w, h = ocr_results["left"][i], ocr_results["top"][i], ocr_results["width"][i], ocr_results["height"][i]
            img_width, img_height = image.size
            words.append(ocr_results["text"][i])
            boxes.append([
                int((x / img_width) * 1000), int((y / img_height) * 1000),
                int(((x + w) / img_width) * 1000), int(((y + h) / img_height) * 1000)
            ])
    
    if not words:
        raise ValueError("No text detected in the image.")
    
    encoding = processor(image, words, boxes=boxes, truncation=True, padding="max_length", max_length=512, return_tensors="pt")
    encoding = {k: v.to(device) for k, v in encoding.items()}
    
    model.to(device).eval()
    with torch.no_grad():
        outputs = model(**encoding)
    
    logits = outputs.logits[0].cpu()
    predictions = logits.argmax(dim=-1).numpy()
    
    predicted_labels = {}
    word_ids = encoding['input_ids'].squeeze().tolist()  # Adjust for word-level handling
    
    # Define required entities
    required_entities = {
        "driving license number": None,
        "name": None,
        "date of birth": None,
        "citizenship no": None,
        "contact no": None,
        "date of issue": None,
        "date of expiry": None
    }
    
    date_pattern = re.compile(r"\d{2}-\d{2}-\d{4}|\d{4}-\d{2}-\d{2}")
    phone_pattern = re.compile(r"\d{10}")
    citizen_pattern = re.compile(r"\d{2}-\d{2}-\d{2}-\d{5}")
    
    # Ensure that predictions and words are aligned
    for i, word_id in enumerate(word_ids):
        if i < len(words):  # Safeguard against index out of range
            text = words[i]
            label = id2label.get(predictions[i], "irrelevant text")
            
            if label in required_entities and required_entities[label] is None:
                required_entities[label] = text
            elif date_pattern.match(text):
                if required_entities["date of birth"] is None:
                    required_entities["date of birth"] = text
                elif required_entities["date of issue"] is None:
                    required_entities["date of issue"] = text
                elif required_entities["date of expiry"] is None:
                    required_entities["date of expiry"] = text
            elif phone_pattern.match(text) and required_entities["contact no"] is None:
                required_entities["contact no"] = text
            elif citizen_pattern.match(text) and required_entities["citizenship no"] is None:
                required_entities["citizenship no"] = text
    
    # Build the result JSON with only text fields
    result_json = {
        entity: {"text": value} if value else {"text": "Not Found"}
        for entity, value in required_entities.items()
    }

    return result_json
