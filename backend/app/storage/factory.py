"""
Storage provider factory.

Decrypts the org's StorageConfig credentials and returns a fully
instantiated StorageProvider ready for use.
"""
from __future__ import annotations

import json
import logging

from cryptography.fernet import Fernet

from app.config import settings
from app.storage import StorageProvider
from app.storage.local import LocalStorageProvider
from app.storage.s3 import S3StorageProvider

logger = logging.getLogger(__name__)


def decrypt_credentials(credentials_encrypted: dict) -> dict:
    """
    Decrypt the JSONB credential blob stored in storage_configs.

    If the blob is already plain (for legacy / test rows that were inserted
    without encryption), return as-is — useful during development.
    """
    raw = credentials_encrypted.get("ciphertext")
    if not raw:
        # Assume already-plain dict (dev / test)
        return credentials_encrypted

    key = settings.encryption_key.encode()
    f = Fernet(key)
    plaintext = f.decrypt(raw.encode())
    return json.loads(plaintext)


def encrypt_credentials(credentials: dict) -> dict:
    """Encrypt a credentials dict for storage in the database."""
    key = settings.encryption_key.encode()
    f = Fernet(key)
    plaintext = json.dumps(credentials, sort_keys=True)
    ciphertext = f.encrypt(plaintext.encode()).decode()
    return {"ciphertext": ciphertext}


def get_storage_provider(backend: str, credentials_encrypted: dict) -> StorageProvider:
    """
    Instantiate the correct StorageProvider for the given backend type.

    backend is one of: local | s3 | r2 | wasabi | minio
    credentials_encrypted is the JSONB blob from storage_configs.
    """
    creds = decrypt_credentials(credentials_encrypted)

    match backend:
        case "local":
            return LocalStorageProvider(base_path=creds["base_path"])

        case "s3":
            return S3StorageProvider(
                bucket=creds["bucket"],
                aws_access_key_id=creds["aws_access_key_id"],
                aws_secret_access_key=creds["aws_secret_access_key"],
                region_name=creds.get("region_name", "us-east-1"),
            )

        case "r2":
            return S3StorageProvider(
                bucket=creds["bucket"],
                aws_access_key_id=creds["aws_access_key_id"],
                aws_secret_access_key=creds["aws_secret_access_key"],
                region_name="auto",
                endpoint_url=creds["endpoint_url"],
            )

        case "wasabi":
            region = creds.get("region_name", "us-east-1")
            return S3StorageProvider(
                bucket=creds["bucket"],
                aws_access_key_id=creds["aws_access_key_id"],
                aws_secret_access_key=creds["aws_secret_access_key"],
                region_name=region,
                endpoint_url=creds.get(
                    "endpoint_url", f"https://s3.{region}.wasabisys.com"
                ),
            )

        case "minio":
            return S3StorageProvider(
                bucket=creds["bucket"],
                aws_access_key_id=creds["aws_access_key_id"],
                aws_secret_access_key=creds["aws_secret_access_key"],
                region_name=creds.get("region_name", "us-east-1"),
                endpoint_url=creds["endpoint_url"],
            )

        case _:
            raise ValueError(f"Unknown storage backend: {backend!r}")
