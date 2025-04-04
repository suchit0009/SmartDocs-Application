from transformers import DonutProcessor, VisionEncoderDecoderModel
import torch
import re
from PIL import Image

# === Load the image ===
image_path = "/Users/suchit/Desktop/Invoice Inference/Shree Mahendra School.jpg"
image = Image.open(image_path).convert("RGB")  # ensure it's in RGB format

# === Load the processor and model ===
processor = DonutProcessor.from_pretrained("naver-clova-ix/donut-base-finetuned-docvqa")
model = VisionEncoderDecoderModel.from_pretrained("naver-clova-ix/donut-base-finetuned-docvqa")

# === Prepare the image ===
pixel_values = processor(image, return_tensors="pt").pixel_values

# === Define the task prompt (question) ===
question = "What is the school name?"
prompt = f"<s_docvqa><s_question>{question}</s_question><s_answer>"

decoder_input_ids = processor.tokenizer(prompt, add_special_tokens=False, return_tensors="pt")["input_ids"]

# === Send model to appropriate device ===
device = "cuda" if torch.cuda.is_available() else "cpu"
model.to(device)

# === Run the model inference ===
outputs = model.generate(
    pixel_values.to(device),
    decoder_input_ids=decoder_input_ids.to(device),
    max_length=model.decoder.config.max_position_embeddings,
    early_stopping=True,
    pad_token_id=processor.tokenizer.pad_token_id,
    eos_token_id=processor.tokenizer.eos_token_id,
    use_cache=True,
    num_beams=1,
    bad_words_ids=[[processor.tokenizer.unk_token_id]],
    return_dict_in_generate=True,
    output_scores=True
)

# === Decode the output ===
seq = processor.batch_decode(outputs.sequences)[0]
seq = seq.replace(processor.tokenizer.eos_token, "").replace(processor.tokenizer.pad_token, "")
seq = re.sub(r"<.*?>", "", seq, count=1).strip()  # Remove task start token like <s_docvqa>
print("Answer:", seq)
