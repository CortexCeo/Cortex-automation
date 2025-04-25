from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.encoders import jsonable_encoder
from fastapi.responses import StreamingResponse
import logging
import json
from typing import Union, List
from pydantic import BaseModel

from api.pinecone import delete_document
from doc_extractor.doc_service import DocumentService
from interactor.indexer import index_file as index_file_interactor
from interactor.retriever import query_file as query_file_interactor
# Configure logging
logger = logging.getLogger(__name__)

api_router = APIRouter()

class QueryRequest(BaseModel):
    user_name: str
    project_id: str
    queries: Union[str, List[str]]

@api_router.post("/index")
async def index_file(
    user_name: str,
    project_id: str,
    file: UploadFile = File(...)
):
    """
    Index a file for a given project with streaming status updates
    
    Args:
        user_name: Name of the user (required)
        project_id: ID of the project (required)
        file: The file to be indexed
    """
    # Read file content immediately to prevent file handle issues
    file_content = await file.read()   
    
    async def status_stream():
        try:
            file_obj = {
                "filename": file.filename,
                "content": file_content,
                "content_type": file.content_type
            }
            async for status in index_file_interactor(file_obj, user_name, project_id):
                yield json.dumps(status) + "\n"
        except Exception as e:
            logger.error(f"Failed to index file: {e}")
            yield json.dumps({"status": "error", "message": str(e)}) + "\n"
    
    return StreamingResponse(status_stream(), media_type="application/x-ndjson")

@api_router.post("/query")
async def query_file(
    request: QueryRequest
):
    """
    Query a file for a given project with streaming updates
    
    Args:
        request: QueryRequest containing:
            - user_name: Name of the user
            - project_id: ID of the project
            - queries: Single query string or list of query strings
    """
    def query_stream():
        for status in query_file_interactor(user_name=request.user_name, query=request.queries, project_id=request.project_id):
            yield json.dumps(status) + "\n"
    
    return StreamingResponse(query_stream(), media_type="application/x-ndjson")

# @api_router.get("/documents/all")
# async def get_all_documents(user_id: str):
#     try:
#         logger.info("Retrieving all documents")
#         service = DocumentService()
#         documents = service.get_user_documents(user_id=user_id)
#         return jsonable_encoder(documents)
#     except Exception as e:
#         logger.error(f"Error retrieving documents: {e}")
#         raise HTTPException(
#             status_code=500,
#             detail=f"Error retrieving documents: {str(e)}"
#         )
        
@api_router.delete("/document/{document_id}")
async def delete_document_by_id(user_id: str, project_id: str, document_id: str):
    try:
        logger.info(f"Deleting document with ID: {document_id}")
        service = DocumentService()
        document = service.get_document_by_id(document_id)
        delete_document(user_id, project_id, document.document_ids)
        service.delete_document_by_id(document_id)
        return {"message": "Document deleted successfully"}
    except Exception as e:
        logger.error(f"Error deleting document: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error deleting document: {str(e)}"
        )