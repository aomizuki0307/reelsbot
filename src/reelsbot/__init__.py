"""Reelsbot: Instagram Reels automation system with abstract and fictional content generation."""

__version__ = "0.1.0"

from reelsbot.caption_generator import CaptionGenerator, CaptionGeneratorError
from reelsbot.config import ReelsbotConfig, load_config
from reelsbot.llm_client import LLMClient, LLMError, create_llm_client
from reelsbot.models import ReelMetadata, ReelPlan
from reelsbot.orchestrator import Orchestrator, OrchestratorError
from reelsbot.planner import Planner, PlannerError
from reelsbot.policy_gate import PolicyGate, PolicyViolationError
from reelsbot.publisher import BasePublisher, DryRunPublisher, PublisherError
from reelsbot.storage import RunStorage, RunStorageError

__all__ = [
    "__version__",
    # Configuration
    "ReelsbotConfig",
    "load_config",
    # LLM Client
    "LLMClient",
    "LLMError",
    "create_llm_client",
    # Models
    "ReelPlan",
    "ReelMetadata",
    # Orchestrator
    "Orchestrator",
    "OrchestratorError",
    # Planner
    "Planner",
    "PlannerError",
    # Policy Gate
    "PolicyGate",
    "PolicyViolationError",
    # Caption Generator
    "CaptionGenerator",
    "CaptionGeneratorError",
    # Storage
    "RunStorage",
    "RunStorageError",
    # Publisher
    "BasePublisher",
    "PublisherError",
    "DryRunPublisher",
]
