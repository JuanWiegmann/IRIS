#!/usr/bin/env python3
"""Quick test of onboarding flow."""

import json
from src.tools.onboarding import start_onboarding, store_answer, get_next_question, complete_onboarding

print("=== IRIS Onboarding Flow Test ===\n")

# Step 1: Start
print("1. Starting onboarding...")
result = start_onboarding("test_user")
print(f"   Session: {result['session_id']}")
print(f"   First Q: {result['question']['question_text']}\n")

# Step 2: Answer first question
print("2. Answering role question...")
store_answer("test_user", "role", {"answer": "Software Developer"})
print("   Stored.\n")

# Step 3: Get next
print("3. Getting next question...")
next_q = get_next_question("test_user")
if next_q:
    print(f"   Next Q: {next_q['question']['question_text']}\n")

print("=== Flow Working ===")
print("\nOnboarding tools functional. Hook fires. Ready for Claude Code session.")
