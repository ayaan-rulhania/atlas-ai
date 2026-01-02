#!/usr/bin/env python3
"""
Thor 1.1 Knowledge Crawler - Daemon Launcher
Starts and manages the continuous knowledge acquisition system.

Usage:
    python start_knowledge_crawler.py start    # Start the crawler
    python start_knowledge_crawler.py stop     # Stop the crawler
    python start_knowledge_crawler.py status   # Check status
    python start_knowledge_crawler.py stats    # Show statistics
"""
import os
import sys
import time
import signal
import argparse
import json
from datetime import datetime
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from brain_learner import BrainLearner, get_brain_learner
from services.knowledge_db import get_knowledge_db


# PID file for daemon management
PID_FILE = os.path.join(os.path.dirname(__file__), "crawler.pid")
LOG_FILE = os.path.join(os.path.dirname(__file__), "crawler.log")


def log(message: str):
    """Log a message with timestamp."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_msg = f"[{timestamp}] {message}"
    print(log_msg)
    
    try:
        with open(LOG_FILE, "a") as f:
            f.write(log_msg + "\n")
    except:
        pass


def get_pid() -> int:
    """Get the PID of the running crawler."""
    if os.path.exists(PID_FILE):
        try:
            with open(PID_FILE, "r") as f:
                return int(f.read().strip())
        except:
            pass
    return None


def save_pid(pid: int):
    """Save the current PID."""
    with open(PID_FILE, "w") as f:
        f.write(str(pid))


def remove_pid():
    """Remove the PID file."""
    if os.path.exists(PID_FILE):
        os.remove(PID_FILE)


def is_running() -> bool:
    """Check if the crawler is running."""
    pid = get_pid()
    if pid is None:
        return False
    
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        # Process not running, clean up stale PID file
        remove_pid()
        return False


def start_crawler(
    interval: int = 5,
    db_path: str = None,
    dictionary_path: str = None,
    daemon: bool = False,
    workers: int = 4
):
    """Start the knowledge crawler."""
    if is_running():
        log("Crawler is already running!")
        return False
    
    log("=" * 60)
    log("  Thor 1.1 Knowledge Crawler")
    log("  Continuous Knowledge Acquisition System")
    log("=" * 60)
    log("")
    
    # Initialize and verify database
    log("Initializing SQLite knowledge database...")
    db = get_knowledge_db(db_path)
    db_stats = db.get_database_stats()
    
    log(f"  - Total knowledge items: {db_stats['total_knowledge_items']}")
    log(f"  - Total topics: {db_stats['total_topics']}")
    log(f"  - Topics pending: {db_stats['topics_by_status'].get('pending', 0)}")
    log(f"  - Topics crawled: {db_stats['topics_by_status'].get('crawled', 0)}")
    log("")
    
    # Check dictionary
    dict_path = dictionary_path or os.path.join(
        os.path.dirname(__file__), "dictionary.json"
    )
    if os.path.exists(dict_path):
        with open(dict_path, "r") as f:
            dictionary = json.load(f)
        log(f"Dictionary loaded: {len(dictionary.get('topics', []))} topics")
    else:
        log(f"Warning: Dictionary not found at {dict_path}")
    
    log("")
    log(f"Starting crawler with {interval}s interval...")
    
    if daemon:
        # Fork into background
        try:
            pid = os.fork()
            if pid > 0:
                # Parent process
                log(f"Crawler started in background (PID: {pid})")
                save_pid(pid)
                return True
        except AttributeError:
            log("Warning: Daemon mode not supported on this platform")
            log("Running in foreground...")
    
    # Save current PID
    save_pid(os.getpid())
    
    # Create and start the learner
    learner = BrainLearner(
        search_interval_seconds=interval,
        db_path=db_path,
        dictionary_path=dictionary_path,
        parallel_workers=workers
    )
    
    # Set up signal handlers
    def shutdown_handler(signum, frame):
        log("\nShutdown signal received...")
        learner.stop()
        remove_pid()
        log("Crawler stopped.")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, shutdown_handler)
    signal.signal(signal.SIGTERM, shutdown_handler)
    
    # Start learning
    learner.start()
    
    log("")
    log("Crawler is now running. Press Ctrl+C to stop.")
    log("")
    
    # Keep main thread alive and show periodic stats
    try:
        last_stats_time = time.time()
        stats_interval = 300  # 5 minutes
        
        while True:
            time.sleep(10)
            
            # Print stats periodically
            if time.time() - last_stats_time >= stats_interval:
                stats = learner.get_stats()
                db_stats = stats['database']
                
                log("")
                log("=" * 40)
                log("  Periodic Status Update")
                log("=" * 40)
                log(f"  Knowledge items: {db_stats['total_knowledge_items']}")
                log(f"  Added (24h): {db_stats['knowledge_added_24h']}")
                log(f"  Topics crawled (24h): {db_stats['topics_crawled_24h']}")
                log(f"  Avg confidence: {db_stats['avg_confidence']:.2f}")
                log("=" * 40)
                log("")
                
                last_stats_time = time.time()
    
    except KeyboardInterrupt:
        shutdown_handler(signal.SIGINT, None)
    
    return True


def stop_crawler():
    """Stop the running crawler."""
    pid = get_pid()
    
    if pid is None:
        log("Crawler is not running.")
        return False
    
    if not is_running():
        log("Crawler is not running (stale PID file removed).")
        return False
    
    log(f"Stopping crawler (PID: {pid})...")
    
    try:
        os.kill(pid, signal.SIGTERM)
        
        # Wait for process to terminate
        for _ in range(10):
            time.sleep(0.5)
            if not is_running():
                break
        
        if is_running():
            log("Process didn't stop gracefully, sending SIGKILL...")
            os.kill(pid, signal.SIGKILL)
        
        remove_pid()
        log("Crawler stopped.")
        return True
    
    except ProcessLookupError:
        log("Process not found (already stopped).")
        remove_pid()
        return True
    except Exception as e:
        log(f"Error stopping crawler: {e}")
        return False


def show_status():
    """Show the crawler status."""
    print("")
    print("=" * 50)
    print("  Thor 1.1 Knowledge Crawler Status")
    print("=" * 50)
    print("")
    
    if is_running():
        pid = get_pid()
        print(f"  Status: RUNNING (PID: {pid})")
    else:
        print("  Status: STOPPED")
    
    # Show database stats
    try:
        db = get_knowledge_db()
        stats = db.get_database_stats()
        
        print("")
        print("  Database Statistics:")
        print(f"    - Total knowledge items: {stats['total_knowledge_items']}")
        print(f"    - Avg confidence: {stats['avg_confidence']:.2f}")
        print(f"    - Avg quality: {stats['avg_quality_score']:.2f}")
        print("")
        print("  Topics:")
        print(f"    - Total: {stats['total_topics']}")
        for status, count in stats['topics_by_status'].items():
            print(f"    - {status.capitalize()}: {count}")
        print("")
        print("  Sources:")
        for source, count in stats.get('sources', {}).items():
            print(f"    - {source}: {count}")
        print("")
        print("  Recent Activity (24h):")
        print(f"    - Knowledge added: {stats['knowledge_added_24h']}")
        print(f"    - Topics crawled: {stats['topics_crawled_24h']}")
        print("")
        print("  User Queries:")
        print(f"    - Total: {stats['total_user_queries']}")
        print(f"    - Unanswered: {stats['unanswered_queries']}")
        
    except Exception as e:
        print(f"  Database: Error getting stats - {e}")
    
    print("")
    print("=" * 50)


def show_stats():
    """Show detailed statistics."""
    print("")
    print("=" * 60)
    print("  Thor 1.1 Knowledge Database Statistics")
    print("=" * 60)
    print("")
    
    try:
        db = get_knowledge_db()
        stats = db.get_database_stats()
        
        # Knowledge Items
        print("  KNOWLEDGE ITEMS")
        print("  " + "-" * 40)
        print(f"    Total items: {stats['total_knowledge_items']:,}")
        print(f"    Average confidence: {stats['avg_confidence']:.3f}")
        print(f"    Average quality score: {stats['avg_quality_score']:.3f}")
        print("")
        
        # Sources breakdown
        print("  SOURCES")
        print("  " + "-" * 40)
        sources = stats.get('sources', {})
        if sources:
            total = sum(sources.values())
            for source, count in sorted(sources.items(), key=lambda x: x[1], reverse=True):
                pct = (count / total) * 100 if total > 0 else 0
                print(f"    {source:20} {count:8,}  ({pct:5.1f}%)")
        else:
            print("    No sources yet")
        print("")
        
        # Topics
        print("  TOPICS")
        print("  " + "-" * 40)
        print(f"    Total topics: {stats['total_topics']:,}")
        for status, count in sorted(stats['topics_by_status'].items()):
            print(f"    {status.capitalize():20} {count:8,}")
        print("")
        
        # Recent Activity
        print("  RECENT ACTIVITY (24 hours)")
        print("  " + "-" * 40)
        print(f"    Knowledge items added: {stats['knowledge_added_24h']:,}")
        print(f"    Topics crawled: {stats['topics_crawled_24h']:,}")
        print("")
        
        # User Queries
        print("  USER QUERIES")
        print("  " + "-" * 40)
        print(f"    Total queries: {stats['total_user_queries']:,}")
        print(f"    Unanswered queries: {stats['unanswered_queries']:,}")
        if stats['total_user_queries'] > 0:
            answer_rate = ((stats['total_user_queries'] - stats['unanswered_queries']) / 
                          stats['total_user_queries']) * 100
            print(f"    Answer rate: {answer_rate:.1f}%")
        print("")
        
        # Estimate
        if stats['knowledge_added_24h'] > 0:
            print("  LEARNING RATE")
            print("  " + "-" * 40)
            items_per_hour = stats['knowledge_added_24h'] / 24
            topics_per_hour = stats['topics_crawled_24h'] / 24
            print(f"    Items per hour: {items_per_hour:.1f}")
            print(f"    Topics per hour: {topics_per_hour:.1f}")
            
            pending = stats['topics_by_status'].get('pending', 0)
            if topics_per_hour > 0 and pending > 0:
                hours_to_complete = pending / topics_per_hour
                days_to_complete = hours_to_complete / 24
                print(f"    Est. time to complete all topics: {days_to_complete:.1f} days")
        
    except Exception as e:
        print(f"  Error getting stats: {e}")
        import traceback
        traceback.print_exc()
    
    print("")
    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(
        description="Thor 1.1 Knowledge Crawler - Daemon Management"
    )
    
    parser.add_argument(
        "command",
        choices=["start", "stop", "status", "stats", "restart"],
        help="Command to execute"
    )
    
    parser.add_argument(
        "--interval", "-i",
        type=int,
        default=5,
        help="Search interval in seconds (default: 5)"
    )
    
    parser.add_argument(
        "--workers", "-w",
        type=int,
        default=4,
        help="Number of parallel workers (default: 4)"
    )
    
    parser.add_argument(
        "--daemon", "-d",
        action="store_true",
        help="Run in background (daemon mode)"
    )
    
    parser.add_argument(
        "--db",
        type=str,
        default=None,
        help="Path to SQLite database"
    )
    
    parser.add_argument(
        "--dictionary",
        type=str,
        default=None,
        help="Path to dictionary.json"
    )
    
    args = parser.parse_args()
    
    if args.command == "start":
        start_crawler(
            interval=args.interval,
            db_path=args.db,
            dictionary_path=args.dictionary,
            daemon=args.daemon,
            workers=args.workers
        )
    
    elif args.command == "stop":
        stop_crawler()
    
    elif args.command == "restart":
        stop_crawler()
        time.sleep(2)
        start_crawler(
            interval=args.interval,
            db_path=args.db,
            dictionary_path=args.dictionary,
            daemon=args.daemon,
            workers=args.workers
        )
    
    elif args.command == "status":
        show_status()
    
    elif args.command == "stats":
        show_stats()


if __name__ == "__main__":
    main()

