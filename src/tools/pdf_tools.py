import os
import pdfplumber
from langchain_core.documents import Document

def load_corpus(corpus_dir: str) -> list[Document]:
    """
    Recursively scans the corpus directory, extracts text from PDF files,
    and returns a list of LangChain Document objects with basic metadata.
    """
    documents = []
    
    if not os.path.exists(corpus_dir):
        print(f"Corpus directory {corpus_dir} does not exist.")
        return documents
        
    for root, _, files in os.walk(corpus_dir):
        for file in files:
            if file.lower().endswith('.pdf'):
                file_path = os.path.join(root, file)
                relative_path = os.path.relpath(file_path, corpus_dir)
                
                try:
                    with pdfplumber.open(file_path) as pdf:
                        page_count = len(pdf.pages)
                        full_text = ""
                        
                        pdf_info = pdf.metadata or {}
                        title = pdf_info.get("Title") or os.path.splitext(file)[0].replace("_", " ").title()
                        
                        for i, page in enumerate(pdf.pages):
                            page_text = page.extract_text()
                            if page_text:
                                full_text += page_text + "\n"
                        
                        if not full_text.strip():
                            print(f"Warning: Extracted empty text from {file_path}")
                            continue
                            
                        doc = Document(
                            page_content=full_text,
                            metadata={
                                "source": file,
                                "relative_path": relative_path,
                                "title": title,
                                "page_count": page_count
                            }
                        )
                        documents.append(doc)
                        print(f"Loaded: {relative_path} ({page_count} pages)")
                except Exception as e:
                    print(f"Error reading PDF {file_path}: {e}")
                    
    print(f"Successfully loaded {len(documents)} documents from the corpus.")
    return documents
