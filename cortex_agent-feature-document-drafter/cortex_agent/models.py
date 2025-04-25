from pydantic import BaseModel


class CortexState(BaseModel):
    query: str
    current_action: str
    current_timestamp: str
    messages: list[str]
    
