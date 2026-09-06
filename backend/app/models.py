from datetime import datetime
from enum import Enum
from typing import Optional

from sqlmodel import JSON, Column, Field, SQLModel


class Verdict(str, Enum):
    below = "below"
    meeting = "meeting"
    exceeding = "exceeding"


class SessionStatus(str, Enum):
    in_progress = "in_progress"
    completed = "completed"


class AssessmentItemType(str, Enum):
    conversation_question = "conversation_question"
    practical_exercise = "practical_exercise"


class TurnDecision(str, Enum):
    continue_assessment = "continue"
    evaluate = "evaluate"


class Role(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    rubric: dict = Field(sa_column=Column(JSON))
    rubric_version: int = 1
    ladder: Optional[dict] = Field(default=None, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Person(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    display_name: str = Field(index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class Employee(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str


class AssessmentSession(SQLModel, table=True):
    __tablename__ = "session"

    id: Optional[int] = Field(default=None, primary_key=True)
    employee_id: Optional[int] = Field(default=None, foreign_key="employee.id")
    person_id: Optional[int] = Field(default=None, foreign_key="person.id")
    role_id: int = Field(foreign_key="role.id")
    rubric_version: Optional[int] = None
    selected_tier_id: Optional[str] = None
    selected_tier_name: Optional[str] = None
    role_title: Optional[str] = None
    next_tier_id: Optional[str] = None
    next_tier_name: Optional[str] = None
    selected_expectations: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    next_expectations: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    status: SessionStatus = Field(default=SessionStatus.in_progress)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None


class QAPair(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: int = Field(foreign_key="session.id")
    order: int
    item_type: AssessmentItemType = Field(default=AssessmentItemType.conversation_question)
    question: str
    answer: Optional[str] = None
    turn_decision: Optional[dict] = Field(default=None, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Evaluation(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: int = Field(foreign_key="session.id", unique=True)
    verdict: Verdict
    rationale: str
    recommendation: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class AIUsage(SQLModel, table=True):
    __tablename__ = "ai_usage"

    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: Optional[int] = Field(default=None, foreign_key="session.id")
    role_id: Optional[int] = Field(default=None, foreign_key="role.id")
    operation: str
    provider: str
    model: str
    input_tokens: int
    output_tokens: int
    created_at: datetime = Field(default_factory=datetime.utcnow)
