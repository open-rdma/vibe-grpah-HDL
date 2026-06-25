from abc import ABC, abstractmethod
import subprocess
import tempfile
import os

class LLMAgent(ABC):
    @abstractmethod
    def generate(self, system_prompt: str, user_prompt: str,
                 context_files: list[str] = None) -> str:
        """Generate text from the LLM."""


class ClaudeCodeAgent(LLMAgent):
    def __init__(self, config: dict = None):
        self.config = config or {}
        self.model = self.config.get('model', 'claude-sonnet-4-6')

    def generate(self, system_prompt: str, user_prompt: str,
                 context_files: list[str] = None) -> str:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt',
                                         delete=False, encoding='utf-8') as f:
            f.write(f"{system_prompt}\n\n---\n\n{user_prompt}")
            prompt_file = f.name

        try:
            result = subprocess.run(
                ['claude', '--print', '--prompt', prompt_file,
                 '--model', self.model],
                capture_output=True, text=True, timeout=300
            )
            if result.returncode != 0:
                raise RuntimeError(f"Claude Code error: {result.stderr}")
            return result.stdout.strip()
        finally:
            os.unlink(prompt_file)


class OpenAIAgent(LLMAgent):
    def __init__(self, config: dict = None):
        self.config = config or {}
        self.model = self.config.get('model', 'gpt-4o')
        self.api_key = self.config.get('api_key', '')

    def generate(self, system_prompt: str, user_prompt: str,
                 context_files: list[str] = None) -> str:
        from openai import OpenAI
        client = OpenAI(api_key=self.api_key)

        messages = [{"role": "system", "content": system_prompt}]
        if context_files:
            for cf in context_files:
                if os.path.exists(cf):
                    with open(cf, 'r', encoding='utf-8') as f:
                        messages.append({"role": "user", "content": f"Context file {cf}:\n```\n{f.read()}\n```"})

        messages.append({"role": "user", "content": user_prompt})

        response = client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.2
        )
        return response.choices[0].message.content.strip()


def create_agent(config: dict) -> LLMAgent:
    provider = config.get('provider', 'claude_code')
    if provider == 'openai':
        return OpenAIAgent(config.get('openai_config', {}))
    return ClaudeCodeAgent(config.get('claude_config', {}))
