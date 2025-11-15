#!/usr/bin/env python3
"""
Script to run database migrations
"""
import os
import sys
from alembic.config import Config
from alembic import command

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

def run_migrations():
    """Run Alembic migrations"""
    alembic_cfg = Config("alembic.ini")
    command.upgrade(alembic_cfg, "head")
    print("Migrations completed successfully!")

if __name__ == "__main__":
    run_migrations()

