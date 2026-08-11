"""
Configuration Module for Recruiter-Pro-AI
Centralized configuration loading from YAML and environment variables
"""
import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Project root directory
PROJECT_ROOT = Path(__file__).parent.parent.parent


@dataclass
class AgentConfig:
    """Configuration for individual agents"""
    enabled: bool = True
    timeout_seconds: int = 60
    retry_count: int = 3
    config: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DatabaseConfig:
    """Database configuration"""
    type: str = "sqlite"
    path: str = "data/database/match_history.db"
    
    # MySQL settings (if type="mysql")
    host: Optional[str] = None
    port: Optional[int] = 3306
    user: Optional[str] = None
    password: Optional[str] = None
    database: Optional[str] = None
    
    @property
    def connection_string(self) -> str:
        """Get database connection string"""
        if self.type == "sqlite":
            db_path = PROJECT_ROOT / self.path
            db_path.parent.mkdir(parents=True, exist_ok=True)
            return str(db_path)
        elif self.type == "mysql":
            return f"mysql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"
        else:
            raise ValueError(f"Unsupported database type: {self.type}")


@dataclass
class ScoringConfig:
    """Scoring algorithm configuration"""
    # Weights for rule-based scoring
    skill_weight: float = 0.60
    experience_weight: float = 0.25
    education_weight: float = 0.10
    keyword_weight: float = 0.05
    
    # ML model settings
    ml_enabled: bool = True
    ml_model_path: str = "ML/models/opt_rf_model.joblib"
    ml_weight: float = 0.40
    rule_weight: float = 0.60
    
    # Decision thresholds
    shortlist_threshold: float = 0.75
    review_threshold: float = 0.50
    reject_threshold: float = 0.50
    
    def validate(self):
        """Validate configuration"""
        total_weight = self.skill_weight + self.experience_weight + self.education_weight + self.keyword_weight
        if abs(total_weight - 1.0) > 0.01:
            raise ValueError(f"Rule weights must sum to 1.0, got {total_weight}")
        
        ml_total = self.ml_weight + self.rule_weight
        if abs(ml_total - 1.0) > 0.01:
            raise ValueError(f"ML and rule weights must sum to 1.0, got {ml_total}")


@dataclass
class LLMConfig:
    """LLM configuration for explanations"""
    enabled: bool = True
    provider: str = "ollama"  # ollama, openai, anthropic
    model: str = "llama3.2:3b"
    base_url: str = "http://localhost:11500"
    temperature: float = 0.2
    max_tokens: int = 500
    timeout_seconds: int = 120  # Increased to 120 seconds for AI Matching Engine
    cache_enabled: bool = True
    cache_ttl_hours: int = 24
    
    # LangChain mode selection
    use_langchain: bool = False  # False = Direct HTTP (fast), True = LangChain (advanced)
    streaming: bool = False      # Enable streaming responses
    enable_tracing: bool = False # Enable LangSmith tracing


@dataclass
class APIConfig:
    """API server configuration"""
    host: str = "0.0.0.0"
    port: int = 8000
    reload: bool = False
    workers: int = 1
    cors_origins: list = field(default_factory=lambda: ["http://localhost:8501"])
    api_docs_enabled: bool = True
    max_upload_size_mb: int = 10


