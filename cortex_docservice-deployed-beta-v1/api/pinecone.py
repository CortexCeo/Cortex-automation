from pinecone import Pinecone, ServerlessSpec
from doc_extractor._utils import gemini_embeddings
from langchain_pinecone import PineconeVectorStore
import os

def get_pinecone_index(index_name: str):
    pinecone_client = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
    return pinecone_client.Index(index_name)

def index_documents(user_id: str, project_id: str, document_id: str, documents: list):
    # Initialize the embedding model
    embeddings = gemini_embeddings
    
    # Add 'source' metadata to each document
    for doc in documents:
        if 'metadata' not in doc:
            doc.metadata = {}
        doc.metadata['source'] = document_id

    # Connect to the existing Pinecone index
    index = get_pinecone_index('cortex-pinecone-index')

    # Create a PineconeVectorStore instance
    vectorstore = PineconeVectorStore(index=index, embedding=embeddings, namespace=f"{user_id}-{project_id}")

    # Add documents to the vector store
    vectorstore.add_documents(documents)
    
def delete_document(user_id: str, project_id: str, document_ids: list):
    print("Deleting document from Pinecone")
    print(f"Document IDs to delete: {document_ids}")
    print(f"User ID: {user_id}, Project ID: {project_id}")
    
    # Validate document_ids is a list of strings
    if not document_ids:
        print("Warning: Empty document_ids list provided, nothing to delete")
        return False
    
    # Ensure all IDs are strings
    document_ids = [str(doc_id) for doc_id in document_ids]
    
    try:
        index = get_pinecone_index('cortex-pinecone-index')
        namespace = f"{user_id}-{project_id}"
        print(f"Deleting from namespace: {namespace}")
        
        # Execute the delete operation
        index.delete(ids=document_ids, namespace=namespace)
        
        print(f"Successfully deleted {len(document_ids)} document(s) from Pinecone")
        return True
    except Exception as e:
        print(f"Error deleting documents from Pinecone: {str(e)}")
        # Re-raise the exception or handle it as needed
        raise
    
def retrieve_documents(user_id: str, project_id: str, query: str, top_k: int = 5):
    # Initialize the embedding model
    embeddings = gemini_embeddings
    # Connect to the existing Pinecone index
    index = get_pinecone_index('cortex-pinecone-index')

    print(f"Retrieving documents for user {user_id} and project {project_id}")
    # Create a Pinecone vector store instance
    vector_store = PineconeVectorStore(index=index, embedding=embeddings, namespace=f"{user_id}-{project_id}")

    # Perform a similarity search within the specified namespace
    results = vector_store.similarity_search_with_relevance_scores(query, k=top_k, namespace=f"{user_id}-{project_id}")

    return results  