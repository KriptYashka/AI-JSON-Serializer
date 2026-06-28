import json
from typing import Any

from src.client import OpenRouterClient
from src.config import settings
from src.models import ChatRequest, Message
from src.schema.loader import load_prompt
from src.schema.models import MappingRule, Schema


async def suggest_mapping(
    headers: list[str],
    schema: Schema,
    profile: str | None = None,
) -> list[MappingRule]:
    prompt_template = load_prompt()

    schema_cols = "\n".join(f"- {c.name} ({c.type}): {c.description}" for c in schema.columns)
    headers_str = "\n".join(f"- {h}" for h in headers)

    prompt = prompt_template.format(schema_cols=schema_cols, headers=headers_str)

    profile_name = profile or settings.default_profile
    profiles = settings.profiles
    if profile_name in profiles:
        model = profiles[profile_name].models[0]
    else:
        model = profiles[list(profiles)[0]].models[0]

    messages = [
        Message(role="system", content=prompt),
        Message(role="user", content="Предложи маппинг."),
    ]

    request = ChatRequest(model=model, messages=messages, temperature=0.1, max_tokens=2000)

    async with OpenRouterClient() as client:
        response = await client.chat_completion(request)
        content = response.choices[0].message.content.strip()

    content = _clean_json(content)
    data: list[dict[str, Any]] = json.loads(content)
    return [MappingRule(**item) for item in data]


def _clean_json(text: str) -> str:
    if text.startswith("```"):
        lines = text.splitlines()
        lines = [l for l in lines if not l.startswith("```")]
        text = "\n".join(lines)
    return text.strip()
