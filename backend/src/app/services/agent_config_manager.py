"""
Agent Configuration Manager for CredenceAI Iteration 0.4

Manages loading, validation, and access to agent configurations.
Configurations can be loaded from YAML files, environment variables, or database.
"""

import os
import yaml
import logging
from typing import Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class AgentConfigManager:
    """
    Centralized configuration management for AI agents.
    
    Features:
    - Load configurations from YAML files
    - Environment variable overrides
    - Default fallback values
    - Configuration validation
    - Runtime config updates
    """
    
    DEFAULT_CONFIG_PATH = "app/config/agent_configs.yaml"
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize configuration manager.
        
        Args:
            config_path: Path to YAML configuration file
        """
        self.config_path = config_path or self.DEFAULT_CONFIG_PATH
        self.config = {}
        self.load_config()
    
    def load_config(self) -> None:
        """Load configuration from YAML file."""
        try:
            # Check if path is absolute or relative
            if os.path.isabs(self.config_path):
                config_file = Path(self.config_path)
            else:
                # Relative to project root
                config_file = Path(__file__).parent.parent.parent / self.config_path
            
            if not config_file.exists():
                logger.warning(f"Config file not found: {config_file}, using defaults")
                self.config = self._get_default_config()
                return
            
            with open(config_file, 'r') as f:
                self.config = yaml.safe_load(f) or {}
            
            logger.info(f"Loaded agent configuration from {config_file}")
            
            # Apply environment variable overrides
            self._apply_env_overrides()
            
        except Exception as e:
            logger.error(f"Failed to load config: {e}, using defaults")
            self.config = self._get_default_config()
    
    def _apply_env_overrides(self) -> None:
        """Apply environment variable overrides to configuration."""
        # Global settings
        if os.getenv("AGENT_DEFAULT_MODEL"):
            self.config.setdefault("global", {})["default_model"] = os.getenv("AGENT_DEFAULT_MODEL")
        
        if os.getenv("AGENT_BUDGET_PER_JOB"):
            self.config.setdefault("global", {})["budget_per_job"] = int(os.getenv("AGENT_BUDGET_PER_JOB"))
        
        # Individual agent enable/disable
        for agent in ["planner", "source_selection", "quality_critic", "entity_resolution", "extraction_validation"]:
            env_var = f"AGENT_{agent.upper()}_ENABLED"
            if os.getenv(env_var):
                agent_key = f"{agent}_agent"
                self.config.setdefault(agent_key, {})["enabled"] = os.getenv(env_var).lower() == "true"
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration as fallback."""
        return {
            "global": {
                "enabled": True,
                "default_model": "gpt-3.5-turbo",
                "default_temperature": 0.7,
                "default_max_tokens": 500,
                "budget_per_job": 10000,
                "api_calls_per_job": 20,
            },
            "planner_agent": {
                "enabled": True,
                "model": "gpt-3.5-turbo",
                "temperature": 0.3,
                "max_tokens": 1000,
                "token_budget": 2000,
            },
            "source_selection_agent": {
                "enabled": True,
                "model": "gpt-3.5-turbo",
                "temperature": 0.5,
                "max_tokens": 500,
                "token_budget": 1000,
            },
            "quality_critic_agent": {
                "enabled": True,
                "model": "gpt-3.5-turbo",
                "temperature": 0.4,
                "max_tokens": 800,
                "token_budget": 1500,
            },
            "entity_resolution_agent": {
                "enabled": True,
                "model": "gpt-3.5-turbo",
                "temperature": 0.2,
                "max_tokens": 600,
                "token_budget": 1500,
            },
            "extraction_validation_agent": {
                "enabled": True,
                "model": "gpt-3.5-turbo",
                "temperature": 0.5,
                "max_tokens": 400,
                "token_budget": 1000,
            },
        }
    
    def get_agent_config(self, agent_name: str) -> Dict[str, Any]:
        """
        Get configuration for a specific agent.
        
        Args:
            agent_name: Name of the agent (e.g., "planner_agent")
            
        Returns:
            Dictionary with agent configuration
        """
        agent_config = self.config.get(agent_name, {})
        
        # Merge with global defaults
        global_config = self.config.get("global", {})
        merged_config = {
            "model": agent_config.get("model", global_config.get("default_model", "gpt-3.5-turbo")),
            "temperature": agent_config.get("temperature", global_config.get("default_temperature", 0.7)),
            "max_tokens": agent_config.get("max_tokens", global_config.get("default_max_tokens", 500)),
            "enabled": agent_config.get("enabled", global_config.get("enabled", True)),
        }
        
        # Include agent-specific settings
        for key, value in agent_config.items():
            if key not in merged_config:
                merged_config[key] = value
        
        return merged_config
    
    def is_agent_enabled(self, agent_name: str) -> bool:
        """
        Check if an agent is enabled.
        
        Args:
            agent_name: Name of the agent
            
        Returns:
            True if enabled, False otherwise
        """
        config = self.get_agent_config(agent_name)
        return config.get("enabled", True)
    
    def get_system_prompt(self, agent_name: str) -> Optional[str]:
        """
        Get system prompt for an agent.
        
        Args:
            agent_name: Name of the agent
            
        Returns:
            System prompt string or None
        """
        config = self.get_agent_config(agent_name)
        return config.get("system_prompt")
    
    def get_token_budget(self, agent_name: str) -> int:
        """
        Get token budget for an agent.
        
        Args:
            agent_name: Name of the agent
            
        Returns:
            Token budget limit
        """
        config = self.get_agent_config(agent_name)
        return config.get("token_budget", 1000)
    
    def get_global_config(self) -> Dict[str, Any]:
        """Get global configuration settings."""
        return self.config.get("global", self._get_default_config()["global"])
    
    def reload_config(self) -> None:
        """Reload configuration from file."""
        logger.info("Reloading agent configuration")
        self.load_config()


# Global instance for easy access
_config_manager_instance = None


def get_config_manager() -> AgentConfigManager:
    """Get global configuration manager instance."""
    global _config_manager_instance
    if _config_manager_instance is None:
        _config_manager_instance = AgentConfigManager()
    return _config_manager_instance
