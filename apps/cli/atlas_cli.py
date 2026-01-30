#!/usr/bin/env python3
"""
Atlas CLI - Command-line interface for Atlas AI
Main entry point for the CLI application.
"""

import sys
import signal

from .ascii_art import print_banner
from .api_client import AtlasAPIClient
from .model_manager import ModelManager


class AtlasCLI:
    """
    Main CLI application class.
    """
    
    def __init__(self, base_url: str = "http://localhost:5000"):
        """
        Initialize the CLI.
        
        Args:
            base_url: Base URL of the Atlas AI server
        """
        self.client = AtlasAPIClient(base_url)
        self.model_manager = ModelManager(default_model="thor-1.1")
        self.running = True
        
        # Set up signal handler for graceful exit
        signal.signal(signal.SIGINT, self._handle_interrupt)
    
    def _handle_interrupt(self, signum, frame):
        """Handle Ctrl+C gracefully."""
        print("\n\nGoodbye!")
        sys.exit(0)
    
    def _print_help(self):
        """Print help message."""
        help_text = """
Atlas CLI - Simple CLI for querying Atlas AI with multiple models

Usage:
    atlas-cli                    Start interactive query session
    atlas-cli --help             Show this help message

Commands:
    /models                      List all available models
    /use <model-name>            Switch to specified model
    /auto                        Enable auto mode (intelligent model selection)
    /status                      Show current status (server, model, mode)
    /clear                       Clear the screen
    /help                       Show this help message
    exit, quit                    Exit the CLI
    
Available Models:
    thor-1.0                     Stable model
    thor-1.1                     Latest model (default)
    thor-lite-1.1                 API/Code specialist
    thor-calc-1.0                Calculator specialist
    antelope-1.0                 Python specialist
    auto                         Auto mode (selects best model based on query)
    
The CLI connects to your local Atlas AI server running on port 5000.
Make sure the server is running before using the CLI:
    cd apps/chatbot && python3 app.py
        """
        print(help_text)
    
    def _check_server(self) -> bool:
        """
        Check if server is running and show helpful message if not.
        
        Returns:
            True if server is accessible, False otherwise
        """
        if not self.client.check_connection():
            # Check if it's the simple mock server
            try:
                import requests
                health = requests.get(f"{self.client.base_url}/api/health", timeout=2)
                if health.status_code == 200:
                    health_data = health.json()
                    if health_data.get('server') == 'simple':
                        print("❌ Error: Simple mock server detected (no ML models).")
                        print(f"   Server URL: {self.client.base_url}")
                        print("\n   The simple_server.py is running, but the CLI needs the full server.")
                        print("\n   Please:")
                        print("   1. Stop the current server (Ctrl+C in the server terminal)")
                        print("   2. Start the full server with:")
                        print("      cd apps/chatbot && python3 app.py")
                        print("\n   The full server will load and use the actual ML models.")
                        return False
            except Exception:
                pass
            
            print("❌ Error: Atlas AI server is not running or not accessible.")
            print(f"   Server URL: {self.client.base_url}")
            print("\n   Please start the server with:")
            print("   cd apps/chatbot && python3 app.py")
            print("\n   Then run atlas-cli again.")
            return False
        return True
    
    def _load_available_models(self):
        """Load available models from the API."""
        try:
            available = self.client.get_available_models()
            self.model_manager.set_available_models(available)
        except Exception as e:
            # If we can't load models, use defaults
            self.model_manager.set_available_models(["thor-1.0", "thor-1.1", "antelope-1.0"])
    
    def _handle_models_command(self):
        """Handle /models command to list available models."""
        print(self.model_manager.format_models_list())
    
    def _handle_use_command(self, args: str):
        """
        Handle /use command to switch models.
        
        Args:
            args: Model name to switch to
        """
        if not args.strip():
            print("❌ Error: Please specify a model name.")
            print("   Usage: /use <model-name>")
            print("   Example: /use thor-1.0")
            return
        
        model_name = args.strip()
        success, message = self.model_manager.set_model(model_name)
        
        if success:
            # Update client's model if not auto mode
            if model_name.lower() != "auto":
                self.client.set_model(model_name.lower())
            print(f"✅ {message}\n")
        else:
            print(f"❌ {message}\n")
    
    def _handle_auto_command(self):
        """Handle /auto command to enable auto mode."""
        success, message = self.model_manager.set_model("auto")
        if success:
            print(f"✅ {message}\n")
        else:
            print(f"❌ {message}\n")
    
    def _handle_status_command(self):
        """Handle /status command to show current status."""
        print("\n📊 CLI Status")
        print("=" * 60)
        print(f"📡 Server: {self.client.base_url}")
        if self.client.check_connection():
            print("   Status: ✅ Connected")
        else:
            print("   Status: ❌ Not connected")
        print(f"🤖 Current Model: {self.model_manager.get_current_model()}")
        if self.model_manager.is_auto_mode():
            print("   Mode: Auto (intelligent selection)")
        else:
            print("   Mode: Manual")
        print("=" * 60 + "\n")
    
    def _handle_clear_command(self):
        """Handle /clear command to clear the screen."""
        import os
        os.system('clear' if os.name != 'nt' else 'cls')
        # Re-print banner and status after clearing
        from .ascii_art import print_banner
        print_banner()
        print(f"📡 Connected to {self.client.base_url}")
        print(f"{self._get_status_line()}\n")
        print("Enter your queries below. Type '/help' for commands, 'exit' or 'quit' to exit.\n")
    
    def _is_command(self, query: str) -> bool:
        """
        Check if the query is a command.
        
        Args:
            query: The user's query string
        
        Returns:
            True if it's a command, False otherwise
        """
        return query.startswith('/')
    
    def _handle_command(self, query: str) -> bool:
        """
        Handle CLI commands.
        
        Args:
            query: The command query
        
        Returns:
            True if command was handled, False if it's not a recognized command
        """
        parts = query.split(maxsplit=1)
        command = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""
        
        if command == "/models":
            self._handle_models_command()
            return True
        elif command == "/use":
            self._handle_use_command(args)
            return True
        elif command == "/auto":
            self._handle_auto_command()
            return True
        elif command == "/status":
            self._handle_status_command()
            return True
        elif command == "/clear":
            self._handle_clear_command()
            return True
        elif command == "/help":
            self._print_help()
            return True
        else:
            print(f"❌ Unknown command: {command}")
            print("   Type '/help' for available commands.\n")
            return True
    
    def _print_response(self, response: dict):
        """
        Print the API response in a clean format.
        
        Args:
            response: Response dictionary from API
        """
        response_text = response.get('response', '')
        if response_text:
            print(f"\n{response_text}\n")
        else:
            print("\n[No response received]\n")
    
    def _execute_query(self, query: str):
        """
        Execute a query and display the response.
        
        Args:
            query: User's query string
        """
        try:
            # Get the appropriate model for this query
            model_to_use = self.model_manager.get_model_for_query(query)
            
            # Show processing indicator with model info
            if self.model_manager.is_auto_mode():
                print(f"🤔 Thinking (auto: {model_to_use})...", end="", flush=True)
            else:
                print("🤔 Thinking...", end="", flush=True)
            
            # Make API call with selected model
            response = self.client.query(query, model=model_to_use)
            
            # Clear processing indicator
            print("\r" + " " * 70 + "\r", end="")  # Clear line
            
            # Print response
            self._print_response(response)
            
        except ConnectionError as e:
            print(f"\n❌ Connection Error: {str(e)}\n")
        except RuntimeError as e:
            print(f"\n❌ Error: {str(e)}\n")
        except Exception as e:
            print(f"\n❌ Unexpected error: {str(e)}\n")
    
    def _get_status_line(self) -> str:
        """
        Get the status line showing current model.
        
        Returns:
            Formatted status string
        """
        current_model = self.model_manager.get_current_model()
        if self.model_manager.is_auto_mode():
            return f"🤖 Model: {current_model} (auto mode)"
        else:
            return f"🤖 Model: {current_model}"
    
    
    def run(self):
        """Run the main CLI loop."""
        # Check for help flag
        if len(sys.argv) > 1 and sys.argv[1] in ('-h', '--help'):
            self._print_help()
            sys.exit(0)
        
        # Print banner
        print_banner()
        
        # Check server connection
        if not self._check_server():
            sys.exit(1)
        
        # Load available models from API
        self._load_available_models()
        
        # Show connection and model info
        print(f"📡 Connected to {self.client.base_url}")
        print(f"{self._get_status_line()}\n")
        print("Enter your queries below. Type '/help' for commands, 'exit' or 'quit' to exit.\n")
        
        # Main query loop
        while self.running:
            try:
                # Get user input with colored prompt
                green = '\033[32m'
                reset = '\033[0m'
                prompt = f"{green}> {reset}"
                
                query = input(prompt).strip()
                
                # Handle exit commands
                if query.lower() in ('exit', 'quit'):
                    print("\nGoodbye!")
                    break
                
                # Skip empty queries
                if not query:
                    continue
                
                # Handle commands
                if self._is_command(query):
                    self._handle_command(query)
                    continue
                
                # Execute query
                self._execute_query(query)
                
            except EOFError:
                # Handle Ctrl+D
                print("\n\nGoodbye!")
                break
            except KeyboardInterrupt:
                # Handle Ctrl+C
                print("\n\nGoodbye!")
                break


def main():
    """Main entry point."""
    cli = AtlasCLI()
    cli.run()


if __name__ == "__main__":
    main()
