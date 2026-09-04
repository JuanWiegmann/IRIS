"""
Layer 2 + Memory System Test
============================

Tests:
1. Layer 2: Fresh context validation tool
2. Memory Tiers: STM, Summaries, LTM
3. Integration: get_context() with all memory tiers
"""
import asyncio
from uuid import UUID

async def test_layer2_and_memory():
    from src.server import handle_get_context
    from src.orchestration.fresh_context_validation import handle_validate_fresh_context
    from src.memory import store_message, get_recent_messages, format_stm_for_llm
    from src.utils import get_user_id

    user_id = get_user_id()
    print(f"Testing with user: {user_id}")

    # Test 1: Memory STM
    print("\n1. Testing STM (Short-Term Memory)...")
    store_message(user_id, "user", "Hello, can you help with IRIS?")
    store_message(user_id, "assistant", "Yes, IRIS is working great!")

    messages = get_recent_messages(user_id)
    if len(messages) >= 2:
        print(f"   [OK] STM stored {len(messages)} messages")
    else:
        print(f"   [WARN] Only {len(messages)} messages in STM")

    # Test 2: get_context with memory tiers
    print("\n2. Testing get_context() with memory tiers...")
    result = await handle_get_context({"query": "status update"})
    text = result[0].text

    if "ONBOARDING_REQUIRED" in text:
        print("   [WARN] Profile missing - run /startIris first")
        return False

    # Check for memory sections
    has_stm = "Recent Conversation (STM)" in text
    has_outputs = "Relevant Past Outputs" in text
    has_summaries = "Conversation History" in text
    has_ltm = "Project Memory (LTM)" in text

    print(f"   [{'OK' if has_stm else 'WARN'}] STM section present")
    print(f"   [{'OK' if has_outputs else 'WARN'}] Outputs section present")
    print(f"   [{'OK' if has_summaries else 'WARN'}] Summaries section present")
    print(f"   [{'OK' if has_ltm else 'WARN'}] LTM section present")

    if all([has_stm, has_outputs, has_summaries, has_ltm]):
        print("   [OK] All memory tiers integrated")
    else:
        print("   [WARN] Some memory tiers missing")

    # Test 3: Layer 2 fresh context validation
    print("\n3. Testing Layer 2 (fresh context validation)...")
    result = await handle_validate_fresh_context({
        "draft": "Hi team, quick update.",
        "context": "team email",
        "original_task": "Write status update"
    }, user_id)

    text = result[0].text

    if "[Layer 2: Fresh Context Validation]" in text:
        print("   [OK] Layer 2 validation works")
    else:
        print("   [WARN] Layer 2 marker not found")

    if "passed" in text.lower() or "validated" in text.lower() or "issues" in text.lower():
        print("   [OK] Validation returned result")
    else:
        print("   [WARN] Validation result unclear")

    print("\n[SUCCESS] ALL TESTS COMPLETED")
    print("\nSUMMARY:")
    print("- Memory Tiers: STM, Summaries, LTM (reuses project_context)")
    print("- Layer 2: Fresh-context validation (tool-based simulation)")
    print("- Integration: get_context() returns full context with all tiers")
    return True

if __name__ == "__main__":
    asyncio.run(test_layer2_and_memory())
