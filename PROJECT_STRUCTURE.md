# LogBERT Hadoop RCA - Project Structure

This document outlines the recommended project structure for the capstone submission.

## 📁 Recommended Directory Structure

```
logbert_hadoop_rca/
├── 📄 README.md                          # Main project documentation
├── 📄 CAPSTONE_OVERVIEW.md              # Academic project overview
├── 📄 CONTRIBUTING.md                    # Contribution guidelines
├── 📄 LICENSE                           # MIT license
├── 📄 .env                             # Environment configuration
├── 📄 .gitignore                       # Git ignore rules
├── 📄 requirements.txt                 # Python dependencies
├── 📄 Dockerfile                       # Container configuration
├── 📄 docker-compose.yml              # Multi-container setup
├── 📄 CHANGELOG.md                     # Version history
├── 📄 pyproject.toml                   # Project metadata
│
├── 📁 docs/                            # Documentation
│   ├── 📄 ARCHITECTURE.md              # System architecture
│   ├── 📄 API_REFERENCE.md             # API documentation
│   ├── 📄 DEPLOYMENT.md                # Deployment guide
│   ├── 📄 RESEARCH_PAPER.md            # Academic writeup
│   ├── 📁 images/                      # Documentation images
│   └── 📁 presentations/               # Slides and posters
│
├── 📁 src/                             # Source code (restructured)
│   ├── 📄 __init__.py
│   ├── 📁 models/                      # ML models
│   │   ├── 📄 __init__.py
│   │   ├── 📄 bert.py                  # BERT implementation
│   │   ├── 📄 logbert.py               # LogBERT model
│   │   ├── 📄 anomaly_detector.py      # Anomaly detection
│   │   └── 📄 deep_svdd.py             # Deep SVDD implementation
│   │
│   ├── 📁 data/                        # Data processing
│   │   ├── 📄 __init__.py
│   │   ├── 📄 preprocessing.py         # Data preprocessing
│   │   ├── 📄 parsers.py              # Log parsers (Drain, etc.)
│   │   ├── 📄 datasets.py             # Dataset classes
│   │   └── 📄 vocabulary.py           # Vocabulary management
│   │
│   ├── 📁 training/                    # Training pipeline
│   │   ├── 📄 __init__.py
│   │   ├── 📄 trainer.py              # Training logic
│   │   ├── 📄 losses.py               # Loss functions
│   │   ├── 📄 metrics.py              # Evaluation metrics
│   │   └── 📄 schedulers.py           # Learning rate scheduling
│   │
│   ├── 📁 inference/                   # Inference pipeline
│   │   ├── 📄 __init__.py
│   │   ├── 📄 pipeline.py             # Main inference pipeline
│   │   ├── 📄 rca_engine.py           # Root cause analysis
│   │   └── 📄 explainer.py            # LLM-based explanations
│   │
│   ├── 📁 api/                         # Web API
│   │   ├── 📄 __init__.py
│   │   ├── 📄 main.py                 # FastAPI app
│   │   ├── 📄 routes.py               # API routes
│   │   ├── 📄 models.py               # Pydantic models
│   │   └── 📄 middleware.py           # API middleware
│   │
│   └── 📁 utils/                       # Utilities
│       ├── 📄 __init__.py
│       ├── 📄 config.py               # Configuration management
│       ├── 📄 logging.py              # Logging setup
│       ├── 📄 visualization.py        # Plotting and visualization
│       └── 📄 helpers.py              # Helper functions
│
├── 📁 tests/                           # Test suite
│   ├── 📄 __init__.py
│   ├── 📄 conftest.py                 # Pytest configuration
│   ├── 📁 unit/                       # Unit tests
│   │   ├── 📄 test_models.py
│   │   ├── 📄 test_preprocessing.py
│   │   ├── 📄 test_training.py
│   │   └── 📄 test_inference.py
│   ├── 📁 integration/                # Integration tests
│   │   ├── 📄 test_api.py
│   │   ├── 📄 test_pipeline.py
│   │   └── 📄 test_end_to_end.py
│   ├── 📁 performance/                # Performance tests
│   │   ├── 📄 test_benchmarks.py
│   │   └── 📄 test_memory_usage.py
│   └── 📁 fixtures/                   # Test data
│       ├── 📁 sample_logs/
│       └── 📁 mock_data/
│
├── 📁 notebooks/                       # Jupyter notebooks
│   ├── 📄 01_data_exploration.ipynb    # EDA notebook
│   ├── 📄 02_model_development.ipynb   # Model development
│   ├── 📄 03_training_analysis.ipynb   # Training analysis
│   ├── 📄 04_evaluation_results.ipynb  # Results analysis
│   └── 📄 05_demo_walkthrough.ipynb    # Live demo
│
├── 📁 configs/                         # Configuration files
│   ├── 📄 model_config.yaml           # Model parameters
│   ├── 📄 training_config.yaml        # Training settings
│   ├── 📄 api_config.yaml             # API configuration
│   └── 📄 deployment_config.yaml      # Deployment settings
│
├── 📁 scripts/                         # Utility scripts
│   ├── 📄 train_model.py              # Training script
│   ├── 📄 evaluate_model.py           # Evaluation script
│   ├── 📄 preprocess_data.py          # Data preprocessing
│   ├── 📄 generate_reports.py         # Report generation
│   └── 📄 setup_environment.py        # Environment setup
│
├── 📁 data/                           # Data directory
│   ├── 📁 raw/                        # Raw datasets
│   │   └── 📁 hadoop_logs/
│   ├── 📁 processed/                  # Processed data
│   │   ├── 📁 train/
│   │   ├── 📁 validation/
│   │   └── 📁 test/
│   ├── 📁 models/                     # Trained models
│   │   ├── 📁 checkpoints/
│   │   ├── 📁 best_models/
│   │   └── 📁 experiments/
│   └── 📁 results/                    # Experiment results
│       ├── 📁 metrics/
│       ├── 📁 visualizations/
│       └── 📁 reports/
│
├── 📁 deployment/                      # Deployment files
│   ├── 📄 docker-compose.prod.yml     # Production compose
│   ├── 📄 kubernetes.yaml             # K8s deployment
│   ├── 📁 helm/                       # Helm charts
│   └── 📁 monitoring/                 # Monitoring setup
│
├── 📁 academic/                        # Academic deliverables
│   ├── 📄 research_paper.pdf          # Main paper
│   ├── 📄 technical_report.pdf        # Technical documentation
│   ├── 📄 presentation.pptx           # Defense presentation
│   ├── 📄 poster.pdf                  # Conference poster
│   ├── 📁 literature_review/          # Background research
│   └── 📁 evaluation_results/         # Experimental results
│
├── 📁 tools/                          # Development tools
│   ├── 📄 setup.py                    # Package setup
│   ├── 📄 lint.sh                     # Code linting
│   ├── 📄 format.sh                   # Code formatting
│   └── 📄 benchmark.py                # Performance benchmarking
│
└── 📁 legacy/                         # Original structure (for reference)
    ├── 📁 AI_MODELS/                  # Original AI models
    ├── 📁 app/                        # Original FastAPI app
    ├── 📁 bert_pytorch/               # Original BERT implementation
    ├── 📁 logparser/                  # Original log parsers
    └── 📁 scripts/                    # Original scripts
```

