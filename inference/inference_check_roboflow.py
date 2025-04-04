from inference_sdk import InferenceHTTPClient
import cv2
import pytesseract
import numpy as np
from datetime import datetime
import re
import json

# Initialize the inference client
CLIENT = InferenceHTTPClient(
    api_url="https://detect.roboflow.com",
    api_key="5F6f0kVy4vHTtc2KEJUH"
)

# Function to extract text from specific regions of the image
def extract_text_from_region(image, x, y, width, height):
    x1 = max(0, x - width // 2)
    y1 = max(0, y - height // 2)
    x2 = min(image.shape[1], x + width // 2)
    y2 = min(image.shape[0], y + height // 2)
    
    roi = image[y1:y2, x1:x2]
    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
    text = pytesseract.image_to_string(thresh, config='--psm 6')
    return text.strip()

# Post-processing functions
def format_date(date_str):
    try:
        for fmt in ('%d%m%Y', '%d/%m/%Y', '%Y%m%d', '%d-%m-%Y'):
            try:
                date_obj = datetime.strptime(date_str.replace('/', '').replace('-', ''), fmt)
                return date_obj.strftime('%d-%m-%Y')
            except ValueError:
                continue
    except:
        pass
    numbers = re.sub(r'[^0-9]', '', date_str)
    if len(numbers) >= 6:
        return f"{numbers[:2]}-{numbers[2:4]}-{numbers[4:8]}"
    return date_str

def clean_number(number_str):
    return re.sub(r'[^0-9,.]', '', number_str)

def clean_text(text_str):
    return re.sub(r'[^a-zA-Z ]', '', text_str)

# Main parsing function
def extract_check_info(image_path):
    # Run inference
    result = CLIENT.infer(image_path, model_id="cheque-parsing/2")

    # Load the image
    image = cv2.imread(image_path)

    # Dictionary to store extracted data
    extracted_data = {}

    # Process each prediction
    for prediction in result['predictions']:
        x = int(prediction['x'])
        y = int(prediction['y'])
        width = int(prediction['width'])
        height = int(prediction['height'])
        class_name = prediction.get('class', 'unknown')
        
        extracted_text = extract_text_from_region(image, x, y, width, height)
        extracted_data[class_name] = extracted_text

    # Format the extracted data
    formatted_data = {}
    for key, value in extracted_data.items():
        if 'date' in key.lower():
            formatted_data['Date'] = format_date(value) if value else "Not Found"
        elif 'bank' in key.lower():
            formatted_data['Bank Name'] = clean_text(value) if value else "Not Found"
        elif 'amount_digit' in key.lower() or 'amount' in key.lower() == 'digit':
            formatted_data['Amount_digit'] = clean_number(value) if value else "Not Found"
        elif 'amount_hand' in key.lower() or 'amount' in key.lower() == 'hand':
            formatted_data['Amount_hand'] = clean_text(value) if value else "Not Found"
        elif 'name' in key.lower():
            formatted_data['Name'] = clean_text(value) if value else "Not Found"
        else:
            formatted_data[key] = value if value else "Not Found"

    result_json = {
        entity: {"text": value} if value else {"text": "Not Found"}
        for entity, value in formatted_data.items()
    }
    print(result_json)

    return result_json


