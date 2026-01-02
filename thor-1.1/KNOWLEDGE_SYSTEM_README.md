# Thor 1.1 Knowledge Acquisition System

## Overview

The Knowledge Acquisition System is an automated, continuous learning system that crawls the web, extracts knowledge, and stores it in a SQLite database. The system uses a mixed topic discovery strategy combining pre-defined topics, user queries, trending topics, and discovered related topics.

## Features

- **Persistent SQLite Storage**: All knowledge is stored in a SQLite database for fast queries and persistence
- **Mixed Topic Discovery**: Automatically learns from dictionary topics, user queries, trending topics, and discovered relationships
- **Multi-Source Learning**: Integrates Wikipedia, DuckDuckGo, and Research Engine for comprehensive knowledge
- **Adaptive Learning**: Prioritizes topics based on user queries and importance
- **Quality Filtering**: Filters low-quality content and scores knowledge by confidence
- **Background Daemon**: Can run continuously in the background
- **Comprehensive Statistics**: Track learning progress and database health

## Quick Start

### 1. Start the Knowledge Crawler

```bash
cd thor-1.1

# Start in foreground (for testing)
python3 start_knowledge_crawler.py start

# Start in background (daemon mode)
python3 start_knowledge_crawler.py start --daemon

# Start with custom interval (e.g., every 10 seconds)
python3 start_knowledge_crawler.py start --interval 10
```

### 2. Check Status

```bash
# Quick status check
python3 start_knowledge_crawler.py status

# Detailed statistics
python3 start_knowledge_crawler.py stats
```

### 3. Stop the Crawler

```bash
python3 start_knowledge_crawler.py stop
```

## Usage Examples

### Basic Usage

```bash
# Start the crawler (default: 30 second interval)
python3 start_knowledge_crawler.py start

# Check if it's running
python3 start_knowledge_crawler.py status

# View detailed statistics
python3 start_knowledge_crawler.py stats

# Stop when done
python3 start_knowledge_crawler.py stop
```

### Advanced Usage

```bash
# Start with custom database location
python3 start_knowledge_crawler.py start --db /path/to/custom/knowledge.db

# Start with custom dictionary
python3 start_knowledge_crawler.py start --dictionary /path/to/dictionary.json

# Start with faster crawling (10 second interval)
python3 start_knowledge_crawler.py start --interval 10

# Start in background daemon mode
python3 start_knowledge_crawler.py start --daemon

# Restart the crawler
python3 start_knowledge_crawler.py restart
```

### Programmatic Usage

```python
from brain_learner import BrainLearner
from services.knowledge_db import get_knowledge_db

# Create and start learner
learner = BrainLearner(
    search_interval_seconds=30,
    db_path=None,  # Use default
    dictionary_path=None  # Use default
)

# Start learning
learner.start()

# Get statistics
stats = learner.get_stats()
print(f"Knowledge items: {stats['database']['total_knowledge_items']}")

# Stop when done
learner.stop()
```

### Querying the Knowledge Database

```python
from services.knowledge_db import get_knowledge_db
from brain.connector import BrainConnector

# Direct database access
db = get_knowledge_db()

# Search for knowledge
results = db.search_knowledge(
    query="machine learning",
    limit=10,
    min_confidence=0.5
)

for item in results:
    print(f"Title: {item['title']}")
    print(f"Content: {item['content'][:100]}...")
    print(f"Confidence: {item['confidence']}")
    print()

# Using BrainConnector (recommended)
connector = BrainConnector(use_sqlite=True)
knowledge = connector.get_relevant_knowledge("What is artificial intelligence?")
```

## Configuration

The system can be configured via `knowledge_config.yaml`:

```yaml
crawler:
  search_interval: 30  # Seconds between searches
  min_request_interval: 2.0  # Rate limiting
  max_consecutive_errors: 5

topic_discovery:
  weights:
    dictionary: 0.5
    user_query: 0.3
    trending: 0.15
    discovered: 0.05
```

## Database Schema

The SQLite database contains several tables:

- **knowledge_items**: Core knowledge storage with embeddings
- **topics**: Queue of topics to learn with priorities
- **learning_sessions**: Track crawling sessions
- **user_queries**: Record queries for adaptive learning
- **related_topics**: Topic relationships graph
- **statistics**: Aggregate statistics

## Topic Discovery Strategy

The system uses a weighted mixed strategy:

1. **Dictionary Topics (50%)**: Pre-defined topics from `dictionary.json`
2. **User Queries (30%)**: Topics extracted from user questions
3. **Trending Topics (15%)**: Popular/trending topics from Wikipedia and news
4. **Discovered Topics (5%)**: Related topics found during crawling

## Knowledge Sources

The system learns from multiple sources:

- **Wikipedia API**: High-quality encyclopedic knowledge
- **DuckDuckGo**: Web search results
- **Research Engine**: Comprehensive multi-engine search (if available)
- **Wikipedia Search**: Related articles discovery

## Quality Filtering

Knowledge items are scored and filtered by:

- **Source Reliability**: Wikipedia > Research Engine > DuckDuckGo
- **Content Quality**: Length, completeness, information density
- **Temporal Relevance**: Newer knowledge is preferred
- **Confidence Score**: Minimum threshold (default: 0.3)

