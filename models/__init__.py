"""
app/models/__init__.py

Importing this module guarantees every model class is registered on
Base.metadata - required by both create_all() and Alembic's
--autogenerate.
"""
from models.user import User
from models.profile import UserProfile, CareerProfile, HealthProfile, FinanceProfile
from models.conversation import Conversation, Message
from models.memory import UserMemory
from models.report import Report

__all__ = [
    "User",
    "UserProfile",
    "CareerProfile",
    "HealthProfile",
    "FinanceProfile",
    "Conversation",
    "Message",
    "UserMemory",
    "Report",
]
