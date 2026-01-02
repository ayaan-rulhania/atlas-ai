"""
Service layer package for Thor 1.1 (Enhanced version with improved capabilities).
Provides cohesive imports for trainer, handlers, and utilities.
Uses lazy imports to avoid circular dependency issues.
"""

# Core services that don't have external dependencies
from .learning_tracker import get_tracker  # noqa: F401
from .knowledge_db import get_knowledge_db  # noqa: F401
from .trending_topics import get_trending_topics_service  # noqa: F401
from .topic_extractor import get_topic_extractor  # noqa: F401

# Services with optional dependencies - import with error handling
try:
    from .auto_trainer import get_auto_trainer  # noqa: F401
except ImportError:
    get_auto_trainer = None

try:
    from .greetings_handler import get_greetings_handler  # noqa: F401
except ImportError:
    get_greetings_handler = None

try:
    from .common_sense_handler import get_common_sense_handler  # noqa: F401
except ImportError:
    get_common_sense_handler = None

try:
    from .research_engine import get_research_engine  # noqa: F401
except ImportError:
    get_research_engine = None

try:
    from .query_intent_analyzer import get_query_intent_analyzer  # noqa: F401
except ImportError:
    get_query_intent_analyzer = None

try:
    from .semantic_relevance import get_semantic_scorer  # noqa: F401
except ImportError:
    get_semantic_scorer = None

try:
    from .creative_response import get_creative_generator  # noqa: F401
except ImportError:
    get_creative_generator = None

try:
    from .image_processor import get_image_processor  # noqa: F401
except ImportError:
    get_image_processor = None

try:
    from .code_handler import get_code_handler  # noqa: F401
except ImportError:
    get_code_handler = None

try:
    from .response_cleaner import get_response_cleaner  # noqa: F401
except ImportError:
    get_response_cleaner = None

