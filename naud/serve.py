"""A server for Claude Code's MessageDisplay hook. The model loads once, then each batch of lines of an
assistant message comes back cleaned. A request is the hook's input JSON, the reply is its output JSON."""
import asyncio
import json
import os
import socket
import sys
from contextlib import suppress
from dataclasses import dataclass, field
from functools import partial
from typing import Any

from .engine import Stream, clean

PATIENCE = 2.0  # seconds to wait for an earlier batch that has not arrived yet

Request = dict[str, Any]


@dataclass
class Message:
    """One assistant message as it streams, with its cleaner and the number of the batch that is next."""

    stream: Stream = field(default_factory=Stream)
    turn: int = 0
    ready: asyncio.Condition = field(default_factory=asyncio.Condition)


async def answer(messages: dict[str, Message], request: Request) -> str:
    """The batch, cleaned. Batches of one message are taken in index order, even when they arrive in another."""
    message = messages.setdefault(request["message_id"], Message())
    async with message.ready:
        with suppress(TimeoutError):
            async with asyncio.timeout(PATIENCE):
                await message.ready.wait_for(lambda: message.turn == request["index"])
        text = message.stream.feed(request["delta"])
        message.turn = request["index"] + 1
        message.ready.notify_all()
    if request["final"]:
        messages.pop(request["message_id"], None)
    return text


def reply(text: str) -> bytes:
    return json.dumps({"hookSpecificOutput": {"hookEventName": "MessageDisplay", "displayContent": text}}).encode()


async def talk(messages: dict[str, Message], reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
    """One connection. An empty request is a probe. One that cannot be answered gets no reply, so the original text shows."""
    try:
        if request := await reader.read():
            writer.write(reply(await answer(messages, json.loads(request))))
    except Exception as e:
        print(e, file=sys.stderr)
    finally:
        writer.close()


async def serve(path: str) -> None:
    async with await asyncio.start_unix_server(partial(talk, {}), path) as server:
        clean("Ready.")
        await server.serve_forever()


def main(path: str) -> None:
    """Serve at the socket path, unless a server already answers there."""
    with socket.socket(socket.AF_UNIX) as probe:
        try:
            probe.connect(path)
            return
        except ConnectionRefusedError:
            os.remove(path)
        except FileNotFoundError:
            pass
    asyncio.run(serve(path))
