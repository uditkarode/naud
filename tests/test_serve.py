import asyncio
import json
from functools import partial
from pathlib import Path
from typing import Any

from naud.serve import Message, answer, talk


def batch(index: int, delta: str, final: bool = False) -> dict[str, Any]:
    return {"message_id": "m", "index": index, "final": final, "delta": delta}


def test_batches_are_cleaned_in_order_however_they_arrive() -> None:
    async def go() -> tuple[str, str]:
        messages: dict[str, Message] = {}
        second, first = await asyncio.gather(answer(messages, batch(1, "```\nvery good\n", final=True)), answer(messages, batch(0, "```\n")))
        return first, second

    assert asyncio.run(go()) == ("```\n", "```\ngood\n")


def test_a_finished_message_is_forgotten() -> None:
    messages: dict[str, Message] = {}
    asyncio.run(answer(messages, batch(0, "Very good.\n", final=True)))
    assert messages == {}


def test_a_request_over_the_socket_gets_the_hook_reply(tmp_path: Path) -> None:
    async def go() -> Any:
        path = str(tmp_path / "naud.sock")
        async with await asyncio.start_unix_server(partial(talk, {}), path):
            reader, writer = await asyncio.open_unix_connection(path)
            writer.write(json.dumps(batch(0, "It is very good.\n", final=True)).encode())
            writer.write_eof()
            return json.loads(await reader.read())

    assert asyncio.run(go()) == {"hookSpecificOutput": {"hookEventName": "MessageDisplay", "displayContent": "It is good.\n"}}
