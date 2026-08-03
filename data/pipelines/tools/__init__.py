"""External tools for the support agent (one module per responsibility)."""

from pipelines.tools.ticket_lookup import (
    TicketLookupInput,
    TicketLookupResult,
    TicketRecord,
    format_ticket_answer,
    lookup_ticket,
)

__all__ = [
    "TicketLookupInput",
    "TicketLookupResult",
    "TicketRecord",
    "format_ticket_answer",
    "lookup_ticket",
]
