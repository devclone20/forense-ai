"""
S3StorageProvider — stores evidence files in any S3-compatible object store.

Supports:
  - AWS S3           (no endpoint_url override needed)
  - Cloudflare R2    (endpoint_url = https://<account>.r2.cloudflarestorage.com)
  - MinIO            (endpoint_url = http://minio:9000)
  - Wasabi           (endpoint_url = https://s3.<region>.wasabisys.com)

Object key layout:
  {org_id}/{case_id}/{evidence_id}_{original_filename}
"""
import asyncio
import hashlib
from collections.abc import AsyncIterator
from functools import partial
from typing import Any

import boto3
from botocore.exceptions import ClientError

from app.storage import StorageProvider, StorageRef

_CHUNK = 65_536


class S3StorageProvider(StorageProvider):
    def __init__(
        self,
        bucket: str,
        aws_access_key_id: str,
        aws_secret_access_key: str,
        region_name: str = "auto",
        endpoint_url: str | None = None,
    ) -> None:
        self._bucket = bucket
        # boto3 client is not async-native; we run blocking calls in a thread pool
        # to avoid blocking the event loop.
        self._client_kwargs: dict[str, Any] = dict(
            service_name="s3",
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name=region_name,
        )
        if endpoint_url:
            self._client_kwargs["endpoint_url"] = endpoint_url

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _make_client(self) -> Any:
        return boto3.client(**self._client_kwargs)

    @staticmethod
    def _key_from_ref(ref: StorageRef) -> str:
        prefix = "s3://"
        value = ref.value
        if value.startswith(prefix):
            # strip "s3://bucket/" prefix to get the key
            without_prefix = value[len(prefix):]
            slash = without_prefix.find("/")
            if slash != -1:
                return without_prefix[slash + 1:]
        return value

    def _make_ref(self, key: str) -> StorageRef:
        return StorageRef(value=f"s3://{self._bucket}/{key}")

    async def _run(self, fn: Any, *args: Any, **kwargs: Any) -> Any:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, partial(fn, *args, **kwargs))

    # ------------------------------------------------------------------
    # StorageProvider implementation
    # ------------------------------------------------------------------

    async def store(
        self,
        evidence_id: str,
        filename: str,
        stream: AsyncIterator[bytes],
    ) -> StorageRef:
        key = f"{evidence_id}_{filename}"

        # Collect stream into memory for upload — boto3's upload_fileobj
        # requires a file-like object.  We collect into a BytesIO which
        # is fine because the quota check upstream already rejected
        # oversized files.
        import io
        buf = io.BytesIO()
        async for chunk in stream:
            if chunk:
                buf.write(chunk)
        buf.seek(0)

        client = self._make_client()
        await self._run(client.upload_fileobj, buf, self._bucket, key)
        return self._make_ref(key)

    async def retrieve(self, ref: StorageRef) -> AsyncIterator[bytes]:
        key = self._key_from_ref(ref)
        client = self._make_client()

        # Get the object synchronously (we're already in executor territory)
        response = await self._run(client.get_object, Bucket=self._bucket, Key=key)
        body = response["Body"]

        async def _gen() -> AsyncIterator[bytes]:
            loop = asyncio.get_running_loop()
            while True:
                chunk = await loop.run_in_executor(None, partial(body.read, _CHUNK))
                if not chunk:
                    return
                yield chunk

        return _gen()

    async def compute_hash(self, ref: StorageRef) -> str:
        key = self._key_from_ref(ref)
        client = self._make_client()
        response = await self._run(client.get_object, Bucket=self._bucket, Key=key)
        body = response["Body"]

        h = hashlib.sha256()
        loop = asyncio.get_running_loop()
        while True:
            chunk = await loop.run_in_executor(None, partial(body.read, _CHUNK))
            if not chunk:
                break
            h.update(chunk)
        return h.hexdigest()

    async def exists(self, ref: StorageRef) -> bool:
        key = self._key_from_ref(ref)
        client = self._make_client()
        try:
            await self._run(client.head_object, Bucket=self._bucket, Key=key)
            return True
        except ClientError as exc:
            if exc.response["Error"]["Code"] in ("404", "NoSuchKey"):
                return False
            raise

    async def delete(self, ref: StorageRef) -> None:
        key = self._key_from_ref(ref)
        client = self._make_client()
        try:
            await self._run(client.delete_object, Bucket=self._bucket, Key=key)
        except ClientError:
            pass
