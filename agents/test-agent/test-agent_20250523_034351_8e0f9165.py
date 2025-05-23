from core.base_agent import BaseAgent

class TestAgent(BaseAgent):
    async def run(self):
        self.logger.info("Test agent running!")
        return {"status": "success"}
