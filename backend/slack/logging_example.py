#!/usr/bin/env python3
"""
Example of how to configure logging for detailed LLM request/response tracking.

This shows different logging levels and how to enable them for debugging
LLM interactions in the Slack analyzer.
"""

import logging
import os
import sys

def setup_detailed_llm_logging():
    """
    Set up detailed logging for LLM interactions.
    
    This configures different log levels to help debug LLM requests and responses.
    """
    
    # Create a custom formatter for LLM logs
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    
    # Configure the slack.llm_analyzer logger specifically
    llm_logger = logging.getLogger('slack.llm_analyzer')
    llm_logger.addHandler(console_handler)
    llm_logger.setLevel(logging.DEBUG)  # Set to DEBUG for detailed logs
    
    # Configure the main slack logger
    slack_logger = logging.getLogger('slack')
    slack_logger.addHandler(console_handler)
    slack_logger.setLevel(logging.INFO)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    print("✅ Detailed LLM logging configured!")
    print("📊 Log levels:")
    print("   - slack.llm_analyzer: DEBUG (detailed LLM request/response logs)")
    print("   - slack: INFO (general Slack API logs)")
    print("   - root: INFO (application logs)")


def setup_trace_logging():
    """
    Set up TRACE level logging for maximum detail.
    
    This will log full LLM requests and responses - use carefully as it can be verbose!
    """
    
    # Add TRACE level (below DEBUG)
    TRACE_LEVEL = 5
    logging.addLevelName(TRACE_LEVEL, "TRACE")
    
    def trace(self, message, *args, **kwargs):
        if self.isEnabledFor(TRACE_LEVEL):
            self._log(TRACE_LEVEL, message, args, **kwargs)
    
    logging.Logger.trace = trace
    
    # Set up formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    
    # Configure LLM logger for TRACE level
    llm_logger = logging.getLogger('slack.llm_analyzer')
    llm_logger.addHandler(console_handler)
    llm_logger.setLevel(TRACE_LEVEL)
    
    print("🔍 TRACE level logging enabled!")
    print("⚠️  WARNING: This will log full LLM requests and responses")
    print("💰 This may expose sensitive data and create large log files")


def example_usage():
    """
    Example of how to use the logging configuration.
    """
    
    print("🎯 LLM Logging Configuration Examples")
    print("=" * 50)
    
    print("\n1. Environment Variable Method:")
    print("   export LLM_LOG_LEVEL=DEBUG")
    print("   python your_script.py")
    
    print("\n2. Programmatic Method:")
    print("   from slack.logging_example import setup_detailed_llm_logging")
    print("   setup_detailed_llm_logging()")
    
    print("\n3. Maximum Detail (TRACE) Method:")
    print("   from slack.logging_example import setup_trace_logging")
    print("   setup_trace_logging()")
    
    print("\n📊 What Each Level Shows:")
    print("   INFO:  Basic flow (starting analysis, results summary)")
    print("   DEBUG: Detailed steps (parsing, token usage, scores)")
    print("   TRACE: Full requests/responses (sensitive data!)")
    
    print("\n🔍 Example Log Output at DEBUG level:")
    print("   🧠 Starting LLM analysis for message 1757486516.496349")
    print("   📤 Sending LLM request for message 1757486516.496349")
    print("   📏 Input size: 1234 characters")
    print("   📥 Received LLM response for message 1757486516.496349")
    print("   💰 Usage: 150 prompt + 75 completion = 225 total tokens")
    print("   📊 Parsed - Score: 0.75, Status: needs_response, Actions: 2")
    print("   ✅ LLM analysis complete for message 1757486516.496349")
    
    print("\n🚨 High Attention Messages:")
    print("   Messages with score > 0.6 get special logging:")
    print("   🚨 HIGH ATTENTION message detected: @user any updates on this?")
    
    print("\n📈 Batch Summary:")
    print("   🎯 Batch LLM analysis complete!")
    print("   ✅ Successful: 8/10")
    print("   🚨 High attention (>0.6): 3")
    print("   ⚠️  Medium attention (0.3-0.6): 2")
    print("   ℹ️  Low attention (≤0.3): 5")


if __name__ == "__main__":
    example_usage()
    
    print("\n" + "=" * 50)
    print("Choose logging level:")
    print("1. Standard (INFO)")
    print("2. Detailed (DEBUG)")
    print("3. Maximum (TRACE)")
    
    choice = input("Enter choice (1-3): ").strip()
    
    if choice == "2":
        setup_detailed_llm_logging()
    elif choice == "3":
        setup_trace_logging()
    else:
        print("ℹ️  Using standard INFO level logging")
    
    print("\n🚀 Logging configured! You can now run your Slack analysis.")
    print("💡 Tip: Set LLM_LOG_LEVEL=DEBUG in your environment for persistent detailed logging")
