from langgraph.graph import StateGraph, START, END
from .state import ComposerState
from .tools import generate_artifact, rewrite_artifact
from langgraph.checkpoint.mongodb import AsyncMongoDBSaver
import os
from utils.logger_config import service_logger
from typing import Annotated
from langchain_core.tools import tool
from langgraph.prebuilt import InjectedState
from langchain_core.runnables import RunnableConfig

def generate_path(state: ComposerState):
    service_logger.info("Generating path")
    service_logger.info(state)
    
    if state.artifact is None:
        return "generate_artifact"
    else:
        return "rewrite_artifact"


composer_graph = StateGraph(ComposerState)

composer_graph.add_node("generate_artifact", generate_artifact)
composer_graph.add_node("rewrite_artifact", rewrite_artifact)

composer_graph.add_conditional_edges(START, generate_path)   
composer_graph.add_edge("generate_artifact", END)
composer_graph.add_edge("rewrite_artifact", END)

@tool("run_composer", description="Run the document/artifact composer and updater", return_direct=True)
async def run_composer(state: Annotated[dict, InjectedState], config: RunnableConfig):
    print("Inside run composer")
    thread_id = config["configurable"]["thread_id"]
    user_id = config["configurable"]["user_id"]
    conf = {"configurable": {"user_id": user_id, "thread_id": f"{thread_id}-composer",}}
    async with AsyncMongoDBSaver.from_conn_string(os.getenv("MONGODB_URI")) as checkpointer:
        app = composer_graph.compile(checkpointer=checkpointer)
        result = await app.ainvoke({"messages": state["messages"]}, conf)
        return result["artifact"]

async def run_composer_directly(inputs, config):
    print("Inside run composer")
    async with AsyncMongoDBSaver.from_conn_string(os.getenv("MONGODB_URI")) as checkpointer:
        app = composer_graph.compile(checkpointer=checkpointer)
        result = await app.ainvoke(inputs, config)
        return result["artifact"]
    
async def get_composer_state(config: RunnableConfig):
    async with AsyncMongoDBSaver.from_conn_string(os.getenv("MONGODB_URI")) as checkpointer:
        app = composer_graph.compile(checkpointer=checkpointer)
        state = await app.aget_state(config)
        return state.values
