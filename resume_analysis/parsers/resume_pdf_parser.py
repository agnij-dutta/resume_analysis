import PyPDF2
import re
import io

def _clean_text(text: str) -> str:
        """Clean and normalize extracted text"""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters but keep basic punctuation
        text = re.sub(r'[^\w\s.,;:!?-]', '', text)
        
        # Normalize line endings
        text = text.replace('\r', '\n')
        text = re.sub(r'\n\s*\n+', '\n\n', text)
        
        return text.strip()


def _parse_resume_pdf(pdf_bytes: bytes) -> str:
    """Extract and clean text from PDF resume"""
    try:
        pdf_file = io.BytesIO(pdf_bytes)
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        
        # Clean extracted text
        text = _clean_text(text)
        print(text)
        return text
        
    except Exception as e:
        raise ValueError(f"Failed to parse PDF resume: {str(e)}")

# usecase

# with open('./demopdfs/resume.pdf', 'rb') as resumefile:
#      _parse_resume_pdf(resumefile.read())

