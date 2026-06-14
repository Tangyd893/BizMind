
from pydantic import BaseModel


class ChatOptions(BaseModel):
    web_search_enabled: bool = False


class ChatRequest(BaseModel):
    thread_id: str
    message: str
    options: ChatOptions | None = None
