# inference/inference_invoice_donut.py
from transformers import DonutProcessor, VisionEncoderDecoderModel
from PIL import Image
import torch
import re
import json

# Device
device = "cuda" if torch.cuda.is_available() else "cpu"

# Load Donut models (once)
cord_processor = DonutProcessor.from_pretrained("naver-clova-ix/donut-base-finetuned-cord-v2", use_fast=True)
cord_model = VisionEncoderDecoderModel.from_pretrained("naver-clova-ix/donut-base-finetuned-cord-v2").to(device)

docvqa_processor = DonutProcessor.from_pretrained("naver-clova-ix/donut-base-finetuned-docvqa", use_fast=True)
docvqa_model = VisionEncoderDecoderModel.from_pretrained("naver-clova-ix/donut-base-finetuned-docvqa").to(device)

def run_information_extraction(image_path):
    """Extract structured information from a document using Donut CORD and simplify it"""
    print("\nRunning Information Extraction...\n")

    image = Image.open(image_path).convert("RGB")
    pixel_values = cord_processor(image, return_tensors="pt").pixel_values.to(device)

    task_prompt = "<s_cord-v2>"
    decoder_input_ids = cord_processor.tokenizer(task_prompt, add_special_tokens=False, return_tensors="pt").input_ids.to(device)

    outputs = cord_model.generate(
        pixel_values,
        decoder_input_ids=decoder_input_ids,
        max_length=cord_model.decoder.config.max_position_embeddings,
        early_stopping=True,
        pad_token_id=cord_processor.tokenizer.pad_token_id,
        eos_token_id=cord_processor.tokenizer.eos_token_id,
        use_cache=True,
        num_beams=1,
        bad_words_ids=[[cord_processor.tokenizer.unk_token_id]],
        return_dict_in_generate=True,
        output_scores=True,
    )

    sequence = cord_processor.batch_decode(outputs.sequences)[0]
    sequence = sequence.replace(cord_processor.tokenizer.eos_token, "").replace(cord_processor.tokenizer.pad_token, "")
    sequence = re.sub(r"<.*?>", "", sequence, count=1).strip()

    try:
        parsed = cord_processor.token2json(sequence)
    except Exception as e:
        print("Failed to parse sequence:", e)
        parsed = {"text_sequence": sequence}

    # Simplify the parsed data into a concise JSON structure
    simplified_data = {
        "invoice_number": "",
        "merchant_name": "",
        "buyer_name": "",
        "subtotal": "",
        "tax": "",
        "total": ""
    }

    # Extract relevant fields from parsed data
    if "menu" in parsed:
        for item in parsed["menu"]:
            if "nm" in item:
                # Invoice Number (assuming PAN or similar identifier)
                if item["nm"].startswith("PAN:"):
                    simplified_data["invoice_number"] = item["nm"].replace("PAN: ", "")
                # Merchant Name (assuming school/business name)
                elif "School" in item["nm"] or "Nepal" in item["nm"]:
                    simplified_data["merchant_name"] = item["nm"]
                # Buyer Name (assuming name field)
                elif item["nm"].startswith("Name:"):
                    simplified_data["buyer_name"] = item["nm"].replace("Name: ", "")

    if "sub_total" in parsed:
        simplified_data["subtotal"] = parsed["sub_total"].get("subtotal_price", "")

    if "sub_total" in parsed and "tax_price" in parsed["sub_total"]:
        simplified_data["tax"] = parsed["sub_total"]["tax_price"]
    else:
        simplified_data["tax"] = "0.00"  # Default if no tax is found

    if "total" in parsed:
        simplified_data["total"] = parsed["total"].get("total_price", "")

    print("Simplified Extracted Info:")
    print(json.dumps(simplified_data, indent=4))
    return simplified_data

# inference/inference_invoice_donut.py
def run_docvqa(image_path, question):
    """Answer a question from a document using Donut DocVQA"""
    print("\nRunning Information Q/A...\n")

    image = Image.open(image_path).convert("RGB")
    pixel_values = docvqa_processor(image, return_tensors="pt").pixel_values.to(device)

    task_prompt = f"<s_docvqa><s_question>{question}</s_question><s_answer>"
    decoder_input_ids = docvqa_processor.tokenizer(task_prompt, add_special_tokens=False, return_tensors="pt").input_ids.to(device)

    # Generate token IDs
    with torch.no_grad():
        outputs = docvqa_model.generate(
            pixel_values,
            decoder_input_ids=decoder_input_ids,
            max_length=64,
            pad_token_id=docvqa_processor.tokenizer.pad_token_id,
            eos_token_id=docvqa_processor.tokenizer.eos_token_id,
            use_cache=True,
            num_beams=1,
            bad_words_ids=[[docvqa_processor.tokenizer.unk_token_id]],
        )

    # Decode the tensor directly
    sequence = docvqa_processor.batch_decode(outputs)[0]
    sequence = sequence.replace(docvqa_processor.tokenizer.eos_token, "").replace(docvqa_processor.tokenizer.pad_token, "")
    sequence = re.sub(r"<.*?>", "", sequence).strip()

    # Extract only the answer (remove the question part)
    answer_start = sequence.find(question) + len(question) if question in sequence else 0
    answer = sequence[answer_start:].strip()

    print(f"Answer: {answer}")
    return answer