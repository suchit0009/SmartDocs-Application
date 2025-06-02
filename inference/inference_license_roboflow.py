from inference_sdk import InferenceHTTPClient
import cv2
import pytesseract
import json
import os
import re
from PIL import Image
import os

def extract_license_info(image_path, device="cpu"):
    """
    Extract text from license fields using Roboflow for detection and Tesseract for OCR,
    with output formatted to match the LayoutLMv3 model structure
    """
    # Load image
    image = cv2.imread(image_path)
    if image is None:
        return {"error": f"Failed to load image: {image_path}"}
    
    # Initialize Roboflow inference client
    CLIENT = InferenceHTTPClient(
        api_url="https://detect.roboflow.com",
        api_key=os.getenv("ROBOFLOW_API_KEY")
    )
    
    # Run detection with Roboflow
    print("Running Roboflow detection...")
    response = CLIENT.infer(image_path, model_id="nepali-driving-license-parsing/2")
    predictions = response['predictions']
    
    # Dictionary to store the extracted information
    extracted_data = {}
    
    # Process each prediction
    print("Extracting text from detected regions...")
    for pred in predictions:
        cls = pred['class']  # Class name (e.g., 'name', 'license_number')
        
        # Extract bounding box coordinates
        x, y, w, h = int(pred['x']), int(pred['y']), int(pred['width']), int(pred['height'])
        
        # Calculate the actual coordinates of the box
        x1 = max(x - w // 2, 0)
        y1 = max(y - h // 2, 0)
        x2 = min(x + w // 2, image.shape[1])
        y2 = min(y + h // 2, image.shape[0])
        
        # Crop the region of interest
        cropped = image[y1:y2, x1:x2]
        
        # Preprocess image to improve OCR
        gray = cv2.cvtColor(cropped, cv2.COLOR_BGR2GRAY)
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # Save the cropped image temporarily
        temp_crop_path = f"temp_crop_{cls}.png"
        cv2.imwrite(temp_crop_path, binary)
        
        # Run Tesseract OCR on the cropped image
        try:
            # Configure Tesseract to improve accuracy for this specific use case
            config = "--psm 7"  # Assume a single line of text
            
            # For numeric fields, restrict character set
            if cls in ["license_number", "contact_number", "dob", "citizenship_number", "doi", "doe"]:
                config = "--psm 7 -c tessedit_char_whitelist=0123456789-/."
            
            text = pytesseract.image_to_string(temp_crop_path, config=config).strip()
            extracted_data[cls] = text
        except Exception as e:
            extracted_data[cls] = f"Error: {str(e)}"
        
        # Clean up temporary file
        if os.path.exists(temp_crop_path):
            os.remove(temp_crop_path)
    
    # Post-process the extracted data
    processed_data = post_process_extracted_data(extracted_data)
    
    # Convert to the structure of the first model's output
    result_json = convert_to_first_model_structure(processed_data)
    
    return result_json

def post_process_extracted_data(data):
    """
    Clean up and format the extracted data with strict rules for numeric fields
    """
    processed = {}
    
    # Process license number - ensure only numbers
    if "license_number" in data:
        # Extract only numbers from the license number
        numbers = re.sub(r'[^0-9]', '', data["license_number"])
        processed["license_number"] = numbers
    
    # Process contact number - ensure only numbers and + symbol
    if "contact_number" in data:
        processed["contact_number"] = re.sub(r'[^0-9+]', '', data["contact_number"])
    
    # Process name - remove "Name:" prefix but keep alphabetic characters
    if "name" in data:
        # Remove "Name:" or similar prefixes
        name = re.sub(r'^Name\s*:?\s*', '', data["name"], flags=re.IGNORECASE)
        processed["name"] = name.strip()
    
    # Process date of birth - ensure only numbers and separators
    if "dob" in data:
        # Extract date pattern (DD-MM-YYYY or similar)
        date_match = re.search(r'(\d{1,2})[-\s.]+(\d{1,2})[-\s.]+(\d{2,4})', data["dob"])
        if date_match:
            day, month, year = date_match.groups()
            # Format as DD-MM-YYYY to match first model format
            processed["dob"] = f"{day.zfill(2)}-{month.zfill(2)}-{year.zfill(4)}"
        else:
            # If no date pattern found, extract only numbers and format separators
            dob_digits = re.sub(r'[^0-9]', '', data["dob"])
            if len(dob_digits) >= 8:
                # Format as DD-MM-YYYY if we have at least 8 digits
                processed["dob"] = f"{dob_digits[:2]}-{dob_digits[2:4]}-{dob_digits[4:8]}"
            else:
                # Just keep the digits if we don't have enough
                processed["dob"] = dob_digits
    
    # Process citizenship number - ensure only numbers and hyphens
    if "citizenship_number" in data:
        # Remove "Citizenship No.:" or similar prefixes
        citizenship = re.sub(r'^(Citizenship\s+No\.?|Citizenship\s+Number)\s*:?\s*_?\s*', '', 
                             data["citizenship_number"], flags=re.IGNORECASE)
        
        # Extract only numbers and hyphens
        citizenship = re.sub(r'[^0-9\-]', '', citizenship)
        processed["citizenship_number"] = citizenship.strip()

    if "doi" in data:
        # Extract date pattern (DD-MM-YYYY or similar)
        date_match = re.search(r'(\d{1,2})[-\s.]+(\d{1,2})[-\s.]+(\d{2,4})', data["doi"])
        if date_match:
            day, month, year = date_match.groups()
            # Format as DD-MM-YYYY to match first model format
            processed["doi"] = f"{day.zfill(2)}-{month.zfill(2)}-{year.zfill(4)}"
        else:
            # If no date pattern found, extract only numbers and format separators
            doi_digits = re.sub(r'[^0-9]', '', data.get("doi", ""))
            if len(doi_digits) >= 8:
                # Format as DD-MM-YYYY if we have at least 8 digits
                processed["doi"] = f"{doi_digits[:2]}-{doi_digits[2:4]}-{doi_digits[4:8]}"
            else:
                # Just keep the digits if we don't have enough
                processed["doi"] = doi_digits

    if "doe" in data:
        # Extract date pattern (DD-MM-YYYY or similar)
        date_match = re.search(r'(\d{1,2})[-\s.]+(\d{1,2})[-\s.]+(\d{2,4})', data["doe"])
        if date_match:
            day, month, year = date_match.groups()
            # Format as DD-MM-YYYY to match first model format
            processed["doe"] = f"{day.zfill(2)}-{month.zfill(2)}-{year.zfill(4)}"
        else:
            # If no date pattern found, extract only numbers and format separators
            doe_digits = re.sub(r'[^0-9]', '', data.get("doe", ""))
            if len(doe_digits) >= 8:
                # Format as DD-MM-YYYY if we have at least 8 digits
                processed["doe"] = f"{doe_digits[:2]}-{doe_digits[2:4]}-{doe_digits[4:8]}"
            else:
                # Just keep the digits if we don't have enough
                processed["doe"] = doe_digits
    
    return processed

def convert_to_first_model_structure(processed_data):
    """
    Convert the processed data to match the structure of the first model's output
    """
    # Define the mapping between Roboflow class names and first model entity names
    mapping = {
        "license_number": "driving license number",
        "name": "name",
        "dob": "date of birth",
        "citizenship_number": "citizenship no",
        "contact_number": "contact no",
        "doi": "date of issue",
        "doe": "date of expiry"
    }
    
    # Create the structure expected by the first model
    result_json = {}
    
    for robo_key, first_key in mapping.items():
        if robo_key in processed_data:
            result_json[first_key] = {"text": processed_data[robo_key]}
        else:
            result_json[first_key] = {"text": "Not Found"}
    
    return result_json
