"""
Update IRIS Profile + Memory
=============================

Updates:
1. Profile: Add new response_structure boundary
2. STM: Store conversation about Layer 2 + Memory
3. Project Memory: Log major features built today
"""
import asyncio
import json
from pathlib import Path
from datetime import datetime

async def update_iris():
    from src.utils import get_user_id
    from src.memory import store_message
    from src.tools.project_context import save_project_update

    user_id = get_user_id()
    print(f"Updating IRIS for user: {user_id}")

    # ═══ 1. UPDATE PROFILE ═══
    print("\n1. Updating profile...")

    profile_path = Path.home() / ".iris" / "data" / "profiles" / f"{user_id}.json"

    if not profile_path.exists():
        print("   [WARN] Profile not found, skipping")
    else:
        with open(profile_path, "r", encoding="utf-8") as f:
            profile = json.load(f)

        # Add new boundary
        new_boundary = (
            "Response structure for long explanations: "
            "Skip complete feature lists and optional extensions. "
            "Instead use simple format: "
            "1. Done? (yes/no - if no, what was the problem) "
            "2. Missing anything?"
        )

        profile["boundaries"]["response_structure"] = new_boundary
        profile["updated_at"] = datetime.utcnow().isoformat()

        with open(profile_path, "w", encoding="utf-8") as f:
            json.dump(profile, f, indent=2)

        print("   [OK] Profile updated with new response_structure boundary")

    # ═══ 2. UPDATE STM ═══
    print("\n2. Updating STM...")

    store_message(
        user_id,
        "user",
        "Build Layer 2 (MCP sampling) and Memory Tiers (STM/Summaries/LTM)"
    )

    store_message(
        user_id,
        "assistant",
        "Built Layer 2 (fresh-context validation tool) + Memory Tiers. "
        "All tests passed. LTM reuses project_context system."
    )

    print("   [OK] STM updated with today's conversation")

    # ═══ 3. UPDATE PROJECT MEMORY (LTM) ═══
    print("\n3. Updating Project Memory (LTM)...")

    save_project_update(
        user_id=user_id,
        project="IRIS",
        update="Completed Layer 2 (MCP Sampling) + Memory Tiers (STM/Summaries/LTM)",
        context=(
            "Layer 2: Tool-based fresh-context validation (workaround for MCP SDK limitation). "
            "Memory: 3 tiers - STM (last 10 msgs), Summaries (compressed history), "
            "LTM (reuses project_context). Integration: get_context() returns all tiers."
        ),
        update_type="major_change"
    )

    print("   [OK] Project memory updated")

    print("\n[SUCCESS] IRIS profile + memory fully updated")
    print("\nNEXT TIME YOU USE IRIS:")
    print("- Responses will be shorter (no feature lists)")
    print("- Format: 1. Done? 2. Missing?")
    print("- get_context() will remember today's work")

if __name__ == "__main__":
    asyncio.run(update_iris())
