# 🤖 ANCA - Autonomous Niche Content Agent

An AI-powered multi-agent system for automated affiliate marketing content creation.

## 🚀 Quick Start with Docker

### Prerequisites
- Docker Desktop installed
- Gemini API key (get one from [Google AI Studio](https://makersuite.google.com/app/apikey))

### Setup

1. **Clone and navigate to the project:**
   ```bash
   cd c:\Users\theje\code\anca
   ```

2. **Create your `.env` file:**
   ```bash
   # Copy the example or create manually
   echo GEMINI_API_KEY=your_api_key_here > .env
   ```

3. **Build and run with Docker Compose:**
   ```bash
   # Build the Docker image
   docker-compose build

   # Run the ANCA system
   docker-compose up
   ```

4. **Check generated articles:**
   Articles will be saved in the `./articles` directory.

### Docker Commands

```bash
# Run in detached mode (background)
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the container
docker-compose down

# Rebuild after code changes
docker-compose up --build

# Run interactively for debugging
docker-compose run --rm anca /bin/bash
```

## 📁 Project Structure

```
anca/
├── agents/          # Agent definitions (future)
├── articles/        # Generated content output
├── tools/           # Custom CrewAI tools
│   ├── scraper_tool.py
│   └── file_writer_tool.py
├── run_crew.py      # Main execution script
├── Dockerfile       # Docker configuration
├── docker-compose.yml
├── requirements.txt # Python dependencies
└── .env            # API keys (not in git)
```

## 🛠️ Development

### Local Development (without Docker)

If you prefer to run locally:

```bash
# Create virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Run the crew
python run_crew.py
```

### Modifying the Topic

Edit `run_crew.py` line 106 to change the topic:
```python
topic = "your topic here"
```

## 🎯 Current Status: Stage 2

- ✅ Stage 1: Local Foundation & Core Tooling
- 🔄 Stage 2: Two-Agent Proof of Concept (Current)
- ⏳ Stage 3: Expertise & Reflection (RAG + SEO Auditor)
- ⏳ Stage 4: Deployment Showcase (FastAPI)
- ⏳ Stage 5: Hosted Resource & Monetization

## 📚 Architecture

See [ANCA.md](./ANCA.md) for full system documentation.

### Current Agents:
1. **Market Researcher** - Finds low-competition keywords
2. **Content Generator** - Creates SEO-optimized articles

### Future Agents:
3. **SEO Auditor** - Quality control with reflection loop
4. **Publisher/Distributor** - Monetization and distribution

## 🐛 Troubleshooting

**Issue: Package installation fails**
- Solution: Use Docker (recommended) or check Python version (requires 3.13+)

**Issue: API key errors**
- Solution: Ensure `.env` file exists with valid `GEMINI_API_KEY`

**Issue: Articles not generating**
- Solution: Check logs with `docker-compose logs -f`

## 📝 License

MIT
