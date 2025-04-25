from bson import ObjectId
from pydantic import BaseModel, Field, field_serializer
from typing import List, Literal
    
class DocumentFeatures(BaseModel):
    summary: str = Field(description="A comprehensive summary of the document in 10-15 lines covering its core content and important sections.")
    highlights: List[str] = Field(description="Five key highlights from the document.")
    document_type: str = Field(description="A one-word descriptor indicating the type of document.")
    domain: str = Field(description="Construct a 2-3 lines of domain text from the document. This will be used to understand the domain of the document.")
    queries: List[str] = Field(description="A list of 5-10 example queries that are relevant to the document.")
    entity_types: List[str] = Field(description="A list of entity types that are relevant to the document.")

class DocumentDescription(BaseModel):
    description: List[str] = Field(description="""Generate a description of document which give an idea of what are the various sections in the document and what is it that the document discusses in brief, walkthrough the document in your comprehensive description. this description will be later on used by you to decide whcih document the user is talking about.""")
    
class Document(DocumentFeatures):
    id: ObjectId = Field(None, alias="_id")
    user_id: str
    project_id: str
    name: str
    status: Literal["extracted", "completed"] = Field(default="extracted")
    
    @classmethod
    def from_features(cls, features: dict, user_id: str, project_id: str, name: str, status: Literal["extracted", "completed"], id: ObjectId = None) -> "Document":
        return cls(
            **features,
            user_id=user_id,
            project_id=project_id,
            name=name,
            status=status,
            id=id
        )

    @field_serializer("id")
    def serialize_objectid(self, v: ObjectId) -> str:
        return str(v)

    class Config:
        extra = "allow"
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: str
        }