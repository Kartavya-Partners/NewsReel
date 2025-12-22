"""Main LangGraph workflow for news video generation."""

from typing import Dict, Any
from langgraph.graph import StateGraph, END
from agents.base_agent import AgentState
from agents.news_collection_agent import NewsCollectionAgent
from agents.summarization_agent import SummarizationAgent
from agents.script_writer_agent import ScriptWriterAgent
from agents.scene_planner_agent import ScenePlannerAgent
from agents.animation_generator_agent import AnimationGeneratorAgent
from agents.voiceover_agent import VoiceoverAgent
from agents.video_composer_agent import VideoComposerAgent
from loguru import logger
import yaml


class NewsVideoWorkflow:
    """LangGraph workflow orchestrating all agents."""
    
    def __init__(self, config_path: str = "config/settings.yaml", generate_video: bool = False):
        """
        Initialize the workflow.
        
        Args:
            config_path: Path to configuration file
            generate_video: Whether to generate video (default: False)
        """
        # Load configuration
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        # Store video generation flag
        self.generate_video = generate_video or self.config.get('video', {}).get('generate_video', False)
        
        # Initialize content agents
        self.news_agent = NewsCollectionAgent(self.config)
        self.summarization_agent = SummarizationAgent(self.config)
        self.script_agent = ScriptWriterAgent(self.config)
        self.scene_agent = ScenePlannerAgent(self.config)
        
        # Initialize video generation agents if needed
        if self.generate_video:
            self.animation_agent = AnimationGeneratorAgent(self.config)
            self.voiceover_agent = VoiceoverAgent(self.config)
            self.composer_agent = VideoComposerAgent(self.config)
        
        # Build workflow graph
        self.graph = self._build_graph()
        
        logger.info(f"NewsVideoWorkflow initialized (video generation: {self.generate_video})")
    
    def _build_graph(self) -> StateGraph:
        """
        Build the LangGraph workflow.
        
        Returns:
            Compiled StateGraph
        """
        # Create graph
        workflow = StateGraph(AgentState)
        
        # Add content generation nodes
        workflow.add_node("collect_news", self._collect_news_node)
        workflow.add_node("filter_content", self._filter_content_node)
        workflow.add_node("summarize", self._summarize_node)
        workflow.add_node("write_script", self._write_script_node)
        workflow.add_node("plan_scenes", self._plan_scenes_node)
        
        # Add video generation nodes if enabled
        if self.generate_video:
            workflow.add_node("generate_animations", self._generate_animations_node)
            workflow.add_node("generate_voiceover", self._generate_voiceover_node)
            workflow.add_node("compose_video", self._compose_video_node)
        
        # Define edges (workflow flow)
        workflow.set_entry_point("collect_news")
        workflow.add_edge("collect_news", "filter_content")
        workflow.add_edge("filter_content", "summarize")
        workflow.add_edge("summarize", "write_script")
        workflow.add_edge("write_script", "plan_scenes")
        
        # Conditional flow based on video generation
        if self.generate_video:
            workflow.add_edge("plan_scenes", "generate_animations")
            workflow.add_edge("generate_animations", "generate_voiceover")
            workflow.add_edge("generate_voiceover", "compose_video")
            workflow.add_edge("compose_video", END)
        else:
            workflow.add_edge("plan_scenes", END)
        
        # Compile graph
        return workflow.compile()
    
    def _collect_news_node(self, state: AgentState) -> AgentState:
        """Node for news collection."""
        return self.news_agent.execute(state)
    
    def _filter_content_node(self, state: AgentState) -> AgentState:
        """Node for content filtering."""
        # Simple filtering: remove articles that are too short
        min_length = self.config['news'].get('min_article_length', 200)
        
        filtered = [
            article for article in state.raw_articles
            if len(article.get('content', '')) >= min_length
        ]
        
        state.filtered_articles = filtered
        logger.info(f"Filtered to {len(filtered)} articles")
        
        return state
    
    def _summarize_node(self, state: AgentState) -> AgentState:
        """Node for summarization."""
        return self.summarization_agent.execute(state)
    
    def _write_script_node(self, state: AgentState) -> AgentState:
        """Node for script writing."""
        return self.script_agent.execute(state)
    
    def _plan_scenes_node(self, state: AgentState) -> AgentState:
        """Node for scene planning."""
        return self.scene_agent.execute(state)
    
    def _generate_animations_node(self, state: AgentState) -> AgentState:
        """Node for animation generation."""
        return self.animation_agent.execute(state)
    
    def _generate_voiceover_node(self, state: AgentState) -> AgentState:
        """Node for voiceover generation."""
        return self.voiceover_agent.execute(state)
    
    def _compose_video_node(self, state: AgentState) -> AgentState:
        """Node for video composition."""
        return self.composer_agent.execute(state)
    
    def run(self, topic: str, category: str = None) -> Dict[str, Any]:
        """
        Run the complete workflow.
        
        Args:
            topic: News topic to search for
            category: Optional category filter
            
        Returns:
            Final state with all generated content
        """
        logger.info(f"Starting workflow for topic: {topic}")
        
        # Create initial state
        initial_state = AgentState(
            topic=topic,
            category=category
        )
        
        # Run workflow
        final_state = self.graph.invoke(initial_state)
        
        logger.info("Workflow completed successfully")
        
        # LangGraph returns a dict, not AgentState
        result = {
            'topic': final_state.get('topic') or topic,
            'summary': final_state.get('summary', ''),
            'narration': final_state.get('narration', ''),
            'scene_plan': final_state.get('scene_plan', []),
            'metadata': final_state.get('metadata', {})
        }
        
        # Add video path if generated
        if self.generate_video and 'video_path' in final_state:
            result['video_path'] = final_state['video_path']
        
        return result
