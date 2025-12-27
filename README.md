# AI News Explainer Video Generator

An **Agentic AI system** that automatically transforms news articles into engaging 1-1.5 minute animated explainer videos.

## 🎯 Project Overview

This project demonstrates a complete **multi-agent AI pipeline** that:
- Fetches latest news from multiple sources
- Intelligently summarizes and filters content
- Generates natural narration scripts
- Plans visual scenes automatically
- Creates animated explainer videos with voiceover

## 🛠️ Tech Stack

- **Python 3.10+** - Core language
- **LangGraph** - Agentic workflow orchestration
- **RSS/GNews API** - News sources (free tier)
- **Ollama (LLaMA 3/Mistral)** - Local LLM for content generation
- **Pollinations.ai** - High resolution AI Image generation
- **Manim** - Professional animation generation
- **MoviePy** - Video composition
- **Edge TTS** - Natural text-to-speech
- **Streamlit** - Interactive web interface

## 🏗️ Architecture

```
User Input → News Collection Agent → Content Filtering Agent → 
Summarization Agent → Script Writer Agent → Scene Planner Agent → 
Animation Generator Agent → Voiceover Agent → Video Composer Agent → 
Final Video Output
```

## 📁 Project Structure

```
kartavya_submission/
├── agents/              # Individual agent implementations
├── workflows/           # LangGraph workflow definitions
├── utils/              # Helper functions
├── assets/             # Images, icons, templates
├── output/             # Generated videos
├── config/             # Configuration files
├── app.py              # Streamlit UI
└── main.py             # CLI entry point
```

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Install Ollama

```bash
# Download from https://ollama.ai
ollama pull llama3
```

### 3. Run the Application

**Web Interface:**
```bash
streamlit run app.py
```

**CLI:**
```bash
python main.py --topic "AI in Healthcare" --category technology
```

## 🎨 Features

- ✅ Multi-agent AI pipeline with LangGraph
- ✅ Automatic news collection and filtering
- ✅ Intelligent content summarization
- ✅ Natural script generation
- ✅ Automated scene planning
- ✅ Professional animations with Manim
- ✅ Natural voiceover with Coqui TTS
- ✅ Complete video composition
- ✅ Interactive web interface

## 📊 Agent Workflow

Each agent has a specific responsibility:

1. **News Collection Agent** - Fetches and deduplicates articles
2. **Content Filtering Agent** - Removes irrelevant/clickbait content
3. **Summarization Agent** - Creates concise factual summaries
4. **Script Writer Agent** - Converts to natural narration
5. **Scene Planner Agent** - Breaks into visual scenes
6. **Animation Generator Agent** - Creates animations with Manim
7. **Voiceover Agent** - Generates TTS audio
8. **Video Composer Agent** - Combines everything into final video

## 🎥 Sample Output

Generated videos are 1-1.5 minutes long with:
- Animated text and graphics
- Professional transitions
- Natural voiceover narration
- Background music (optional)
- Clean, modern aesthetic

## 📝 Configuration

Edit `config/settings.yaml` to customize:
- News sources and API keys
- LLM model selection
- Animation style and templates
- Video output settings
- TTS voice preferences

## 🧪 Example Usage

```python
from workflows.news_video_workflow import NewsVideoWorkflow

workflow = NewsVideoWorkflow()
result = workflow.run(
    topic="Artificial Intelligence",
    category="technology",
    duration=90  # seconds
)

print(f"Video generated: {result['output_path']}")
```

## 🎓 Educational Value

This project demonstrates:
- **Agentic AI** - Multi-step autonomous agents
- **LangGraph** - State machine workflows
- **Local LLMs** - Privacy-focused AI
- **Multimedia Generation** - Combining text, audio, video
- **Production Pipeline** - End-to-end automation

## 📄 License

MIT License - Free for educational and commercial use

## 👨‍💻 Author

Created as a demonstration of modern Agentic AI + GenAI capabilities

---

**Perfect for**: AI/ML portfolios, job applications, technical interviews
