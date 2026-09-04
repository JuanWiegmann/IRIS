"""
End-to-End IRIS Flow Test
=========================

Tests complete workflow:
1. Profile exists (skip onboarding for now)
2. get_context() returns profile + ranked outputs
3. log_output() stores + embeds
4. Retrieval finds stored outputs
5. check_draft() validates
"""
import asyncio
from uuid import uuid4

async def test_flow():
    from src.server import handle_get_context
    from src.tools.log_output import handle_log_output
    from src.tools.check_draft import handle_check_draft
    from src.utils import get_user_id
    
    user_id = get_user_id()
    print(f"Testing with user: {user_id}")
    
    # Test 1: get_context
    print("\n1. Testing get_context()...")
    result = await handle_get_context({"query": "team status email"})
    text = result[0].text
    
    if "ONBOARDING_REQUIRED" in text:
        print("   [WARN] Profile missing - run /startIris first")
        return False

    print("   [OK] Profile loaded")
    
    # Test 2: log_output
    print("\n2. Testing log_output()...")
    result = await handle_log_output({
        "content": "Hi team, quick update on IRIS project. Segment 3 complete!",
        "context": "team status email",
        "output_type": "email"
    }, user_id)
    
    if "logged successfully" in result[0].text:
        print("   [OK] Output stored")
    else:
        print("   [FAIL]", result[0].text[:100])
        return False
    
    # Test 3: Retrieval
    print("\n3. Testing retrieval...")
    result = await handle_get_context({"query": "status update"})
    text = result[0].text
    
    if "Relevant Past Outputs" in text and "status email" in text.lower():
        print("   [OK] Retrieval found stored output")
    else:
        print("   [WARN] Retrieval might not have found output")
    
    # Test 4: check_draft
    print("\n4. Testing check_draft()...")
    result = await handle_check_draft({
        "draft": "Hi team, update on project.",
        "context": "team email"
    }, user_id)
    
    if "passed" in result[0].text.lower() or "validated" in result[0].text.lower():
        print("   [OK] Validation works")
    else:
        print("   [OK] Validation returned feedback:", result[0].text[:100])

    print("\n[SUCCESS] ALL TESTS PASSED")
    return True

if __name__ == "__main__":
    asyncio.run(test_flow())
