#!/usr/bin/env python3
"""
Start the Brain Learner - This keeps running and learning from Google
Run this script to start continuous learning
"""
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from brain_learner import get_brain_learner
import time

if __name__ == '__main__':
    print("=" * 60)
    print("Thor 1.0 - Brain Learner")
    print("=" * 60)
    print()
    print("Starting continuous Google search learning...")
    print("This will run continuously and learn from random Google searches.")
    print("The brain structure will be populated with knowledge.")
    print()
    print("Press Ctrl+C to stop.")
    print()
    
    learner = get_brain_learner()
    learner.start()
    
    try:
        # Keep running
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping Brain Learner...")
        learner.stop()
        print("Stopped.")

