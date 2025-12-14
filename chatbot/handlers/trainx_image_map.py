"""
TrainX image mappings for deterministic, hardcoded image responses.

Usage:
- Mapping is keyed by canonical subject.
- Aliases map many user phrasings to a canonical subject.
"""

TRAINX_IMAGE_MAP = {
    # Example provided by user
    "dog": "https://hips.hearstapps.com/clv.h-cdn.co/assets/16/18/gettyimages-586890581.jpg?crop=0.668xw:1.00xh;0.219xw,0",
    # Add a few sensible defaults to avoid broken demos
    "boy": "https://images.pexels.com/photos/346796/pexels-photo-346796.jpeg",
    "tomato": "https://images.pexels.com/photos/1435735/pexels-photo-1435735.jpeg",
    "ice cream": "https://images.pexels.com/photos/461430/pexels-photo-461430.jpeg",
}

TRAINX_ALIASES = {
    "puppy": "dog",
    "pup": "dog",
    "doggo": "dog",
    "kid": "boy",
    "child": "boy",
    "tomatoe": "tomato",
    "tomatoes": "tomato",
    "icecream": "ice cream",
    "gelato": "ice cream",
}


def resolve_subject_alias(subject: str) -> str:
    """
    Resolve an incoming subject to its canonical TrainX subject if one exists.
    """
    if not subject:
        return ""
    key = subject.strip().lower()
    return TRAINX_ALIASES.get(key, key)
