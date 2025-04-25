from pydantic import BaseModel, Field
from typing import List
from langchain_core.documents import Document
from langchain_core.prompts import PromptTemplate
from doc_extractor._utils import gemini_flash
from doc_extractor.models import DocumentFeatures, DocumentDescription

from google import genai
from google.genai import types
import os

def generate_document_description(file_obj):
    
    if file_obj['content_type'] == 'application/pdf':
        client = genai.Client(api_key=os.getenv('GEMINI_API_KEY_BETA'))

        prompt = """
        Act as a PhD-level scientist, demonstrating rigorous analytical thinking, precision, and thoroughness in your approach. 
Your queries should reflect deep academic insight, mastery of foundational principles, and meticulous attention to detail. 
Ensure your approach is methodical and scholarly, designed to uncover nuanced insights, verify assumptions, and uphold 
academic standards of research quality.

        Generate a description of document which give an idea of what are the various sections in the document and what is it that the document 
        discusses in brief, walkthrough the document in your comprehensive description. this description will be later on used by you to decide
        whcih document the user is talking about. Give the output only as text and do not include any extra text.

        ###Description###
        """
        response = client.models.generate_content(
        model="gemini-2.0-flash-thinking-exp",
        contents=[
            types.Part.from_bytes(
                data=file_obj['content'],
                mime_type='application/pdf',
            ),
            prompt],)
        return response.text
    else:
        extracted_text = "\n".join([doc.page_content for doc in file_obj['extracted_text']])
        template = PromptTemplate(template="""Generate a description of document which give an idea of what are the various sections in the document and what is it that the document discusses in brief, walkthrough the document in your comprehensive description. this description will be later on used by you to decide whcih document the user is talking about. Give the output only as text and do not include any extra text.
        ###Document###
        {document}
        
        ###Description###""")
        response = gemini_flash.invoke(template.format(document=extracted_text))
        return response.content

prompt_template = PromptTemplate(
    template="""
    Act as a PhD-level scientist, demonstrating rigorous analytical thinking, precision, and thoroughness in your approach. 
    Your queries should reflect deep academic insight, mastery of foundational principles, and meticulous attention to detail. 
    Ensure your approach is methodical and scholarly, designed to uncover nuanced insights, verify assumptions, and uphold 
    academic standards of research quality.

    Look for actionable insights, key findings, and practical recommendations in the document.

    ###Document###
    {combined_text}
    """,
    input_variables=["combined_text"]
)

def generate_document_features(documents: List[Document], llm: any = gemini_flash) -> DocumentFeatures:
    """
    Combines a list of documents, sends them to the LLM with structured output instructions,
    and returns a DocumentFeatures object containing all the features defined in DocumentFeatures.
    
    Parameters:
        documents (List[Document]): List of documents to analyze.
        llm (any): An instantiated LLM (or any compatible model) from LangChain.
    
    Returns:
        DocumentFeatures: A structured output object with all the document features.
    """
    combined_text = "\n\n".join([doc.page_content for doc in documents])
    
    model = llm.with_structured_output(DocumentFeatures)
    formatted_prompt = prompt_template.format(combined_text=combined_text)
    response = model.invoke(formatted_prompt)
    return response


