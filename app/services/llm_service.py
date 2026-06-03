class LLMService:

    async def extract_tasks(
        self,
        text: str,
    ):

        return {
            "has_task": True,
            "tasks": [
                {
                    "title": text,
                    "assignee_raw": None,
                    "deadline_raw": None,
                    "confidence": 0.9,
                }
            ]
        }


llm_service = LLMService()