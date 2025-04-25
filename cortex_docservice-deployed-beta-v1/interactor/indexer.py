import uuid
from doc_extractor import DocExtractor
from typing import AsyncGenerator, Dict, Any
from api.pinecone import index_documents
from doc_extractor.doc_service import DocumentService
from doc_extractor.feature_extractor import generate_document_description, generate_document_features
from doc_extractor.models import Document


async def index_file(file_obj: Dict[str, Any], user_name: str, project_id: str) -> AsyncGenerator[Dict[str, Any], None]:
    doc_extractor = DocExtractor()
    vector_document_ids = []
    yield {"status": "Reading", "message": "Reading document..."}
    chunks = await doc_extractor.extract(file_obj)
    yield {"status": "Understanding", "message": "Understanding document structure..."}
    features = generate_document_features(chunks)
    file_obj["extracted_text"] = chunks
    description = generate_document_description(file_obj)
    features = features.model_dump()
    features["description"] = description
    
    for chunk in chunks:
        doc_id = str(uuid.uuid4())
        chunk.id = doc_id
        vector_document_ids.append(doc_id)
        
    features["document_ids"] = vector_document_ids
    document = Document.from_features(features, user_name, project_id, file_obj["filename"], "extracted")
    doc_service = DocumentService()
    doc_service.insert_document(document)
    
    index_documents(user_name, project_id, document.id, chunks)    
    doc_service.update_status(document.id, "completed")
    
    yield {"status": "Completed", "message": "Document indexed successfully", "features": features}
    
    

    