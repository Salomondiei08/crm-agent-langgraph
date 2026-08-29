"""Server-side OpenAI adapter for the optional real-model lesson mode."""
import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

CRM_ENV = Path(__file__).resolve().parents[2] / ".env"


def _load_environment() -> None:
    """Load the CRM environment without printing or copying secret values."""
    load_dotenv(CRM_ENV, override=False)


def _client() -> OpenAI:
    _load_environment()
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY_NOT_CONFIGURED")
    return OpenAI(api_key=os.environ["OPENAI_API_KEY"])


def classify_ticket_with_openai(ticket: str) -> str:
    """Ask OpenAI for one supported ticket category."""
    response = _client().responses.create(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        instructions="Classify support tickets. Reply with exactly one word: billing, technical, account, or other.",
        input=ticket,
        store=False,
    )
    category = response.output_text.strip().lower().split()[0]
    if category not in {"billing", "technical", "account", "other"}:
        raise RuntimeError(f"OPENAI_INVALID_CATEGORY:{category}")
    return category


def draft_reply_with_openai(ticket: str, category: str, context: str) -> str:
    """Ask OpenAI to draft a concise support reply from retrieved context."""
    response = _client().responses.create(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        instructions="Write a concise, helpful support reply. Do not claim an action was completed. Use the supplied policy.",
        input=f"Ticket: {ticket}\nCategory: {category}\nPolicy: {context}",
        store=False,
    )
    return response.output_text.strip()
