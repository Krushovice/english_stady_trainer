import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.conversation import ConversationRole


class StartConversationRequest(BaseModel):
    topic: str | None = Field(default=None, max_length=200)


class SendConversationMessageRequest(BaseModel):
    text: str = Field(min_length=1, max_length=1000)


class ConversationMessageResponse(BaseModel):
    id: uuid.UUID
    role: ConversationRole
    content: str
    created_at: datetime


class ConversationAnalysisResponse(BaseModel):
    recurring_mistakes: str
    useful_vocabulary: str
    natural_alternatives: str
    grammar_topics_to_review: str
    recommended_practice: str


class ConversationSessionResponse(BaseModel):
    id: uuid.UUID
    topic: str | None
    started_at: datetime
    ended_at: datetime | None
    messages: list[ConversationMessageResponse]
    analysis: ConversationAnalysisResponse | None
