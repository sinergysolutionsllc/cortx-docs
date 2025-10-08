"""
CORTX RulePack SDK

SDK for building domain-specific validation containers that plug into CORTX.
"""

from cortx_rulepack_sdk.base import RulePackBase
from cortx_rulepack_sdk.client import RulePackClient
from cortx_rulepack_sdk.contracts import (
    ExplanationRequest,
    ExplanationResponse,
    RulePackInfo,
    RulePackMetadata,
    ValidationFailure,
    ValidationMode,
    ValidationOptions,
    ValidationRequest,
    ValidationResponse,
)
from cortx_rulepack_sdk.registry import RegistryClient, RulePackRegistration

__version__ = "0.1.0"

__all__ = [
    # Base classes
    "RulePackBase",
    # Contracts
    "RulePackInfo",
    "ValidationRequest",
    "ValidationResponse",
    "ValidationFailure",
    "ExplanationRequest",
    "ExplanationResponse",
    "RulePackMetadata",
    "ValidationOptions",
    "ValidationMode",
    # Clients
    "RulePackClient",
    "RegistryClient",
    "RulePackRegistration",
]
