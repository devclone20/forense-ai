"""
Case number formatters.

ABC + concrete implementations. Adding a new format = subclass + register.
"""
import re
from abc import ABC, abstractmethod


class CaseNumberFormatter(ABC):
    """Abstract base for case number formatters."""

    @abstractmethod
    def format(self, counter: int, year: int) -> str:
        """
        Produce a case number string.

        Args:
            counter: The atomic sequence value for this org+year.
            year: The 4-digit year.

        Returns:
            Formatted case number string.
        """

    @abstractmethod
    def parse_counter(self, case_number: str) -> int | None:
        """Extract the counter value from a formatted case number, or None if unparseable."""


class DefaultFormatter(CaseNumberFormatter):
    """
    Default format: FOR-{YYYY}-{NNNNN:05d}
    Example: FOR-2026-00042
    """

    _PATTERN = re.compile(r"^FOR-(\d{4})-(\d{5})$")

    def format(self, counter: int, year: int) -> str:
        return f"FOR-{year}-{counter:05d}"

    def parse_counter(self, case_number: str) -> int | None:
        m = self._PATTERN.match(case_number)
        if m:
            return int(m.group(2))
        return None


class CustomTemplateFormatter(CaseNumberFormatter):
    """
    Template-based formatter using organisation-defined format strings.

    Supported tokens:
      {YYYY}   — 4-digit year
      {YY}     — 2-digit year
      {NNNNN}  — zero-padded 5-digit counter
      {N}      — unpadded counter

    Example template: "DIG-{YYYY}-{NNNNN}" → "DIG-2026-00042"
    """

    def __init__(self, template: str) -> None:
        self._template = template

    def format(self, counter: int, year: int) -> str:
        return (
            self._template
            .replace("{YYYY}", str(year))
            .replace("{YY}", str(year)[-2:])
            .replace("{NNNNN}", f"{counter:05d}")
            .replace("{N}", str(counter))
        )

    def parse_counter(self, case_number: str) -> int | None:
        # Best-effort: find the last numeric group
        groups = re.findall(r"\d+", case_number)
        if groups:
            return int(groups[-1])
        return None


def get_formatter(number_format: str) -> CaseNumberFormatter:
    """Return the appropriate formatter for a given format string."""
    if number_format == "FOR-{YYYY}-{NNNNN}" or not number_format:
        return DefaultFormatter()
    return CustomTemplateFormatter(number_format)
