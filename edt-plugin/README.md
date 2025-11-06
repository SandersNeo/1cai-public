# 1C AI Assistant EDT Plugin

Eclipse plugin for 1C:Enterprise Development Tools with AI capabilities.

**🎉 Новое в версии 1.1: Полная интеграция с оркестратором анализа!**

## ✨ Features

### 5 Views:

1. **AI Assistant** - Chat interface with AI about your 1C configuration
2. **Metadata Graph** - Visualize metadata graph from Neo4j
3. **Semantic Search** - Search code by meaning using vector search
4. **Code Optimizer** - AI-powered code optimization
5. **Analysis Dashboard** ✨ NEW - Отображение результатов полного анализа конфигурации

### Context Menu Actions:

Right-click on any BSL function:
- **Quick Analysis** ✨ NEW - Быстрый анализ функции (метрики, зависимости, проблемы)
- **Analyze with AI** - Get AI analysis of function
- **Optimize Function** - Get AI optimization suggestions
- **Find Similar Code** - Find semantically similar functions
- **Show Call Graph** - Visualize function dependencies

### Main Menu:

**1C AI Assistant** menu:
- **Run Full Analysis** ✨ NEW - Запустить полный анализ конфигурации (6 шагов)
- **Quick Analysis** ✨ NEW - Быстрый анализ (только парсинг)
- **Refresh Dependencies** ✨ NEW - Обновить граф зависимостей
- **Update Best Practices** ✨ NEW - Обновить best practices
- **Generate Code...** - Мастер генерации кода

### Keyboard Shortcuts:

- **Ctrl+Alt+A** - Open AI Assistant
- **Ctrl+Alt+S** - Semantic Search
- **Ctrl+Alt+Q** ✨ NEW - Quick Analysis (текущей функции)
- **Ctrl+Alt+O** - Optimize Code

## Building

### Prerequisites:

- Java 17+
- Maven 3.8+
- Eclipse/EDT SDK

### Build:

```bash
cd edt-plugin
mvn clean package
```

Output: `target/com.1cai.edt-1.0.0-SNAPSHOT.jar`

## Installation

### Method 1: From Update Site (after build)

1. In EDT: **Help → Install New Software**
2. Click **Add → Local**
3. Browse to: `edt-plugin/target/repository`
4. Select **1C AI Assistant**
5. Click **Next → Finish**
6. Restart EDT

### Method 2: Direct JAR (for development)

1. Build plugin
2. Copy JAR to: `<EDT_HOME>/plugins/`
3. Restart EDT with `-clean` flag

## Configuration

### 1. Set Backend URLs

**Window → Preferences → 1C AI Assistant → Connection Settings**

- MCP Server URL: `http://localhost:6001`
- Graph API URL: `http://localhost:8080`
- Click **Test Connection**

### 2. Enable Features

**Window → Preferences → 1C AI Assistant**

- ✓ Enable AI Assistant
- ✓ Auto-suggest (optional)

## Usage

### Open Views:

**Window → Show View → Other... → 1C AI Assistant**

Select view:
- AI Assistant
- Metadata Graph
- Semantic Search
- Code Optimizer

### Use Context Menu:

1. Open BSL module
2. Right-click on function
3. Select action from **1C AI Assistant** submenu

## 🚀 Quick Start

### 1. Backend Setup

Plugin requires running backend services:

```bash
# Start all services
docker-compose -f docker-compose.yml -f docker-compose.stage1.yml up -d

# Or start specific services
python -m uvicorn src.api.graph_api:app --port 8080
python -m uvicorn src.ai.mcp_server:app --port 6001
```

### 2. Configure Plugin

**Window → Preferences → 1C AI Assistant → Connection Settings**

- MCP Server URL: `http://localhost:6001`
- Graph API URL: `http://localhost:8080`
- Click **Test Connection** to verify

### 3. Run Analysis

**1C AI Assistant → Run Full Analysis**

- Enter configuration name (e.g., `ERPCPM`)
- Wait for completion (15-20 minutes)
- Dashboard will auto-update with results

### 4. View Results

**Window → Show View → Other... → 1C AI Assistant → Analysis Dashboard**

Shows:
- 📊 Architecture statistics
- 🔗 Dependencies graph
- ✅ Best practices score
- 📈 Code quality trends

## Development

### Project Structure:

```
edt-plugin/
├── plugin.xml           # Plugin configuration
├── META-INF/
│   └── MANIFEST.MF     # OSGi manifest
├── pom.xml             # Maven build
├── build.properties
└── src/com/1cai/edt/
    ├── Activator.java  # Plugin activator
    ├── views/          # View classes
    │   ├── AIAssistantView.java
    │   ├── MetadataGraphView.java
    │   ├── SemanticSearchView.java
    │   └── CodeOptimizerView.java
    ├── actions/        # Context menu actions
    │   ├── AnalyzeFunctionAction.java
    │   ├── OptimizeFunctionAction.java
    │   ├── FindSimilarCodeAction.java
    │   └── ShowCallGraphAction.java
    ├── services/       # Backend integration
    │   └── BackendConnector.java
    └── preferences/    # Preference pages
        ├── MainPreferencePage.java
        └── ConnectionPreferencePage.java
```

### Dependencies:

- Eclipse Platform
- 1C EDT API (`com._1c.g5.v8.dt.*`)
- Apache HttpClient
- Gson (JSON)

