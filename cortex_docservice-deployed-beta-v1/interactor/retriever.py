from typing import Union, List
from api.pinecone import retrieve_documents
from doc_extractor.doc_service import DocumentService
from interactor.prompt import COMPOSER_PROMPT
from langchain_core.prompts import PromptTemplate
from doc_extractor._utils import gemini_flash

def store_documents_as_key_value(retrieved_documents):
    document_dict = {}

    for doc, score in retrieved_documents:
        source = doc.metadata.get('source')
        if source not in document_dict:
            document_dict[source] = []
        
        document_dict[source].append(doc.page_content)

    # Combine chunks into a single string for each document and prepend the header
    for source in document_dict:
        document_dict[source] = '##### RETRIEVED TEXT FROM VECTORSTORE ####### ' + '---------------PAGE CHANGE-----------------'.join(document_dict[source])

    return document_dict   

def append_metadata_to_documents(document_dict, docservice: DocumentService):
    document_number = 1
    for source in document_dict:
        # Retrieve the document to get its metadata
        document = docservice.get_document_by_id(source)
        
        # Prepare the metadata string with labels
        metadata_string = (
            f"##### DOCUMENT {document_number} #######\n"
            f"##### DOCUMENT DESCRIPTION TO GET THE CONTEXT OF THE DOCUMENT TO WHICH THE RETRIEVED TEXT BELONGS TO #######\n"
            f"Document Name: {document.name}\n"
            f"Document Type: {document.document_type}\n"
            f"Document Description: {document.description}\n"
            f"Document Domain: {document.domain}\n"
        )
        
        # Append the metadata to the document content
        document_dict[source] = metadata_string + document_dict[source]
        document_number += 1
    return document_dict

def concatenate_all_documents(document_dict):
    # Join all document strings into a single string
    combined_document = ' '.join(document_dict.values())
    return combined_document

def query_file(user_name: str, project_id: str, query: Union[str, List[str]]):
    # Use the same working_dir as used in indexing
    # Convert single query to list for uniform handling
    queries = [query] if isinstance(query, str) else query
    docservice = DocumentService()
        
    try:
        for q in queries:
 
            yield {
                "type": "processing",
                "query": q
            }
            retrieved_documents = retrieve_documents(user_name, project_id, q)
            document_dict = store_documents_as_key_value(retrieved_documents)
            print(document_dict)
            document_dict = append_metadata_to_documents(document_dict, docservice)
            combined_document = concatenate_all_documents(document_dict)
            prompt = PromptTemplate.from_template(COMPOSER_PROMPT)
            formatted_prompt = prompt.format(context=combined_document, query=q)
            response_iterable = gemini_flash.stream(formatted_prompt)
            response = ""
            for chunk in response_iterable:
                print(chunk.content, end=' ', flush=True)
                response += chunk.content
                yield {
                    "type": "response-streaming",
                    "chunk" : chunk.content,
                }

            print("--------------------------------")
            yield {
                "type": "response",
                "query": q,
                "response" : response,
            }
                
    except Exception as e:
        yield {
            "type": "error",
            "message": str(e)
        }   

