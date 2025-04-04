import cv2
import pytesseract
import json
from inference_sdk import InferenceHTTPClient

def extract_passport_info(image_path):
    """Function to extract passport information from an image using Roboflow and Tesseract OCR"""
    
    # Initialize Roboflow client inside the function
    CLIENT = InferenceHTTPClient(
        api_url="https://detect.roboflow.com",
        api_key="5F6f0kVy4vHTtc2KEJUH"
    )

    # Load image
    image = cv2.imread(image_path)
    if image is None:
        raise FileNotFoundError(f"Image not found: {image_path}")

    # Roboflow detection
    print("Running Roboflow detection...")
    result = CLIENT.infer(image_path, model_id="passport-information-parsing/1")
    predictions = result['predictions']

    # Store Tesseract OCR results
    ocr_results = {}

    # Loop over predicted fields and extract text
    print("Extracting text from detected fields...")
    for pred in predictions:
        cls = pred['class']
        x, y, w, h = int(pred['x']), int(pred['y']), int(pred['width']), int(pred['height'])

        # Compute bounding box coordinates
        x1 = max(x - w // 2, 0)
        y1 = max(y - h // 2, 0)
        x2 = min(x + w // 2, image.shape[1])
        y2 = min(y + h // 2, image.shape[0])

        # Crop region
        crop = image[y1:y2, x1:x2]

        # Preprocess for better OCR
        gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        # Tesseract OCR config
        config = "--psm 7"
        if cls in ["passport_number", "dob", "date_of_issue", "date_of_expiry"]:
            config += " -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-/"

        # Run OCR
        text = pytesseract.image_to_string(binary, config=config).strip()
        ocr_results[cls] = text

    # Print final key-value result
    print("\nExtracted Passport Info (Tesseract OCR):")
    print(json.dumps(ocr_results, indent=4))

    return ocr_results

