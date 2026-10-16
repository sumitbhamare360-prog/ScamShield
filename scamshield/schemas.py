from __future__ import annotations
from typing import List, Optional, Tuple, Dict, Any
from pydantic import BaseModel, Field


class Evidence(BaseModel):
    rule_id: str
    reason: str
    severity: float = Field(ge=0.0, le=1.0)
    span: Optional[Tuple[int, int]] = None


class Message(BaseModel):
    text: str
    channel: str = Field(description="'sms' | 'whatsapp' | 'email' | 'unknown'")
    sender: Optional[str] = None
    subject: Optional[str] = None


class Extracted(BaseModel):
    masked_text: str
    urls: List[str] = Field(default_factory=list)
    phones: List[str] = Field(default_factory=list)
    upi_ids: List[str] = Field(default_factory=list)
    amounts: List[str] = Field(default_factory=list)
    display_name: Optional[str] = None
    sender_domain: Optional[str] = None
    reply_to_domain: Optional[str] = None


class CheckResult(BaseModel):
    name: str
    score: Optional[float] = Field(default=None, ge=0.0, le=100.0)
    weight: float
    status: str = Field(description="'ok' | 'not_applicable' | 'not_checked' | 'error'")
    evidence: List[Evidence] = Field(default_factory=list)
    detail: str = ""


class Verdict(BaseModel):
    score: int
    category: str
    confidence: str = Field(description="'high' | 'medium' | 'low'")
    confidence_note: str
    scam_type: str
    uncertain: bool
    model_agreement: Optional[float] = None
    highlights: List[Dict[str, Any]] = Field(default_factory=list)
    checks: Dict[str, CheckResult] = Field(default_factory=dict)
    actions: List[str] = Field(default_factory=list)
    report_text: str
    scan_id: Optional[int] = None
