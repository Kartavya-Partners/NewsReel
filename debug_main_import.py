
import sys
import os
print(f"Python executable: {sys.executable}")
print(f"CWD: {os.getcwd()}")
print(f"Path: {sys.path}")

try:
    print("Importing workflows.news_video_workflow...")
    from workflows.news_video_workflow import NewsVideoWorkflow
    print("SUCCESS: workflows.news_video_workflow imported")
except Exception as e:
    print(f"FAILURE: {e}")
    import traceback
    traceback.print_exc()

try:
    print("Importing agents.animation_generator_agent...")
    from agents.animation_generator_agent import AnimationGeneratorAgent
    print("SUCCESS: agents.animation_generator_agent imported")
except Exception as e:
    print(f"FAILURE: {e}")
    import traceback
    traceback.print_exc()