## 🔧 Migration Steps

To restructure your current project for capstone submission:

### 1. Create New Structure
```bash
# Create new directory structure
mkdir -p src/{models,data,training,inference,api,utils}
mkdir -p tests/{unit,integration,performance,fixtures}
mkdir -p {docs,notebooks,configs,scripts,academic,tools}
mkdir -p data/{raw,processed,models,results}
mkdir -p deployment/{helm,monitoring}
```

### 2. Move Existing Code
```bash
# Move models
mv bert_pytorch/model/* src/models/
mv bert_pytorch/trainer/* src/training/

# Move data processing
mv logparser/* src/data/
mv AI_MODELS/preprocessing/* src/data/

# Move API
mv app/* src/api/

# Move scripts
mv scripts/* scripts/

# Move tests
mv tests/* tests/unit/

# Preserve original for reference
mkdir legacy
mv {AI_MODELS,app,bert_pytorch,logparser} legacy/
```

### 3. Update Import Statements
```python
# Update all import statements to use new structure
# Old: from bert_pytorch.model import BERT
# New: from src.models.bert import BERT

# Old: from logparser import Drain
# New: from src.data.parsers import Drain
```

### 4. Create Academic Deliverables
```bash
# Create academic documents
touch academic/research_paper.pdf
touch academic/technical_report.pdf
touch academic/presentation.pptx
touch academic/poster.pdf
```

