from google import genai
from google.genai.types import Tool, GenerateContentConfig, GoogleSearch, DynamicRetrievalConfig, DynamicRetrievalConfigMode
from utils.logger_config import service_logger
import os

def google_search(query):
    query = query + " ## Search Instructions## Provide references with URLs. Give the most relevant information first. Do a thorough search and provide all the information you can find."
    # Initialize the client
    client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
    
    # Set the model ID
    model_id = "gemini-2.0-flash"
    
    # Create the Google Search tool
    google_search_tool = Tool(
        google_search=GoogleSearch()
    )
    
    # Generate content using the model
    response = client.models.generate_content(
        model=model_id,
        contents=query,
        config=GenerateContentConfig(
            tools=[google_search_tool],
            response_modalities=["TEXT"],
        )
    )
    # Print the response content
    final_response = ""
    for each in response.candidates[0].content.parts:
        final_response += each.text
    
    service_logger.info("google search response: ", final_response)
    return final_response
