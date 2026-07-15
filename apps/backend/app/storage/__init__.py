"""
Storage abstraction layer for evidence files.

Consumers interact only with StorageProvider / StorageRef.
The concrete backend is determined at runtime by get_storage_provider().
"""
from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from dataclasses import dataclass


@dataclass(frozen=True)
class StorageRef:
    """
    Opaque reference to a stored file.
    Never serialised to the frontend — only stored in the evidences.storage_ref
    column and consumed by the backend.

    Format examples:
      local://relative/path/from/base
      s3://bucket-name/org/case/evidence_id
    """

    value: str

    def __str__(self) -> str:
        return self.value


class StorageProvider(ABC):
    """Abstract interface every storage backend must implement."""

    @abstractmethod
    async def store(
        self,
        evidence_id: str,
        filename: str,
        stream: AsyncIterator[bytes],
    ) -> StorageRef:
        """
        Persist the byte stream under a deterministic key derived from
        evidence_id + filename.  Returns an opaque StorageRef.
        """
        ...

    @abstractmethod
    async def retrieve(self, ref: StorageRef) -> AsyncIterator[bytes]:
        """Stream the bytes for ref back to the caller."""
        ...

    @abstractmethod
    async def compute_hash(self, ref: StorageRef) -> str:
        """
        Re-read the stored object and return its SHA-256 hex digest.
        Used by the integrity-verification flow.
        """
        ...

    @abstractmethod
    async def exists(self, ref: StorageRef) -> bool:
        """Return True if the object exists in the backend."""
        ...

    @abstractmethod
    async def delete(self, ref: StorageRef) -> None:
        """
        Remove the object.  Only called to clean up after a failed ingest.
        Never exposed as a user-facing operation.
        """
        ...
