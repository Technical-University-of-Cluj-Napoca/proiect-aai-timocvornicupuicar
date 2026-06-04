import os
from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma

load_dotenv()

def get_embeddings():
    from langchain_huggingface import HuggingFaceEmbeddings
    return HuggingFaceEmbeddings(
        model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    )

def build_index(documents: list[Document], persist_directory: str = "vectorstore") -> Chroma:
    """
    Splits legal documents into chunks, embeds them, and saves the vector store in ChromaDB.
    """

    chunk_size = 1200
    chunk_overlap = 120
    
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        separators=["\n\n", "\n", ". ", " ", ""]
    )
    
    print(f"Splitting {len(documents)} source documents into chunks...")
    chunks = text_splitter.split_documents(documents)
    print(f"Created {len(chunks)} chunks from the source documents.")

    for idx, chunk in enumerate(chunks):
        chunk.metadata["chunk_index"] = idx
        
    embeddings = get_embeddings()
    print("Initializing ChromaDB and building vector embeddings index...")
    
    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=persist_directory
    )
    
    print(f"ChromaDB index successfully built and saved to {persist_directory}/")
    return vectorstore
