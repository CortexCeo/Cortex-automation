from typing import Dict, List, Optional
from datetime import datetime
from pymongo import ReturnDocument
from utils.mongodb import MongoDBConfig
from cortex_service.models import Conversation, Message
from bson import ObjectId
from utils.logger_config import service_logger as logger

class ConversationService:
    
    def __init__(self):
        db_config = MongoDBConfig()
        self.db = db_config.connect()
        logger.info("ConversationService initialized and database connected.")

    def store_message(
        self,
        message: Message,
        user_id: str,
        project_id: str,
        conversation_id: Optional[str] = None,
    ) -> Conversation:
        logger.debug("Processing message for user_id: %s; conversation_id: %s", user_id, conversation_id)
        if conversation_id:
            logger.info("Updating conversation with id '%s' for user '%s'", conversation_id, user_id)
            # Directly update the conversation document without fetching it first.
            updated_doc = self.db["conversation"].find_one_and_update(
                {"_id": ObjectId(conversation_id)},
                {
                    "$push": {"messages": message.model_dump()},
                    "$set": {"last_updated": datetime.utcnow()},
                },
                return_document=ReturnDocument.AFTER,
            )
            if updated_doc is None:
                logger.error("Conversation with id '%s' not found", conversation_id)
                raise ValueError(f"Conversation with id '{conversation_id}' not found.")
            
            if hasattr(message, "table") and message.table is not None:
                updated_doc["output_table"] = message.table
            
            # updated_doc["_id"] = str(updated_doc["_id"])
            conversation = Conversation(**updated_doc)
        else:
            logger.info("Creating new conversation for user '%s'", user_id)
            # Create a new conversation document if no conversation_id is provided.
            conversation = Conversation(user_id=user_id, project_id=project_id, messages=[message])
            result = self.db["conversation"].insert_one(conversation.model_dump())
            conversation.id = result.inserted_id
        
        return conversation
    
    def get_user_conversations(self, user_id: str) -> List[Conversation]:
        """Retrieve all conversations for a specific user."""
        logger.info("Retrieving conversations for user_id: %s", user_id)
        # Query the database for conversations that match the given user_id.
        documents = self.db["conversation"].find({"user_id": user_id})
        conversations = [Conversation(**doc) for doc in documents]
        logger.info("Found %d conversations for user '%s'", len(conversations), user_id)
        return conversations
    
    def get_conversation(self, conversation_id: str) -> Conversation:
        """Retrieve a conversation by its conversation id."""
        logger.debug("Retrieving conversation with id: %s", conversation_id)
        # Note: There's an inconsistency in collection names ("conversation" vs "conversations"),
        # ensure that you use the correct one for your MongoDB configuration.
        document = self.db["conversation"].find_one({"_id": ObjectId(conversation_id)})
        if document is None:
            logger.error("Conversation with id '%s' not found", conversation_id)
            return False
            # raise ValueError(f"Conversation with id '{conversation_id}' not found.")
        logger.info("Conversation with id '%s' retrieved successfully", conversation_id)
        return Conversation(**document)

    def delete_conversation(self, conversation_id: str) -> bool:
        """Delete a conversation by its conversation id."""
        logger.debug("Deleting conversation with id: %s", conversation_id)
        result = self.db["conversation"].delete_one({"_id": ObjectId(conversation_id)})
        if result.deleted_count == 0:
            logger.error("Conversation with id '%s' not found", conversation_id)
            return False
        logger.info("Conversation with id '%s' deleted successfully", conversation_id)
        return True