from pydantic import BaseModel, Field
from typing import Annotated
from langgraph.graph.message import add_messages
from typing import List

class TitleSchema(BaseModel):
    title: str = Field(description="A short title to give to the artifact. Should be less than 5 words.")

class ShouldHandoff(BaseModel):
    should_handoff: bool = Field(default=False, description="Whether to handoff to the Cortex agent.")

class Artifact(BaseModel):
    current_index: int = Field(default=0, description="The current index of the artifact to generate.")
    contents: List[dict] = Field(default=[], description="The contents of the artifact to generate.")
    
class ComposerState(BaseModel):
    artifact: Artifact = Field(default=None, description="The artifacts to be rewritten.")
    recentHumanMessage: str = Field(default=None, description="The most recent human message to be used for rewriting the artifact.")
    messages: Annotated[list, add_messages]
    additionalContext: str = Field(default="", description="Additional context to be used for rewriting the artifact.")
    