## 📝 Key Files to Create

### 1. pyproject.toml
```toml
[build-system]
requires = ["setuptools>=45", "wheel", "setuptools_scm[toml]>=6.2"]
build-backend = "setuptools.build_meta"

[project]
name = "logbert-hadoop-rca"
version = "1.0.0"
description = "Intelligent Root Cause Analysis for Hadoop Clusters using LogBERT"
authors = [{name = "Your Name", email = "your.email@university.edu"}]
license = {text = "MIT"}
readme = "README.md"
requires-python = ">=3.8"
```

### 2. CHANGELOG.md
```markdown
# Changelog

## [1.0.0] - 2025-07-19

### Added
- Initial release of LogBERT Hadoop RCA system
- Complete training pipeline with Deep SVDD
- FastAPI web service for real-time analysis
- Comprehensive test suite and documentation
```

### 3. .gitignore
```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Jupyter Notebook
.ipynb_checkpoints

# PyTorch
*.pth
*.pt

# Data
data/raw/*
data/processed/*
!data/raw/.gitkeep
!data/processed/.gitkeep

# Logs
logs/
*.log

# Environment
.env
.venv
env/
venv/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Academic
academic/*.pdf
academic/*.docx
academic/*.pptx
```

## 🎓 Academic Best Practices

### 1. Documentation Standards
- Use academic citation format
- Include literature review
- Provide comprehensive methodology
- Document all experiments and results

### 2. Code Quality
- Follow PEP 8 style guidelines
- Maintain >90% test coverage
- Use type hints throughout
- Include comprehensive docstrings

### 3. Reproducibility
- Pin all dependency versions
- Provide seed values for random operations
- Document hardware requirements
- Include data provenance information

### 4. Evaluation Methodology
- Use proper train/validation/test splits
- Include statistical significance testing
- Provide ablation studies
- Compare against relevant baselines

## 📊 Capstone Submission Checklist

### Required Deliverables
- [ ] Complete source code with new structure
- [ ] Comprehensive documentation
- [ ] Research paper (10-15 pages)
- [ ] Technical report (20-30 pages)
- [ ] Presentation slides (20-30 slides)
- [ ] Live demonstration
- [ ] Test suite with >90% coverage
- [ ] Deployment instructions

### Academic Requirements
- [ ] Literature review with 20+ citations
- [ ] Novel technical contribution clearly identified
- [ ] Experimental methodology documented
- [ ] Results analysis with statistical validation
- [ ] Future work and limitations discussed
- [ ] Ethical considerations addressed
- [ ] Reproducibility package provided

### Technical Requirements
- [ ] Clean, well-documented code
- [ ] Proper software engineering practices
- [ ] Production-ready deployment
- [ ] Comprehensive testing
- [ ] Performance benchmarking
- [ ] Security considerations
- [ ] Scalability analysis

This restructured project will present much more professionally for your capstone submission and demonstrate software engineering best practices alongside your technical contributions.
