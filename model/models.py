from pydantic import BaseModel, Field, RootModel
from typing import Optional, Dict, Any, List, Union
from enum import Enum


class Metadata(BaseModel):
    Summary:list[str] = Field(default_factory=list, description="List of summary points about the document.")
    Title: Optional[str] = None
    Author: Optional[str] = None
    DateCreated: Optional[str] = None
    LastModified: Optional[str] = None
    Publisher: Optional[str] = None
    Language: Optional[str] = None
    PageCount: Union[int, str, None] = None
    SentimentTone: Optional[str] = None
    

class ChangeFormat(BaseModel):
    Page: str
    Changes: str


class SummaryResponse(RootModel[list[ChangeFormat]]):
    pass


class PromptType(str, Enum):
    DOCUMENT_ANALYSIS = "document_analyzer_prompt"
    DOCUMENT_COMPARISON = "document_comparison_prompt"
    CONTEXTUALIZE_QUESTION = "contextualize_question"
    CONTEXT_QA = "context_qa"