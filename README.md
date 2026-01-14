# 🎬 AI NewsReel Generator

**Automated "Text-to-Video" Agentic System using Google Gemini & Python.**

AI NewsReel is a fully autonomous video generation pipeline that turns any news topic into a professional, 60-second news explainer video suitable for YouTube Shorts, Instagram Reels, or TikTok. It leverages a **Multi-Agent Architecture** to research, write, plan, and compose videos without human intervention.

## 🚀 Key Features

*   **🤖 Multi-Agent Orchestration:** Four specialized AI agents work in sequence:
    *   **Researcher:** Fetches and filters real-time news from Google News RSS.
    *   **Scriptwriter:** Drafts broadcast-quality narration (BBC/Reuters style).
    *   **Scene Planner:** Segment scripts into strict 5-6 second scenes for maximum engagement.
    *   **Visual Director:** Generates accurate AI image prompts (Unreal Engine style) using Gemini 2.0.
*   **⚡ Powered by Gemini 2.0:** Optimized for the "Gemini 2.0 Flash Lite" model with smart rate-limiting and auto-retry logic to maximize Free Tier usage.
*   **🎨 Dynamic Visuals:** Uses **Pollinations.ai** for uncensored, high-quality AI image generation, with fallback to real news images.
*   **🗣️ Professional Voiceovers:** Integrated **Edge-TTS** for ultra-realistic neural voice narration.
*   **🎥 Automated Editing:** Uses **MoviePy** to stitch images, audio, and transitions into a final MP4, complete with "Zoom/Pan" Ken Burns effects.
*   **📺 Streamlit Dashboard:** A user-friendly UI to track agent progress live and view a persistent gallery of generated videos.

## 🛠️ Tech Stack

*   **Core:** Python 3.10+
*   **LLM:** Google Gemini 2.5 Flash (`google-generativeai`)
*   **Frontend:** Streamlit
*   **Video Engine:** MoviePy
*   **Audio:** Edge-TTS
*   **Visuals:** Pollinations.ai API & DuckDuckGo Images
*   **Config:** YAML & Pydantic for rigid type validation

## ⚙️ How It Works

1.  **Input:** User provides a topic (e.g., "8th Pay Commission").
2.  **Process:**
    *   System scrapes latest articles.
    *   Summarizes facts into a 150-word script.
    *   Splits script into ~10 visual scenes.
    *   Generates or fetches relevant images for each scene.
    *   Synthesizes voiceover.
3.  **Output:** A polished 1080p vertical/horizontal video file ready for upload.

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
Create a `.env` file and add your Google API Key:
```env
GOOGLE_API_KEY=your_gemini_key_here
```

**Run:**
```bash
python -m streamlit run interface/app.py
```

## 🏗️ Architecture

```
User Input → News Collection Agent → Content Filtering Agent → 
Summarization Agent → Script Writer Agent → Scene Planner Agent → 
Visual Asset Agent → Voiceover Agent → Video Composer Agent → 
Final Video Output
```

## 📁 Project Structure

```
NewsReel/
├── core/                # Backend Logic (Agents, Workflows)
│   ├── agents/          # Individual agent implementations
│   ├── workflows/       # LangGraph workflow definitions
│   ├── utils/           # Helper functions
│   └── config/          # Configuration files
├── interface/           # Frontend (Streamlit)
│   ├── app.py           # Streamlit UI Entry Point
│   └── assets/          # Images, icons
├── tests/               # Verification Scripts
├── output/              # Generated videos
└── main.py              # CLI entry point
```

## 📄 License

MIT License - Free for educational and commercial use

## 👨‍💻 Author

Created by [Chaudhary Pawan](https://github.com/chaudhary-pawan) as a demonstration of modern Agentic AI + GenAI capabilities.