## Monitoring and Statistics

### Status Command

```bash
python3 start_knowledge_crawler.py status
```

Shows:
- Crawler status (running/stopped)
- Total knowledge items
- Topics by status
- Recent activity (24h)
- User queries

### Stats Command

```bash
python3 start_knowledge_crawler.py stats
```

Shows detailed statistics:
- Knowledge items breakdown
- Sources distribution
- Topics statistics
- Learning rate estimates
- Time to complete all topics

## Integration with Thor

The knowledge system integrates seamlessly with Thor's inference:

1. **BrainConnector** queries SQLite first, then legacy JSON
2. **User queries** are automatically recorded and prioritized
3. **Research Engine** uses learned knowledge when available
4. **RAG Enhancer** uses SQLite for semantic search

## Troubleshooting

### Crawler Won't Start

- Check if database file is writable
- Verify dictionary.json exists
- Check log file: `crawler.log`

### No Knowledge Being Added

- Check internet connection
- Verify rate limits aren't too strict
- Check for errors in log file
- Try reducing `min_request_interval`

### Database Errors

- Ensure SQLite is available: `python3 -c "import sqlite3; print('OK')"`
- Check database file permissions
- Try deleting `knowledge.db` to recreate schema

### Import Errors

- Ensure all dependencies are installed
- Check Python path includes `thor-1.1` directory
- Some optional dependencies (sentence-transformers, faiss) are optional

## Performance Tips

### High-Speed Learning

The system now uses **parallel processing** for significantly faster learning:

1. **Parallel Workers**: Use `--workers` flag to increase parallel workers (default: 4)
   ```bash
   python3 start_knowledge_crawler.py start --workers 8
   ```

2. **Faster Interval**: Reduce `search_interval` (default: 5s)
   ```bash
   python3 start_knowledge_crawler.py start --interval 2 --workers 8
   ```

3. **Performance Scaling**:
   - **4 workers, 5s interval**: ~48 items/hour, ~21 days to complete all topics
   - **8 workers, 2s interval**: ~180 items/hour, ~5.5 days to complete
   - **16 workers, 1s interval**: ~576 items/hour, ~1.7 days to complete

### Other Optimizations

1. **Better Quality**: Increase `min_confidence` threshold
2. **More Topics**: Add topics to `dictionary.json`
3. **Background Mode**: Use `--daemon` flag for production
4. **Rate Limiting**: Adjust `min_request_interval` in config if needed

## File Structure

```
thor-1.1/
├── knowledge.db              # SQLite database (created automatically)
├── dictionary.json           # Topic dictionary (10,000+ topics)
├── knowledge_config.yaml     # Configuration file
├── crawler.log              # Log file
├── crawler.pid              # PID file (when running)
├── brain_learner.py         # Main learning engine
├── start_knowledge_crawler.py  # Daemon launcher
└── services/
    ├── knowledge_db.py      # SQLite database layer
    ├── trending_topics.py   # Trending topic discovery
    └── topic_extractor.py   # Topic extraction from queries
```

## API Reference

### BrainLearner

```python
learner = BrainLearner(
    search_interval_seconds=5,      # Default: 5s (was 30s)
    db_path=None,
    dictionary_path=None,
    parallel_workers=4              # Default: 4 parallel workers
)

learner.start()           # Start learning
learner.stop()            # Stop learning
learner.pause()           # Pause learning
learner.resume()          # Resume learning
stats = learner.get_stats()  # Get statistics
```

### KnowledgeDatabase

```python
db = get_knowledge_db()

# Add knowledge
db.add_knowledge(topic, content, title, source, url, confidence)

# Search knowledge
results = db.search_knowledge(query, limit=10, min_confidence=0.3)

# Get statistics
stats = db.get_database_stats()

# Add topic to queue
db.add_topic(topic, category, source, priority)

# Get next topic
topic = db.get_next_topic()
```

## Examples

### Example 1: Start and Monitor

```bash
# Start crawler
python3 start_knowledge_crawler.py start --interval 30

# In another terminal, monitor progress
watch -n 60 'python3 start_knowledge_crawler.py stats'
```

### Example 2: Query Learned Knowledge

```python
from services.knowledge_db import get_knowledge_db

db = get_knowledge_db()

# Search for specific topic
results = db.search_knowledge("quantum computing", limit=5)

for item in results:
    print(f"{item['title']}: {item['content'][:200]}...")
```

### Example 3: Add Custom Topics

```python
from services.knowledge_db import get_knowledge_db

db = get_knowledge_db()

# Add high-priority custom topics
db.add_topic("custom topic 1", category="custom", source="manual", priority=9)
db.add_topic("custom topic 2", category="custom", source="manual", priority=9)
```

## Best Practices

1. **Start Slow**: Begin with default 30-second interval, then optimize
2. **Monitor Regularly**: Check stats daily to ensure healthy operation
3. **Backup Database**: Regularly backup `knowledge.db` file
4. **Clean Old Data**: Run cleanup periodically to remove stale knowledge
5. **Respect Rate Limits**: Don't set intervals too low to avoid being blocked

## Support

For issues or questions:
- Check `crawler.log` for error messages
- Run `python3 start_knowledge_crawler.py status` for diagnostics
- Review database stats for anomalies

