import torch
from PIL import Image
from transformers import LayoutLMv3ForSequenceClassification, LayoutLMv3Tokenizer, LayoutLMv3Processor, LayoutLMv3FeatureExtractor
import os

# Define label mappings
idx2label = {0: 'Resume', 1: 'License', 2: 'Passport', 3: 'Invoice', 4: 'Check'}

# Load the model and tokenizer from Hugging Face
model_name = "Suchit037/Final-Document-Classification"

# Use the base model from Hugging Face to initialize the processor
tokenizer = LayoutLMv3Tokenizer.from_pretrained("microsoft/layoutlmv3-base")
feature_extractor = LayoutLMv3FeatureExtractor.from_pretrained("microsoft/layoutlmv3-base")
processor = LayoutLMv3Processor(feature_extractor, tokenizer)

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

import os
model = LayoutLMv3ForSequenceClassification.from_pretrained(
    model_name,
    token=os.getenv('HUGGINGFACE_TOKEN')  # Read the token from an environment variable
)

model.to(device)

def classify_document(image_path):
    """
    Classifies the document at the given image path.
    
    Args:
        image_path (str): Path to the image to classify.
    
    Returns:
        str: Predicted label for the document.
    """
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Error: Image file not found at {image_path}")
    
    # Open the image and preprocess it
    image = Image.open(image_path).convert("RGB")
    
    # Preprocess the image and prepare the input tensors
    encoded_inputs = processor(image, return_tensors="pt").to(device)
    
    # Perform inference using the model
    model.eval()  # Switch to evaluation mode
    with torch.no_grad():  # No need to track gradients during inference
        outputs = model(**encoded_inputs)
    
    # Get the predicted logits
    logits = outputs.logits
    
    # Use argmax to get the predicted label
    pred_label_idx = torch.argmax(logits, dim=1).item()
    pred_label = idx2label[pred_label_idx]
    
    return pred_label

