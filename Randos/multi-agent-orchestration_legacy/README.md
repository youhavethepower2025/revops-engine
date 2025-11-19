# Multi-Agent AI Orchestration System

A comprehensive multi-agent AI orchestration platform with environmental monitoring capabilities, integrating state-of-the-art frameworks for autonomous agent collaboration, memory management, and workflow orchestration.

## 🚀 Key Components Installed

### Core Orchestration
- **CrewAI** - Role-based autonomous agents with 5.76x performance optimization
- **LangChain** - Comprehensive orchestration backbone with 400+ integrations
- **LangGraph** - Graph-based workflow orchestration

### Memory & Consciousness
- **Mem0** - Hierarchical memory system with 26% accuracy improvement
- **Qdrant** - Vector database for semantic memory

### Multimodal Interactions
- **Pipecat** - Real-time multimodal conversational AI
- **OpenAI** - LLM integration for agent intelligence

### Workflow & Experiments
- **Prefect** - Modern Python-native workflow automation
- **MLflow** - Experiment tracking and model registry

### Environmental Monitoring
- Custom environmental monitoring module
- Biodiversity tracking system
- Emergency response capabilities

## 📁 Project Structure

```
multi-agent-orchestration/
├── core/                  # Core orchestration logic
├── environmental/         # Environmental monitoring modules
│   └── environmental_monitor.py
├── memory/               # Memory management systems
├── workflows/            # Prefect workflow definitions
├── experiments/          # MLflow experiments
├── main.py              # Main orchestration script
├── requirements.txt     # Python dependencies
└── venv/               # Virtual environment
```

## 🔧 Installation

The system is already installed in a virtual environment. To activate:

```bash
cd "/Users/aijesusbro/AI Projects/multi-agent-orchestration"
source venv/bin/activate
```

## 🏃 Running the System

### Basic Usage

```bash
# Set your OpenAI API key
export OPENAI_API_KEY="your-api-key-here"

# Run the main orchestration
python main.py
```

### Environmental Monitoring Only

```bash
python -m environmental.environmental_monitor
```

## 🎯 Key Features

### Multi-Agent Collaboration
- Specialized agents for different domains
- Sequential and hierarchical task processing
- Autonomous decision-making with delegation

### Environmental Focus
- Real-time sensor data collection
- Biodiversity index calculation
- Habitat health assessment
- Emergency response system

### Memory Systems
- Hierarchical memory (L1/L2/L3 cache-like)
- User/Session/Agent context management
- Vector-based semantic search

### Workflow Orchestration
- DAG-based task automation
- Event-driven architecture
- Real-time monitoring and alerts

## 📊 Architectural Patterns

1. **Hierarchical Memory Systems** - Multi-level caching for efficient retrieval
2. **Event-Driven Architecture** - Real-time processing of agent interactions
3. **Plugin-Based Extensibility** - Easy integration of new capabilities
4. **Sequential → Concurrent → Hierarchical** - Flexible workflow patterns

## 🔬 Experiment Tracking

MLflow UI can be accessed at:
```bash
mlflow ui
# Navigate to http://localhost:5000
```

## 🚨 Emergency Response

The system includes automatic emergency detection for:
- High CO2 levels (>1000 ppm)
- Poor water quality (pH outside 6.5-8.5)
- Temperature extremes
- Biodiversity threats

## 📈 Performance Metrics

- **CrewAI**: 5.76x faster execution than alternatives
- **Mem0**: 26% accuracy improvement, 91% faster responses
- **Token Usage**: 90% reduction through intelligent caching

## 🔗 Next Steps

1. Configure API keys in environment variables
2. Customize agent roles and goals in `main.py`
3. Add specific environmental sensors
4. Deploy Prefect workflows to cloud
5. Set up continuous monitoring dashboards

## 📝 Notes

- The system requires an OpenAI API key for LLM features
- Environmental data is currently simulated; connect real sensors for production
- MLflow experiments are stored locally by default

## 🤝 Contributing

To extend the system:
1. Add new agents in `main.py`
2. Create custom tasks in the workflows directory
3. Implement new environmental sensors
4. Add memory persistence backends

## 📜 License

This project integrates multiple open-source components. Please review individual library licenses.