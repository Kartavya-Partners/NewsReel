# 🎬 AI NewsReel Generator

**Automated "Text-to-Video" Agentic System using Google Gemini & Wan 2.2.**

AI NewsReel is a fully autonomous video generation pipeline that turns any news topic into a professional, 60-second news explainer video suitable for YouTube Shorts, Instagram Reels, or TikTok. It leverages a **Multi-Agent Architecture** with **NVIDIA L4 GPU** for cost-efficient INT8 quantized video generation.

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
*   **Video Gen:** Wan 2.2 INT8 (GCP L4 GPU)
*   **GPU:** NVIDIA L4 (24GB VRAM)
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
```

**GCP L4 GPU Setup (Optional):**

For cost-efficient cloud video generation, you can use **NVIDIA L4 GPU** on GCP with INT8 quantization.

**Quick setup:**
1. Create an L4 Spot instance on GCP
2. Clone the Wan-Video repository
3. Download INT8 model weights to `./weights/Wan2.2-I2V-14B-720P-INT8`
4. Update `core/config/settings.yaml` with your GCP details:
   ```yaml
   gcp:
     project_id: "your-project-id"
     zone: "us-central1-a"
     instance_name: "wan-video-l4-vm"
     bucket_name: "your-bucket-name"
   ```

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
│   └── config/          # Configuration files (settings.yaml)
├── docs/                # Documentation
│   └── archive/         # Archived documentation
├── scripts/             # Setup & Verification Scripts
│   └── archive/         # Archived scripts
├── interface/           # Frontend (Streamlit)
│   └── app.py           # Streamlit UI Entry Point
├── tests/               # Verification Scripts
├── output/              # Generated videos
└── main.py              # CLI entry point
```



## 📄 License

MIT License - Free for educational and commercial use

## 👨‍💻 Author

Created by [Chaudhary Pawan](https://github.com/chaudhary-pawan) as a demonstration of modern Agentic AI + GenAI capabilities.
