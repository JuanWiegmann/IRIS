"""
IRIS Storage Inspector
=====================

CLI tool for inspecting IRIS's local storage.

Provides 100% transparency into what IRIS knows about the user.

Usage:
    python -m src.inspect
    python -m src.inspect --user-id <uuid>
    python -m src.inspect --detailed
"""

import argparse
import asyncio
from pathlib import Path
from uuid import UUID

from src.storage.file_store import get_iris_root, get_profile_store, get_output_store
from src.storage.embedding_store import get_embedding_store


# ═══════════════════════════════════════════════════════════
# INSPECTION FUNCTIONS
# ═══════════════════════════════════════════════════════════

async def inspect_storage(user_id: UUID, detailed: bool = False) -> None:
    """
    Inspect IRIS storage for a user.

    Args:
        user_id: User UUID
        detailed: Show detailed output contents
    """
    iris_root = get_iris_root()

    print("═" * 60)
    print("IRIS Storage Report")
    print("═" * 60)
    print()

    # ═══ USER INFO ═══
    print(f"User ID: {user_id}")
    print(f"Storage Root: {iris_root}")
    print()

    # ═══ PROFILE ═══
    profile_store = get_profile_store()

    if await profile_store.exists(user_id):
        profile = await profile_store.read(user_id)
        profile_path = iris_root / "profiles" / f"{user_id}.json"
        profile_size = profile_path.stat().st_size if profile_path.exists() else 0

        print("┌─ Profile")
        print(f"│  Path: {profile_path}")
        print(f"│  Size: {profile_size:,} bytes")
        print(f"│  Language: {profile.language}")
        print(f"│  Tone: {', '.join([t.value for t in profile.tone])}")
        print(f"│  Format: {profile.format_preference.value}")
        print(f"│  Confidence: {profile.confidence:.0%}")
        print(f"│  Updated: {profile.updated_at.strftime('%Y-%m-%d %H:%M')}")

        if profile.boundaries:
            print(f"│  Boundaries:")
            for category, rule in profile.boundaries.items():
                print(f"│    - {category}: {rule[:50]}...")

        print("└─")
    else:
        print("┌─ Profile")
        print("│  Status: Not found")
        print("└─")

    print()

    # ═══ OUTPUTS ═══
    output_store = get_output_store()
    outputs = await output_store.list_all(user_id)

    if outputs:
        total_words = sum(o["metadata"].get("word_count", 0) for o in outputs)
        outputs_dir = iris_root / "outputs" / str(user_id)

        # Calculate total size
        total_size = sum(
            f.stat().st_size
            for f in outputs_dir.glob("*.json")
            if f.is_file()
        )

        print("┌─ Outputs")
        print(f"│  Count: {len(outputs)} files")
        print(f"│  Total Size: {total_size:,} bytes")
        print(f"│  Total Words: {total_words:,}")
        print(f"│  Directory: {outputs_dir}")
        print("│")
        print("│  Recent Outputs:")

        # Show last 5 outputs
        for output in outputs[-5:]:
            output_id = output["id"]
            context = output.get("context", "")
            created = output.get("created_at", "")
            word_count = output["metadata"].get("word_count", 0)
            output_type = output.get("output_type", "other")

            print(f"│    {output_id}. {context} ({output_type}, {word_count} words)")
            print(f"│       Created: {created}")

            if detailed and "content" in output:
                # Show first 100 chars of content
                content_preview = output["content"][:100].replace("\n", " ")
                print(f"│       Preview: {content_preview}...")

        print("└─")
    else:
        print("┌─ Outputs")
        print("│  Status: No outputs stored yet")
        print("└─")

    print()

    # ═══ EMBEDDINGS ═══
    embedding_store = get_embedding_store()

    if await embedding_store.exists(user_id):
        embeddings_path = iris_root / "embeddings" / f"{user_id}.npy"
        embeddings_size = embeddings_path.stat().st_size if embeddings_path.exists() else 0

        # Load to get count
        embeddings, output_ids = await embedding_store.load(user_id)

        print("┌─ Embeddings")
        print(f"│  Count: {len(embeddings)} vectors")
        print(f"│  Dimensions: 768 (text-embedding-3-small)")
        print(f"│  Size: {embeddings_size:,} bytes")
        print(f"│  Path: {embeddings_path}")
        print("└─")
    else:
        print("┌─ Embeddings")
        print("│  Status: No embeddings stored yet")
        print("└─")

    print()

    # ═══ SUMMARY ═══
    profile_size_kb = profile_size / 1024 if await profile_store.exists(user_id) else 0
    outputs_size_kb = total_size / 1024 if outputs else 0
    embeddings_size_kb = embeddings_size / 1024 if await embedding_store.exists(user_id) else 0
    total_size_kb = profile_size_kb + outputs_size_kb + embeddings_size_kb

    print("┌─ Storage Summary")
    print(f"│  Profile: {profile_size_kb:.1f} KB")
    print(f"│  Outputs: {outputs_size_kb:.1f} KB ({len(outputs)} files)")
    print(f"│  Embeddings: {embeddings_size_kb:.1f} KB")
    print(f"│  Total: {total_size_kb:.1f} KB")
    print("└─")
    print()

    print("═" * 60)


async def list_all_users() -> None:
    """List all users with IRIS data."""
    profile_store = get_profile_store()
    user_ids = await profile_store.list_all()

    if not user_ids:
        print("No users found.")
        return

    print("═" * 60)
    print(f"Found {len(user_ids)} user(s):")
    print()

    for user_id in user_ids:
        profile = await profile_store.read(user_id)
        output_store = get_output_store()
        outputs = await output_store.list_all(user_id)

        print(f"• {user_id}")
        print(f"  Language: {profile.language}")
        print(f"  Outputs: {len(outputs)}")
        print(f"  Last updated: {profile.updated_at.strftime('%Y-%m-%d %H:%M')}")
        print()

    print("═" * 60)


# ═══════════════════════════════════════════════════════════
# CLI ENTRY POINT
# ═══════════════════════════════════════════════════════════

def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Inspect IRIS's local storage",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m src.inspect
  python -m src.inspect --user-id 00000000-0000-0000-0000-000000000001
  python -m src.inspect --detailed
  python -m src.inspect --list-users
        """
    )

    parser.add_argument(
        "--user-id",
        type=str,
        help="User UUID to inspect (default: demo user)"
    )

    parser.add_argument(
        "--detailed",
        action="store_true",
        help="Show detailed output contents"
    )

    parser.add_argument(
        "--list-users",
        action="store_true",
        help="List all users with IRIS data"
    )

    args = parser.parse_args()

    # List users mode
    if args.list_users:
        asyncio.run(list_all_users())
        return

    # Inspect specific user
    if args.user_id:
        user_id = UUID(args.user_id)
    else:
        # Default: demo user
        user_id = UUID("00000000-0000-0000-0000-000000000001")

    asyncio.run(inspect_storage(user_id, detailed=args.detailed))


if __name__ == "__main__":
    main()
