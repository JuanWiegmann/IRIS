"""
Research-Backed Onboarding Targets

All targets cite scientific evidence for inclusion.
Adaptive flow: Q1 (role) + Q2 (AI usage) → select relevant targets.
"""

from src.onboarding.schema import (
    BarrierType,
    OnboardingTarget,
    ProfileType,
    QuestionTemplate,
    QuestionType,
)


def get_all_targets() -> dict[str, OnboardingTarget]:
    """Get all possible onboarding targets."""
    return {
        # ═══════════════════════════════════════════════════════════
        # ANCHOR QUESTIONS (Always asked first)
        # ═══════════════════════════════════════════════════════════
        "role": OnboardingTarget(
            id="role",
            dimension="Professional Role & Responsibilities",
            research_basis="Foundation for adaptive question selection",
            applies_to_profile_types=[
                ProfileType.CODE_HEAVY,
                ProfileType.COMMUNICATION_HEAVY,
                ProfileType.ARCHITECTURE,
                ProfileType.GENERAL,
            ],
            priority=1,  # MUST ask
            question_template=QuestionTemplate(
                question_text="What do you do for work?",
                question_type=QuestionType.OPEN,
                example_prompt="Examples: 'Backend Developer', 'Team Lead', 'Solution Architect'",
            ),
            barrier_type=BarrierType.EXPLICIT_STATEMENT,
            barrier_criteria={"min_evidence_count": 1},
        ),
        "ai_usage": OnboardingTarget(
            id="ai_usage",
            dimension="AI Usage Context",
            research_basis="Determines which dimensions matter most (Wu 2024: context-driven relevance)",
            applies_to_profile_types=[
                ProfileType.CODE_HEAVY,
                ProfileType.COMMUNICATION_HEAVY,
                ProfileType.ARCHITECTURE,
                ProfileType.GENERAL,
            ],
            priority=1,  # MUST ask
            question_template=QuestionTemplate(
                question_text="What do you use AI for?",
                question_type=QuestionType.EXAMPLE_GUIDED,
                example_prompt="Examples: 'Writing code', 'Explaining concepts', 'Architecture decisions', 'Documentation'",
            ),
            barrier_type=BarrierType.EXPLICIT_STATEMENT,
            barrier_criteria={"min_evidence_count": 1},
        ),
        # ═══════════════════════════════════════════════════════════
        # CODE-HEAVY PATH (Developer, code review, debugging)
        # ═══════════════════════════════════════════════════════════
        "technical_depth": OnboardingTarget(
            id="technical_depth",
            dimension="Technical Detail Level",
            research_basis="Wu 2024: Response format is primary driver of personalization quality",
            applies_to_profile_types=[ProfileType.CODE_HEAVY, ProfileType.ARCHITECTURE],
            priority=2,  # Core for code-heavy users
            question_template=QuestionTemplate(
                question_text="Your colleague asks: 'How should we implement caching?' Which response style helps you more?",
                question_type=QuestionType.EDGE_CASE,
                options=[
                    {
                        "label": "Version A (Executive Summary)",
                        "value": "high_level",
                        "example_content": "Use Redis with 1h TTL. Reduces DB load by ~70%. Implementation: 2-3 days. Need Docker container.",
                    },
                    {
                        "label": "Version B (Technical Deep-Dive)",
                        "value": "detailed",
                        "example_content": """**Recommended Approach:**
Redis-based caching layer between API and DB

**Architecture:**
- Cache key: f"api:{endpoint}:{params_hash}"
- TTL: 3600s (configurable per endpoint)
- Invalidation: event-driven on data updates

**Expected Impact:**
- DB load reduction: ~70%
- Response time: 200ms → 20ms
- Infrastructure: 1 Redis cluster (HA setup)

**Implementation Estimate:**
- Backend changes: 2 days
- Infrastructure: 1 day
- Testing & rollout: 1 day

**Code Example:**
```python
@cache_response(ttl=3600)
def get_user_data(user_id):
    return db.query(...)
```""",
                    },
                    {"label": "Depends on question complexity", "value": "adaptive"},
                ],
            ),
            barrier_type=BarrierType.EDGE_CASE_CHOICE,
            barrier_criteria={"choices_made": 1},
        ),
        "code_documentation_style": OnboardingTarget(
            id="code_documentation_style",
            dimension="Code Documentation Preference",
            research_basis="GATE: Concrete examples reveal preferences users can't articulate",
            applies_to_profile_types=[ProfileType.CODE_HEAVY],
            priority=3,  # Core for developers
            question_template=QuestionTemplate(
                question_text="When I show code examples, which style fits your workflow?",
                question_type=QuestionType.EDGE_CASE,
                options=[
                    {
                        "label": "Style A (Self-Documenting)",
                        "value": "minimal",
                        "example_content": """def cache_get_or_fetch(key: str, fetcher: Callable, ttl: int = 3600):
    if cached := redis.get(key):
        return cached
    result = fetcher()
    redis.setex(key, ttl, result)
    return result""",
                    },
                    {
                        "label": "Style B (Explicitly Documented)",
                        "value": "documented",
                        "example_content": """def cache_get_or_fetch(key: str, fetcher: Callable, ttl: int = 3600):
    '''
    Get from cache or execute fetcher and cache result.

    Args:
        key: Cache key identifier
        fetcher: Function to call on cache miss
        ttl: Time-to-live in seconds (default 1h)

    Returns:
        Cached or freshly fetched result
    '''
    # Check cache first
    if cached := redis.get(key):
        return cached

    # Cache miss: fetch and store
    result = fetcher()
    redis.setex(key, ttl, result)
    return result""",
                    },
                    {"label": "Depends on complexity", "value": "adaptive"},
                ],
            ),
            barrier_type=BarrierType.EDGE_CASE_CHOICE,
            barrier_criteria={"choices_made": 1},
        ),
        "error_handling_approach": OnboardingTarget(
            id="error_handling_approach",
            dimension="Error/Debug Approach Preference",
            research_basis="Westhaeusser 2025: Work style preferences measurably impact UX",
            applies_to_profile_types=[ProfileType.CODE_HEAVY],
            priority=5,  # Nice to have
            question_template=QuestionTemplate(
                question_text="When you ask about an error or bug:",
                question_type=QuestionType.BINARY,
                options=[
                    {
                        "label": "Give me the most likely cause and fix first",
                        "value": "solution_first",
                    },
                    {
                        "label": "Show me the debugging approach step-by-step",
                        "value": "debug_process",
                    },
                ],
            ),
            barrier_type=BarrierType.BINARY_ANSWER,
            barrier_criteria={"min_evidence_count": 1},
        ),
        # ═══════════════════════════════════════════════════════════
        # COMMUNICATION-HEAVY PATH (Lead, manager, documentation)
        # ═══════════════════════════════════════════════════════════
        "communication_formality": OnboardingTarget(
            id="communication_formality",
            dimension="Professional Communication Style",
            research_basis="GATE: Edge-cases reveal tone preferences better than self-reporting",
            applies_to_profile_types=[ProfileType.COMMUNICATION_HEAVY],
            priority=2,  # Core for communication-heavy
            question_template=QuestionTemplate(
                question_text="You need to report a blocker to your team lead. Which message would you send?",
                question_type=QuestionType.EDGE_CASE,
                options=[
                    {
                        "label": "Version A (Direct)",
                        "value": "direct",
                        "example_content": """Subject: API Keys Missing – Blocker

Missing AWS API keys for test environment.
Can't proceed with integration tests.
Need them by EOD tomorrow.""",
                    },
                    {
                        "label": "Version B (Contextual)",
                        "value": "contextual",
                        "example_content": """Subject: Status Update – Blocker

Quick update on API integration:

Implementation is done, but I'm blocked on testing because AWS API keys for the test environment haven't been provisioned yet.

Could you help get those by EOD tomorrow? That would keep us on track for Friday demo.""",
                    },
                    {"label": "Depends on audience", "value": "adaptive"},
                ],
            ),
            barrier_type=BarrierType.EDGE_CASE_CHOICE,
            barrier_criteria={"choices_made": 1},
        ),
        "explanation_depth": OnboardingTarget(
            id="explanation_depth",
            dimension="Explanation Depth for Different Audiences",
            research_basis="Wu 2024: Context-aware responses improve quality",
            applies_to_profile_types=[ProfileType.COMMUNICATION_HEAVY],
            priority=3,  # Core for leads/managers
            question_template=QuestionTemplate(
                question_text="Your non-technical stakeholder asks: 'Why is this taking longer?' Which explanation fits better?",
                question_type=QuestionType.EDGE_CASE,
                options=[
                    {
                        "label": "Version A (Business-Focused)",
                        "value": "business_focused",
                        "example_content": """The database migration is more complex than expected. We're ensuring no data loss.
New timeline: 2 weeks. Risk: low if we proceed carefully.""",
                    },
                    {
                        "label": "Version B (Technical Detail)",
                        "value": "technical_detail",
                        "example_content": """The migration involves schema changes across 15 tables with referential integrity constraints.
We need to:
1. Create backup strategies
2. Test data transformation scripts
3. Validate consistency post-migration

This adds complexity but prevents data corruption.
Timeline: 2 weeks with proper testing.""",
                    },
                    {"label": "Depends on audience", "value": "adaptive"},
                ],
            ),
            barrier_type=BarrierType.EDGE_CASE_CHOICE,
            barrier_criteria={"choices_made": 1},
        ),
        "documentation_style": OnboardingTarget(
            id="documentation_style",
            dimension="Documentation Detail Level",
            research_basis="Westhaeusser 2025: Format preferences learned > stated",
            applies_to_profile_types=[ProfileType.COMMUNICATION_HEAVY],
            priority=5,  # Nice to have
            question_template=QuestionTemplate(
                question_text="When I help with documentation:",
                question_type=QuestionType.BINARY,
                options=[
                    {
                        "label": "Concise and to-the-point (README, quick guides)",
                        "value": "concise",
                    },
                    {
                        "label": "Comprehensive with examples (full documentation)",
                        "value": "comprehensive",
                    },
                ],
            ),
            barrier_type=BarrierType.BINARY_ANSWER,
            barrier_criteria={"min_evidence_count": 1},
        ),
        # ═══════════════════════════════════════════════════════════
        # ARCHITECTURE PATH (Architect, design decisions)
        # ═══════════════════════════════════════════════════════════
        "decision_support_style": OnboardingTarget(
            id="decision_support_style",
            dimension="Architectural Decision Support Style",
            research_basis="GATE: Forced choices reveal decision-making preferences",
            applies_to_profile_types=[ProfileType.ARCHITECTURE],
            priority=2,  # Core for architects
            question_template=QuestionTemplate(
                question_text="When you ask about architectural choices:",
                question_type=QuestionType.BINARY,
                options=[
                    {
                        "label": "Give me the recommended approach with rationale",
                        "value": "recommendation",
                    },
                    {
                        "label": "Show me 2-3 options with pros/cons/tradeoffs",
                        "value": "options_with_tradeoffs",
                    },
                ],
            ),
            barrier_type=BarrierType.BINARY_ANSWER,
            barrier_criteria={"min_evidence_count": 1},
        ),
        "technical_breadth": OnboardingTarget(
            id="technical_breadth",
            dimension="Technical Analysis Breadth",
            research_basis="Wu 2024: Response format drives quality",
            applies_to_profile_types=[ProfileType.ARCHITECTURE],
            priority=3,  # Core for architects
            question_template=QuestionTemplate(
                question_text="You're evaluating a new service architecture. Which analysis helps you more?",
                question_type=QuestionType.EDGE_CASE,
                options=[
                    {
                        "label": "Version A (Focused)",
                        "value": "focused",
                        "example_content": """**Recommended:** Event-driven with Kafka

Pros: Decoupling, scalability, async processing
Cons: Complexity, eventual consistency
Effort: 3-4 weeks
Risk: Medium (team needs Kafka expertise)""",
                    },
                    {
                        "label": "Version B (Comprehensive)",
                        "value": "comprehensive",
                        "example_content": """**Three Approaches:**

1. Event-Driven (Kafka)
   Pros: [...]  Cons: [...]  Effort: 3-4 weeks

2. API Gateway Pattern (Kong)
   Pros: [...]  Cons: [...]  Effort: 2-3 weeks

3. Service Mesh (Istio)
   Pros: [...]  Cons: [...]  Effort: 4-5 weeks

**Recommendation:** Event-driven given your scale requirements and team expertise.""",
                    },
                ],
            ),
            barrier_type=BarrierType.EDGE_CASE_CHOICE,
            barrier_criteria={"choices_made": 1},
        ),
        # ═══════════════════════════════════════════════════════════
        # UNIVERSAL QUESTIONS (Asked to everyone after Q1+Q2)
        # ═══════════════════════════════════════════════════════════
        "language": OnboardingTarget(
            id="language",
            dimension="Response Language",
            research_basis="Basic requirement for generation",
            applies_to_profile_types=[
                ProfileType.CODE_HEAVY,
                ProfileType.COMMUNICATION_HEAVY,
                ProfileType.ARCHITECTURE,
                ProfileType.GENERAL,
            ],
            priority=1,  # MUST ask
            question_template=QuestionTemplate(
                question_text="In which language should I respond?",
                question_type=QuestionType.BINARY,
                options=[
                    {"label": "Deutsch", "value": "de"},
                    {"label": "English", "value": "en"},
                    {"label": "Both (depends on context)", "value": "both"},
                ],
            ),
            barrier_type=BarrierType.BINARY_ANSWER,
            barrier_criteria={"min_evidence_count": 1},
        ),
        "current_focus": OnboardingTarget(
            id="current_focus",
            dimension="Current Projects/Focus Areas",
            research_basis="Wu 2024: Context needed for relevance-ranked retrieval",
            applies_to_profile_types=[
                ProfileType.CODE_HEAVY,
                ProfileType.COMMUNICATION_HEAVY,
                ProfileType.ARCHITECTURE,
                ProfileType.GENERAL,
            ],
            priority=2,  # Core for context
            question_template=QuestionTemplate(
                question_text="What are you currently working on or focused on?",
                question_type=QuestionType.OPEN,
                example_prompt="Examples: 'Migrating to microservices', 'Building ML pipeline', 'Learning React'",
            ),
            barrier_type=BarrierType.EXPLICIT_STATEMENT,
            barrier_criteria={"min_evidence_count": 1},
        ),
        "learning_approach": OnboardingTarget(
            id="learning_approach",
            dimension="Learning/Explanation Approach",
            research_basis="GATE: Concrete scenarios reveal tacit learning preferences",
            applies_to_profile_types=[
                ProfileType.CODE_HEAVY,
                ProfileType.COMMUNICATION_HEAVY,
                ProfileType.ARCHITECTURE,
                ProfileType.GENERAL,
            ],
            priority=4,  # Nice to have
            question_template=QuestionTemplate(
                question_text="When learning something new, do you prefer:",
                question_type=QuestionType.BINARY,
                options=[
                    {
                        "label": "Start with concrete example/code, then explain theory",
                        "value": "example_first",
                    },
                    {
                        "label": "Start with concept/architecture, then show implementation",
                        "value": "concept_first",
                    },
                ],
            ),
            barrier_type=BarrierType.BINARY_ANSWER,
            barrier_criteria={"min_evidence_count": 1},
        ),
        "proactivity": OnboardingTarget(
            id="proactivity",
            dimension="Proactivity Preference",
            research_basis="Westhaeusser 2025: User control over AI initiative measurably impacts UX",
            applies_to_profile_types=[
                ProfileType.CODE_HEAVY,
                ProfileType.COMMUNICATION_HEAVY,
                ProfileType.ARCHITECTURE,
                ProfileType.GENERAL,
            ],
            priority=4,  # Nice to have
            question_template=QuestionTemplate(
                question_text="When I see potential issues or better approaches:",
                question_type=QuestionType.BINARY,
                options=[
                    {
                        "label": "Point them out proactively",
                        "value": "proactive",
                    },
                    {
                        "label": "Only answer what's asked, no extra suggestions",
                        "value": "reactive",
                    },
                ],
            ),
            barrier_type=BarrierType.BINARY_ANSWER,
            barrier_criteria={"min_evidence_count": 1},
        ),
        "privacy": OnboardingTarget(
            id="privacy",
            dimension="Privacy & Storage Boundaries",
            research_basis="GDPR/privacy requirement, user control over data",
            applies_to_profile_types=[
                ProfileType.CODE_HEAVY,
                ProfileType.COMMUNICATION_HEAVY,
                ProfileType.ARCHITECTURE,
                ProfileType.GENERAL,
            ],
            priority=1,  # MUST ask (legal requirement)
            question_template=QuestionTemplate(
                question_text="May I store technical context (projects, tech stack) to provide better answers in future conversations?",
                question_type=QuestionType.BINARY,
                options=[
                    {"label": "Yes, store work context", "value": "store_all"},
                    {
                        "label": "Only general preferences, no project details",
                        "value": "preferences_only",
                    },
                    {
                        "label": "No, fresh start each time",
                        "value": "no_storage",
                    },
                ],
            ),
            barrier_type=BarrierType.EXPLICIT_STATEMENT,
            barrier_criteria={"min_evidence_count": 1},
        ),
    }
