from tools.prompt import PROMPTS
from utils import gemini_flash, gemini_flash_thinking
from langchain_core.output_parsers import JsonOutputParser
from utils.logger_config import cortex_logger
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage

def format_conversation(messages, max_messages=5):
    """
    Formats LangChain messages into a structured string for prompt input.

    Parameters:
    - messages (list): List of LangChain message objects.
    - max_messages (int): Maximum number of recent messages to include.

    Returns:
    - str: Formatted conversation string.
    """
    formatted_messages = []
    
    for msg in messages[-max_messages:]:  # Consider only the most recent messages
        if isinstance(msg, HumanMessage):
            formatted_messages.append(f"User: {msg.content}")
        elif isinstance(msg, AIMessage):
            formatted_messages.append(f"AI: {msg.content}")
        elif isinstance(msg, SystemMessage):
            formatted_messages.append(f"System: {msg.content}")
        elif isinstance(msg, ToolMessage):
            # Tool messages usually contain a name and result from an external tool call
            tool_name = msg.name if hasattr(msg, "name") else "Unknown Tool"
            formatted_messages.append(f"Tool [{tool_name}]: {msg.content}")

    return "\n".join(formatted_messages) if formatted_messages else "No sufficient conversation history."

def table_operator(input_text):
    cortex_logger.info(f"input_text for table operator: {input_text}")
    prompt = PROMPTS["table_composer"].format(input_text=input_text)
    response = gemini_flash_thinking.invoke(prompt)
    parser = JsonOutputParser()
    return parser.parse(response.content)

def text_corpus_builder(messages):
    cortex_logger.info(f"messages for text corpus builder: {messages}")
    prompt = PROMPTS["text_corpus_builder"].format(recent_conversation_history=format_conversation(messages), user_intent=messages[-1].content)
    cortex_logger.info(f"prompt for text corpus builder: {prompt}")
    response = gemini_flash.invoke(prompt)
    cortex_logger.info(f"response for text corpus builder: {response.content}")
    return response.content


