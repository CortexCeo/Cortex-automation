import datetime
import json
import os
from pydantic import Field
from reasoning_agent import knowledge_engine
from cortex_agent.prompts import PROMPTS
from utils import gemini_flash
from langchain_core.tools import tool
from typing_extensions import Annotated
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import SystemMessage
from langgraph.checkpoint.mongodb import AsyncMongoDBSaver      
from utils.logger_config import cortex_logger
from tools.google_search import google_search
from langchain_core.messages import ToolMessage
from langchain_core.runnables import RunnableConfig
from cortex_service.document import DocumentService
from reasoning_agent.services import format_documents

InternalKnowledgeSearch = Annotated[str, Field(description="Search the internal knowledge base for the given query.")]
EnableSearch = Annotated[bool, Field(description="Enable the internet search tool and search the internet for the given query along with the internal knowledge search tool if the user has mentioned it in the query or else dont use the internet search tool.")]
GoogleSearchQuery = Annotated[str, Field(description="A relevant query to search the internet for relevant information")]

@tool(return_direct=True)
async def internal_knowledge_search(query: InternalKnowledgeSearch, enable_search: EnableSearch, config: RunnableConfig):
    """Search the internal knowledge base for the query."""
    user_id = config["configurable"]["user_id"]
    project_id = config["configurable"]["project_id"]
    print("user id in cortex agent", user_id)
    print("project id in cortex agent", project_id)

    result = ""
    async for s in knowledge_engine.astream({"query": query, "enable_search": enable_search, "user_id": user_id, "project_id": project_id} , stream_mode="updates"):
        if "final_answer" in s:
            result = s["final_answer"]
    return {"final_answer": result}

@tool   
async def internet_search(query: GoogleSearchQuery):
    """Search the internet for the query."""
    return google_search(query) 

@tool
async def get_user_documents_info(config: RunnableConfig):
    """Get user documents."""
    user_id = config["configurable"]["user_id"]
    project_id = config["configurable"]["project_id"]
    print("user id in cortex agent", user_id)
    print("project id in cortex agent", project_id)
    
    document_service = DocumentService()
    documents = document_service.get_user_documents(user_id, project_id)
    print("documents", documents)
    return format_documents(documents)



connection_kwargs = {
    "autocommit": True,
    "prepare_threshold": 0,
}

async def run_cortex(inputs, config):
    # manage_memory_tool = create_manage_memory_tool(namespace=("memories",f"{config['configurable']['user_id']}"))
    # search_memory_tool = create_search_memory_tool(namespace=("memories",f"{config['configurable']['user_id']}")) 
    async with AsyncMongoDBSaver.from_conn_string(os.getenv("MONGODB_URI")) as checkpointer:
        # async with AsyncPostgresStore.from_conn_string(
        # os.getenv("DB_URI"),
        # index={
        #     "dims": 768,
        #     "embed": gemini_embeddings,
        #     }
        # ) as store:
            cortex = create_react_agent(
                        model=gemini_flash,
                        tools=[internal_knowledge_search, internet_search, get_user_documents_info],
                        prompt=SystemMessage(PROMPTS["cortex"].format(current_date_time=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))),
                        checkpointer=checkpointer,
                        # store=store,
                    )

            async for s in cortex.astream(inputs, config, stream_mode="custom"):
                if "final-answer-streaming" in s:
                    yield {"type": "final-answer-streaming", "content": s["final-answer-streaming"]}
                elif "retriever_updates" in s:
                    if "response" in s["retriever_updates"]:
                        yield {"type": "response", "content": s["retriever_updates"]["response"]}
                    elif "query" in s["retriever_updates"]:
                        yield {"type": "query", "content": s["retriever_updates"]["query"]}
                    elif "type" in s["retriever_updates"] and s["retriever_updates"]["type"] == "response-streaming":
                        yield {"type": "response-streaming", "content": s["retriever_updates"]["chunk"]}
            
            state = await cortex.aget_state(config=config)
            cortex_logger.info(state.values)
            final_message = state.values["messages"][-1]
            
            if isinstance(final_message, ToolMessage):
                if final_message.name == "internal_knowledge_search":
                    content = json.loads(final_message.content)
                    yield {"type": "complete", "content": content["final_answer"]}
            else:
                yield {"type": "complete", "content": final_message.content}
