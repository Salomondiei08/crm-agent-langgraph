from lab.graph import Command, build_graph

def test_technical_ticket_completes_without_interrupt():
    graph = build_graph()
    result = graph.invoke({"ticket": "The app shows an error", "events": []}, {"configurable": {"thread_id": "technical"}})
    assert result["category"] == "technical"
    assert result["final_reply"]
    assert "human_decision" not in " ".join(result["events"])

def test_billing_ticket_pauses_and_resumes():
    graph = build_graph(); config = {"configurable": {"thread_id": "billing"}}
    paused = graph.invoke({"ticket": "I was charged twice", "events": []}, config)
    assert "__interrupt__" in paused
    result = graph.invoke(Command(resume="approve"), config)
    assert result["approved"] is True
    assert result["final_reply"]

def test_checkpoint_keeps_thread_state():
    graph = build_graph(); config = {"configurable": {"thread_id": "memory"}}
    graph.invoke({"ticket": "I cannot login", "events": []}, config)
    snapshot = graph.get_state(config)
    assert snapshot.values["category"] == "account"