@dataclass
class Config:
    """Main application configuration"""
    # Environment
    env: str = "development"
    debug: bool = False
    
    # Components
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    scoring: ScoringConfig = field(default_factory=ScoringConfig)
    llm: LLMConfig = field(default_factory=LLMConfig)
    api: APIConfig = field(default_factory=APIConfig)
    
    # Agents
    agent1: AgentConfig = field(default_factory=AgentConfig)
    agent2: AgentConfig = field(default_factory=AgentConfig)
    agent3: AgentConfig = field(default_factory=AgentConfig)
    agent4: AgentConfig = field(default_factory=AgentConfig)
    
    # Data paths
    # Was "data/jobs/jobs.json" - a directory that has never existed in this
    # repo. Nothing read the field, so the wrong value went unnoticed; load_jobs()
    # now reads it, which is what makes it wrong in a way anyone would catch.
    jobs_data_path: str = "data/json/jobs.json"
    # The controlled vocabulary the job corpus was generated against: 667
    # canonical skills, 1,523 aliases, covering all eight job categories.
    # Replaces skills_canonical.json, which held 105 engineering-leaning skills
    # and recognised 2.3% of the corpus.
    skills_database_path: str = "data/dictionaries/skills.json"
    
    # Processing settings
    max_jobs_to_score: int = 5000
    top_k_matches: int = 10
    batch_size: int = 100
    
    @classmethod
    def from_yaml(cls, yaml_path: Path) -> "Config":
        """Load configuration from YAML file"""
        if not yaml_path.exists():
            print(f"⚠️  Config file not found: {yaml_path}, using defaults")
            return cls()
        
        with open(yaml_path, 'r') as f:
            data = yaml.safe_load(f) or {}
        
        # Parse nested configurations
        config = cls()
        
        if 'database' in data:
            config.database = DatabaseConfig(**data['database'])
        
        if 'scoring' in data:
            config.scoring = ScoringConfig(**data['scoring'])
            config.scoring.validate()
        
        if 'llm' in data:
            config.llm = LLMConfig(**data['llm'])
        
        if 'api' in data:
            config.api = APIConfig(**data['api'])
        
        # Update from environment variables (override YAML)
        config._load_from_env()
        
        return config
    
    def _load_from_env(self):
        """Load configuration from environment variables"""
        # Database
        if os.getenv('DATABASE_TYPE'):
            self.database.type = os.getenv('DATABASE_TYPE')
        if os.getenv('DATABASE_PATH'):
            self.database.path = os.getenv('DATABASE_PATH')
        if os.getenv('MYSQL_HOST'):
            self.database.host = os.getenv('MYSQL_HOST')
        if os.getenv('MYSQL_USER'):
            self.database.user = os.getenv('MYSQL_USER')
        if os.getenv('MYSQL_PASSWORD'):
            self.database.password = os.getenv('MYSQL_PASSWORD')
        if os.getenv('MYSQL_DATABASE'):
            self.database.database = os.getenv('MYSQL_DATABASE')
        
        # LLM
        if os.getenv('LLM_ENABLED'):
            self.llm.enabled = os.getenv('LLM_ENABLED').lower() == 'true'
        if os.getenv('LLM_MODEL'):
            self.llm.model = os.getenv('LLM_MODEL')
        if os.getenv('OLLAMA_BASE_URL'):
            self.llm.base_url = os.getenv('OLLAMA_BASE_URL')
        
        # API
        if os.getenv('API_HOST'):
            self.api.host = os.getenv('API_HOST')
        if os.getenv('API_PORT'):
            self.api.port = int(os.getenv('API_PORT'))
        if os.getenv('CORS_ORIGINS'):
            self.api.cors_origins = os.getenv('CORS_ORIGINS').split(',')
        
        # Environment
        if os.getenv('ENV'):
            self.env = os.getenv('ENV')
        if os.getenv('DEBUG'):
            self.debug = os.getenv('DEBUG').lower() == 'true'
    
    @property
    def is_production(self) -> bool:
        """Check if running in production"""
        return self.env == 'production'
    
    @property
    def is_development(self) -> bool:
        """Check if running in development"""
        return self.env == 'development'


# Singleton instance
_config: Optional[Config] = None


def get_config(reload: bool = False) -> Config:
    """
    Get application configuration (singleton)
    
    Args:
        reload: Force reload configuration
    
    Returns:
        Config instance
    """
    global _config
    
    if _config is None or reload:
        # Try to load from config file
        config_paths = [
            PROJECT_ROOT / "config" / "agents.yaml",
            PROJECT_ROOT / "config" / "config.yaml",
        ]
        
        for config_path in config_paths:
            if config_path.exists():
                _config = Config.from_yaml(config_path)
                break
        
        if _config is None:
            _config = Config()
            _config._load_from_env()
    
    return _config


def load_decision_rules() -> Dict[str, Any]:
    """Load decision rules from YAML"""
    rules_path = PROJECT_ROOT / "config" / "decision_rules.yaml"
    
    if not rules_path.exists():
        # Return defaults
        return {
            "thresholds": {
                "shortlist_min": 0.75,
                "review_min": 0.50,
                "reject_below": 0.50
            },
            "overqualification_multiplier": 2.0,
            "critical_skill_weight": 0.3
        }
    
    with open(rules_path, 'r') as f:
        return yaml.safe_load(f)


# Initialize configuration on module import
config = get_config()
