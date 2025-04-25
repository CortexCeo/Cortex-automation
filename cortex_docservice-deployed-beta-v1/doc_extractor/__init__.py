from langchain_core.documents import Document
from doc_extractor.feature_extractor import generate_document_description, generate_document_features
from doc_extractor.models import DocumentFeatures
from doc_extractor.parser.gemini_parser import GeminiDocumentParser
import re
from typing import List

class ParserException(Exception):
    """Exception raised when parsing document content fails."""
    pass

class DocumentException(Exception):
    """Exception raised when document extraction fails."""
    pass

from .parser import parser


class DocExtractor:
    def __init__(self):
        self.llama_parser = parser
        
    def split_docs_by_separator(self, parsed_results, separator="\n---\n"):
        """Split docs into sub-documents based on a separator."""
        sub_docs = []
        doc_chunks = parsed_results.split(separator)
        for doc_chunk in doc_chunks:
            sub_doc = Document(
                page_content=doc_chunk,
                metadata={}
            )
            sub_docs.append(sub_doc)

        return sub_docs
    
    def word_count(self, text: str) -> int:
        return len(text.split())
    
    def parse_chunks_to_documents(self, parsed_input: str) -> List[Document]:
        chunks = re.findall(r'<chunk>(.*?)</chunk>', parsed_input, re.DOTALL)
        merged_chunks = []

        for chunk in chunks:
            cleaned_chunk = re.sub(r'```html|```', '', chunk).strip()

            if self.word_count(merged_chunks[-1]) < 250 if merged_chunks else False:
                merged_chunks[-1] += "\n" + cleaned_chunk
            else:
                merged_chunks.append(cleaned_chunk)

        documents = [Document(page_content=chunk) for chunk in merged_chunks]

        return documents

    def parse_from_gemini(self, file):
        gemini_parser = GeminiDocumentParser(file)
        parsed_data = gemini_parser.read_and_parse_document()
        return self.parse_chunks_to_documents(parsed_data)
    
    async def parse_from_llamaparser(self, file):
        parsed_data = await self.llama_parser.load_data(file)
        if "parsed_content" not in parsed_data:
                raise ParserException(f"Parsing failed {parsed_data['details']}")
            
        parsed_text = parsed_data["parsed_content"]
        docs = self.split_docs_by_separator(parsed_text)
        return docs
    
    async def extract_text(self, file):
        if file['content_type'] == 'application/pdf':
            parsed_chunks = self.parse_from_gemini(file)
            return parsed_chunks
        else:
            parsed_chunks = await self.parse_from_llamaparser(file)
            return parsed_chunks
      
    async def extract(self, file):
        try:
            chunks = await self.extract_text(file)
            return chunks
        except ParserException:
            raise
        except Exception as e:
            raise DocumentException(f"Failed to extract text: {str(e)}")
