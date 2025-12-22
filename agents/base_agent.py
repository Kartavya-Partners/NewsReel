"""Base Agent class for all agents in the system."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, List
from loguru import logger
from pydantic import BaseModel, Field


class AgentState(BaseModel):
    """Base state model for agent communication."""

    # ---- Core pipeline ----
    topic: str
    category: Optional[str] = None
    raw_articles: Optional[list] = None
    filtered_articles: Optional[list] = None
    summary: Optional[str] = None
    narration: Optional[str] = None
    scene_plan: Optional[list] = None

    # ---- Video generation (NEW) ----
    scene_clips: List[str] = Field(default_factory=list)
    audio_files: List[str] = Field(default_factory=list)
    video_path: Optional[str] = None

    # ---- Legacy / compatibility ----
    animations: Optional[list] = None
    voiceover_path: Optional[str] = None
    final_video_path: Optional[str] = None

    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        arbitrary_types_allowed = True



class BaseAgent(ABC):
    """Abstract base class for all agents."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the agent.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.name = self.__class__.__name__
        logger.info(f"Initialized {self.name}")
    
    @abstractmethod
    def execute(self, state: AgentState) -> AgentState:
        """
        Execute the agent's task.
        
        Args:
            state: Current agent state
            
        Returns:
            Updated agent state
        """
        pass
    
    def log_progress(self, message: str, level: str = "info"):
        """Log agent progress."""
        log_func = getattr(logger, level)
        log_func(f"[{self.name}] {message}")
    
    def validate_input(self, state: AgentState, required_fields: list) -> bool:
        """
        Validate that required fields are present in state.
        
        Args:
            state: Current agent state
            required_fields: List of required field names
            
        Returns:
            True if all required fields are present
        """
        for field in required_fields:
            if getattr(state, field, None) is None:
                self.log_progress(
                    f"Missing required field: {field}",
                    level="error"
                )
                return False
        return True
