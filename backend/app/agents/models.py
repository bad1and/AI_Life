from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
import uuid


class Emotion(BaseModel):
    pleasure: float = 0.5
    arousal: float = 0.5

    def get_icon(self) -> str:
        if self.pleasure > 0.7:
            return "😊"
        elif self.pleasure < 0.3:
            return "😢"
        return "😐"


class Agent(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    personality: str = "дружелюбный"
    mood: float = 0.5
    location: str = "общая зона"
    goal: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "personality": self.personality,
            "mood": self.mood,
            "location": self.location,
            "goal": self.goal,
            "created_at": self.created_at.isoformat()
        }


class Memory(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    agent_id: str
    content: str
    emotion: str
    timestamp: datetime = Field(default_factory=datetime.now)