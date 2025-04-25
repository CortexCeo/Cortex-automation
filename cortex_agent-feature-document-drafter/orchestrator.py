import os
import asyncio
import datetime
from langgraph_swarm import create_swarm
from langgraph.checkpoint.mongodb import AsyncMongoDBSaver
from utils.logger_config import service_logger as logger
# Import components from your agents.
from composer_agent.graph import run_composer
from utils import gemini_flash
from cortex_agent.graph import (
    PROMPTS,
    internal_knowledge_search,
    internet_search,
)
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import SystemMessage
from langgraph_swarm import create_handoff_tool

async def main():
    
    handoff_tool = create_handoff_tool(
    agent_name="Composer",
    description="Transfer to Composer agent to answer the ones related to drafting/creating/editing/updating artifacts or documents",
    )   
    cortex = create_react_agent(
        name="Cortex",
        model=gemini_flash,
        tools=[internal_knowledge_search, internet_search, handoff_tool],
        prompt=SystemMessage(
            PROMPTS["cortex"].format(
                current_date_time=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )
        ),
        # checkpointer=checkpointer,
    )
    
    composer_handoff_tool = create_handoff_tool(
        agent_name="Cortex",
        description="Transfer to Cortex agent to answer the user's query which is not related to drafting/creating/editing/updating artifacts or documents",
    )
    
    composer = create_react_agent(
        name="Composer",
        model=gemini_flash,
        tools=[run_composer, composer_handoff_tool],
        prompt=SystemMessage(
            PROMPTS["composer"].format(current_date_time=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        ),
    )


    # Use a shared MongoDBSaver for the swarm.
    async with AsyncMongoDBSaver.from_conn_string(os.getenv("MONGODB_URI")) as checkpointer:
        # Create the swarm; here, "Composer" is set as the default active agent.
        swarm = create_swarm([composer, cortex], default_active_agent="Cortex")
        app = swarm.compile(checkpointer=checkpointer)

        # Example configuration and input message.
        config = {"configurable": {"user_id": "dipak-122", "thread_id": "15"}}
        inputs = {"messages": [{"role": "user", "content": "explain me the working of LLMs"}]}

        result = await app.ainvoke(inputs, config)
        print("Swarm invocation result:")
        print(result)

if __name__ == "__main__":
    asyncio.run(main())