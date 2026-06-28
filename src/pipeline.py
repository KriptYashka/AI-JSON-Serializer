import json
from typing import Any

from src.client import OpenRouterClient
from src.config import settings
from src.models import ChatRequest, Message
from src.schema.loader import load_prompt
from src.schema.models import MappingRule, Schema


def _clean_json(text: str) -> str:
    if text.startswith("```"):
        lines = text.splitlines()
        lines = [l for l in lines if not l.startswith("```")]
        text = "\n".join(lines)
    return text.strip()


def _format_schema(schema: Schema) -> str:
    return "\n".join(f"- {c.name} ({c.type}): {c.description}" for c in schema.columns)


def _format_mapping(rules: list[MappingRule]) -> str:
    return "\n".join(f"  {r.from_} → {r.to}" for r in rules)


async def _generate(
    headers: list[str],
    schema: Schema,
    profile_name: str,
    feedback: str = "",
) -> list[MappingRule]:
    prompt_tpl = load_prompt("generate.txt")
    schema_cols = _format_schema(schema)
    headers_str = "\n".join(f"- {h}" for h in headers)

    fb = f"Замечания ревьювера:\n{feedback}\n\n" if feedback else ""
    prompt = prompt_tpl.format(schema_cols=schema_cols, headers=headers_str, feedback=fb)

    model = settings.profiles[profile_name].models[0]

    messages = [
        Message(role="system", content=prompt),
    ]

    request = ChatRequest(model=model, messages=messages, temperature=0.1, max_tokens=2000)

    async with OpenRouterClient() as client:
        response = await client.chat_completion(request)
        content = response.choices[0].message.content.strip()

    content = _clean_json(content)
    data: list[dict[str, Any]] = json.loads(content)
    return [MappingRule(**item) for item in data]


async def _review(
    headers: list[str],
    schema: Schema,
    mapping_rules: list[MappingRule],
    profile_name: str,
) -> str:
    prompt_tpl = load_prompt("review.txt")
    schema_cols = _format_schema(schema)
    headers_str = "\n".join(f"- {h}" for h in headers)
    mapping_str = _format_mapping(mapping_rules)

    prompt = prompt_tpl.format(
        schema_cols=schema_cols,
        headers=headers_str,
        mapping=mapping_str,
    )

    model = settings.profiles[profile_name].models[0]

    messages = [
        Message(role="system", content=prompt),
    ]

    request = ChatRequest(model=model, messages=messages, temperature=0.0, max_tokens=1000)

    async with OpenRouterClient() as client:
        response = await client.chat_completion(request)
        return response.choices[0].message.content.strip()


async def run_pipeline(
    headers: list[str],
    schema: Schema,
    cheap_profile: str = "cheap",
    expensive_profile: str = "expensive",
    max_rounds: int = 3,
) -> list[MappingRule]:
    if expensive_profile not in settings.profiles:
        return await _generate(headers, schema, cheap_profile)

    prev_feedback = ""
    for round_num in range(1, max_rounds + 1):
        print(f"  [раунд {round_num}] Генерация…")
        feedback = prev_feedback
        mapping = await _generate(headers, schema, cheap_profile, feedback=feedback)
        print(f"  [раунд {round_num}] Проверка…")
        verdict = await _review(headers, schema, mapping, expensive_profile)

        if verdict.strip().upper().startswith("APPROVED"):
            print(f"  [раунд {round_num}] ✓ Утверждено")
            return mapping

        prev_feedback = verdict
        print(f"  [раунд {round_num}] ✗ Замечания:\n{verdict}\n")

    print(f"  [✗] Достигнут лимит раундов. Возвращается последний вариант.")
    return mapping
