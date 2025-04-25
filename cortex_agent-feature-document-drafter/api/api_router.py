import json
from fastapi import APIRouter, HTTPException, Request, Depends
from fastapi.encoders import jsonable_encoder
from fastapi.responses import StreamingResponse
from cortex_service.conversation import ConversationService
from chat import Chat    
from cortex_service.models import Message
from utils.logger_config import service_logger as logger
from bson import ObjectId

# Custom JSON encoder to handle ObjectId serialization
class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        return super().default(obj)

api_router = APIRouter()

@api_router.post("/chat/stream")
async def stream_chat_api(request: Request):
    try:
        # Parse request body
        data = await request.json()
        user_id = data.get("user_id")
        project_id = data.get("project_id")
        conversation_id = data.get("conversation_id", "")
        message_content = data.get("message")
        print("user id", user_id)
        print("project id", project_id)
        print("conversation id", conversation_id)
        print("message", message_content)
        if not user_id or not project_id or not message_content:
            raise HTTPException(status_code=400, detail="Missing required parameters: user_id, project_id, or message")
        
        logger.info(f"SSE streaming connection established for user_id: {user_id} and project_id: {project_id}")
        
        if conversation_id:
            logger.info(f"Continuing streaming conversation with id: {conversation_id}")
        else:
            logger.info(f"Starting new streaming conversation for user_id: {user_id}")
        
        # Create a streaming response
        return StreamingResponse(
            stream_chat_content(user_id, project_id, conversation_id, message_content),
            media_type="text/event-stream"
        )
                
    except Exception as e:
        logger.error("Error in /chat/stream endpoint: %s", str(e))
        raise HTTPException(status_code=500, detail="Internal Server Error")

async def stream_chat_content(user_id: str, project_id: str, conversation_id: str, message_content: str):
    """Generate the SSE stream for chat content"""
    try:
        conversation_service = ConversationService()
        
        # Store user message
        message = Message(content=message_content, sender="user")
        conversation_id = conversation_service.store_message(message, user_id, project_id, conversation_id).id
        
        # Stream the response
        final_content = ""
        reasoning = []
        table = None
        logger.info(f"Streaming conversation with id: {conversation_id}")
        
        # Send initial event to confirm connection
        yield f"data: {json.dumps({'type': 'connected', 'conversation_id': conversation_id}, cls=CustomJSONEncoder)}\n\n"
        
        async for partial_result in Chat.stream_chat_payload(message_content, user_id, project_id, conversation_id):
            # Send each partial result as an SSE event
            yield f"data: {json.dumps({'type': 'stream', 'data': partial_result}, cls=CustomJSONEncoder)}\n\n"
            
            # Keep track of the final content if it's a response
            if partial_result.get("type") == "query":
                reasoning.append({"subquery": partial_result.get("content", "")})
            elif partial_result.get("type") == "response":
                reasoning[-1]["response"] = partial_result.get("content", "")
            elif partial_result.get("type") == "complete":
                final_content = partial_result.get("content", "")
                if partial_result.get("table"):
                    table = json.loads(partial_result.get("table", ""))
        
        # Store the final message in the conversation
        if final_content:
            message_kwargs = {
                "content": final_content,
                "sender": "cortex"
            }
            if table:
                message_kwargs["table"] = table
                
            if reasoning:
                message_kwargs["reasoning"] = reasoning
            
            final_message = Message(**message_kwargs)
            conversation_service.store_message(final_message, user_id, project_id, conversation_id)
        
        # Send a completion message
        yield f"data: {json.dumps({'type': 'finished', 'data': None}, cls=CustomJSONEncoder)}\n\n"
        
    except Exception as e:
        logger.error(f"Error in stream_chat_content: {str(e)}")
        yield f"data: {json.dumps({'type': 'error', 'data': str(e)}, cls=CustomJSONEncoder)}\n\n"

@api_router.get("/get/conversation")
async def get_conversation_api(conversation_id: str):
    try:
        service = ConversationService()
        conversation = service.get_conversation(conversation_id=conversation_id)
        if conversation:
            return {"conversation": jsonable_encoder(conversation)}
        else:
            # Return a clear 404 if the conversation is not found
            raise HTTPException(
                status_code=404,
                detail=f"Conversation with id '{conversation_id}' not found"
            )
    except Exception as e:
        logger.error("Error in /get/conversation endpoint: %s", str(e))
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/get/conversation/all")
async def get_all_conversations_api(user_id: str):
    try:
        service = ConversationService()
        conversations = service.get_user_conversations(user_id)
        return {"conversations": conversations}
    except Exception as e:
        logger.error("Error in /get/conversation/all endpoint: %s", str(e))
        raise HTTPException(status_code=500, detail=str(e))

@api_router.delete("/conversation/{conversation_id}")
async def delete_conversation_api(conversation_id: str):
    try:
        logger.info(f"Deleting conversation with id: {conversation_id}")
        service = ConversationService()
        success = service.delete_conversation(conversation_id=conversation_id)
        if success:
            return {"message": f"Conversation '{conversation_id}' deleted successfully"}
        else:
            raise HTTPException(
                status_code=404,
                detail=f"Conversation with id '{conversation_id}' not found"
            )
    except Exception as e:
        logger.error("Error in /conversation/{conversation_id} DELETE endpoint: %s", str(e))
        raise HTTPException(status_code=500, detail=str(e))