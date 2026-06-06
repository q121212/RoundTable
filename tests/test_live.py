import asyncio

import pytest

from app.live import ProjectEventBus


@pytest.mark.asyncio
async def test_project_event_bus_publishes_to_matching_project():
    bus = ProjectEventBus()
    gt_queue = await bus.subscribe("GT")
    ops_queue = await bus.subscribe("OPS")

    await bus.publish("gt", {"event": "ticket_changed", "ticket": {"key": "GT-1"}})

    assert await asyncio.wait_for(gt_queue.get(), timeout=0.2) == {
        "event": "ticket_changed",
        "ticket": {"key": "GT-1"},
    }
    with pytest.raises(asyncio.TimeoutError):
        await asyncio.wait_for(ops_queue.get(), timeout=0.05)

    await bus.unsubscribe("GT", gt_queue)
    await bus.unsubscribe("OPS", ops_queue)
