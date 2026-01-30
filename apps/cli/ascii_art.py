"""
ASCII art generation utilities for Atlas CLI
"""


def get_atlas_text() -> str:
    """
    Generate green-colored large ASCII "ATLAS" text.
    
    Uses simple block letters if pyfiglet is not available,
    otherwise uses pyfiglet for better rendering.
    
    Returns:
        String containing green-colored ASCII "ATLAS" text
    """
    try:
        import pyfiglet
        atlas_art = pyfiglet.figlet_format("ATLAS", font="block")
    except ImportError:
        # Fallback to simple ASCII if pyfiglet not available
        atlas_art = """
  █████╗ ████████╗██╗     █████╗ ████████╗
 ██╔══██╗╚══██╔══╝██║    ██╔══██╗╚══██╔══╝
 ███████║   ██║   ██║    ███████║   ██║   
 ██╔══██║   ██║   ██║    ██╔══██║   ██║   
 ██║  ██║   ██║   ███████╗██║  ██║   ██║   
 ╚═╝  ╚═╝   ╚═╝   ╚══════╝╚═╝  ╚═╝   ╚═╝   
        """
    
    # Color the ATLAS text green using ANSI escape codes
    green = '\033[32m'  # Green
    reset = '\033[0m'   # Reset
    
    return f"{green}{atlas_art}{reset}"


def print_banner():
    """
    Print the complete Atlas CLI banner (ATLAS text only).
    """
    atlas = get_atlas_text()
    
    print(atlas)
    print()  # Empty line for spacing
