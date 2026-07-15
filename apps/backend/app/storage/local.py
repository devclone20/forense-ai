"""
LocalStorageProvider — stores evidence files on the local filesystem.

Intended for:
  - Development / demo environments
  - On-premises deployments with a mounted NFS/SAN volume

Directory layout:
  {base_path}/{org_id}/{case_id}/{evidence_id}_{original_filename}
"""
import hashlib
from collections.abc import AsyncIterator
from pathlib import Path

import aiofiles
import aiofiles.os

from app.storage import StorageProvider, StorageRef


class LocalStorageProvider(StorageProvider):
    def __init__(self, base_path: str) -> None:
        self._base = Path(base_path)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _resolve(self, ref: StorageRef) -> Path:
        """Convert a local:// StorageRef back to an absolute Path."""
        value = ref.value
        prefix = "local://"
        if value.startswith(prefix):
            value = value[len(prefix):]
        return self._base / value

    @staticmethod
    def _make_ref(relative: str) -> StorageRef:
        return StorageRef(value=f"local://{relative}")

    # ------------------------------------------------------------------
    # StorageProvider implementation
    # ------------------------------------------------------------------

    async def store(
        self,
        evidence_id: str,
        filename: str,
        stream: AsyncIterator[bytes],
    ) -> StorageRef:
        # evidence_id is already "org_id/case_id/uuid" from the service layer
        target = self._base / f"{evidence_id}_{filename}"
        await aiofiles.os.makedirs(str(target.parent), exist_ok=True)

        async with aiofiles.open(target, "wb") as fh:
            async for chunk in stream:
                if chunk:
                    await fh.write(chunk)

        relative = target.relative_to(self._base)
        return self._make_ref(str(relative))

    async def retrieve(self, ref: StorageRef) -> AsyncIterator[bytes]:
        path = self._resolve(ref)

        async def _gen() -> AsyncIterator[bytes]:
            async with aiofiles.open(path, "rb") as fh:
                while True:
                    chunk = await fh.read(65_536)
                    if not chunk:
                        return
                    yield chunk

        return _gen()

    async def compute_hash(self, ref: StorageRef) -> str:
        path = self._resolve(ref)
        h = hashlib.sha256()
        async with aiofiles.open(path, "rb") as fh:
            while True:
                chunk = await fh.read(65_536)
                if not chunk:
                    break
                h.update(chunk)
        return h.hexdigest()

    async def exists(self, ref: StorageRef) -> bool:
        path = self._resolve(ref)
        return await aiofiles.os.path.exists(str(path))

    async def delete(self, ref: StorageRef) -> None:
        path = self._resolve(ref)
        try:
            await aiofiles.os.remove(str(path))
        except FileNotFoundError:
            pass
