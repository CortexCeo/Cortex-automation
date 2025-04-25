from dotenv import load_dotenv
import os
import logging
import httpx
import asyncio

# Configure logging
logger = logging.getLogger(__name__)

load_dotenv()

class LLAMAPARSER:
    """
    A static class for parsing documents and queries.
    """
    
    @staticmethod
    async def load_data(file_obj):
        logger.info(f"Uploading file {file_obj['filename']} to LlamaParse")
        llama_url = "https://api.cloud.llamaindex.ai/api/parsing/upload"
        headers = {
            "Authorization": f"Bearer {os.getenv('LLAMAPARSER_API_KEY')}",
            "accept": "application/json",
        }
        files = {
            "file": (file_obj['filename'], file_obj['content'], file_obj['content_type']),
            "result_type": "markdown"
        }

        async with httpx.AsyncClient() as client:
            try:
                job_id = await LLAMAPARSER._upload_file(client, llama_url, headers, files, file_obj['filename'])
                await LLAMAPARSER._poll_job(client, job_id, headers, file_obj['filename'])
                parsed_content = await LLAMAPARSER._retrieve_result(client, job_id, headers, file_obj['filename'])
                return {"message": "File processed successfully", "parsed_content": parsed_content}
            except Exception as e:
                return LLAMAPARSER._handle_exception(e, file_obj['filename'])

    @staticmethod
    async def _upload_file(client, url, headers, files, filename):
        response = await client.post(url, headers=headers, files=files)
        response.raise_for_status()
        result = response.json()
        job_id = result.get("id")
        if not job_id:
            raise ValueError("No job ID returned from LlamaParse")
        logger.info(f"File {filename} uploaded successfully with job ID {job_id}")
        return job_id

    @staticmethod
    async def _poll_job(client, job_id, headers, filename):
        status_url = f"https://api.cloud.llamaindex.ai/api/parsing/job/{job_id}"
        while True:
            status_response = await client.get(status_url, headers=headers)
            status_response.raise_for_status()
            status_result = status_response.json()
            status = status_result.get("status")

            if status == "SUCCESS":
                logger.info(f"Parsing completed for job ID {job_id}")
                break
            elif status == "FAILED":
                logger.error(f"Parsing failed for job ID {job_id}")
                raise ValueError("Parsing failed")
            
            logger.info(f"Parsing in progress for job ID {job_id}. Retrying in 2 seconds...")
            await asyncio.sleep(2)

    @staticmethod
    async def _retrieve_result(client, job_id, headers, filename):
        result_url = f"https://api.cloud.llamaindex.ai/api/parsing/job/{job_id}/result/markdown"
        result_response = await client.get(result_url, headers=headers)
        result_response.raise_for_status()
        parsed_content = result_response.json().get("markdown", "")
        return parsed_content

    @staticmethod
    def _handle_exception(e, filename):
        if isinstance(e, httpx.HTTPStatusError):
            logger.error(f"HTTP error occurred while processing {filename}: {e.response.text}")
            return {"error": "HTTP error occurred", "details": e.response.text}
        else:
            logger.error(f"An error occurred while processing {filename}: {str(e)}")
            return {"error": "An error occurred", "details": str(e)}

    def __new__(cls):
        logger.warning("Attempted to instantiate static class Parser")
        raise NotImplementedError("Cannot instantiate a static class")

# Example usage
# documents = Parser.load_documents("../data/kag_paper.pdf")
# Parser.store_parsed_document(parsed_data, "parsed_document", "./parsed_docs")
