import json
import pytesseract
from PIL import Image
from inference_sdk import InferenceHTTPClient

def extract_resume_info(image_path):
    """Extract raw OCR text from each detected resume section using Roboflow + Tesseract"""

    # Initialize Roboflow client
    CLIENT = InferenceHTTPClient(
        api_url="https://detect.roboflow.com",
        api_key="5F6f0kVy4vHTtc2KEJUH"
    )

    # Run inference
    result = CLIENT.infer(image_path, model_id="resume-parsing-odjft/3")
    image = Image.open(image_path)
    width, height = image.size

    # Dictionary to hold raw OCR output
    raw_extracted_info = {}

    # Loop through each detected section
    for prediction in result["predictions"]:
        label = prediction["class"]
        x, y, w, h = prediction["x"], prediction["y"], prediction["width"], prediction["height"]
        
        # Compute bounding box
        x1, y1 = int(x - w / 2), int(y - h / 2)
        x2, y2 = int(x + w / 2), int(y + h / 2)
        
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(width, x2), min(height, y2)
        
        # Crop section from image
        section_image = image.crop((x1, y1, x2, y2))

        # Run OCR
        section_text = pytesseract.image_to_string(section_image).strip()
        raw_extracted_info[label] = section_text

    # Output raw extracted results
    print("\nExtracted Raw Text Data:")
    print(json.dumps(raw_extracted_info, indent=2))

    return raw_extracted_info

