import json
import logging
import urllib.request
import urllib.error
from typing import List

logger = logging.getLogger(__name__)


class EvaluationQuestionGenerator:
    def __init__(self, api_key: str, model: str = "llama-3.3-70b-versatile",
                 temperature: float = 0, timeout: int = 60,
                 questions_per_chunk: int = 3):
        self.api_key = api_key
        self.model = model
        self.temperature = temperature
        self.timeout = timeout
        self.questions_per_chunk = questions_per_chunk

    def generate(self, chunk_text: str) -> List[str]:
        if not self.api_key:
            logger.warning("GROQ_API_KEY not set — skipping question generation")
            return []
        prompt = (
            f"Generate exactly {self.questions_per_chunk} concise retrieval evaluation "
            f"questions for the following text chunk. Return only the questions, one per line.\n\n"
            f"Text:\n{chunk_text[:2000]}"
        )
        payload = json.dumps({
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": self.temperature,
        }).encode("utf-8")

        req = urllib.request.Request(
            "https://api.groq.com/openai/v1/chat/completions",
            data=payload,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                body = json.loads(resp.read().decode("utf-8"))
            content = body["choices"][0]["message"]["content"].strip()
            questions = [q.strip() for q in content.splitlines() if q.strip()]
            return questions[: self.questions_per_chunk]
        except urllib.error.HTTPError as e:
            if e.code in (401, 403):
                logger.error("Groq auth error %s — check GROQ_API_KEY", e.code)
            else:
                logger.error("Groq HTTP error %s", e.code)
            return []
        except Exception as exc:
            logger.error("Question generation failed: %s", exc)
            return []
