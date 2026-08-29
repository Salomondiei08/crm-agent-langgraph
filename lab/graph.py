"""A deterministic LangGraph workflow designed for classroom exploration."""
import os
from typing import Literal
from typing_extensions import TypedDict
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt

Category = Literal["billing", "technical", "account", "other"]

class SupportState(TypedDict, total=False):
    ticket: str
    category: Category
    context: list[str]
    draft: str
    approved: bool
    final_reply: str
    events: list[str]

def append_event(state: SupportState, event: str) -> list[str]:
    return [*state.get("events", []), event]


def _contains_any(ticket: str, keywords: tuple[str, ...]) -> bool:
    """Return whether a ticket contains at least one classification keyword."""
    return any(keyword in ticket for keyword in keywords)


def _classify_text(ticket: str) -> Category:
    """Classify a ticket with transparent rules suitable for teaching."""
    if _contains_any(ticket, ("charged", "invoice", "payment", "refund")):
        return "billing"
    if _contains_any(ticket, ("error", "bug", "not working", "broken")):
        return "technical"
    if _contains_any(ticket, ("password", "profile", "login")):
        return "account"
    return "other"


def classify_ticket(state: SupportState) -> dict:
    if os.getenv("LANGGRAPH_USE_OPENAI", "false").lower() in {"1", "true", "yes"}:
        from .openai_runtime import classify_ticket_with_openai

        category = classify_ticket_with_openai(state["ticket"])
    else:
        category = _classify_text(state["ticket"].lower())
    return {"category": category, "events": append_event(state, f"classified:{category}")}

def route_after_classification(state: SupportState) -> str:
    return "retrieve_context"

def retrieve_context(state: SupportState) -> dict:
    knowledge = {
        "billing": "Billing policy: duplicate charges are investigated and refundable charges require review.",
        "technical": "Technical policy: collect the error message and affected device before escalation.",
        "account": "Account policy: identity-sensitive changes require the account owner.",
        "other": "General policy: acknowledge the request and ask for the missing details.",
    }
    return {"context": [knowledge[state["category"]]], "events": append_event(state, "context_retrieved")}

def draft_reply(state: SupportState) -> dict:
    if os.getenv("LANGGRAPH_USE_OPENAI", "false").lower() in {"1", "true", "yes"}:
        from .openai_runtime import draft_reply_with_openai

        draft = draft_reply_with_openai(state["ticket"], state["category"], state["context"][0])
    else:
        draft = f"Thanks for contacting support. I classified this as {state['category']}. {state['context'][0]}"
    return {"draft": draft, "events": append_event(state, "draft_created")}

def requires_human_review(state: SupportState) -> bool:
    return state["category"] in {"billing", "account"}

def review_or_finalize(state: SupportState) -> str:
    return "human_review" if requires_human_review(state) else "finalize"

def human_review(state: SupportState) -> dict:
    decision = interrupt({"type": "approval", "question": "Approve this support reply?", "draft": state["draft"]})
    return {"approved": decision == "approve", "events": append_event(state, f"human_decision:{decision}")}

def finalize(state: SupportState) -> dict:
    if state.get("approved", True) is False:
        reply = "I’m sorry, but this request needs additional verification before we proceed."
    else:
        reply = state["draft"]
    return {"final_reply": reply, "events": append_event(state, "finalized")}

def build_graph():
    builder = StateGraph(SupportState)
    builder.add_node("classify", classify_ticket)
    builder.add_node("retrieve_context", retrieve_context)
    builder.add_node("draft_reply", draft_reply)
    builder.add_node("human_review", human_review)
    builder.add_node("finalize", finalize)
    builder.add_edge(START, "classify")
    builder.add_conditional_edges(
        "classify",
        route_after_classification,
        {"retrieve_context": "retrieve_context"},
    )
    builder.add_edge("retrieve_context", "draft_reply")
    builder.add_conditional_edges(
        "draft_reply",
        review_or_finalize,
        {"human_review": "human_review", "finalize": "finalize"},
    )
    builder.add_edge("human_review", "finalize")
    builder.add_edge("finalize", END)
    return builder.compile(checkpointer=InMemorySaver())

def run_ticket(graph, ticket: str, thread_id: str = "demo-thread") -> dict:
    config = {"configurable": {"thread_id": thread_id}}
    result = graph.invoke({"ticket": ticket, "events": []}, config)
    if "__interrupt__" not in result:
        return result
    print(f"\nApproval required:\n{result['__interrupt__'][0].value['draft']}")
    decision = input("Decision (approve/reject): ").strip().lower()
    return graph.invoke(Command(resume=decision), config)

if __name__ == "__main__":
    print(build_graph().get_graph().draw_mermaid())
