#!/usr/bin/env python3
"""
Script to enable detailed LLM logging for debugging.

This script configures logging to show complete LLM inputs and outputs
including all message content, system prompts, and responses.

Usage:
    python enable_detailed_llm_logging.py
    
Then start your FastAPI server and make requests to see detailed logs.
"""

import logging
import sys
import os

def setup_detailed_llm_logging():
    """
    Set up comprehensive logging for LLM interactions.
    
    This will log:
    - Complete message content (all previous, next, replies)
    - Full system prompt sent to LLM
    - Complete user prompt with JSON data
    - Full LLM response
    - Token usage and timing
    """
    
    # Create a detailed formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    
    # Configure specific loggers for maximum detail
    loggers_to_configure = [
        'llm_interactions.generateConversationSummarySlack',
        'slack.llm_analyzer',
        'slack.endpoints',
        'slack'
    ]
    
    for logger_name in loggers_to_configure:
        logger = logging.getLogger(logger_name)
        logger.handlers.clear()  # Remove existing handlers
        logger.addHandler(console_handler)
        logger.setLevel(logging.INFO)  # Set to INFO to see all our custom logs
        logger.propagate = False  # Don't propagate to avoid duplicate logs
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    print("✅ Detailed LLM logging enabled!")
    print("📊 Configured loggers:")
    for logger_name in loggers_to_configure:
        print(f"   - {logger_name}: INFO level")
    
    print("\n📋 What you'll see in logs:")
    print("   🎯 Complete original message content")
    print("   ⬅️  All previous messages with timestamps and users")
    print("   ➡️  All next messages with timestamps and users") 
    print("   💬 All replies with timestamps and users")
    print("   📋 Complete system prompt sent to LLM")
    print("   👤 Complete user prompt with formatted JSON")
    print("   📥 Complete LLM response (raw)")
    print("   💰 Token usage (prompt + completion + total)")
    print("   📊 Analysis results and scoring")
    
    print("\n🚀 Now start your FastAPI server and make requests!")
    print("   uvicorn main:app --reload")
    print("   curl 'http://localhost:8000/slack/user/satya.prakash/analyzed-messages'")


def setup_file_logging(log_file="llm_detailed.log"):
    """
    Set up file logging in addition to console logging.
    
    Args:
        log_file: Path to log file (default: llm_detailed.log)
    """
    
    # Create file handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    ))
    
    # Add file handler to our loggers
    loggers_to_configure = [
        'llm_interactions.generateConversationSummarySlack',
        'slack.llm_analyzer',
        'slack.endpoints',
        'slack'
    ]
    
    for logger_name in loggers_to_configure:
        logger = logging.getLogger(logger_name)
        logger.addHandler(file_handler)
    
    print(f"✅ File logging enabled: {log_file}")
    print("💾 All detailed LLM logs will also be saved to file")


def main():
    """Main function to set up logging."""
    
    print("🎯 LLM Detailed Logging Setup")
    print("=" * 50)
    
    # Set up console logging
    setup_detailed_llm_logging()
    
    # Ask if user wants file logging too
    print("\n" + "=" * 50)
    choice = input("Also enable file logging? (y/n): ").strip().lower()
    
    if choice in ['y', 'yes']:
        log_file = input("Log file name (default: llm_detailed.log): ").strip()
        if not log_file:
            log_file = "llm_detailed.log"
        setup_file_logging(log_file)
    
    print("\n" + "=" * 50)
    print("🎉 Logging configuration complete!")
    print("\n📚 Next steps:")
    print("1. Start your FastAPI server: uvicorn main:app --reload")
    print("2. Make a request to the analyzed messages endpoint")
    print("3. Watch the detailed logs in your console (and file if enabled)")
    
    print("\n🔍 Example request:")
    print("curl 'http://localhost:8000/slack/user/satya.prakash/analyzed-messages?context_limit=5&search_limit=10'")
    
    print("\n⚠️  Note: This will generate VERY detailed logs including:")
    print("   - Complete message content")
    print("   - Full system prompts")
    print("   - Complete LLM responses")
    print("   - May contain sensitive information")


if __name__ == "__main__":
    main()
