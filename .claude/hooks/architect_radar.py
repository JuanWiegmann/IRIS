"""
Architect Radar Hook (PostToolUse)

Fires AFTER an Edit or Write tool completes.
Analyzes the change and checks if it touches a Claude Certified Architect topic.
If yes, surfaces a learning opportunity with a link to the relevant module.
"""

import json
import sys
import re
from pathlib import Path


# Certification topic detection rules
# Each rule: (patterns_to_match, topic_name, learning_path, brief_description)
TOPIC_RULES = [
    {
        "patterns": [r"class.*Agent", r"def invoke", r"tool_use", r"while.*loop", r"max_iterations"],
        "topic": "Agentic Loops & Tool Use",
        "module": "learning/01_agentic_loops/README.md",
        "hint": "The observe-think-act cycle. How agents decide when to use tools and when to stop.",
    },
    {
        "patterns": [r"system.*prompt", r"few.?shot", r"structured.*output", r"json_schema", r"<examples>"],
        "topic": "Prompt Engineering",
        "module": "learning/02_prompt_engineering/README.md",
        "hint": "How you instruct the LLM. System prompts, examples, output constraints.",
    },
    {
        "patterns": [r"coordinator", r"handoff", r"agent.*agent", r"pipeline", r"orchestrat"],
        "topic": "Multi-Agent Orchestration",
        "module": "learning/03_multi_agent/README.md",
        "hint": "Multiple agents working together. Routing, handoffs, sequential pipelines.",
    },
    {
        "patterns": [r"retry", r"circuit.?breaker", r"timeout", r"logging", r"metrics", r"tracing"],
        "topic": "Production Readiness",
        "module": "learning/04_production/README.md",
        "hint": "Making AI systems reliable. Error recovery, observability, cost control.",
    },
    {
        "patterns": [r"ollama", r"bedrock", r"model_id", r"route.*model", r"provider", r"LLMClient"],
        "topic": "LLM Routing & Providers",
        "module": "learning/05_llm_routing/README.md",
        "hint": "Choosing the right model for the task. Local vs cloud, cost vs quality.",
    },
    {
        "patterns": [r"embed", r"vector", r"retriev", r"long.?term", r"short.?term", r"ChromaDB", r"similarity"],
        "topic": "Persistent Memory & RAG",
        "module": "learning/06_memory/README.md",
        "hint": "How AI remembers. Embeddings, vector search, memory tiers.",
    },
    {
        "patterns": [r"profile", r"preference", r"onboarding", r"GATE", r"elicit", r"edge.?case"],
        "topic": "User Modeling & Preference Elicitation",
        "module": "learning/07_user_profiles/README.md",
        "hint": "Building a model of who the user is. GATE methodology, implicit learning.",
    },
]


def detect_topics(content: str) -> list:
    """Find all certification topics that the content touches."""
    detected = []
    for rule in TOPIC_RULES:
        for pattern in rule["patterns"]:
            if re.search(pattern, content, re.IGNORECASE):
                detected.append(rule)
                break
    return detected


def main():
    try:
        input_data = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        json.dump({"continue": True}, sys.stdout)
        return

    tool_input = input_data.get("tool_input", {})
    file_path = tool_input.get("file_path", "")
    content = tool_input.get("content", "") or tool_input.get("new_string", "")

    # Skip non-source files
    if not file_path or not content:
        json.dump({"continue": True}, sys.stdout)
        return

    # Skip learning materials themselves, configs, plans
    skip_paths = [".claude/plans", ".claude/projects", "learning/", "CLAUDE.md"]
    if any(skip in file_path.replace("\\", "/") for skip in skip_paths):
        json.dump({"continue": True}, sys.stdout)
        return

    topics = detect_topics(content)

    if not topics:
        json.dump({"continue": True}, sys.stdout)
        return

    # Build learning message
    lines = ["Architect Radar detected certification-relevant patterns:"]
    for topic in topics[:3]:  # Max 3 topics per change
        lines.append(f"  [{topic['topic']}] {topic['hint']}")
        lines.append(f"  Deep-dive: {topic['module']}")
    lines.append("Ask for a deep-dive on any topic if you want to understand more.")

    message = "\n".join(lines)

    output = {
        "continue": True,
        "hookSpecificOutput": {
            "hookEventName": "PostToolUse",
            "additionalContext": message
        }
    }
    json.dump(output, sys.stdout)


if __name__ == "__main__":
    main()
