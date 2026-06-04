from app.services.llm_client import llm_client


class LLMService:
    async def extract_tasks(self, text: str):
        result = await llm_client.extract_tasks(text)
        return result.model_dump()


llm_service = LLMService()
