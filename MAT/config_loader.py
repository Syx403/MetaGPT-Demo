"""
Filename: MetaGPT-Ewan/MAT/config_loader.py
Created Date: Sunday, December 29th 2025
Author: Ewan Su
Description: Centralized configuration loader for MAT framework.

This module loads API keys and settings from config/config2.yaml file,
so users only need to fill in their API keys in one place.

Usage:
    from MAT.config_loader import MATConfig
    
    config = MATConfig()
    tavily_key = config.get_tavily_api_key()
    openai_key = config.get_openai_api_key()
"""

import os
import yaml
from pathlib import Path
from typing import Optional, Dict, Any
from metagpt.logs import logger


class MATConfig:
    """
    Centralized configuration loader for MAT framework.
    
    Loads configuration from config/config2.yaml and provides
    easy access to API keys and settings.
    
    Priority order:
    1. Environment variables (for CI/CD or security)
    2. config2.yaml file
    3. Default values
    """
    
    # Default config path relative to project root
    DEFAULT_CONFIG_PATH = "config/config2.yaml"
    
    # Singleton instance
    _instance: Optional["MATConfig"] = None
    _config: Dict[str, Any] = {}
    
    def __new__(cls):
        """Singleton pattern to ensure only one config instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_config()
        return cls._instance
    
    def _find_project_root(self) -> Path:
        """
        Find the project root directory by looking for config/config2.yaml.
        
        Returns:
            Path to project root directory
        """
        # Start from current file location
        current = Path(__file__).resolve().parent
        
        # Walk up the directory tree looking for config/config2.yaml
        for _ in range(5):  # Limit search depth
            config_path = current / "config" / "config2.yaml"
            if config_path.exists():
                return current
            current = current.parent
        
        # Fallback: try common locations
        possible_roots = [
            Path.cwd(),
            Path(__file__).resolve().parent.parent,  # MAT/../
            Path(__file__).resolve().parent.parent.parent,  # MAT/../../
        ]
        
        for root in possible_roots:
            config_path = root / "config" / "config2.yaml"
            if config_path.exists():
                return root
        
        # Return current working directory as fallback
        return Path.cwd()
    
    def _load_config(self):
        """
        Load configuration from YAML file.
        """
        project_root = self._find_project_root()
        config_path = project_root / self.DEFAULT_CONFIG_PATH
        
        if config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    self._config = yaml.safe_load(f) or {}
                logger.info(f"✅ Loaded config from: {config_path}")
            except Exception as e:
                logger.warning(f"⚠️ Failed to load config: {e}")
                self._config = {}
        else:
            logger.warning(f"⚠️ Config file not found: {config_path}")
            self._config = {}
        
        # Store project root for later use
        self._project_root = project_root
    
    @property
    def project_root(self) -> Path:
        """Get the project root directory."""
        return self._project_root
    
    def get_tavily_api_key(self) -> Optional[str]:
        """
        Get Tavily API key.
        
        Priority: Environment variable > config file
        
        Returns:
            Tavily API key or None if not configured
        """
        # First check environment variable
        env_key = os.getenv("TAVILY_API_KEY")
        if env_key:
            return env_key
        
        # Then check config file
        tavily_config = self._config.get("tavily", {})
        config_key = tavily_config.get("api_key", "")
        
        if config_key and config_key != "":
            return config_key
        
        return None
    
    def get_openai_api_key(self) -> Optional[str]:
        """
        Get OpenAI API key.
        
        Priority: Environment variable > config file
        
        Returns:
            OpenAI API key or None if not configured
        """
        # First check environment variable
        env_key = os.getenv("OPENAI_API_KEY")
        if env_key:
            return env_key
        
        # Then check config file
        llm_config = self._config.get("llm", {})
        config_key = llm_config.get("api_key", "")
        
        # Return key if it's a valid OpenAI format (starts with "sk-")
        if config_key and config_key.startswith("sk-"):
            return config_key
        
        return None
    
    def get_tavily_config(self) -> Dict[str, Any]:
        """
        Get full Tavily configuration.
        
        Returns:
            Dictionary with Tavily settings
        """
        default_config = {
            "api_key": None,
            "search_depth": "advanced",
            "max_results": 10,
            "include_answer": True,
            "include_raw_content": True
        }
        
        tavily_config = self._config.get("tavily", {})
        
        # Merge with defaults
        merged = {**default_config, **tavily_config}
        
        # Override with environment variable if set
        env_key = os.getenv("TAVILY_API_KEY")
        if env_key:
            merged["api_key"] = env_key
        
        return merged
    
    def get_llm_config(self) -> Dict[str, Any]:
        """
        Get full LLM configuration.
        
        Returns:
            Dictionary with LLM settings
        """
        default_config = {
            "api_type": "openai",
            "base_url": "https://api.openai.com/v1",
            "api_key": None,
            "model": "gpt-4o-mini"
        }
        
        llm_config = self._config.get("llm", {})
        
        # Merge with defaults
        merged = {**default_config, **llm_config}
        
        # Override with environment variable if set
        env_key = os.getenv("OPENAI_API_KEY")
        if env_key:
            merged["api_key"] = env_key
        
        return merged
    
    def get_mat_config(self) -> Dict[str, Any]:
        """
        Get MAT framework specific configuration.
        
        Returns:
            Dictionary with MAT settings
        """
        default_config = {
            "search_output_dir": "MAT/data/search_results",
            "log_level": "INFO",
            "use_tavily": True
        }
        
        mat_config = self._config.get("mat", {})
        
        return {**default_config, **mat_config}
    
    def get_search_output_dir(self) -> Path:
        """
        Get the search output directory path.

        Returns:
            Path to search output directory
        """
        mat_config = self.get_mat_config()
        output_dir = mat_config.get("search_output_dir", "MAT/report/SA")
        
        # Make it absolute if relative
        output_path = Path(output_dir)
        if not output_path.is_absolute():
            output_path = self._project_root / output_path
        
        # Ensure directory exists
        output_path.mkdir(parents=True, exist_ok=True)
        
        return output_path
    
    def get_ragflow_config(self) -> Dict[str, Any]:
        """
        Get RAGFlow API configuration.

        Returns:
            Dictionary with RAGFlow settings including rerank_id
        """
        default_config = {
            "endpoint": "http://<your-ragflow-ip>:9380/api/v1/retrieval",
            "api_key": "<your-api-key>",
            "dataset_id": "<your-dataset-id>",
            "top_k": 5,
            "rerank_id": None  # Optional: Advanced reranking model
        }

        ragflow_config = self._config.get("ragflow", {})

        # Merge with defaults
        merged = {**default_config, **ragflow_config}

        return merged
    
    def get_rag_output_dir(self) -> Path:
        """
        Get the RAG output directory path for saving RAG results.

        Returns:
            Path to RAG output directory
        """
        mat_config = self.get_mat_config()
        output_dir = mat_config.get("rag_output_dir", "MAT/report/RA")
        
        # Make it absolute if relative
        output_path = Path(output_dir)
        if not output_path.is_absolute():
            output_path = self._project_root / output_path
        
        # Ensure directory exists
        output_path.mkdir(parents=True, exist_ok=True)
        
        return output_path
    
    def is_ragflow_configured(self) -> bool:
        """
        Check if RAGFlow API is properly configured.
        
        Returns:
            True if RAGFlow API key and dataset_id are set
        """
        config = self.get_ragflow_config()
        api_key = config.get("api_key", "")
        dataset_id = config.get("dataset_id", "")
        endpoint = config.get("endpoint", "")
        
        is_configured = (
            api_key != "<your-api-key>" and
            dataset_id != "<your-dataset-id>" and
            "<your-ragflow-ip>" not in endpoint and
            len(api_key) > 0 and
            len(dataset_id) > 0
        )
        
        return is_configured
    
    def get_technicals_config(self) -> Dict[str, Any]:
        """
        Get technical analysis configuration.
        
        Returns:
            Dictionary with technical analysis settings
        """
        default_config = {
            "default_period": 60,  # Default period in days
            "rsi_period": 14,
            "bb_period": 20,
            "bb_std": 2.0,
            "sma_period": 200,
            "atr_period": 14,
            "mean_reversion_thresholds": {
                "rsi_oversold_strong": 30.0,
                "rsi_oversold": 40.0,
                "rsi_overbought": 60.0,
                "rsi_overbought_strong": 70.0
            }
        }
        
        technicals_config = self._config.get("technicals", {})
        
        # Merge with defaults (config overrides defaults)
        merged = {**default_config, **technicals_config}
        
        # Handle nested mean_reversion_thresholds
        if "mean_reversion_thresholds" in technicals_config:
            merged["mean_reversion_thresholds"] = {
                **default_config["mean_reversion_thresholds"],
                **technicals_config["mean_reversion_thresholds"]
            }
        
        return merged
    
    def get_technical_output_dir(self) -> Path:
        """
        Get the technical analysis output directory path.

        Returns:
            Path to technical analysis output directory
        """
        mat_config = self.get_mat_config()
        output_dir = mat_config.get("technical_output_dir", "MAT/report/TA")
        
        # Make it absolute if relative
        output_path = Path(output_dir)
        if not output_path.is_absolute():
            output_path = self._project_root / output_path
        
        # Ensure directory exists
        output_path.mkdir(parents=True, exist_ok=True)
        
        return output_path
    
    def is_tavily_configured(self) -> bool:
        """
        Check if Tavily API is properly configured.
        
        Returns:
            True if Tavily API key is set
        """
        key = self.get_tavily_api_key()
        return key is not None and len(key) > 0
    
    def is_openai_configured(self) -> bool:
        """
        Check if OpenAI API is properly configured.
        
        Returns:
            True if OpenAI API key is set
        """
        key = self.get_openai_api_key()
        return key is not None and len(key) > 0
    
    def get_log_level(self) -> str:
        """
        Get the configured log level.
        
        Returns:
            Log level string (DEBUG, INFO, WARNING, ERROR)
        """
        mat_config = self.get_mat_config()
        return mat_config.get("log_level", "INFO")
    
    def use_tavily(self) -> bool:
        """
        Check if Tavily should be used (both configured and enabled).
        
        Returns:
            True if Tavily should be used for deep dive
        """
        mat_config = self.get_mat_config()
        use_flag = mat_config.get("use_tavily", True)
        return use_flag and self.is_tavily_configured()
    
    def print_config_status(self):
        """
        Print configuration status for debugging.
        """
        logger.info("="*60)
        logger.info("📋 MAT Configuration Status")
        logger.info("="*60)
        logger.info(f"Project Root: {self._project_root}")
        logger.info(f"Config File: {self._project_root / self.DEFAULT_CONFIG_PATH}")
        logger.info(f"OpenAI API: {'✅ Configured' if self.is_openai_configured() else '❌ Not configured'}")
        logger.info(f"Tavily API: {'✅ Configured' if self.is_tavily_configured() else '❌ Not configured'}")
        logger.info(f"RAGFlow API: {'✅ Configured' if self.is_ragflow_configured() else '❌ Not configured'}")
        logger.info(f"Use Tavily: {self.use_tavily()}")
        logger.info(f"Log Level: {self.get_log_level()}")
        logger.info(f"Search Output: {self.get_search_output_dir()}")
        logger.info(f"RAG Output: {self.get_rag_output_dir()}")
        logger.info(f"Technical Output: {self.get_technical_output_dir()}")
        logger.info("="*60)


# Convenience function for quick access
def get_config() -> MATConfig:
    """
    Get the singleton MATConfig instance.
    
    Returns:
        MATConfig singleton instance
    """
    return MATConfig()

