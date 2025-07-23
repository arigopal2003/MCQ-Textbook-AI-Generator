import os
import fitz  # PyMuPDF
import re
import json

# === CONFIG ===
chapter_folder = 'chapters'  # Folder where PDFs are placed
output_json_file = 'final_output.json'
content_txt_file = 'content.txt'

all_mcqs = []
question_global_no = 1
content_dump = ""

def extract_mcqs(text, chapter_name):
    global question_global_no
    extracted = []

    # Find MCQ blocks between "Choose the correct answer" and next section
    mcq_blocks = re.finditer(
        r"(?i)(choose the correct answer)(.*?)(?=(fill in the blanks|$))",
        text,
        re.DOTALL
    )

    for block in mcq_blocks:
        mcq_block = block.group(2)
        
        # Split into individual MCQs
        mcq_items = re.findall(r"(\d+[\)\.]\s*(.*?))(?=\n\d+[\)\.]|\Z)", mcq_block, re.DOTALL)

        for item in mcq_items:
            full_question = item[0]
            # Extract question text
            q_match = re.search(r"\d+[\)\.]\s*(.*?)(?=\s+[aA][\)\.])", full_question, re.DOTALL)
            
            # Extract options
            options = re.findall(r"([a-dA-D][\)\.]\s*(.*?)(?=\s+[a-dA-D][\)\.]|\Z))", full_question, re.DOTALL)
            
            if q_match and len(options) >= 4:
                question_text = q_match.group(1).replace('\n', ' ').strip()
                
                # Format options uniformly
                options_clean = [
                    f"({chr(97+i).lower()}) {opt[1].strip()}" 
                    for i, opt in enumerate(options[:4])  # Take first 4 options
                ]
                
                extracted.append({
                    "chapter": chapter_name,
                    "question_no": question_global_no,
                    "question": question_text,
                    "options": options_clean
                })
                question_global_no += 1
            else:
                print(f"⚠️ Skipped malformed question in {chapter_name}:\n{item[0][:100]}...")

    return extracted

def process_chapters():
    global all_mcqs, content_dump
    
    if not os.path.exists(chapter_folder):
        print(f"❌ Folder '{chapter_folder}' not found!")
        return False

    pdf_files = sorted([f for f in os.listdir(chapter_folder) if f.lower().endswith('.pdf')])
    if not pdf_files:
        print("❌ No PDF files found in 'chapters/' folder.")
        return False

    for file in pdf_files:
        chapter_path = os.path.join(chapter_folder, file)
        chapter_name = os.path.splitext(file)[0]

        print(f"\n📘 Processing: {chapter_name}...")

        try:
            doc = fitz.open(chapter_path)
            chapter_text = ""
            
            # Extract text from each page
            for page in doc:
                chapter_text += page.get_text("text") + "\n"
            doc.close()

            # Store raw content for debugging
            content_dump += f"\n\n--- {chapter_name} ---\n\n{chapter_text}"

            # Extract MCQs
            mcqs = extract_mcqs(chapter_text, chapter_name)
            all_mcqs.extend(mcqs)
            print(f"✅ Extracted {len(mcqs)} MCQs from {chapter_name}")

        except Exception as e:
            print(f"❌ Error processing {file}: {str(e)}")
            continue
    
    return True

# === MAIN EXECUTION ===
if process_chapters():
    # Save raw text content
    with open(content_txt_file, 'w', encoding='utf-8') as txt_file:
        txt_file.write(content_dump)
    print(f"\n📄 Saved full text to '{content_txt_file}'")

    # Save MCQ data
    with open(output_json_file, 'w', encoding='utf-8') as json_file:
        json.dump(all_mcqs, json_file, indent=4, ensure_ascii=False)
    print(f"📦 Total MCQs extracted: {len(all_mcqs)}")
    print(f"📁 JSON saved to '{output_json_file}'")
else:
    print("❌ Processing failed. Please check the error messages.")