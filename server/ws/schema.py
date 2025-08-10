from pydantic import BaseModel


class ClientMove(BaseModel):
    t: str
    dx: int
    dy: int
    seq: int


class ClientChat(BaseModel):
    t: str
    channel: str
    msg: str


class ClientPing(BaseModel):
    t: str
    ts: int | None = None


class ServerPong(BaseModel):
    t: str = "pong"
    ts: int


class ServerEventMsg(BaseModel):
    t: str = "event"
    type: str = "msg"
    payload: dict





