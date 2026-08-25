"""
Test Profile Schema and Storage
================================

Tests for user profile data model and persistence.
"""

import pytest
from pathlib import Path
from uuid import UUID, uuid4
from datetime import datetime

from src.profile import (
    UserProfile,
    Tone,
    FormatPreference,
    create_default_profile,
    format_profile_for_llm,
    ProfileStore,
    get_or_create_profile,
)


# ═══════════════════════════════════════════════════════════
# SCHEMA TESTS
# ═══════════════════════════════════════════════════════════

def test_default_profile():
    """Test creating a default profile."""
    profile = create_default_profile()

    assert profile.language == "en-US"
    assert Tone.PROFESSIONAL in profile.tone
    assert profile.format_preference == FormatPreference.CONCISE
    assert profile.confidence == 0.1
    assert len(profile.boundaries) == 0
    assert len(profile.current_projects) == 0


def test_profile_validation():
    """Test Pydantic validation on profile creation."""
    # Valid profile
    profile = UserProfile(
        language="de-DE",
        tone=[Tone.PROFESSIONAL, Tone.APPROACHABLE],
        format_preference=FormatPreference.BULLET_POINTS,
        confidence=0.75
    )

    assert profile.language == "de-DE"
    assert len(profile.tone) == 2
    assert profile.confidence == 0.75


def test_profile_confidence_bounds():
    """Test that confidence is bounded between 0.0 and 1.0."""
    # Should fail: confidence > 1.0
    with pytest.raises(ValueError):
        UserProfile(confidence=1.5)

    # Should fail: confidence < 0.0
    with pytest.raises(ValueError):
        UserProfile(confidence=-0.1)

    # Should pass: valid range
    profile = UserProfile(confidence=0.5)
    assert profile.confidence == 0.5


def test_format_profile_for_llm():
    """Test formatting profile as markdown."""
    profile = UserProfile(
        language="de-DE",
        tone=[Tone.PROFESSIONAL, Tone.FRIENDLY],
        format_preference=FormatPreference.EXAMPLES_HEAVY,
        boundaries={"formality": "Avoid overly formal"},
        current_projects=["KIM", "Certification"],
        recent_context="Working on profiles"
    )

    formatted = format_profile_for_llm(profile)

    # Check key sections are present
    assert "## User Profile" in formatted
    assert "de-DE" in formatted
    assert "professional" in formatted.lower()
    assert "examples_heavy" in formatted
    assert "### Boundaries" in formatted
    assert "Avoid overly formal" in formatted
    assert "### Current Projects" in formatted
    assert "KIM" in formatted


# ═══════════════════════════════════════════════════════════
# STORAGE TESTS
# ═══════════════════════════════════════════════════════════

@pytest.fixture
def temp_store(tmp_path):
    """Create a temporary ProfileStore for testing."""
    return ProfileStore(data_dir=tmp_path / "profiles")


@pytest.mark.asyncio
async def test_create_and_read_profile(temp_store):
    """Test creating and reading a profile."""
    profile = create_default_profile()
    profile.language = "de-DE"

    # Create
    created = await temp_store.create(profile)
    assert created.id == profile.id

    # Read
    loaded = await temp_store.read(profile.id)
    assert loaded is not None
    assert loaded.id == profile.id
    assert loaded.language == "de-DE"


@pytest.mark.asyncio
async def test_create_duplicate_profile_fails(temp_store):
    """Test that creating a duplicate profile raises an error."""
    profile = create_default_profile()

    # Create first time - should succeed
    await temp_store.create(profile)

    # Create second time - should fail
    with pytest.raises(FileExistsError):
        await temp_store.create(profile)


@pytest.mark.asyncio
async def test_save_updates_timestamp(temp_store):
    """Test that saving a profile updates the updated_at timestamp."""
    profile = create_default_profile()
    await temp_store.create(profile)

    original_time = profile.updated_at

    # Wait a tiny bit (to ensure timestamp difference)
    import asyncio
    await asyncio.sleep(0.01)

    # Update and save
    profile.language = "fr-FR"
    await temp_store.save(profile)

    # Reload and check timestamp changed
    loaded = await temp_store.read(profile.id)
    assert loaded.updated_at > original_time
    assert loaded.language == "fr-FR"


@pytest.mark.asyncio
async def test_delete_profile(temp_store):
    """Test deleting a profile."""
    profile = create_default_profile()
    await temp_store.create(profile)

    # Verify exists
    assert await temp_store.exists(profile.id)

    # Delete
    deleted = await temp_store.delete(profile.id)
    assert deleted is True

    # Verify gone
    assert not await temp_store.exists(profile.id)
    loaded = await temp_store.read(profile.id)
    assert loaded is None


@pytest.mark.asyncio
async def test_delete_nonexistent_profile(temp_store):
    """Test deleting a profile that doesn't exist."""
    fake_id = uuid4()
    deleted = await temp_store.delete(fake_id)
    assert deleted is False


@pytest.mark.asyncio
async def test_list_all_profiles(temp_store):
    """Test listing all profile IDs."""
    # Create multiple profiles
    profile1 = create_default_profile()
    profile2 = create_default_profile()

    await temp_store.create(profile1)
    await temp_store.create(profile2)

    # List all
    all_ids = await temp_store.list_all()
    assert len(all_ids) == 2
    assert profile1.id in all_ids
    assert profile2.id in all_ids


@pytest.mark.asyncio
async def test_get_or_create_profile_new(temp_store):
    """Test get_or_create with a new user."""
    user_id = uuid4()

    profile = await get_or_create_profile(user_id, temp_store)

    # Should create default profile with the given ID
    assert profile.id == user_id
    assert profile.confidence == 0.1  # Default

    # Should be persisted
    assert await temp_store.exists(user_id)


@pytest.mark.asyncio
async def test_get_or_create_profile_existing(temp_store):
    """Test get_or_create with an existing user."""
    # Create profile
    profile = create_default_profile()
    profile.language = "de-DE"
    await temp_store.create(profile)

    # Get or create should return existing
    loaded = await get_or_create_profile(profile.id, temp_store)
    assert loaded.id == profile.id
    assert loaded.language == "de-DE"


# ═══════════════════════════════════════════════════════════
# INTEGRATION TEST
# ═══════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_profile_round_trip(temp_store):
    """Test full create-read-update-delete cycle."""
    # Create
    profile = UserProfile(
        language="de-DE",
        tone=[Tone.TECHNICAL, Tone.FRIENDLY],
        format_preference=FormatPreference.STEP_BY_STEP,
        boundaries={"test": "value"},
        current_projects=["Project A"],
        recent_context="Test context"
    )

    await temp_store.create(profile)

    # Read
    loaded = await temp_store.read(profile.id)
    assert loaded.language == "de-DE"
    assert len(loaded.tone) == 2
    assert loaded.boundaries["test"] == "value"

    # Update
    loaded.confidence = 0.8
    loaded.current_projects.append("Project B")
    await temp_store.save(loaded)

    # Re-read
    updated = await temp_store.read(profile.id)
    assert updated.confidence == 0.8
    assert len(updated.current_projects) == 2

    # Delete
    await temp_store.delete(profile.id)
    assert await temp_store.read(profile.id) is None
