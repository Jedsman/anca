# ANCA Dev Container

## 🚀 Quick Start

1. **Install Prerequisites:**
   - [Docker Desktop](https://www.docker.com/products/docker-desktop)
   - [VS Code](https://code.visualstudio.com/)
   - [Dev Containers Extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers)

2. **Open in Dev Container:**
   - Open this folder in VS Code
   - Press `F1` → Select "Dev Containers: Reopen in Container"
   - Wait for container to build (first time takes ~5 minutes)

3. **Start Coding:**
   - All dependencies are pre-installed
   - Python 3.13 ready to go
   - Full IntelliSense and debugging support

## 🎯 Features

### Installed Extensions
- Python (IntelliSense, linting, debugging)
- Ruff (fast Python linter/formatter)
- YAML support
- Spell checker

### Development Tools
- Git
- GitHub CLI
- IPython (interactive Python)
- Pytest (testing framework)
- Ruff (linting & formatting)

### Debugging
Press `F5` or use the Debug panel to:
- Run the full ANCA crew
- Debug individual Python files
- Run tests with breakpoints

## 📁 Workspace Structure

```
/workspace/          # Your code (mounted from host)
├── run_crew.py      # Main entry point
├── agents/          # Agent definitions
├── tools/           # Custom tools
└── articles/        # Generated content
```

## 💡 Useful Commands

```bash
# Run ANCA crew
python run_crew.py

# Interactive Python shell
ipython

# Run tests
pytest

# Format code
ruff format .

# Lint code
ruff check .

# Install new package
pip install package-name
# Then add to requirements.txt
```

## 🔧 Customization

Edit `.devcontainer/devcontainer.json` to:
- Add more VS Code extensions
- Change Python settings
- Add additional tools
- Modify port forwarding

## 🐛 Troubleshooting

**Container won't build:**
- Ensure Docker Desktop is running
- Check Docker has enough resources (4GB+ RAM recommended)

**Extensions not working:**
- Reload window: `F1` → "Developer: Reload Window"

**Can't see .env file:**
- It's mounted from the host, ensure it exists in project root

**Need to rebuild:**
- `F1` → "Dev Containers: Rebuild Container"
