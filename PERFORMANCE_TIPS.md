# 🔧 Configuration Tips for Better Performance

## LLM Timeout Issues

If you're experiencing timeout errors with Ollama, try these solutions:

### 1. **Increase Timeout** (Already Applied)
The timeout has been increased to 300 seconds (5 minutes) in `config/settings.yaml`:
```yaml
llm:
  timeout: 300  # 5 minutes
```

### 2. **Reduce Token Count** (Already Applied)
Reduced `max_tokens` to 1000 for faster generation:
```yaml
llm:
  max_tokens: 1000  # Faster than 2000
```

### 3. **Use Faster Model**
If llama3 is too slow, try mistral:
```yaml
llm:
  model: "mistral"  # Faster alternative
```

### 4. **Reduce Content Length**
Edit `config/settings.yaml`:
```yaml
content:
  summary_length: 100  # Reduced from 150
  target_duration: 60  # Reduced from 90
```

### 5. **Check Ollama Performance**
```bash
# Check if Ollama is running
ollama list

# Test Ollama directly
ollama run llama3 "Hello, how are you?"
```

### 6. **Restart Ollama**
If it's slow or hanging:
```bash
# Windows: Right-click Ollama in system tray → Quit
# Then restart Ollama application
```

---

## Optimized Settings for Slow Systems

If your system is slow, use these settings in `config/settings.yaml`:

```yaml
llm:
  model: "mistral"  # Faster than llama3
  temperature: 0.5  # Lower = faster
  max_tokens: 500   # Shorter responses
  timeout: 600      # 10 minutes for safety

content:
  summary_length: 80
  target_duration: 45

news:
  max_articles: 3  # Fewer articles = faster
```

---

## Testing Tips

### Use Common Topics
Topics with more news coverage work better:
- ✅ "artificial intelligence"
- ✅ "technology"
- ✅ "climate change"
- ❌ "AI in Public Sector Unit in India" (too specific)

### Test Command
```bash
python test_workflow.py
```

This uses a common topic that should have articles.

---

## Troubleshooting

**Issue:** "Collected 0 articles"
- **Cause:** Topic too specific or no matching RSS content
- **Fix:** Use broader topics like "technology" or "artificial intelligence"

**Issue:** LLM timeout
- **Cause:** Local LLM is slow or overloaded
- **Fix:** 
  1. Reduce `max_tokens` in config
  2. Switch to `mistral` model
  3. Restart Ollama

**Issue:** Slow generation
- **Cause:** System resources
- **Fix:** Close other applications, use optimized settings above

---

## Performance Benchmarks

Typical generation times on average hardware:

| Stage | Time (llama3) | Time (mistral) |
|-------|---------------|----------------|
| News Collection | 5-10s | 5-10s |
| Summarization | 60-120s | 30-60s |
| Script Writing | 60-120s | 30-60s |
| Scene Planning | 30-60s | 15-30s |
| **Total** | **3-5 min** | **1.5-3 min** |

---

**Current Status:** ✅ Timeout increased, tokens reduced, ready for testing!
