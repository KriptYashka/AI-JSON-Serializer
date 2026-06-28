from pydantic import BaseModel


class Message(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    model: str
    messages: list[Message]
    temperature: float | None = None
    max_tokens: int | None = None
    top_p: float | None = None
    frequency_penalty: float | None = None
    presence_penalty: float | None = None


class TokenUsage(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class Choice(BaseModel):
    index: int
    message: Message
    finish_reason: str = "stop"


class ChatResponse(BaseModel):
    id: str
    model: str
    choices: list[Choice]
    usage: TokenUsage | None = None


class ModelPricing(BaseModel):
    prompt: float
    completion: float


class ModelInfo(BaseModel):
    id: str
    name: str
    context_length: int | None = None
    pricing: ModelPricing | None = None
