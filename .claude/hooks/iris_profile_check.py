#!/usr/bin/env python3
"""
IRIS Profile Check Hook
======================

Runs at session start to ensure user has a profile.

If no profile exists, instructs Claude to begin onboarding immediately.

This enforces the strict profile-first protocol.
"""

import sys
from pathlib import Path
from uuid import UUID

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.profile.store import profile_exists


def main():
    """Check if demo user has profile."""
    import io
    import asyncio
    import os
    from src.onboarding.store import OnboardingStore
    from src.onboarding.profile_generator import generate_profile_from_onboarding
    from src.profile.store import ProfileStore

    # Fix Windows encoding for emojis
    if sys.platform == "win32":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    # TODO: Get real user_id from MCP session context
    # For now, use demo user
    demo_user_id = UUID("00000000-0000-0000-0000-000000000001")

    if not profile_exists(demo_user_id):
        # Check for completed onboarding session
        # OnboardingStore uses filesystem username, not app user_id
        fs_username = os.environ.get("USERNAME", "demo_user")
        onboarding_store = OnboardingStore()
        completed_session = onboarding_store.get_latest_completed_session(fs_username)

        if completed_session and completed_session.is_completed:
            # Auto-generate profile from completed session
            profile = generate_profile_from_onboarding(completed_session)
            profile.id = demo_user_id

            # Save profile
            profile_store = ProfileStore()
            asyncio.run(profile_store.create(profile))

            # Profile now exists - exit silently
            sys.exit(0)

        # No profile and no completed session - block
        msg = """
======================================================================
IRIS ONBOARDING REQUIRED
======================================================================

No user profile exists. Onboarding must complete before IRIS can personalize.

PROTOCOL:
1. Immediately call: start_onboarding(user_id='demo_user')
2. Present first question conversationally (not raw JSON)
3. After each answer -> store_answer() -> next question
4. Continue until complete_onboarding()
5. Then call get_context() to load new profile

BLOCKING:
- Do NOT answer other questions until onboarding completes
- Redirect user: 'Let me learn your preferences first (5 min)'
- All IRIS tools blocked except onboarding tools

START NOW with friendly greeting + first onboarding question.
======================================================================
"""
        print(msg)
        sys.exit(0)

    # Profile exists - no message needed
    sys.exit(0)


if __name__ == "__main__":
    main()
