import os
import sys
from dotenv import load_dotenv

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.tools.pdf_tools import load_corpus
from src.tools.vector_tools import build_index

load_dotenv()

def main():
    vectorstore_dir = "vectorstore"

    if os.path.exists(vectorstore_dir) and os.listdir(vectorstore_dir):
        print(f"Warning: Vectorstore directory '{vectorstore_dir}' already exists and is not empty.")
        print("To prevent duplicate embeddings, index building has been aborted.")
        print("If you want to rebuild the index, please delete the 'vectorstore/' folder first and run again.")
        sys.exit(0)
        
    print("No existing index found. Initializing index building process...")

    corpus_dir = "corpus"
    if not os.path.exists(corpus_dir):
        print(f"Error: Corpus directory '{corpus_dir}' does not exist.")
        print("Please run scripts/download_corpus.py first to collect reference documents.")
        sys.exit(1)

    print("Loading documents from corpus...")
    documents = load_corpus(corpus_dir)
    
    if not documents:
        print("Error: No documents loaded from the corpus. Please check your corpus files.")
        sys.exit(1)

    print(f"Loaded {len(documents)} documents. Starting index build...")
    build_index(documents, persist_directory=vectorstore_dir)
    print("Index build completed successfully!")

if __name__ == "__main__":
    main()
