"""
Utility Functions
=================

Common utilities used across IRIS.
"""

import getpass
from uuid import UUID, uuid5, NAMESPACE_DNS


def get_system_user() -> str:
    """
    Get the current system username.

    Returns:
        System username (e.g., "AV013EV")
    """
    return getpass.getuser()


def get_user_id() -> UUID:
    """
    Get consistent UUID for the current system user.

    Uses UUID5 with DNS namespace for deterministic generation.
    Same user always gets same UUID across sessions.

    Returns:
        UUID for current system user
    """
    username = get_system_user()
    return uuid5(NAMESPACE_DNS, f"iris.user.{username}")


def iris_response(content: str) -> str:
    """
    Format response with IRIS Janus logo.

    Prepends the Janus butler face to all tool responses.
    Two-faced design: left looks at past (memory), right looks at present (context).

    Args:
        content: Response content

    Returns:
        Formatted response with Janus logo
    """
    return f"**( ←_• )( •_→ )** {content}"
