from typing import TypedDict
from pydantic import BaseModel, Field
from typing_extensions import Annotated
import operator
    
class Subqueries(BaseModel):
    subqueries: list[str] = Field(description="a list of strings, each string is a subquery generated from the user query")

class FinalAnswer(BaseModel):
    final_answer: str = Field(description="a string, a detailed answer to the user query")

class CheckTable(BaseModel):
    check_table: bool = Field(description="a boolean, true if a table is required, false otherwise")

class OverallState(TypedDict):
    query: str
    subqueries: list[str]
    subquery_results: list[dict]
    final_answer: str
    enable_search: bool
    # show_table: bool
    table: list[dict]
    project_id: str
    user_id: str