## Troubleshooting

### Plugin doesn't appear in EDT

1. Check EDT version (must be 2023.3.6+)
2. Check Java version (must be 17+)
3. Restart EDT with `-clean` flag
4. Check Error Log view

### Backend connection failed

1. Verify services running: `docker-compose ps`
2. Test URLs manually:
   - http://localhost:8080/health
   - http://localhost:6001/mcp
3. Check firewall settings

### Views don't show data

1. Check backend connection in Preferences
2. Verify data migrated to databases
3. Check backend logs

## License

MIT License

## 📚 Documentation

- **README.md** (this file) - Getting started
- **ENHANCEMENT_PROPOSALS.md** - Detailed improvement proposals (43 pages)
- **IMPROVEMENT_SUMMARY.md** - Summary of improvements
- **NEXT_STEPS.md** - Implementation guide for developers

## 🎯 Examples

### Example 1: Quick Analysis

```
1. Open BSL module in EDT
2. Place cursor on function
3. Press Ctrl+Alt+Q (or right-click → Quick Analysis)
4. View results:
   - 📊 Metrics: LOC, complexity, parameters
   - 🔗 Dependencies: who calls, what calls
   - ⚠️ Problems: missing error handling, magic numbers
   - 💡 Suggestions: refactoring recommendations
```

### Example 2: Run Full Analysis

```
1. Menu: 1C AI Assistant → Run Full Analysis
2. Enter configuration: ERPCPM
3. Wait for completion (progress shown in Progress View)
4. View results in Analysis Dashboard:
   - Total modules: 4,517
   - Catalogs: 1,344
   - Documents: 847
   - Best practices score: 89.1%
```

### Example 3: View Dependencies

```
1. Open Analysis Dashboard
2. Click "Показать граф" in Dependencies section
3. View interactive graph:
   - Circular dependencies highlighted
   - Impact analysis available
   - Export to PNG
```

## 🆕 What's New in v1.1

### Analysis Dashboard View ✨
- Real-time display of orchestrator results
- Architecture statistics from JSON files
- Dependencies visualization
- Best practices scoring
- Trends tracking

### Orchestrator Integration ✨
- Run analysis directly from EDT menu
- Progress tracking with real-time updates
- Automatic view refresh on completion
- Support for partial analysis (deps only, BP only)

### Quick Analysis Action ✨
- Instant function metrics
- Local analysis (no backend needed)
- Backend integration for dependencies
- Problem detection and suggestions
- Keyboard shortcut: Ctrl+Alt+Q

## 🔧 Architecture

```
EDT Plugin
    ↓
    ├─→ Views (UI)
    │   ├─ AI Assistant
    │   ├─ Semantic Search
    │   ├─ Code Optimizer
    │   ├─ Metadata Graph
    │   └─ Analysis Dashboard ✨ NEW
    │
    ├─→ Actions (User interactions)
    │   ├─ Quick Analysis ✨ NEW
    │   ├─ Analyze Function
    │   ├─ Optimize Function
    │   └─ Run Orchestrator ✨ NEW
    │
    └─→ Services (Backend integration)
        ├─ BackendConnector (MCP Server, Graph API)
        └─ OrchestratorRunner ✨ NEW (runs analysis pipeline)
            ↓
            scripts/orchestrate_edt_analysis.sh
            ↓
            ├─ Step 1: Parse EDT
            ├─ Steps 2-5: Parallel analysis
            │   ├─ Architecture
            │   ├─ ML Dataset
            │   ├─ Dependencies
            │   └─ Best Practices
            └─ Step 6: Documentation
            ↓
            output/analysis/*.json
            ↓
            Analysis Dashboard (auto-refresh)
```

## 📊 Performance

### Time Savings

**Without plugin**:
- Switch to terminal
- Run orchestrator manually
- Wait 15-20 minutes
- Open JSON files manually
- Analyze results
= **25-30 minutes total**

**With plugin**:
- Menu → Run Full Analysis → OK
- Continue working (background job)
- Get notification when done
- View results in Dashboard
= **2 minutes active time**

**Savings: 23-28 minutes per analysis run!**

## 🐛 Known Issues

1. **EDT API Integration** - Currently using placeholders for function extraction
   - TODO: Integrate with `com._1c.g5.v8.dt.bsl.model`
   - Workaround: Manual function selection works

2. **Graph Visualization** - Metadata graph view needs enhancement
   - TODO: Add interactive graph library (JGraphX)
   - Current: Text-based display

3. **Windows Support** - Orchestrator runner needs PowerShell wrapper
   - TODO: Create `orchestrate_edt_analysis.ps1`
   - Workaround: Use WSL or Git Bash

## 🤝 Contributing

Interested in improving the plugin? See:
- **NEXT_STEPS.md** - Implementation guide
- **ENHANCEMENT_PROPOSALS.md** - Detailed roadmap

Priority tasks:
1. ⭐ EDT API integration for real function extraction
2. ⭐ Interactive graph visualization
3. ⭐ Code generation wizard
4. Unit tests
5. Localization (EN/RU)

## Support

See main project documentation:
- [START_HERE.md](../START_HERE.md)
- [DEPLOYMENT_INSTRUCTIONS.md](../DEPLOYMENT_INSTRUCTIONS.md)

## License

MIT License







