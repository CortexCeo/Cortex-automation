from cortex_agent.graph import run_cortex

class Chat:
    def __init__(self):
        pass
    
    @staticmethod
    async def stream_chat_payload(message_content: str, user_id: str, project_id: str, conversation_id: str):
        """Process a chat message and stream the response."""
        inputs = {"messages": [message_content]}
        config = {"configurable": {"thread_id": conversation_id, "user_id": user_id, "project_id": project_id}}
        async for partial_result in run_cortex(inputs, config):
            yield partial_result
