import asyncio

from app.services.llm_service import LLMService


def test_heuristic_extraction_normalizes_task_fields():
    service = LLMService()

    result = asyncio.run(service.extract_tasks("Иван, подготовь демо стенда до завтра"))

    assert result["has_task"] is True
    assert result["tasks"][0]["title"] == "подготовь демо стенда до завтра"
    assert result["tasks"][0]["assignee_raw"] == "Иван"
    assert result["tasks"][0]["deadline_raw"] == "до завтра"
    assert result["tasks"][0]["action"] == "create"
