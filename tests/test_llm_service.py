import asyncio

from app.services.llm_service import LLMService


def test_heuristic_extraction_normalizes_task_fields():
    service = LLMService()

    result = asyncio.run(service.extract_tasks("Иван, подготовь демо стенда до завтра"))

    assert result["has_task"] is True
    assert result["tasks"][0]["title"] == "подготовь демо стенда"
    assert result["tasks"][0]["assignee_raw"] == "Иван"
    assert result["tasks"][0]["deadline_raw"] == "до завтра"
    assert result["tasks"][0]["action"] == "create"


def test_heuristic_extraction_uses_transcript_speaker_not_modal_words():
    service = LLMService()

    result = asyncio.run(
        service.extract_tasks(
            "Даниил: прод бы доделать до завтра\n"
            "Даниил: прод бы доделать\n"
            "Даниил: надо доделать backend часть"
        )
    )

    assert result["has_task"] is True
    assert [task["assignee_raw"] for task in result["tasks"]] == ["Даниил", None]
    assert {task["assignee_raw"] for task in result["tasks"]}.isdisjoint({"бы", "надо"})
    assert result["tasks"][0]["deadline_raw"] == "до завтра"
    assert [task["title"] for task in result["tasks"]] == ["доделать", "доделать backend часть"]
