# utils/document_loader.py

from langchain_community.document_loaders import PyPDFLoader, TextLoader
def load_document(file_path: str) -> str:
    if file_path.endswith(".pdf"):
        loader = PyPDFLoader(file_path)
    else:
        loader = TextLoader(file_path)

    documents = loader.load()
    return "\n".join([doc.page_content for doc in documents])