import cv2
import pytesseract
import json
from ultralytics import YOLO
import numpy as np
import re

def post_process_text(text, field_type):
    """
    Post-process OCR output to clean and format text based on the field type.

    Args:
        text (str): Raw OCR output.
        field_type (str): Type of field (e.g., 'passport_number', 'name', 'dob', 'nationality').

    Returns:
        str: Cleaned and formatted text.
    """
    text = text.strip()

    if field_type == "passport_number":
        # Expect format like PA0006877 (2 letters + 7 digits)
        text = text.upper()
        text = re.sub(r'[^A-Z0-9]', '', text)  # Keep only alphanumeric
        # Replace common misreads
        text = text.replace('O', '0').replace('S', '5').replace('I', '1').replace('E', '8').replace('G', '6')
        if len(text) >= 9:
            text = text[:9]  # Truncate to 9 characters
        # Validate: 2 letters + 7 digits
        if re.match(r'^[A-Z]{2}\d{7}$', text):
            return text
        return ""

    elif field_type in ["name-aw6u", "surname", "nationality"]:
        # Capitalize and keep only letters and spaces
        text = text.upper()
        text = re.sub(r'[^A-Z\s]', '', text)
        # Remove extra spaces
        text = " ".join(text.split())
        return text

    elif field_type == "dob":
        # Expect format like "23 APR 2003"
        text = text.upper()
        # Replace common misreads
        text = text.replace('O', '0').replace('S', '5')
        # Extract day, month, year
        match = re.match(r'(\d{1,2})\s*([A-Z]{3,})\s*(\d{4})', text)
        if match:
            day, month, year = match.groups()
            month = month[:3]  # Truncate to 3 letters (e.g., APRI -> APR)
            return f"{int(day):02d} {month} {year}"
        # Fallback: clean and try to format
        text = re.sub(r'[^A-Z0-9\s]', '', text)
        parts = text.split()
        if len(parts) >= 3:
            day = parts[0].zfill(2) if parts[0].isdigit() else "00"
            month = parts[1][:3] if len(parts[1]) >= 3 else parts[1]
            year = parts[-1] if parts[-1].isdigit() and len(parts[-1]) == 4 else "0000"
            return f"{day} {month} {year}"
        return ""

    return text

def extract_passport_info(image_path):
    """
    Extract passport information from an image using a custom YOLOv8 model and Tesseract OCR.
    Visualize detected bounding boxes with OpenCV to confirm model performance.

    Args:
        image_path (str): Path to the passport image.

    Returns:
        dict: JSON-compatible dictionary with Passport Number, Name, Nationality, and Date of Birth.
    """
    # Hardcode the model path
    model_path = "/Users/suchit/Desktop/YEAR 3/FYP/SmartDocs-Application copy/model/Passport/runs/detect/train/weights/best.pt"
    
    # Load the YOLOv8 model
    model = YOLO(model_path)

    # Load image
    image = cv2.imread(image_path)
    if image is None:
        raise FileNotFoundError(f"Image not found: {image_path}")
    
    # Create a copy for visualization
    annotated_image = image.copy()

    # Run YOLOv8 detection
    print("Running YOLOv8 detection...")
    results = model(image)[0]

    # Initialize dictionary for OCR results
    ocr_results = {}
    name_parts = []

    # Define desired attributes
    desired_attributes = {'citizenship_number', 'dob', 'document_type', 'name-aW6U', 'passport_number', 'surname'}

    # Visualize bounding boxes
    print("Drawing bounding boxes for visualization...")
    for box in results.boxes:
        cls_id = int(box.cls)
        cls_name = results.names[cls_id].lower()
        if cls_name not in desired_attributes:
            continue

        # Get bounding box coordinates
        x1, y1, x2, y2 = map(int, box.xyxy[0])
        x1, y1 = max(x1, 0), max(y1, 0)
        x2, y2 = min(x2, image.shape[1]), min(y2, image.shape[0])

        # Draw rectangle and label
        color = (0, 255, 0)
        cv2.rectangle(annotated_image, (x1, y1), (x2, y2), color, 2)
        label = f"{cls_name} ({float(box.conf):.2f})"
        cv2.putText(annotated_image, label, (x1, y1 - 10), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

    # Save annotated image
    output_path = image_path.rsplit(".", 1)[0] + "_annotated.jpg"
    cv2.imwrite(output_path, annotated_image)
    print(f"Annotated image saved to: {output_path}")

    # Process detections for OCR
    print("Extracting text from detected fields...")
    for box in results.boxes:
        cls_id = int(box.cls)
        cls_name = results.names[cls_id].lower()
        if cls_name not in desired_attributes:
            continue

        # Add padding to bounding box
        padding = 10
        x1, y1, x2, y2 = map(int, box.xyxy[0])
        x1, y1 = max(x1 - padding, 0), max(y1 - padding, 0)
        x2, y2 = min(x2 + padding, image.shape[1]), min(y2 + padding, image.shape[0])

        # Crop region
        crop = image[y1:y2, x1:x2]
        if crop.size == 0:
            continue

        # Minimal preprocessing: only convert to grayscale
        gray_crop = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)

        # Save crop for debugging
        crop_output_path = f"crop_{cls_name}.jpg"
        cv2.imwrite(crop_output_path, gray_crop)
        print(f"Crop for {cls_name} saved to: {crop_output_path}")

        # Tesseract OCR configuration
        config = "--psm 6"
        if cls_name == "passport_number":
            config = "--psm 8 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
        elif cls_name == "dob":
            config = "--psm 8 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ "
        elif cls_name in ["name-aw6u", "surname", "nationality"]:
            config = "--psm 6 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ "

        # Run OCR
        text = pytesseract.image_to_string(gray_crop, config=config).strip()

        # Post-process the OCR output
        text = post_process_text(text, cls_name)

        # Store result
        if cls_name == "passport_number":
            ocr_results["Passport Number"] = text
        elif cls_name == "dob":
            ocr_results["Date of Birth"] = text
        elif cls_name in ["name-aw6u", "surname"]:
            name_parts.append(text)
        elif cls_name == "nationality":
            ocr_results["Nationality"] = text

    # Combine name parts
    ocr_results["Name"] = " ".join(name_parts).strip() if name_parts else ""

    # Ensure all required attributes
    required_keys = ["Passport Number", "Name", "Nationality", "Date of Birth"]
    for key in required_keys:
        if key not in ocr_results:
            ocr_results[key] = ""

    # Print extracted info
    print("\nExtracted Passport Info:")
    print(json.dumps(ocr_results, indent=4))

    return ocr_results