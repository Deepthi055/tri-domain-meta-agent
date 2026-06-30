"""
app/schemas/report.py
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class ReportCreate(BaseModel):
    domain: str  # "career" | "health" | "finance" — which advisory report to generate
    conversation_id: Optional[str] = None  # if given, summarizes that conversation


class ReportOut(BaseModel):
    id: str
    report_name: str
    file_path: str
    generated_at: datetime

    class Config:
        from_attributes = True
