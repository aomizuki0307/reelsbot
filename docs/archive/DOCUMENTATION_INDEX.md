# reelsbot Documentation Index

Welcome to the reelsbot documentation! This index will help you find the right documentation for your needs.

---

## Quick Navigation

| Document | Purpose | Audience | Length |
|----------|---------|----------|--------|
| **[README.md](README.md)** | User guide, installation, usage | End users, new developers | 725 lines |
| **[RUNBOOK.md](RUNBOOK.md)** | Operations, deployment, monitoring | DevOps, system administrators | 973 lines |
| **[ARCHITECTURE.md](ARCHITECTURE.md)** | Technical design, implementation details | Developers, architects | 1,678 lines |
| **[Makefile](Makefile)** | Build automation, common tasks | All users | 134 lines |

---

## Getting Started

### I'm a New User
Start here:
1. **[README.md](README.md)** - Read the Quick Start section
2. Install dependencies using the Makefile
3. Configure your `.env` file
4. Run the demo: `make run-demo`

### I'm Deploying to Production
Follow this path:
1. **[README.md](README.md)** - Installation section
2. **[RUNBOOK.md](RUNBOOK.md)** - Setup & Deployment section
3. **[RUNBOOK.md](RUNBOOK.md)** - Scheduling & Automation section
4. Set up monitoring and backups

### I'm a Developer
Recommended reading order:
1. **[README.md](README.md)** - Project overview and features
2. **[ARCHITECTURE.md](ARCHITECTURE.md)** - System design and components
3. **[README.md](README.md)** - Development section
4. Run tests: `make test`

### I Need to Troubleshoot
Find solutions here:
1. **[README.md](README.md)** - Troubleshooting section (common issues)
2. **[RUNBOOK.md](RUNBOOK.md)** - Troubleshooting section (operations)
3. **[RUNBOOK.md](RUNBOOK.md)** - Log Analysis section

---

## Documentation Contents

### README.md - User Documentation
Comprehensive user guide covering:

- **Overview** (What is reelsbot?)
- **Quick Start** (Get running in <10 minutes)
- **Installation** (Step-by-step setup)
- **Configuration** (Environment variables, API keys)
- **Usage** (CLI commands and examples)
- **Content Types** (A-type vs E-type explained)
- **Output Structure** (Understanding generated files)
- **Troubleshooting** (Common issues and solutions)
- **Development** (Running tests, contributing)

**Best for:** First-time users, installation, basic usage

### RUNBOOK.md - Operations Manual
Production operations and deployment:

- **System Requirements** (Hardware, software, API access)
- **Setup & Deployment** (Production installation)
- **Operations** (Daily workflows, batch processing)
- **Scheduling & Automation** (Windows Task Scheduler setup)
- **Monitoring & Logging** (Health checks, metrics)
- **Troubleshooting** (Operational issues)
- **Maintenance** (Daily, weekly, monthly tasks)
- **Disaster Recovery** (Backup and restore procedures)
- **Security** (API keys, access control)

**Best for:** DevOps teams, system administrators, production deployment

### ARCHITECTURE.md - Technical Documentation
Deep technical design and implementation:

- **System Overview** (High-level architecture)
- **Architecture Layers** (4-layer design)
- **Component Details** (Phase 1-4 components)
- **Data Models** (ReelPlan, ReelMetadata schemas)
- **Design Decisions** (FFmpeg, LLM abstraction, policy gate)
- **Extension Points** (Instagram API, external generators)
- **Safety & Compliance** (Policy validation, brand safety)
- **Performance** (Optimization strategies)
- **Future Enhancements** (Roadmap)

**Best for:** Developers, architects, understanding internals

### Makefile - Build Automation
Windows-compatible automation commands:

- `make help` - Show all available targets
- `make setup` - Install dependencies and create environment
- `make install` - Install package in development mode
- `make test` - Run tests with coverage
- `make lint` - Run code quality checks
- `make format` - Format code
- `make clean` - Clean outputs and cache
- `make run-demo` - Generate demo videos (1 A + 1 E)
- `make check-deps` - Verify all dependencies installed

**Best for:** Quick commands, automation, CI/CD integration

---

## Common Tasks - Quick Reference

### Installation
```powershell
# See: README.md - Installation section
make setup
notepad .env  # Configure API keys
make check-deps
```

### Generate Your First Video
```powershell
# See: README.md - Usage section
make run-demo
```

### Deploy to Production
```powershell
# See: RUNBOOK.md - Setup & Deployment section
git clone https://github.com/yourusername/reelsbot.git
cd reelsbot
make setup
# Configure .env with production API keys
# Setup Windows Task Scheduler (see RUNBOOK.md)
```

### Understand the Architecture
```
# See: ARCHITECTURE.md - System Overview section
Read the high-level architecture diagram
Review component responsibilities
Understand data flow
```

### Troubleshoot Issues
```powershell
# See: README.md or RUNBOOK.md - Troubleshooting sections

# Check logs
Get-Content logs\run_*.log -Tail 50

# Verify configuration
python -m reelsbot info

# Test FFmpeg
ffmpeg -version

# Run diagnostics
make check-deps
```

---

## Documentation Standards

All documentation follows these principles:

- **Windows-First**: All commands work on Windows (PowerShell/CMD)
- **Cross-Platform**: Also compatible with Linux/macOS where possible
- **Examples**: Every concept includes concrete examples
- **Troubleshooting**: Common issues addressed proactively
- **Links**: Cross-references between documents
- **Code Blocks**: Syntax highlighting for all code examples

---

## Version Information

- **reelsbot Version**: 0.1.0
- **Documentation Last Updated**: 2025-12-19
- **Python Requirement**: 3.10+
- **Coverage**: 3,510 lines across 4 documents

---

## Additional Resources

### Project Files
- **pyproject.toml** - Project configuration and dependencies
- **.env.example** - Environment variable template
- **policies/blocked_terms.txt** - Content policy configuration

### Phase Summaries
- **PHASE1_SUMMARY.md** - Foundation implementation
- **PHASE2_SUMMARY.md** - Business logic implementation
- **PHASE3_IMPLEMENTATION_SUMMARY.md** - Video generation
- **PHASE4_IMPLEMENTATION_SUMMARY.md** - Orchestration
- **PROJECT_COMPLETE.md** - Overall project completion
- **TEST_SUITE_SUMMARY.md** - Testing details

### External Documentation
- [Anthropic API Docs](https://docs.anthropic.com/)
- [OpenAI API Docs](https://platform.openai.com/docs)
- [FFmpeg Documentation](https://ffmpeg.org/documentation.html)
- [Instagram Graph API](https://developers.facebook.com/docs/instagram-api)

---

## Getting Help

If you can't find what you need in the documentation:

1. **Check the documentation index** (this file)
2. **Search within documents** using Ctrl+F
3. **Review troubleshooting sections** in README.md and RUNBOOK.md
4. **Check logs** in `logs/` directory
5. **Open an issue** on GitHub with:
   - What you were trying to do
   - What happened instead
   - Relevant log excerpts
   - Your configuration (without API keys!)

---

## Contributing to Documentation

Documentation improvements are welcome! When contributing:

1. Follow the existing style and structure
2. Include concrete examples
3. Test all commands on Windows
4. Add cross-references to related sections
5. Update this index if adding new documents

---

**Happy automating with reelsbot!**

For questions or issues, visit: https://github.com/yourusername/reelsbot
