# 🎬 AI NewsReel Generator

**Automated "Text-to-Video" Agentic System using Google Gemini & Wan 2.2.**

AI NewsReel is a fully autonomous video generation pipeline that turns any news topic into a professional, 60-second news explainer video suitable for YouTube Shorts, Instagram Reels, or TikTok. It leverages a **Multi-Agent Architecture** to research, write, plan, and compose videos without human intervention.

## 🚀 Key Features

*   **🤖 Multi-Agent Orchestration:** Four specialized AI agents work in sequence:
    *   **Researcher:** Fetches real-time news (Strict "Last 2 Years" filter) from Google News RSS.
    *   **Scriptwriter:** Drafts broadcast-quality narration (Journalistic 5W+1H style) with complete endings.
    *   **Scene Planner:** Segments scripts into a strict **5-scene** structure for maximum engagement.
    *   **Visual Director:** Generates accurate AI video prompts using a single-shot Gemini 2.0 call.
*   **⚡ Optimized for Free Tier:**
    *   **Smart Quota Handling:** Detects `429 Daily Limit` errors and stops gracefully.
    *   **Batch Processing:** Visual Planner uses a single API call for all scenes (80% quota reduction).
    *   **Token Optimization:** Increased limits to prevent narration truncation.
*   **Core:** Python 3.10+
*   **LLM:** Google Gemini 2.5 Flash (`google-genai`)
*   **Video Gen:** Wan 2.2 (Local Inference on GCP)
*   **Frontend:** Streamlit
*   **Video Engine:** MoviePy
*   **Audio:** Edge-TTS (Neural)
*   **Config:** YAML & Pydantic for rigid type validation

## ⚙️ How It Works

1.  **Input:** User provides a topic (e.g., "Aravali Protest").
2.  **Process:**
    *   **NewsCollectionAgent:** Scrapes relevant articles using a 2-year recency filter.
    *   **SummarizationAgent:** Creates a factual summary (no 2018 noise).
    *   **ScriptWriterAgent:** Writes a 5-scene script with a definitive conclusion.
    *   **VisualAssetAgent:** Generates videos using Wan 2.2 (or falls back to images).
    *   **VideoComposerAgent:** Stitches everything into a final `.mp4`.
3.  **Output:** A polished 1080p vertical video file.

## 📦 Installation

```bash
git clone https://github.com/chaudhary-pawan/NewsReel.git
cd NewsReel
python -m venv venv
# Activate venv:
# Windows: venv\Scripts\activate
# Mac/Linux: source venv/bin/activate
pip install -r requirements.txt
```

**Configuration:**
Create a `.env` file and add your Keys:
```env
# Gemini (Required for Agents)
GOOGLE_API_KEY=your_gemini_key_here

# PiAPI (Optional - Only if not using Local Wan 2.2)
PIAPI_API_KEY=your_piapi_key_here
```

**GCP / Local Wan 2.2 Setup:**
To run with local Wan 2.2 inference (recommended for GCP):
1. Clone the `Wan-Video` repository next to this folder:
   ```bash
   git clone https://github.com/Wan-Video/Wan-Video.git ../Wan-Video
   ```
2. Download weights to `weights/Wan2.2-I2V-14B-720P-INT8`.
3. The system will auto-detect and use the local model.

**Run:**
```bash
# GUI Mode
streamlit run interface/app.py

# CLI Mode
python main.py --topic "Your Topic Here"
```

## 🏗️ Architecture

```
User Input → News Collection Agent (Recency Filter) → 
Summarization Agent (Journalistic Tone) → 
Script Writer Agent (Complete Endings) → 
Scene Planner Agent (Max 5 Scenes) → 
Visual Asset Agent (Wan 2.2 Video) → 
Voiceover Agent → Video Composer Agent → 
Final Video Output
```

## 📁 Project Structure

```
NewsReel/
├── core/                # Backend Logic (Agents, Workflows)
│   ├── agents/          # Individual agent implementations
│   ├── workflows/       # LangGraph workflow definitions
│   ├── utils/           # Helper functions (WanClient, LLMClient)
│   └── config/          # Configuration files
├── interface/           # Frontend (Streamlit)
│   ├── app.py           # Streamlit UI Entry Point
├── tests/               # Verification Scripts (probe_wan_api.py)
├── output/              # Generated videos
└── main.py              # CLI entry point
```

## 📄 License

MIT License - Free for educational and commercial use

## 👨‍💻 Author

Created by [Chaudhary Pawan](https://github.com/chaudhary-pawan) as a demonstration of modern Agentic AI + GenAI capabilities.
