import logging
import tiktoken
from django.conf import settings
from openai import OpenAI


logger = logging.getLogger(__name__)


class GPTService:
    """Wrapper around OpenAI Chat Completions with context control."""

    def __init__(self):
        self.client = OpenAI(api_key=getattr(settings, 'OPENAI_API_KEY', None))
        self.model = getattr(settings, 'OPENAI_MODEL', 'gpt-4o-mini')

    def _count_tokens(self, text: str, model: str = 'gpt-3.5-turbo') -> int:
        try:
            enc = tiktoken.encoding_for_model(model)
        except Exception:
            enc = tiktoken.get_encoding('cl100k_base')
        return len(enc.encode(text or ''))

    def build_context(self, system_prompt: str, messages, max_context_messages: int):
        """
        Build ordered context for OpenAI: [system] + last N messages.
        messages is a queryset/list of {'role','content'} ordered asc by created_at.
        """
        history = []
        if system_prompt:
            history.append({'role': 'system', 'content': system_prompt})

        # Include only the last N of existing messages
        if max_context_messages and max_context_messages > 0:
            messages = list(messages)[-max_context_messages:]

        for m in messages:
            history.append({'role': m['role'], 'content': m['content']})

        return history

    def chat(self, system_prompt: str, messages, max_context_messages: int = 20):
        try:
            history = self.build_context(system_prompt, messages, max_context_messages)
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=history,
                temperature=getattr(settings, 'OPENAI_TEMPERATURE', 0.2),
                max_tokens=getattr(settings, 'OPENAI_MAX_TOKENS', 512),
            )
            content = completion.choices[0].message.content
            usage = completion.usage or None
            tokens = usage.total_tokens if usage else 0
            return content, tokens, completion
        except Exception as e:
            logger.error(f"OpenAI Chat error: {e}")
            raise


