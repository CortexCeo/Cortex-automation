from google.genai import types
from google import genai
from PyPDF2 import PdfReader, PdfWriter
import os
import io
import concurrent.futures

class GeminiDocumentParser:
    def __init__(self, file_obj):
        self.file_content = file_obj['content']
        self.mime_type = file_obj['content_type']
        self.client = genai.Client(api_key=os.getenv('GEMINI_API_KEY_BETA'))

    def process_pdf_chunk(self, pdf_bytes, prompt):
        print("processing pdf chunk")
        response = self.client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[
                types.Part.from_bytes(
                    data=pdf_bytes.getvalue(),
                    mime_type='application/pdf',
                ),
                prompt
            ]
        )
        print("finished processing pdf chunk")
        return response.text

    def process_text_chunk(self, wrapped_chunk, prompt):
        response = self.client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[
                types.Part.from_string(
                    data=wrapped_chunk,
                    mime_type=self.mime_type,
                ),
                prompt
            ]
        )
        return response.text

    def read_and_parse_document(self):
        prompt = """
        OCR the following content into Markdown. Tables should be formatted as HTML.
        Do not surround your output with triple backticks.

        Chunk the document into sections of roughly 250 - 1000 words. Our goal is 
        to identify parts of the document with the same semantic theme. These chunks will 
        be embedded and used in a RAG pipeline.

        Surround the chunks with <chunk> </chunk> HTML tags.
        """
        responses = []
        tasks = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            if self.mime_type == "application/pdf":
                reader = PdfReader(io.BytesIO(self.file_content))
                total_pages = len(reader.pages)
                if total_pages > 5:
                    for i in range(0, total_pages, 5):
                        writer = PdfWriter()
                        for j in range(i, min(i + 5, total_pages)):
                            writer.add_page(reader.pages[j])
                        pdf_bytes = io.BytesIO()
                        writer.write(pdf_bytes)
                        tasks.append(executor.submit(self.process_pdf_chunk, pdf_bytes, prompt))
                else:
                    pdf_bytes = io.BytesIO(self.file_content)
                    tasks.append(executor.submit(self.process_pdf_chunk, pdf_bytes, prompt))
                    
            elif self.mime_type in [
                "application/x-javascript", "text/javascript",
                "application/x-python", "text/x-python",
                "text/plain", "text/html", "text/css",
                "text/md", "text/csv", "text/xml", "text/rtf"
            ]:
                text_content = self.file_content.decode('utf-8', errors='replace')
                words = text_content.split()
                chunks = []
                current_chunk = []
                current_word_count = 0
                # Split into chunks of up to 1000 words.
                for word in words:
                    current_chunk.append(word)
                    current_word_count += 1
                    if current_word_count >= 1000:
                        chunks.append(" ".join(current_chunk))
                        current_chunk = []
                        current_word_count = 0
                if current_chunk:
                    chunks.append(" ".join(current_chunk))
                # Merge chunks smaller than 250 words with the previous chunk.
                merged_chunks = []
                for chunk in chunks:
                    word_count = len(chunk.split())
                    if merged_chunks and word_count < 250:
                        merged_chunks[-1] += " " + chunk
                    else:
                        merged_chunks.append(chunk)
                for chunk in merged_chunks:
                    wrapped_chunk = f"<chunk>\n{chunk}\n</chunk>"
                    tasks.append(executor.submit(self.process_text_chunk, wrapped_chunk, prompt))
            else:
                raise ValueError("Unsupported document type")
            # Gather results as they complete
            responses = [task.result() for task in tasks]
        return "\n".join(responses)