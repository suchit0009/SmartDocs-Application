# SmartDocs

AI-powered document management system for automatic classification, information extraction, and visual question answering. 


## Demo Video

[📹 Watch Demo Video](https://youtu.be/jNIeMRsMjMQ)

## Features

- **Document Upload & Classification** - Automatically categorize documents (Licenses, Passports, Invoices, etc.)
- **Information Extraction** - Extract key data from documents 
- **Document Sharing** - Share documents with other users securely
- **Visual Question Answering** - Ask questions about document content
- **Interactive Dashboard** - Manage documents with grid/table views

## Models

- **LayoutLMv2** - Fine-tuned on custom dataset of License, Cheque, Passport, Invoice, and Resume documents for precise classification
- **Donut** - Pre-trained model fine-tuned on CORD dataset for OCR-free information extraction and DocVQA

## Installation

```bash
# Clone repository
git clone https://github.com/yourusername/smartdocs.git
cd smartdocs

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install transformers

# Run application
python manage.py runserver
```

Access at `http://localhost:8000`

## Usage

1. **Login** - Access the dashboard with your credentials
2. **Upload** - Click "Upload Document" to add files
3. **Share** - Share documents with other users from the dashboard
4. **View** - Browse classified documents in organized sections
5. **Manage** - Edit, delete, or query document content

## Project Structure

```
smartdocs/
├── accounts/          # User authentication & dashboard
├── documents/         # Document upload & management
├── sharing/           # Document sharing functionality
├── models/           # AI model scripts
├── static/           # CSS/JS files
└── requirements.txt  # Dependencies
```

## Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/name`)
3. Commit changes (`git commit -m "Add feature"`)
4. Push branch (`git push origin feature/name`)
5. Open pull request
