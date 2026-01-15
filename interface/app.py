import streamlit as st
import sys
import os
from pathlib import Path
import json
import time
from dotenv import load_dotenv

# Load environment variables (API Keys)
load_dotenv()

# Ensure imports work (add root to path)
import sys
import os
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(root_dir)

from core.workflows.news_video_workflow import NewsVideoWorkflow
from loguru import logger

# Constants
CONFIG_PATH = os.path.join(root_dir, "core", "config", "settings.yaml")

# ------------------------------------------------------------------
# Page Config
# ------------------------------------------------------------------
st.set_page_config(
    page_title="NewsAI - Auto Video Generator",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ------------------------------------------------------------------
# Custom CSS
# ------------------------------------------------------------------
st.markdown("""
<style>
    .stButton>button {
        width: 100%;
        background-color: #FF4B4B;
        color: white;
        font-weight: bold;
        padding: 0.5rem;
    }
    .stButton>button:hover {
        background-color: #FF2B2B;
        border-color: #FF2B2B;
    }
    h1 {
        color: #FAFAFA;
    }
    .status-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #262730;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# ------------------------------------------------------------------
# Sidebar: Settings
# ------------------------------------------------------------------
with st.sidebar:
    st.image("https://img.icons8.com/color/96/000000/video-camera.png", width=80)
    st.title("Settings")
    
    st.header("🔍 News Source")
    category = st.selectbox(
        "News Category",
        ["General", "Technology", "Politics", "Sports", "Business", "Entertainment"],
        index=0
    )
    
    st.header("🎨 Visual Style")
    use_real_images = st.toggle("Prioritize Real Images", value=True)
    
    st.header("🗣️ Audio")
    voice_speed = st.slider("Narration Speed", 0.5, 2.0, 1.05, 0.05)
    
    st.divider()
    
    with st.expander("Advanced Config"):
        st.write("Edit `config/settings.yaml` for granular control.")
        if st.button("Reload Config"):
            st.cache_data.clear()
            st.success("Config reloaded!")

    st.divider()
    st.header("📂 Recent Videos")
    output_dir = Path("output")
    if output_dir.exists():
        video_files = sorted(list(output_dir.glob("*.mp4")), key=os.path.getmtime, reverse=True)
        if video_files:
            selected_video = st.selectbox("Select to play:", [f.name for f in video_files])
            if selected_video:
                st.session_state['selected_video_path'] = str(output_dir / selected_video)
        else:
            st.write("No videos found yet.")
    else:
        st.write("Output directory missing.")

# ------------------------------------------------------------------
# Main Interface
# ------------------------------------------------------------------

st.title("🎬 AI News Generator")
st.markdown("Turning headlines into broadcast-quality videos in minutes.")

# Input Section
col1, col2 = st.columns([3, 1])
with col1:
    topic = st.text_input("Enter News Topic", placeholder="e.g., 'Aravali Protest in India'")

with col2:
    st.write("") # Spacer
    st.write("")
    generate_btn = st.button("Generate Video", type="primary")

# ------------------------------------------------------------------
# Execution Logic
# ------------------------------------------------------------------

# Display Selected Video from Sidebar (Persistent View)
if 'selected_video_path' in st.session_state and os.path.exists(st.session_state['selected_video_path']):
    if not generate_btn: # Only show if not currently generating
        st.divider()
        st.subheader(f"📺 Playing: {os.path.basename(st.session_state['selected_video_path'])}")
        st.video(st.session_state['selected_video_path'])

if generate_btn and topic:
    
    # Placeholder for status updates
    status_container = st.empty()
    progress_bar = st.progress(0)
    log_area = st.empty()
    
    # Custom Logger Sink for Streamlit
    class StreamlitSink:
        def __init__(self):
            self.logs = []
            
        def write(self, message):
            self.logs.append(message.strip())
            # Show FULL logs
            full_logs = "\n".join(self.logs)
            log_area.code(full_logs, language="text")
            
            # Update Progress based on keywords (heuristic)
            if "NewsCollectionAgent" in message: progress_bar.progress(10)
            elif "SummarizationAgent" in message: progress_bar.progress(30)
            elif "ScriptWriterAgent" in message: progress_bar.progress(50)
            elif "VisualPlannerAgent" in message: progress_bar.progress(70)
            elif "VideoComposerAgent" in message: progress_bar.progress(90)
            elif "VIDEO GENERATED" in message: progress_bar.progress(100)

            # Check for immediate result feedback
            if "[RESULT] SUMMARY:" in message:
                content = message.split("[RESULT] SUMMARY:", 1)[1].strip()
                with summary_container.container():
                     with st.expander("📄 Generated Summary", expanded=False):
                        st.info(content)
            
            if "[RESULT] NARRATION:" in message:
                content = message.split("[RESULT] NARRATION:", 1)[1].strip()
                with narration_container.container():
                    with st.expander("🎙️ Generated Script", expanded=True):
                        st.success(content)

    # Hack loguru to print to streamlit
    sink = StreamlitSink()
    logger.add(sink.write, format="{time:HH:mm:ss} | {message}")

    # placeholders for results
    summary_container = st.empty()
    narration_container = st.empty()

    try:
        with st.status("🚀 Production Pipeline Running...", expanded=True) as status:
            
            st.write("Initializing Agents...")
            workflow = NewsVideoWorkflow(
                config_path=CONFIG_PATH,
                generate_video=True
            )
            
            # Run
            st.write(f"Searching for news on: **{topic}**...")
            result = workflow.run(topic=topic, category=category.lower())
            
            status.update(label="✅ Complete!", state="complete", expanded=False)
            
        # ------------------------------------------------------------------
        # Result Display
        # ------------------------------------------------------------------
        st.divider()
        st.header("✨ Your Video")
        
        if 'video_path' in result and os.path.exists(result['video_path']):
            video_file = open(result['video_path'], 'rb')
            video_bytes = video_file.read()
            st.video(video_bytes)
            
            # Download Button
            st.download_button(
                label="Download MP4",
                data=video_bytes,
                file_name=os.path.basename(result['video_path']),
                mime='video/mp4'
            )
        else:
            st.error("Video file was not generated successfully.")
            
        # Script Display
        with st.expander("View Generated Script"):
            st.markdown(result.get("narration", "No script available."))

    except Exception as e:
        st.error(f"Workflow Failed: {e}")
        logger.exception(e)

elif generate_btn and not topic:
    st.warning("Please enter a topic first.")
