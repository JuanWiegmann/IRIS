"""
Onboarding Target Schema - GATE Methodology

Research basis:
- GATE (Li et al. 2023): Edge-case questions reveal tacit preferences
- Wu et al. 2024: User outputs are primary personalization driver
- Westhaeusser et al. 2025: 5-7 questions capture essentials, 18-22% better learned vs. stated

Design: Adaptive 10-question flow based on role + AI usage context
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class QuestionType(str, Enum):
    """Question types from GATE research."""

    EDGE_CASE = "edge_case"  # Most effective: shows 2-3 examples, forces choice
    BINARY = "binary"  # Systematic exploration: yes/no or A/B
    OPEN = "open"  # Minimal use: factual info only
    EXAMPLE_GUIDED = "example_guided"  # Open with example options


class BarrierType(str, Enum):
    """How satisfaction is measured."""

    EDGE_CASE_CHOICE = "edge_case_choice"  # User picked between concrete examples
    BINARY_ANSWER = "binary_answer"  # User chose A or B
    EXPLICIT_STATEMENT = "explicit_statement"  # User directly stated preference
    MINIMUM_EVIDENCE = "minimum_evidence"  # N pieces of evidence collected
    CONFIDENCE_THRESHOLD = "confidence_threshold"  # Confidence score >= X


class ProfileType(str, Enum):
    """Detected user profile type (determines question path)."""

    CODE_HEAVY = "code_heavy"  # Developer writing/reviewing code
    COMMUNICATION_HEAVY = "communication_heavy"  # Lead/manager writing docs/emails
    ARCHITECTURE = "architecture"  # Architect making design decisions
    GENERAL = "general"  # Default if unclear


class QuestionTemplate(BaseModel):
    """Template for a question with examples."""

    question_text: str = Field(..., description="Question to ask")
    question_type: QuestionType
    options: Optional[List[Dict[str, str]]] = Field(
        None,
        description="Options for binary/edge-case questions. Each: {label, value, example_content?}",
    )
    example_prompt: Optional[str] = Field(
        None, description="Example prompt for open questions"
    )


class OnboardingTarget(BaseModel):
    """
    A dimension to learn about the user.

    Based on Wu 2024: Focus on dimensions that measurably improve personalization.
    """

    id: str = Field(..., description="Unique identifier (e.g., 'technical_depth')")
    dimension: str = Field(..., description="What this target captures")
    research_basis: str = Field(
        ..., description="Citation for why this matters (Wu 2024, GATE, etc.)"
    )
    applies_to_profile_types: List[ProfileType] = Field(
        ..., description="Which profile types need this dimension"
    )
    priority: int = Field(
        ..., ge=1, le=10, description="1=must ask, 10=optional enhancement"
    )

    # Question templates
    question_template: QuestionTemplate

    # Barrier (when is this satisfied?)
    barrier_type: BarrierType
    barrier_criteria: Dict[str, Any] = Field(
        ...,
        description="Criteria for satisfaction (e.g., {'min_confidence': 0.7} or {'choices_made': 1})",
    )

    # State
    satisfied: bool = Field(default=False, description="Has barrier been met?")
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    evidence: List[Dict[str, Any]] = Field(
        default_factory=list, description="Collected evidence"
    )

    def is_satisfied(self) -> bool:
        """Check if barrier criteria are met."""
        if self.barrier_type == BarrierType.EDGE_CASE_CHOICE:
            # User made at least one edge-case choice
            return len(self.evidence) >= 1

        elif self.barrier_type == BarrierType.BINARY_ANSWER:
            # User answered at least one binary question
            return len(self.evidence) >= 1

        elif self.barrier_type == BarrierType.EXPLICIT_STATEMENT:
            # User explicitly stated something
            return len(self.evidence) >= 1

        elif self.barrier_type == BarrierType.MINIMUM_EVIDENCE:
            # N pieces of evidence required
            required = self.barrier_criteria.get("min_evidence_count", 1)
            return len(self.evidence) >= required

        elif self.barrier_type == BarrierType.CONFIDENCE_THRESHOLD:
            # Confidence score above threshold
            threshold = self.barrier_criteria.get("min_confidence", 0.7)
            return self.confidence >= threshold

        return False

    def add_evidence(self, evidence: Dict[str, Any], confidence_delta: float = 0.0):
        """Add evidence and update satisfaction."""
        self.evidence.append(
            {
                "timestamp": datetime.utcnow().isoformat(),
                "data": evidence,
            }
        )
        self.confidence = min(1.0, self.confidence + confidence_delta)
        self.satisfied = self.is_satisfied()


class OnboardingSession(BaseModel):
    """Tracks an active onboarding session."""

    user_id: str
    session_id: str
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None

    # Phase 1: Anchor questions (always asked first)
    role: Optional[str] = None  # Q1: What do you do for work?
    ai_usage: Optional[str] = None  # Q2: What do you use AI for?

    # Detected profile type (determines question path)
    profile_type: Optional[ProfileType] = None

    # All targets for this session
    targets: Dict[str, OnboardingTarget] = Field(default_factory=dict)

    # Progress tracking
    questions_asked: int = Field(default=0)
    questions_remaining: List[str] = Field(
        default_factory=list, description="Target IDs to ask about"
    )
    current_target_id: Optional[str] = None

    # Session state
    is_completed: bool = Field(default=False)
    time_budget_seconds: int = Field(default=300, description="Target: 5 minutes")

    def add_answer(
        self, target_id: str, evidence: Dict[str, Any], confidence_delta: float = 0.3
    ):
        """Record an answer and update progress."""
        if target_id not in self.targets:
            raise ValueError(f"Unknown target: {target_id}")

        target = self.targets[target_id]
        target.add_evidence(evidence, confidence_delta)

        self.questions_asked += 1

        # Populate role/ai_usage fields for anchor questions
        if target_id == "role":
            self.role = evidence.get("answer") or evidence.get("chosen_option")
        elif target_id == "ai_usage":
            self.ai_usage = evidence.get("answer") or evidence.get("chosen_option")

        # Remove from remaining if satisfied
        if target.satisfied and target_id in self.questions_remaining:
            self.questions_remaining.remove(target_id)

    def get_next_target(self) -> Optional[OnboardingTarget]:
        """Get next target to ask about (priority order)."""
        if not self.questions_remaining:
            return None

        # Sort by priority (1 = highest)
        remaining_targets = [
            self.targets[tid]
            for tid in self.questions_remaining
            if tid in self.targets
        ]
        remaining_targets.sort(key=lambda t: t.priority)

        return remaining_targets[0] if remaining_targets else None

    def get_satisfied_dimensions(self) -> List[str]:
        """Get list of satisfied dimension names."""
        return [
            target.dimension
            for target in self.targets.values()
            if target.satisfied
        ]

    def get_core_satisfaction_rate(self) -> float:
        """Percentage of core targets (priority 1-3) satisfied."""
        core_targets = [t for t in self.targets.values() if t.priority <= 3]
        if not core_targets:
            return 1.0

        satisfied_core = [t for t in core_targets if t.satisfied]
        return len(satisfied_core) / len(core_targets)

    def can_complete(self) -> bool:
        """Can onboarding be completed? (Core targets satisfied)."""
        return self.get_core_satisfaction_rate() >= 0.8  # 80% of core targets

    def complete(self):
        """Mark session as complete."""
        self.is_completed = True
        self.completed_at = datetime.utcnow()


class InformationPool(BaseModel):
    """
    Information IRIS provides to LLM before/after each question.

    Design: Transparent progress + research-backed guidance.
    """

    # Before question
    session_progress: Dict[str, Any] = Field(
        ...,
        description="Current state: questions asked, core satisfied, time elapsed",
    )

    next_target: Optional[Dict[str, Any]] = Field(
        None,
        description="Next target to ask about: dimension, question template, research basis",
    )

    recommended_strategy: Optional[str] = Field(
        None, description="How to ask this question (based on research)"
    )

    # After answer
    validation_result: Optional[Dict[str, Any]] = Field(
        None,
        description="Was barrier met? New confidence? Inferred preferences?",
    )

    should_continue: bool = Field(
        default=True, description="Should LLM continue asking?"
    )

    completion_reason: Optional[str] = Field(
        None, description="Why stopping (core complete, time budget, user request)"
    )
