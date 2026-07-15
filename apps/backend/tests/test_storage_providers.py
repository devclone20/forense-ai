"""
Storage provider unit tests.

LocalStorageProvider is tested against the real filesystem (tmp_path).
S3StorageProvider is tested with a mocked boto3 client.
"""
from __future__ import annotations

import hashlib
import io
import uuid
from collections.abc import AsyncIterator
from unittest.mock import MagicMock, patch

import pytest

from app.storage import StorageRef
from app.storage.local import LocalStorageProvider


# ── Helpers ────────────────────────────────────────────────────────────────────

async def _stream(data: bytes, chunk: int = 1024) -> AsyncIterator[bytes]:
    for i in range(0, len(data), chunk):
        yield data[i:i + chunk]


# ── LocalStorageProvider ──────────────────────────────────────────────────────

class TestLocalStorageProvider:
    async def test_store_retrieve_roundtrip(self, tmp_path):
        """store → retrieve → bytes match."""
        provider = LocalStorageProvider(base_path=str(tmp_path))
        content = b"forensic test data " * 500

        ref = await provider.store("org/case/ev-id", "file.bin", _stream(content))
        assert ref.value.startswith("local://")

        # Retrieve
        out = io.BytesIO()
        stream = await provider.retrieve(ref)
        async for chunk in stream:
            out.write(chunk)

        assert out.getvalue() == content

    async def test_compute_hash_matches_sha256(self, tmp_path):
        """compute_hash returns correct SHA-256 hex."""
        provider = LocalStorageProvider(base_path=str(tmp_path))
        content = b"hash-verification-content"
        expected = hashlib.sha256(content).hexdigest()

        ref = await provider.store("org/case/ev-hash", "data.bin", _stream(content))
        computed = await provider.compute_hash(ref)

        assert computed == expected

    async def test_exists_true_after_store(self, tmp_path):
        provider = LocalStorageProvider(base_path=str(tmp_path))
        content = b"exists-test"

        ref = await provider.store("org/case/ev-exists", "x.bin", _stream(content))
        assert await provider.exists(ref) is True

    async def test_exists_false_for_unknown_ref(self, tmp_path):
        provider = LocalStorageProvider(base_path=str(tmp_path))
        ref = StorageRef(value="local://nonexistent/path/file.bin")
        assert await provider.exists(ref) is False

    async def test_delete_removes_file(self, tmp_path):
        provider = LocalStorageProvider(base_path=str(tmp_path))
        content = b"delete-me"

        ref = await provider.store("org/case/ev-del", "del.bin", _stream(content))
        assert await provider.exists(ref) is True

        await provider.delete(ref)
        assert await provider.exists(ref) is False

    async def test_delete_nonexistent_is_safe(self, tmp_path):
        """Deleting a file that doesn't exist must not raise."""
        provider = LocalStorageProvider(base_path=str(tmp_path))
        ref = StorageRef(value="local://no/such/file.bin")
        await provider.delete(ref)  # must not raise

    async def test_large_file_never_buffered(self, tmp_path):
        """
        Store and hash a 'large' file (1 MB) streamed in 4 KB chunks.
        Verifies the streaming path works end-to-end.
        """
        provider = LocalStorageProvider(base_path=str(tmp_path))
        content = b"A" * (1024 * 1024)
        expected = hashlib.sha256(content).hexdigest()

        ref = await provider.store("org/case/ev-large", "large.bin", _stream(content, chunk=4096))
        assert await provider.compute_hash(ref) == expected


# ── S3StorageProvider (mocked boto3) ──────────────────────────────────────────

class TestS3StorageProviderMocked:
    def _make_provider(self):
        from app.storage.s3 import S3StorageProvider
        return S3StorageProvider(
            bucket="test-bucket",
            aws_access_key_id="AKID",
            aws_secret_access_key="SECRET",
            region_name="us-east-1",
        )

    async def test_store_calls_upload_fileobj(self):
        provider = self._make_provider()
        content = b"s3-test-content"

        mock_client = MagicMock()
        mock_client.upload_fileobj = MagicMock()

        with patch.object(provider, "_make_client", return_value=mock_client):
            ref = await provider.store("org/case/ev-s3", "f.bin", _stream(content))

        assert ref.value == f"s3://test-bucket/org/case/ev-s3_f.bin"
        mock_client.upload_fileobj.assert_called_once()

    async def test_retrieve_streams_body(self):
        provider = self._make_provider()
        content = b"s3-retrieve-content"

        mock_body = MagicMock()
        reads = [content[i:i+8] for i in range(0, len(content), 8)] + [b""]
        mock_body.read = MagicMock(side_effect=reads)

        mock_client = MagicMock()
        mock_client.get_object = MagicMock(return_value={"Body": mock_body})

        ref = StorageRef(value="s3://test-bucket/org/case/ev-s3_f.bin")
        with patch.object(provider, "_make_client", return_value=mock_client):
            stream = await provider.retrieve(ref)
            buf = io.BytesIO()
            async for chunk in stream:
                buf.write(chunk)

        assert buf.getvalue() == content

    async def test_compute_hash_matches(self):
        provider = self._make_provider()
        content = b"s3-hash-content"
        expected = hashlib.sha256(content).hexdigest()

        mock_body = MagicMock()
        reads = [content[i:i+8] for i in range(0, len(content), 8)] + [b""]
        mock_body.read = MagicMock(side_effect=reads)

        mock_client = MagicMock()
        mock_client.get_object = MagicMock(return_value={"Body": mock_body})

        ref = StorageRef(value="s3://test-bucket/some/key")
        with patch.object(provider, "_make_client", return_value=mock_client):
            computed = await provider.compute_hash(ref)

        assert computed == expected

    async def test_exists_returns_true_on_head_object_success(self):
        provider = self._make_provider()
        mock_client = MagicMock()
        mock_client.head_object = MagicMock(return_value={})

        ref = StorageRef(value="s3://test-bucket/some/key")
        with patch.object(provider, "_make_client", return_value=mock_client):
            assert await provider.exists(ref) is True

    async def test_exists_returns_false_on_404(self):
        from botocore.exceptions import ClientError
        provider = self._make_provider()

        err = ClientError({"Error": {"Code": "404", "Message": "Not Found"}}, "HeadObject")
        mock_client = MagicMock()
        mock_client.head_object = MagicMock(side_effect=err)

        ref = StorageRef(value="s3://test-bucket/missing/key")
        with patch.object(provider, "_make_client", return_value=mock_client):
            assert await provider.exists(ref) is False
