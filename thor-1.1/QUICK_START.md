# Quick Start Guide - Knowledge Acquisition System

## 🚀 Getting Started in 3 Steps

### Step 1: Start the Crawler

```bash
cd thor-1.1
python3 start_knowledge_crawler.py start
```

The crawler will:
- Load 2,470+ topics from `dictionary.json`
- Start learning continuously every 30 seconds
- Store knowledge in `knowledge.db` SQLite database

### Step 2: Monitor Progress

```bash
# Check status
python3 start_knowledge_crawler.py status

# View detailed stats
python3 start_knowledge_crawler.py stats
```

### Step 3: Use the Knowledge

```python
from brain.connector import BrainConnector

connector = BrainConnector(use_sqlite=True)
knowledge = connector.get_relevant_knowledge("What is machine learning?")
```

## 📋 Common Commands

```bash
# Start crawler
python3 start_knowledge_crawler.py start

# Start with more workers for even faster learning
python3 start_knowledge_crawler.py start --workers 8

# Start with faster interval (2 seconds) and more workers
python3 start_knowledge_crawler.py start --interval 2 --workers 8

# Start in background
python3 start_knowledge_crawler.py start --daemon

# Check status
python3 start_knowledge_crawler.py status

# View statistics
python3 start_knowledge_crawler.py stats

# Stop crawler
python3 start_knowledge_crawler.py stop

# Restart crawler
python3 start_knowledge_crawler.py restart
```

## 📊 What Gets Learned?

The system automatically learns about:
- **Science & Technology**: AI, physics, chemistry, biology
- **Programming**: Languages, frameworks, algorithms
- **History**: Events, people, civilizations
- **Mathematics**: Concepts, theorems, formulas
- **Arts & Culture**: Literature, music, art
- **And 2,470+ more topics!**

## 🔍 Query Examples

```python
from services.knowledge_db import get_knowledge_db

db = get_knowledge_db()

# Search for knowledge
results = db.search_knowledge("quantum computing", limit=5)

for item in results:
    print(f"{item['title']}")
    print(f"{item['content'][:200]}...")
    print(f"Confidence: {item['confidence']:.2f}\n")
```

## ⚙️ Configuration

Edit `knowledge_config.yaml` to customize:
- Search interval
- Topic discovery weights
- Quality filters
- Logging settings

## 📈 Expected Performance (High-Speed Mode)

- **Learning Rate**: ~48 items/hour (with 4 workers, 5s interval)
- **Topics/Hour**: ~12 topics (with 4 workers, 5s interval)
- **Database Growth**: ~1,150 items/day (with 4 workers, 5s interval)
- **Time to Complete**: ~21 days for all 2,470 topics (with 4 workers)
- **Speed Improvement**: ~72x faster than original sequential mode!

## 🛠️ Troubleshooting

**Crawler won't start?**
```bash
# Check logs
tail -f crawler.log

# Verify database
python3 -c "from services.knowledge_db import get_knowledge_db; db = get_knowledge_db(); print('OK')"
```

**No knowledge being added?**
- Check internet connection
- Verify rate limits in config
- Check for errors in `crawler.log`

**Import errors?**
- Ensure you're in `thor-1.1` directory
- Some dependencies are optional (sentence-transformers, faiss)

## 📚 Full Documentation

See `KNOWLEDGE_SYSTEM_README.md` for complete documentation.

