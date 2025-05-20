import google.generativeai as genai
from PIL import Image
import os
import fitz  # PyMuPDF for handling PDFs
import tempfile
import time

# Replace with your actual Gemini API key
API_KEY = "AIzaSyANLa1avWZm2_fOFqVdTMwM9n8ZXrclA10"
genai.configure(api_key=API_KEY)

# Initialize the Gemini model
model = genai.GenerativeModel("gemini-1.5-flash")

# Function to extract text from PDF
def extract_text_from_pdf(pdf_path, output_file="text.txt", extract_tamil=True):
    try:
        # Verify the PDF file exists
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found at: {pdf_path}")
        
        # Open the PDF
        pdf_document = fitz.open(pdf_path)
        all_text = ""
        
        # Two approaches: direct text extraction or OCR via Gemini for complex PDFs
        
        # First try direct extraction
        print(f"PDF has {len(pdf_document)} pages. Extracting text...")
        for page_num in range(len(pdf_document)):
            page = pdf_document[page_num]
            text = page.get_text()
            
            # If we got text and don't need specialized Tamil extraction
            if text.strip() and not extract_tamil:
                all_text += f"\n--- Page {page_num + 1} ---\n{text}\n"
            
            # If Tamil extraction is needed or no text was found via direct extraction
            # (indicating it might be an image-based PDF), use Gemini API
            else:
                print(f"Using Gemini OCR for page {page_num + 1}...")
                # Get image from page
                pix = page.get_pixmap()
                
                # Create a unique temp file in a way that works better on Windows
                temp_img_path = os.path.join(tempfile.gettempdir(), f"pdf_page_{page_num}_{int(time.time())}_{os.getpid()}.png")
                pix.save(temp_img_path)
                
                try:
                    # Process with Gemini
                    image = Image.open(temp_img_path)
                    
                    prompt = "Extract all text from the provided image."
                    if extract_tamil:
                        prompt = "Extract all Tamil text from the provided image. Preserve the original order of the text as it appears. If any English words are present within parentheses (e.g., (spine)), retain them in English without translation. Otherwise, extract only Tamil text. At the end of each page, append [x] to indicate a page break."
                    
                    response = model.generate_content([prompt, image])
                    page_text = response.text.strip()
                
                finally:
                    # Close the image first
                    if 'image' in locals():
                        image.close()
                    
                    # Wait a moment to ensure the file is released
                    time.sleep(0.1)
                    
                    # Try to delete the temp file, but don't fail if we can't
                    try:
                        os.remove(temp_img_path)
                    except Exception as e:
                        print(f"Warning: Could not delete temporary file {temp_img_path}: {e}")
                        # Continue processing even if we can't delete the temp file
                
                all_text += f"\n--- Page {page_num + 1} ---\n{page_text}\n"
        
        # Save the extracted text
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(all_text)
        
        return f"Text successfully extracted from PDF and saved to {output_file}"
    
    except Exception as e:
        return f"Error processing PDF: {str(e)}"

# Keep the existing image extraction function
def extract_tamil_text(image_path, output_file="text.txt"):
    try:
        # Verify the image file exists
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image file not found at: {image_path}")

        # Open and load the image
        image = Image.open(image_path)

        # Define the prompt to extract Tamil text
        prompt = "Extract all Tamil text from the provided image. Return the Tamil text and if any English words are present, return them as English."

        # Send the image and prompt to the Gemini API
        response = model.generate_content([prompt, image])

        # Get the extracted text
        extracted_text = response.text.strip()

        # Check if any text was extracted
        if not extracted_text:
            return "No text found in the image."
        
        # Save the result to a file
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(extracted_text)
            
        return f"Extracted text successfully saved to {output_file}"

    except Exception as e:
        return f"Error processing image: {str(e)}"

if __name__ == "__main__":
    # Ask user what type of file they want to process
    file_type = input("Enter file type (pdf/image): ").lower().strip()
    
    if file_type == "pdf":
        pdf_path = input("Enter PDF file path: ")
        output_file = input("Enter output file name (default: extracted_text.txt): ") or "extracted_text.txt"
        
        # Ask if Tamil extraction is needed
        tamil_extraction = input("Is Tamil text extraction needed? (y/n): ").lower().strip() == 'y'
        
        result = extract_text_from_pdf(pdf_path, output_file, tamil_extraction)
        print(result)
    
    elif file_type == "image":
        image_path = input("Enter image file path: ")
        output_file = input("Enter output file name (default: text.txt): ") or "text.txt"
        
        result = extract_tamil_text(image_path, output_file)
        print(result)
    
    else:
        print("Invalid file type. Please enter 'pdf' or 'image'.")