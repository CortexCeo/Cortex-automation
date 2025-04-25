from composer_agent.utils import validate_state
from .state import Artifact, ComposerState, TitleSchema
from .prompt import NEW_ARTIFACT_PROMPT, UPDATE_ENTIRE_ARTIFACT_PROMPT
from utils import gemini_flash, gemini_flash_thinking
from utils.logger_config import service_logger
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import SystemMessage, AIMessage, HumanMessage
from .prompt import TITLE_GENERATION_PROMPT
from .state import TitleSchema

def filter_messages(messages):
    initial_messages = [msg for msg in messages if isinstance(msg, (AIMessage, HumanMessage))]
    non_empty_messages = [msg for msg in initial_messages if msg.content != ""]
    return non_empty_messages

async def generate_artifact(
    state: ComposerState,
):
    service_logger.info("Generating artifact")
    system_instruction = SystemMessage(content=NEW_ARTIFACT_PROMPT)
    chat_prompt = ChatPromptTemplate.from_messages([
    system_instruction,
    MessagesPlaceholder(variable_name="conversation")
    ])
    formatted_messages = chat_prompt.format_messages(conversation=filter_messages(state.messages))
    service_logger.info(formatted_messages)
    response = await gemini_flash_thinking.ainvoke(formatted_messages)
    title_response = await gemini_flash.with_structured_output(TitleSchema).ainvoke(TITLE_GENERATION_PROMPT.format(artifact=response.content))
    artifact_dict = {}
    artifact_dict["artifact"] = response.content 
    artifact_dict["title"] = title_response.title
    artifact_dict["index"] = 1
    
    artifact = Artifact(
        current_index=1,
        contents=[artifact_dict]
    )
    service_logger.info(response.content)
    if not response:
        service_logger.error("No response found in response")
        raise Exception("No response found in response")

    state.artifact = artifact
    return state


async def rewrite_artifact(
    state: ComposerState,
):
    """Rewrites the artifact content using a language model."""
    service_logger.info("Rewriting artifact")
    validated_state = validate_state(state)
    current_artifact_content = validated_state["current_artifact_content"]
    recent_human_message = validated_state["recent_human_message"]

    formatted_prompt = UPDATE_ENTIRE_ARTIFACT_PROMPT.format(artifactContent=current_artifact_content)

    model_messages = [{"role": "system", "content": formatted_prompt}] + [recent_human_message]
    new_artifact_response = await gemini_flash_thinking.ainvoke(model_messages)    
    title_response = await gemini_flash.with_structured_output(TitleSchema).ainvoke(TITLE_GENERATION_PROMPT.format(artifact=new_artifact_response.content))
    new_artifact_dict = {}
    new_artifact_dict["artifact"] = new_artifact_response.content
    new_artifact_dict["title"] = title_response.title
    new_artifact_dict["index"] = state.artifact.current_index + 1
    service_logger.info(new_artifact_dict)
    state.artifact = Artifact(
        current_index=state.artifact.current_index + 1,
        contents=state.artifact.contents + [new_artifact_dict]
    )
    return state
