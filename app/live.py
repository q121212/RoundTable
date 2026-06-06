import asyncio
import json
from collections import defaultdict
from typing import Any, DefaultDict, Dict, Set


class ProjectEventBus:
    def __init__(self) -> None:
        self._subscribers: DefaultDict[str, Set[asyncio.Queue[Dict[str, Any]]]] = defaultdict(set)
        self._lock = asyncio.Lock()

    async def subscribe(self, project_key: str) -> asyncio.Queue[Dict[str, Any]]:
        queue: asyncio.Queue[Dict[str, Any]] = asyncio.Queue(maxsize=100)
        async with self._lock:
            self._subscribers[project_key.upper()].add(queue)
        return queue

    async def unsubscribe(self, project_key: str, queue: asyncio.Queue[Dict[str, Any]]) -> None:
        async with self._lock:
            subscribers = self._subscribers.get(project_key.upper())
            if not subscribers:
                return
            subscribers.discard(queue)
            if not subscribers:
                self._subscribers.pop(project_key.upper(), None)

    async def publish(self, project_key: str, event: Dict[str, Any]) -> None:
        async with self._lock:
            subscribers = list(self._subscribers.get(project_key.upper(), set()))
        for queue in subscribers:
            if queue.full():
                try:
                    queue.get_nowait()
                except asyncio.QueueEmpty:
                    pass
            queue.put_nowait(event)


project_events = ProjectEventBus()


def sse_message(event_name: str, data: Dict[str, Any]) -> str:
    return "event: %s\ndata: %s\n\n" % (event_name, json.dumps(data, ensure_ascii=False, default=str))
