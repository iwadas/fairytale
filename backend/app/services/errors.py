"""Domain errors raised by services; routers translate them to HTTP responses."""


class NotFoundError(LookupError):
    """The requested entity does not exist. ``str(error)`` is the client-facing detail."""
