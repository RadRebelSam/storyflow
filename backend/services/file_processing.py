import re
from fastapi import UploadFile, HTTPException
from pypdf import PdfReader
import io

async def parse_uploaded_file(file: UploadFile) -> str:
    """
    Parses an uploaded file (TXT, PDF, or SRT) and returns plain text.
    """
    filename = file.filename.lower()
    content = await file.read()
    
    if filename.endswith(".txt"):
        return content.decode("utf-8")
        
    elif filename.endswith(".pdf"):
        try:
            # Use io.BytesIO to wrap data for PdfReader
            pdf_file = io.BytesIO(content)
            reader = PdfReader(pdf_file)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            return text
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to parse PDF: {str(e)}")
            
    elif filename.endswith(".srt"):
        try:
            text_content = content.decode("utf-8")
            return clean_srt(text_content)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to parse SRT: {str(e)}")
            
    else:
        raise HTTPException(status_code=400, detail="Unsupported file format. Please upload .txt, .pdf, or .srt")

def clean_srt(srt_content: str) -> str:
    """
    Removes SRT timestamps and sequence numbers.
    """
    lines = srt_content.splitlines()
    cleaned_lines = []
    
    # Regex to identify timestamp lines: 00:00:01,000 --> 00:00:04,000
    timestamp_pattern = re.compile(r'\d{2}:\d{2}:\d{2},\d{3} --> \d{2}:\d{2}:\d{2},\d{3}')
    
    for line in lines:
        line = line.strip()
        # Skip empty lines
        if not line:
            continue
        # Skip numeric sequence identifiers (1, 2, 3...) - careful not to skip actual text numbers if they are alone
        # But in SRT, a line that is just a number usually precedes a timestamp.
        # A simple heuristic: if it's a number and the NEXT line is a timestamp (hard to check in single pass without index).
        # Alternatively, SRT structure is: Number \n Timestamp \n Text \n\n
        
        # Safe check: specific timestamp format
        if timestamp_pattern.match(line):
            continue
            
        # Skip standalone numbers that are likely indices? 
        # Making this strict might delete "100" from a speech.
        # Let's rely on the fact that indices usually come before timestamps.
        # If we removed the timestamp, the index is usually the line before. 
        # But iterating line by line is hard.
        
        # Better approach: Block processing.
        pass

    # Regex block replacement approach is safer for SRT
    # Remove sequence numbers and timestamps
    # Pattern: Digit(s) \n Timestamp --> Timestamp \n Text...
    
    # 1. Remove timestamps
    text = re.sub(r'\d{2}:\d{2}:\d{2},\d{3} --> \d{2}:\d{2}:\d{2},\d{3}', '', srt_content)
    
    # 2. Remove standalone numbers on their own lines (indices)
    text = re.sub(r'^\d+\s*$', '', text, flags=re.MULTILINE)
    
    # 3. Clean up extra newlines
    text = re.sub(r'\n+', '\n', text).strip()
    
    return text
