"""
Service layer package for Thor 1.1 (Enhanced version with improved capabilities).
Provides cohesive imports for trainer, handlers, and utilities.
"""
from .auto_trainer import get_auto_trainer  # noqa: F401
from .learning_tracker import get_tracker  # noqa: F401
from .greetings_handler import get_greetings_handler  # noqa: F401
from .common_sense_handler import get_common_sense_handler  # noqa: F401
from .research_engine import get_research_engine  # noqa: F401
from .query_intent_analyzer import get_query_intent_analyzer  # noqa: F401
from .semantic_relevance import get_semantic_scorer  # noqa: F401
from .creative_response import get_creative_generator  # noqa: F401
from .image_processor import get_image_processor  # noqa: F401
from .code_handler import get_code_handler  # noqa: F401
from .response_cleaner import get_response_cleaner  # noqa: F401

