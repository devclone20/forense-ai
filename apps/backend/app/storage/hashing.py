"""
Streaming SHA-256 hashing utilities.

All functions operate on async byte iterators so that arbitrarily large
files are never fully loaded into memory.
"""
import asyncio
import hashlib
from collections.abc import AsyncIterator


async def hash_stream(
    stream: AsyncIterator[bytes],
    chunk_size: int = 65_536,
) -> tuple[str, int]:
    """
    Consume *stream*, calculate SHA-256 and total byte count on-the-fly.

    Returns (hex_hash, size_bytes).
    The caller must not attempt to read from *stream* after this call.
    """
    h = hashlib.sha256()
    size = 0
    async for chunk in stream:
        if not chunk:
            continue
        h.update(chunk)
        size += len(chunk)
    return h.hexdigest(), size


async def tee_stream(
    stream: AsyncIterator[bytes],
) -> tuple[AsyncIterator[bytes], AsyncIterator[bytes]]:
    """
    Duplicate an async byte iterator into two independent iterators.

    Both forks receive every chunk exactly once, enabling simultaneous
    hashing and storage without buffering the whole file.

    Implementation: one asyncio.Queue per consumer.  A background task
    feeds both queues.  Sentinel value (None) signals end-of-stream.
    """
    queue_a: asyncio.Queue[bytes | None] = asyncio.Queue(maxsize=4)
    queue_b: asyncio.Queue[bytes | None] = asyncio.Queue(maxsize=4)

    async def _feeder() -> None:
        try:
            async for chunk in stream:
                await queue_a.put(chunk)
                await queue_b.put(chunk)
        finally:
            await queue_a.put(None)
            await queue_b.put(None)

    # Start the feeder as a background task; it will run concurrently
    # as the two consumer iterators are consumed.
    asyncio.create_task(_feeder())

    async def _reader(q: asyncio.Queue[bytes | None]) -> AsyncIterator[bytes]:
        while True:
            chunk = await q.get()
            if chunk is None:
                return
            yield chunk

    return _reader(queue_a), _reader(queue_b)
