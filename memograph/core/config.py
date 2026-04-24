"""Configuration management for MemoGraph.

This module provides a MemographConfig class for managing user configuration,
including settings and profiles stored in ~/.memograph/config.yaml.
"""

import logging
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)


class MemographConfig:
    """Manage MemoGraph configuration and profiles.
    
    Configuration is stored in ~/.memograph/config.yaml and includes:
    - Global settings (default_vault, default_provider, etc.)
    - User profiles with profile-specific settings
    
    Example:
        >>> config = MemographConfig()
        >>> config.set("default_vault", "./my-vault")
        >>> vault = config.get("default_vault")
        >>> 
        >>> # Profile management
        >>> config.create_profile("work", {"vault": "./work-vault"})
        >>> config.use_profile("work")
    """
    
    def __init__(self, config_path: str | None = None):
        """Initialize configuration manager.
        
        Args:
            config_path: Optional custom config file path.
                        Defaults to ~/.memograph/config.yaml
        """
        if config_path:
            self.config_file = Path(config_path).expanduser()
        else:
            config_dir = Path.home() / ".memograph"
            config_dir.mkdir(parents=True, exist_ok=True)
            self.config_file = config_dir / "config.yaml"
        
        self._config = self._load_config()
        logger.debug(f"Config loaded from: {self.config_file}")
    
    def _load_config(self) -> dict[str, Any]:
        """Load configuration from file."""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    config = yaml.safe_load(f) or {}
                return config
            except Exception as e:
                logger.warning(f"Failed to load config: {e}, using defaults")
                return self._default_config()
        else:
            return self._default_config()
    
    def _default_config(self) -> dict[str, Any]:
        """Get default configuration."""
        return {
            'default_vault': None,
            'default_provider': 'ollama',
            'profiles': {},
            'active_profile': None,
        }
    
    def _save_config(self) -> None:
        """Save configuration to file."""
        try:
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_file, 'w') as f:
                yaml.dump(self._config, f, default_flow_style=False)
            logger.debug(f"Config saved to: {self.config_file}")
        except Exception as e:
            logger.error(f"Failed to save config: {e}")
            raise
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value.
        
        Args:
            key: Configuration key
            default: Default value if key not found
            
        Returns:
            Configuration value or default
            
        Example:
            >>> config = MemographConfig()
            >>> vault = config.get("default_vault", "./vault")
        """
        value = self._config.get(key, default)
        logger.debug(f"Config get: {key} = {value}")
        return value
    
    def set(self, key: str, value: Any) -> None:
        """Set configuration value.
        
        Args:
            key: Configuration key
            value: Value to set
            
        Example:
            >>> config = MemographConfig()
            >>> config.set("default_vault", "./my-vault")
        """
        self._config[key] = value
        self._save_config()
        logger.info(f"Config set: {key} = {value}")
    
    def list_all(self) -> dict[str, Any]:
        """List all configuration settings.
        
        Returns:
            Dictionary of all configuration settings
            
        Example:
            >>> config = MemographConfig()
            >>> settings = config.list_all()
            >>> for key, value in settings.items():
            ...     print(f"{key}: {value}")
        """
        return dict(self._config)
    
    def delete(self, key: str) -> bool:
        """Delete a configuration key.
        
        Args:
            key: Configuration key to delete
            
        Returns:
            True if key was deleted, False if key didn't exist
        """
        if key in self._config:
            del self._config[key]
            self._save_config()
            logger.info(f"Config deleted: {key}")
            return True
        return False
    
    # Profile Management
    
    def create_profile(self, name: str, settings: dict[str, Any]) -> None:
        """Create a new configuration profile.
        
        Args:
            name: Profile name
            settings: Profile settings dictionary
            
        Example:
            >>> config = MemographConfig()
            >>> config.create_profile("work", {
            ...     "vault": "./work-vault",
            ...     "provider": "openai"
            ... })
        """
        if 'profiles' not in self._config:
            self._config['profiles'] = {}
        
        self._config['profiles'][name] = settings
        self._save_config()
        logger.info(f"Profile created: {name}")
    
    def use_profile(self, name: str) -> None:
        """Switch to a specific profile.
        
        Args:
            name: Profile name to activate
            
        Raises:
            KeyError: If profile doesn't exist
            
        Example:
            >>> config = MemographConfig()
            >>> config.use_profile("work")
        """
        if 'profiles' not in self._config or name not in self._config['profiles']:
            raise KeyError(f"Profile '{name}' not found")
        
        self._config['active_profile'] = name
        self._save_config()
        logger.info(f"Switched to profile: {name}")
    
    def get_profile(self, name: str) -> dict[str, Any]:
        """Get profile settings.
        
        Args:
            name: Profile name
            
        Returns:
            Profile settings dictionary
            
        Raises:
            KeyError: If profile doesn't exist
        """
        if 'profiles' not in self._config or name not in self._config['profiles']:
            raise KeyError(f"Profile '{name}' not found")
        
        return self._config['profiles'][name]
    
    def get_active_profile(self) -> str | None:
        """Get the currently active profile name.
        
        Returns:
            Active profile name or None if no profile is active
        """
        return self._config.get('active_profile')
    
    def get_active_profile_settings(self) -> dict[str, Any] | None:
        """Get settings for the currently active profile.
        
        Returns:
            Active profile settings or None if no profile is active
        """
        active = self.get_active_profile()
        if active:
            return self.get_profile(active)
        return None
    
    def list_profiles(self) -> list[str]:
        """List all profile names.
        
        Returns:
            List of profile names
            
        Example:
            >>> config = MemographConfig()
            >>> profiles = config.list_profiles()
            >>> for profile in profiles:
            ...     print(profile)
        """
        return list(self._config.get('profiles', {}).keys())
    
    def delete_profile(self, name: str) -> bool:
        """Delete a profile.
        
        Args:
            name: Profile name to delete
            
        Returns:
            True if profile was deleted, False if it didn't exist
            
        Example:
            >>> config = MemographConfig()
            >>> config.delete_profile("old-profile")
        """
        if 'profiles' in self._config and name in self._config['profiles']:
            del self._config['profiles'][name]
            
            # Clear active profile if it was deleted
            if self._config.get('active_profile') == name:
                self._config['active_profile'] = None
            
            self._save_config()
            logger.info(f"Profile deleted: {name}")
            return True
        return False
    
    def profile_exists(self, name: str) -> bool:
        """Check if a profile exists.
        
        Args:
            name: Profile name to check
            
        Returns:
            True if profile exists
        """
        return name in self._config.get('profiles', {})