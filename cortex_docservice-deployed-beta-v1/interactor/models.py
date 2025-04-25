from pydantic import BaseModel
from typing import List

class Entity(BaseModel):
    name: str
    description: str
    type: str
    score: float
    
class Relationship(BaseModel):
    source: str
    target: str
    description: str
    chunks: List[str]
    score: float
