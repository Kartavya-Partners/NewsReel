"""Main LangGraph workflow for news video generation."""

from typing import Dict, Any
from langgraph.graph import StateGraph, END
from core.agents.base_agent import AgentState

# Content agents
from core.agents.news_collection_agent import NewsCollectionAgent
from core.agents.summarization_agent import SummarizationAgent
from core.agents.script_writer_agent import ScriptWriterAgent
from core.agents.scene_planner_agent import ScenePlannerAgent

# Visual agents (NEW)
from core.agents.visual_planner_agent import VisualPlannerAgent
from core.agents.visual_asset_agent import VisualAssetAgent

# Video generation agents
from core.agents.animation_generator_agent import AnimationGeneratorAgent
from core.agents.voiceover_agent import VoiceoverAgent
from core.agents.video_composer_agent import VideoComposerAgent

from loguru import logger
import yaml


class NewsVideoWorkflow:
    """LangGraph workflow orchestrating all agents."""

    def __init__(self, config_path: str = "config/settings.yaml", generate_video: bool = False):
        """
        Initialize the workflow.

        Args:
            config_path: Path to configuration file
            generate_video: Whether to generate video
        """
        # Load configuration
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)

        # Video generation flag
        self.generate_video = generate_video or self.config.get('video', {}).get('generate_video', False)

        # -------- Content agents --------
        self.news_agent = NewsCollectionAgent(self.config)
        self.summarization_agent = SummarizationAgent(self.config)
        self.script_agent = ScriptWriterAgent(self.config)
        self.scene_agent = ScenePlannerAgent(self.config)

        # -------- Visual reasoning agents (ALWAYS INITIALIZED) --------
        self.visual_planner_agent = VisualPlannerAgent(self.config)
        self.visual_asset_agent = VisualAssetAgent(self.config)

        # -------- Video generation agents (ONLY IF ENABLED) --------
        if self.generate_video:
            self.animation_agent = AnimationGeneratorAgent(self.config)
            self.voiceover_agent = VoiceoverAgent(self.config)
            self.composer_agent = VideoComposerAgent(self.config)

        # Build graph
        self.graph = self._build_graph()

        logger.info(f"NewsVideoWorkflow initialized (video generation: {self.generate_video})")

    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow."""
        workflow = StateGraph(AgentState)

        # -------- Nodes --------
        workflow.add_node("collect_news", self._collect_news_node)
        workflow.add_node("filter_content", self._filter_content_node)
        workflow.add_node("summarize", self._summarize_node)
        workflow.add_node("write_script", self._write_script_node)
        workflow.add_node("plan_scenes", self._plan_scenes_node)

        # Visual planning nodes (NEW)
        workflow.add_node("plan_visuals", self._plan_visuals_node)
        workflow.add_node("fetch_visual_assets", self._fetch_visual_assets_node)

        # Video generation nodes
        if self.generate_video:
            workflow.add_node("generate_animations", self._generate_animations_node)
            workflow.add_node("generate_voiceover", self._generate_voiceover_node)
            workflow.add_node("compose_video", self._compose_video_node)

        # -------- Edges --------
        workflow.set_entry_point("collect_news")

        workflow.add_edge("collect_news", "filter_content")
        workflow.add_edge("filter_content", "summarize")
        workflow.add_edge("summarize", "write_script")
        workflow.add_edge("write_script", "plan_scenes")

        if self.generate_video:
            workflow.add_edge("plan_scenes", "plan_visuals")
            workflow.add_edge("plan_visuals", "fetch_visual_assets")
            workflow.add_edge("fetch_visual_assets", "generate_animations")
            workflow.add_edge("generate_animations", "generate_voiceover")
            workflow.add_edge("generate_voiceover", "compose_video")
            workflow.add_edge("compose_video", END)
        else:
            workflow.add_edge("plan_scenes", END)

        return workflow.compile()

    # -------- Node implementations --------

    def _collect_news_node(self, state: AgentState) -> AgentState:
        return self.news_agent.execute(state)

    def _filter_content_node(self, state: AgentState) -> AgentState:
        # Reduced strictness: 50 chars is enough for a short lead
        min_length = self.config['news'].get('min_article_length', 50)
        
        filtered = []
        for article in state.raw_articles:
            content_len = len(article.get('content', ''))
            if content_len >= min_length:
                filtered.append(article)
            else:
                logger.info(f"Filtered out article '{article.get('title')}' (length {content_len} < {min_length})")
                
        state.filtered_articles = filtered
        logger.info(f"Filtered to {len(state.filtered_articles)} articles (from {len(state.raw_articles)} raw)")
        
        # SAFETY VALVE: If all filtered out, use raw articles if they have ANY content
        if not state.filtered_articles and state.raw_articles:
            logger.warning("All articles were filtered out! Reverting to raw articles as fallback.")
            state.filtered_articles = state.raw_articles
            
        return state

    def _summarize_node(self, state: AgentState) -> AgentState:
        return self.summarization_agent.execute(state)

    def _write_script_node(self, state: AgentState) -> AgentState:
        return self.script_agent.execute(state)

    def _plan_scenes_node(self, state: AgentState) -> AgentState:
        return self.scene_agent.execute(state)

    # -------- NEW VISUAL NODES --------

    def _plan_visuals_node(self, state: AgentState) -> AgentState:
        """LLM decides what should appear visually in each scene."""
        return self.visual_planner_agent.execute(state)

    def _fetch_visual_assets_node(self, state: AgentState) -> AgentState:
        """Fetches images/videos for each scene."""
        return self.visual_asset_agent.execute(state)

    # -------- VIDEO NODES --------

    def _generate_animations_node(self, state: AgentState) -> AgentState:
        return self.animation_agent.execute(state)

    def _generate_voiceover_node(self, state: AgentState) -> AgentState:
        return self.voiceover_agent.execute(state)

    def _compose_video_node(self, state: AgentState) -> AgentState:
        return self.composer_agent.execute(state)

    # -------- Runner --------

    def run(self, topic: str, category: str = None) -> Dict[str, Any]:
        import uuid
        run_id = str(uuid.uuid4())[:8]  # Short ID
        logger.info(f"Starting workflow run: {run_id} for topic: {topic}")

        initial_state = AgentState(
            run_id=run_id,
            topic=topic, 
            category=category
        )
        final_state = self.graph.invoke(initial_state)

        result = {
            "topic": final_state.get("topic", topic),
            "summary": final_state.get("summary", ""),
            "narration": final_state.get("narration", ""),
            "scene_plan": final_state.get("scene_plan", []),
            "metadata": final_state.get("metadata", {}),
            "raw_articles": final_state.get("raw_articles", []),
            "filtered_articles": final_state.get("filtered_articles", [])
        }

        if self.generate_video and "video_path" in final_state:
            result["video_path"] = final_state["video_path"]

        logger.info("Workflow completed successfully")
        return result
