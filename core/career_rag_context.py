from contextlib import contextmanager
from contextvars import ContextVar
from collections.abc import Iterator


_active_career_rag_context: ContextVar[str | None] = ContextVar(
    "active_career_rag_context",
    default=None,
)


def get_active_career_rag_context() -> str | None:
    return _active_career_rag_context.get()


@contextmanager
def use_career_rag_context(context: str) -> Iterator[None]:
    token = _active_career_rag_context.set(context)
    try:
        yield
    finally:
        _active_career_rag_context.reset(token)
