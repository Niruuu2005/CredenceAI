"""
Agent Policy Validator for CredenceAI Iteration 0.4

Ensures AI agents cannot bypass security policies and safety guardrails.
Critical for maintaining system integrity and preventing policy violations.

GUARDRAILS (Non-negotiable):
- Agents CANNOT override robots.txt rules
- Agents CANNOT bypass SSRF protection
- Agents CANNOT change MIME validation results
- Agents CANNOT index rejected/unsafe payloads
- All agent decisions must be logged
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class PolicyViolationError(Exception):
    """Raised when an agent attempts to violate security policy."""
    pass


class AgentPolicyValidator:
    """
    Validates that agent decisions comply with security policies.
    
    This validator ensures agents operate within strict boundaries and
    cannot compromise system security or bypass safety mechanisms.
    """
    
    # Blocked actions that agents cannot perform
    BLOCKED_ACTIONS = [
        "bypass_robots_txt",
        "bypass_ssrf_protection",
        "bypass_mime_validation",
        "index_rejected_content",
        "modify_crawl_policy",
        "disable_rate_limiting",
        "access_private_ips",
        "skip_content_validation"
    ]
    
    def __init__(self, enforce: bool = True):
        """
        Initialize policy validator.
        
        Args:
            enforce: Whether to enforce policies (should always be True in production)
        """
        self.enforce = enforce
        if not enforce:
            logger.warning("⚠️  Policy enforcement is DISABLED - use only for testing!")
    
    def validate_agent_recommendation(
        self,
        agent_name: str,
        recommendation: Dict[str, Any],
        context: Dict[str, Any]
    ) -> bool:
        """
        Validate that an agent's recommendation complies with policies.
        
        Args:
            agent_name: Name of the agent
            recommendation: Agent's recommendation/decision
            context: Context including policy decisions
            
        Returns:
            True if valid, raises PolicyViolationError if invalid
            
        Raises:
            PolicyViolationError: If recommendation violates policy
        """
        if not self.enforce:
            return True
        
        # Check for blocked actions
        requested_actions = recommendation.get("actions", [])
        for action in requested_actions:
            if action in self.BLOCKED_ACTIONS:
                self._raise_violation(
                    agent_name,
                    f"Attempted blocked action: {action}",
                    recommendation
                )
        
        # Validate crawl recommendations
        if "crawl" in recommendation.get("decision", "").lower():
            self._validate_crawl_recommendation(agent_name, recommendation, context)
        
        # Validate indexing recommendations
        if "index" in recommendation.get("decision", "").lower():
            self._validate_indexing_recommendation(agent_name, recommendation, context)
        
        # Validate URL recommendations
        if "url" in recommendation or "urls" in recommendation:
            self._validate_url_recommendation(agent_name, recommendation, context)
        
        logger.debug(f"Policy validation passed for {agent_name}")
        return True
    
    def _validate_crawl_recommendation(
        self,
        agent_name: str,
        recommendation: Dict[str, Any],
        context: Dict[str, Any]
    ) -> None:
        """Validate that crawl recommendation respects policy decisions."""
        url = recommendation.get("url") or context.get("url")
        
        if not url:
            return  # No URL to validate
        
        # Check if policy service has already denied this URL
        policy_decision = context.get("crawl_policy_decision", {})
        
        if policy_decision.get("decision") == "denied":
            # Agent CANNOT override a denied crawl policy decision
            denied_reasons = policy_decision.get("reasons", [])
            self._raise_violation(
                agent_name,
                f"Attempted to crawl policy-denied URL: {url}. "
                f"Reasons: {', '.join(denied_reasons)}",
                recommendation
            )
        
        # Check robots.txt compliance
        if not policy_decision.get("robots_allowed", True):
            self._raise_violation(
                agent_name,
                f"Attempted to crawl URL blocked by robots.txt: {url}",
                recommendation
            )
        
        # Check SSRF protection
        if policy_decision.get("private_ip_blocked", False):
            self._raise_violation(
                agent_name,
                f"Attempted to crawl private IP address: {url}",
                recommendation
            )
        
        # Check MIME type
        if not policy_decision.get("content_type_allowed", True):
            content_type = policy_decision.get("content_type", "unknown")
            self._raise_violation(
                agent_name,
                f"Attempted to crawl disallowed content type: {content_type}",
                recommendation
            )
    
    def _validate_indexing_recommendation(
        self,
        agent_name: str,
        recommendation: Dict[str, Any],
        context: Dict[str, Any]
    ) -> None:
        """Validate that indexing recommendation respects quality decisions."""
        # Check if content was marked as rejected
        quality_decision = context.get("quality_decision", {})
        
        if quality_decision.get("decision") == "reject":
            self._raise_violation(
                agent_name,
                "Attempted to index content that was marked as rejected",
                recommendation
            )
        
        # Check extraction validation
        extraction_status = context.get("extraction_status", {})
        
        invalid_statuses = ["CAPTCHA", "LOGIN_WALL", "SOFT_404", "PAYWALL"]
        if extraction_status.get("status") in invalid_statuses:
            self._raise_violation(
                agent_name,
                f"Attempted to index invalid extraction: {extraction_status.get('status')}",
                recommendation
            )
    
    def _validate_url_recommendation(
        self,
        agent_name: str,
        recommendation: Dict[str, Any],
        context: Dict[str, Any]
    ) -> None:
        """Validate URL recommendations for security issues."""
        urls = recommendation.get("urls", [recommendation.get("url")])
        urls = [u for u in urls if u]  # Filter None values
        
        for url in urls:
            # Check for private IP patterns
            if self._is_private_url(url):
                self._raise_violation(
                    agent_name,
                    f"Attempted to access private URL: {url}",
                    recommendation
                )
            
            # Check for suspicious schemes
            if not url.startswith(("http://", "https://")):
                self._raise_violation(
                    agent_name,
                    f"Attempted to use non-HTTP(S) scheme: {url}",
                    recommendation
                )
    
    def _is_private_url(self, url: str) -> bool:
        """Check if URL contains private IP address."""
        import re
        
        # Patterns for private IPs
        private_patterns = [
            r'://10\.\d+\.\d+\.\d+',
            r'://192\.168\.\d+\.\d+',
            r'://172\.(1[6-9]|2[0-9]|3[0-1])\.\d+\.\d+',
            r'://127\.\d+\.\d+\.\d+',
            r'://localhost',
            r'://169\.254\.\d+\.\d+',  # Link-local
        ]
        
        for pattern in private_patterns:
            if re.search(pattern, url):
                return True
        
        return False
    
    def _raise_violation(
        self,
        agent_name: str,
        message: str,
        recommendation: Dict[str, Any]
    ) -> None:
        """Raise policy violation error with logging."""
        full_message = f"Policy violation by {agent_name}: {message}"
        
        logger.error(
            f"🚨 POLICY VIOLATION: {full_message}",
            extra={
                "agent_name": agent_name,
                "violation": message,
                "recommendation": recommendation,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )
        
        raise PolicyViolationError(full_message)
    
    def validate_batch_recommendations(
        self,
        agent_name: str,
        recommendations: List[Dict[str, Any]],
        context: Dict[str, Any]
    ) -> List[bool]:
        """
        Validate multiple recommendations at once.
        
        Args:
            agent_name: Name of the agent
            recommendations: List of recommendations
            context: Context for validation
            
        Returns:
            List of boolean validation results (True = valid, False = invalid)
        """
        results = []
        
        for rec in recommendations:
            try:
                self.validate_agent_recommendation(agent_name, rec, context)
                results.append(True)
            except PolicyViolationError:
                results.append(False)
        
        return results
    
    def get_allowed_actions(self) -> List[str]:
        """Get list of actions agents are allowed to perform."""
        # These are safe actions agents can recommend
        return [
            "recommend_source",
            "assess_quality",
            "suggest_entity",
            "validate_extraction",
            "decompose_query",
            "prioritize_results",
            "flag_for_review"
        ]
    
    def get_blocked_actions(self) -> List[str]:
        """Get list of actions agents are NOT allowed to perform."""
        return self.BLOCKED_ACTIONS.copy()


# Global validator instance
_policy_validator_instance = None


def get_policy_validator(enforce: bool = True) -> AgentPolicyValidator:
    """Get global policy validator instance."""
    global _policy_validator_instance
    if _policy_validator_instance is None:
        _policy_validator_instance = AgentPolicyValidator(enforce=enforce)
    return _policy_validator_instance
