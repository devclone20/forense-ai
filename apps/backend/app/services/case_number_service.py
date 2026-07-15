"""
Case number service.

Generates atomic, unique, collision-free case numbers using PostgreSQL's
INSERT ... ON CONFLICT DO UPDATE counter pattern.
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.number_formatters import get_formatter


class CaseNumberService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def generate_number(
        self,
        org_id: uuid.UUID,
        number_format: str = "FOR-{YYYY}-{NNNNN}",
    ) -> str:
        """
        Atomically increment the sequence counter for this org+year and return
        the formatted case number.

        Uses INSERT ... ON CONFLICT DO UPDATE to ensure atomicity even under
        concurrent requests. The RETURNING clause gives us the final counter
        in a single round-trip.
        """
        year = datetime.now(timezone.utc).year

        stmt = text("""
            INSERT INTO case_number_sequences (organization_id, year, counter)
            VALUES (:org_id, :year, 1)
            ON CONFLICT (organization_id, year)
            DO UPDATE SET counter = case_number_sequences.counter + 1
            RETURNING counter
        """)
        result = await self._session.execute(stmt, {"org_id": str(org_id), "year": year})
        counter: int = result.scalar_one()

        formatter = get_formatter(number_format)
        return formatter.format(counter=counter, year=year)
