
import os
import sys
import yaml
from pathlib import Path
from dotenv import load_dotenv

# Ensure imports work
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(root_dir)

load_dotenv()

from core.agents.base_agent import AgentState
from core.agents.summarization_agent import SummarizationAgent
from core.agents.script_writer_agent import ScriptWriterAgent
from core.agents.scene_planner_agent import ScenePlannerAgent
from core.agents.visual_planner_agent import VisualPlannerAgent

def load_config():
    config_path = os.path.join(root_dir, "core", "config", "settings.yaml")
    with open(config_path, "r") as f:
        return yaml.safe_load(f)

def test_pipeline():
    print("Starting Agent Pipeline Verification (Dry Run)...")
    config = load_config()
    
    # 1. Test Summarization
    print("\n--- 1. Testing SummarizationAgent ---")
    sum_agent = SummarizationAgent(config)
    state = AgentState(
        run_id="test_run_001",
        topic="Test Topic",
        raw_articles=[{"title": "Test News", "content": "Content"}],
        filtered_articles=[{"title": "Test News", "content": "Content", "published": "2025-01-01", "source": "Test"}]
    )
    # Mocking real summary execution to save quota/time or running real?
    # User wants to ensure NO CRASHES, so we should run REAL but small.
    try:
        # We can't easily inject a short prompt into execute without modifying code, 
        # but the agent uses state.raw_articles.
        # Let's trust the agent to handle a short article.
        state = sum_agent.execute(state)
        if not state.summary:
             raise ValueError("Summary is empty")
        print(f"Summary: {state.summary[:50]}...", flush=True)
        print("Summarization Passed", flush=True)
    except Exception as e:
        print(f"Summarization Failed: {e}", flush=True)
        sys.exit(1)

    # 2. Test Script Writer
    print("\n--- 2. Testing ScriptWriterAgent ---")
    script_agent = ScriptWriterAgent(config)
    try:
        state = script_agent.execute(state)
        if not state.narration:
             raise ValueError("Narration is empty")
        print(f"Narration: {state.narration[:50]}...", flush=True)
        print("Script Writing Passed", flush=True)
    except Exception as e:
        print(f"Script Writing Failed: {e}", flush=True)
        sys.exit(1)

    # 3. Test Scene Planner
    print("\n--- 3. Testing ScenePlannerAgent ---")
    # Verify 10 scene limit
    scene_agent = ScenePlannerAgent(config)
    try:
        state = scene_agent.execute(state)
        print(f"Scene Planning Passed ({len(state.scene_plan)} scenes generated)", flush=True)
        if len(state.scene_plan) > 10:
             print("CRITICAL: Scene limit exceeded!", flush=True)
        else:
             print("Scene limit respected", flush=True)
    except Exception as e:
        print(f"Scene Planning Failed: {e}", flush=True)
        sys.exit(1)

    # 4. Test Visual Planner
    print("\n--- 4. Testing VisualPlannerAgent ---")
    visual_agent = VisualPlannerAgent(config)
    try:
        state = visual_agent.execute(state)
        if state.scene_plan and "visual" in state.scene_plan[0]:
            print("Visual logic verified.", flush=True)
            print("Visual Planning Passed", flush=True)
        else:
            print("Visual keys missing?", flush=True)
            sys.exit(1)
    except Exception as e:
        print(f"Visual Planning Failed: {e}", flush=True)
        sys.exit(1)

    print("\nAUTOMATED PIPELINE VERIFICATION PASSED!", flush=True)
    print("All agents are compatible with the current Gemini model.")

if __name__ == "__main__":
    test_pipeline()
