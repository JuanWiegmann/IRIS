"""
Test Profile Database Storage
==============================

Tests for database-backed profile storage (PostgreSQL + pgvector).
"""

import pytest
from uuid import uuid4

from src.profile import UserProfile, Tone, FormatPreference, create_default_profile
from src.profile.store_db import ProfileStoreDB, get_or_create_profile_db


# ═══════════════════════════════════════════════════════════
# DATABASE STORE TESTS
# ═══════════════════════════════════════════════════════════

@pytest.fixture
def db_store():
    """Get ProfileStoreDB instance."""
    return ProfileStoreDB()


@pytest.mark.asyncio
async def test_db_create_and_read_profile(db_store):
    """Test creating and reading a profile from database."""
    profile = create_default_profile()
    profile.language = "de-DE"

    # Create
    created = await db_store.create(profile)
    assert created.id == profile.id

    # Read
    loaded = await db_store.read(profile.id)
    assert loaded is not None
    assert loaded.id == profile.id
    assert loaded.language == "de-DE"


@pytest.mark.asyncio
async def test_db_profile_with_tones_and_boundaries(db_store):
    """Test profile with multiple tones and boundaries."""
    profile = UserProfile(
        language="de-DE",
        tone=[Tone.PROFESSIONAL, Tone.APPROACHABLE],
        format_preference=FormatPreference.BULLET_POINTS,
        boundaries={"formality": "Avoid overly formal", "technical": "Deep background"},
        confidence=0.75
    )

    await db_store.create(profile)

    # Read back
    loaded = await db_store.read(profile.id)
    assert len(loaded.tone) == 2
    assert Tone.PROFESSIONAL in loaded.tone
    assert Tone.APPROACHABLE in loaded.tone
    assert len(loaded.boundaries) == 2
    assert loaded.boundaries["formality"] == "Avoid overly formal"


@pytest.mark.asyncio
async def test_db_save_updates_profile(db_store):
    """Test that save() updates an existing profile."""
    profile = create_default_profile()
    await db_store.create(profile)

    # Modify and save
    profile.language = "fr-FR"
    profile.tone.append(Tone.FRIENDLY)
    profile.current_projects.append("Test Project")
    await db_store.save(profile)

    # Reload
    loaded = await db_store.read(profile.id)
    assert loaded.language == "fr-FR"
    assert Tone.FRIENDLY in loaded.tone
    assert "Test Project" in loaded.current_projects


@pytest.mark.asyncio
async def test_db_delete_profile(db_store):
    """Test deleting a profile."""
    profile = create_default_profile()
    await db_store.create(profile)

    # Verify exists
    assert await db_store.exists(profile.id)

    # Delete
    deleted = await db_store.delete(profile.id)
    assert deleted is True

    # Verify gone
    assert not await db_store.exists(profile.id)
    loaded = await db_store.read(profile.id)
    assert loaded is None


@pytest.mark.asyncio
async def test_db_list_all_profiles(db_store):
    """Test listing all profile IDs."""
    # Create multiple profiles
    profile1 = create_default_profile()
    profile2 = create_default_profile()

    await db_store.create(profile1)
    await db_store.create(profile2)

    # List all
    all_ids = await db_store.list_all()
    assert profile1.id in all_ids
    assert profile2.id in all_ids


@pytest.mark.asyncio
async def test_db_get_or_create_new():
    """Test get_or_create with a new user."""
    user_id = uuid4()

    profile = await get_or_create_profile_db(user_id)

    # Should create default profile
    assert profile.id == user_id
    assert profile.confidence == 0.1


@pytest.mark.asyncio
async def test_db_get_or_create_existing(db_store):
    """Test get_or_create with an existing user."""
    # Create profile
    profile = create_default_profile()
    profile.language = "de-DE"
    await db_store.create(profile)

    # Get or create should return existing
    loaded = await get_or_create_profile_db(profile.id)
    assert loaded.id == profile.id
    assert loaded.language == "de-DE"


@pytest.mark.asyncio
async def test_db_profile_round_trip(db_store):
    """Test full create-read-update-delete cycle with database."""
    # Create
    profile = UserProfile(
        language="de-DE",
        tone=[Tone.TECHNICAL, Tone.FRIENDLY],
        format_preference=FormatPreference.STEP_BY_STEP,
        boundaries={"test": "value"},
        current_projects=["Project A"],
        recent_context="Test context"
    )

    await db_store.create(profile)

    # Read
    loaded = await db_store.read(profile.id)
    assert loaded.language == "de-DE"
    assert len(loaded.tone) == 2
    assert loaded.boundaries["test"] == "value"

    # Update
    loaded.confidence = 0.8
    loaded.current_projects.append("Project B")
    await db_store.save(loaded)

    # Re-read
    updated = await db_store.read(profile.id)
    assert updated.confidence == 0.8
    assert len(updated.current_projects) == 2

    # Delete
    await db_store.delete(profile.id)
    assert await db_store.read(profile.id) is None
