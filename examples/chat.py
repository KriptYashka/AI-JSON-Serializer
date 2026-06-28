import asyncio
import sys

from src.client import OpenRouterClient
from src.config import settings, ModelProfile
from src.models import ChatRequest, Message


async def main() -> None:
    if not settings.profiles:
        print("Нет ни одного profile.* в config.ini")
        return

    name = sys.argv[1] if len(sys.argv) > 1 else settings.default_profile
    profile = settings.profiles.get(name)

    if not profile:
        print(f"Профиль '{name}' не найден. Доступны: {', '.join(settings.profiles)}")
        return

    model = profile.models[0]
    print(f"Профиль: {profile.name} | Модель: {model}\n")

    async with OpenRouterClient() as client:
        messages: list[Message] = []

        while True:
            try:
                user_input = input(">>> ")
            except (EOFError, KeyboardInterrupt):
                print()
                break

            if not user_input.strip():
                continue

            messages.append(Message(role="user", content=user_input))

            request = ChatRequest(
                model=model,
                messages=messages,
                temperature=profile.temperature,
                max_tokens=profile.max_tokens,
            )

            response = await client.chat_completion(request)
            reply = response.choices[0].message

            print(f"{reply.role}: {reply.content}\n")
            messages.append(reply)


if __name__ == "__main__":
    asyncio.run(main())
