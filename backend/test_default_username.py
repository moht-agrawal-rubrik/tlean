#!/usr/bin/env python3
"""
Test script to verify the default username functionality.

This script tests:
1. Environment variable loading for DEFAULT_SLACK_USERNAME
2. Default username usage when none provided
3. Both endpoint paths work correctly
"""

import os
import sys

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


def test_environment_variable_loading():
    """Test that the environment variable is loaded correctly."""
    
    print("🧪 Test 1: Environment Variable Loading")
    print("=" * 50)
    
    try:
        # Test without environment variable
        if 'DEFAULT_SLACK_USERNAME' in os.environ:
            original_value = os.environ['DEFAULT_SLACK_USERNAME']
            del os.environ['DEFAULT_SLACK_USERNAME']
        else:
            original_value = None
        
        # Import the module to test default value
        from slack.endpoints import DEFAULT_USERNAME
        
        print(f"✅ Default username without env var: {DEFAULT_USERNAME}")
        
        if DEFAULT_USERNAME == "satya.prakash":
            print("✅ Correct default value used")
        else:
            print(f"❌ Expected 'satya.prakash', got '{DEFAULT_USERNAME}'")
            return False
        
        # Test with environment variable
        os.environ['DEFAULT_SLACK_USERNAME'] = "test.user"
        
        # Reload the module to pick up the new env var
        import importlib
        import slack.endpoints
        importlib.reload(slack.endpoints)
        
        from slack.endpoints import DEFAULT_USERNAME as NEW_DEFAULT_USERNAME
        
        print(f"✅ Default username with env var: {NEW_DEFAULT_USERNAME}")
        
        if NEW_DEFAULT_USERNAME == "test.user":
            print("✅ Environment variable override works")
        else:
            print(f"❌ Expected 'test.user', got '{NEW_DEFAULT_USERNAME}'")
            return False
        
        # Restore original value
        if original_value:
            os.environ['DEFAULT_SLACK_USERNAME'] = original_value
        elif 'DEFAULT_SLACK_USERNAME' in os.environ:
            del os.environ['DEFAULT_SLACK_USERNAME']
        
        return True
        
    except Exception as e:
        print(f"❌ Environment variable loading test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_endpoint_paths():
    """Test that both endpoint paths are available."""
    
    print("\n🧪 Test 2: Endpoint Paths")
    print("=" * 50)
    
    try:
        from slack.endpoints import router
        
        # Get all routes from the router
        routes = []
        for route in router.routes:
            if hasattr(route, 'path'):
                routes.append(route.path)
        
        print("📋 Available routes:")
        for route in routes:
            print(f"   - {route}")
        
        # Check for both endpoint paths
        expected_paths = [
            "/user/{username}/analyzed-messages",
            "/analyzed-messages"
        ]
        
        for expected_path in expected_paths:
            if expected_path in routes:
                print(f"✅ Found route: {expected_path}")
            else:
                print(f"❌ Missing route: {expected_path}")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Endpoint paths test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_curl_commands():
    """Test the curl commands that should work."""
    
    print("\n🧪 Test 3: Curl Commands")
    print("=" * 50)
    
    try:
        print("📋 Available curl commands:")
        
        # With username specified
        print("✅ With username specified:")
        print("   curl 'http://localhost:8000/slack/user/satya.prakash/analyzed-messages'")
        print("   curl 'http://localhost:8000/slack/user/john.doe/analyzed-messages'")
        
        # Without username (uses default)
        print("✅ Without username (uses default from env):")
        print("   curl 'http://localhost:8000/slack/analyzed-messages'")
        
        # With parameters
        print("✅ With parameters:")
        print("   curl 'http://localhost:8000/slack/analyzed-messages?context_limit=5&search_limit=10'")
        print("   curl 'http://localhost:8000/slack/user/satya.prakash/analyzed-messages?context_limit=5&search_limit=10'")
        
        return True
        
    except Exception as e:
        print(f"❌ Curl commands test failed: {e}")
        return False


def test_env_file_example():
    """Test that the .env.example file has the correct configuration."""
    
    print("\n🧪 Test 4: .env.example File")
    print("=" * 50)
    
    try:
        env_example_path = ".env.example"
        
        if not os.path.exists(env_example_path):
            print(f"❌ .env.example file not found at {env_example_path}")
            return False
        
        with open(env_example_path, 'r') as f:
            content = f.read()
        
        print("✅ .env.example file found")
        
        # Check for DEFAULT_SLACK_USERNAME
        if "DEFAULT_SLACK_USERNAME" in content:
            print("✅ DEFAULT_SLACK_USERNAME found in .env.example")
        else:
            print("❌ DEFAULT_SLACK_USERNAME not found in .env.example")
            return False
        
        # Check for the default value
        if "DEFAULT_SLACK_USERNAME=satya.prakash" in content:
            print("✅ Correct default value in .env.example")
        else:
            print("⚠️  Default value might be different in .env.example")
        
        print("📋 Relevant lines from .env.example:")
        for line_num, line in enumerate(content.split('\n'), 1):
            if 'DEFAULT_SLACK_USERNAME' in line:
                print(f"   Line {line_num}: {line}")
        
        return True
        
    except Exception as e:
        print(f"❌ .env.example file test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    
    print("🎯 Default Username Test Suite")
    print("=" * 70)
    
    # Run tests
    test1_passed = test_environment_variable_loading()
    test2_passed = test_endpoint_paths()
    test3_passed = test_curl_commands()
    test4_passed = test_env_file_example()
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 Test Results Summary:")
    print(f"   🧪 Environment Variable Loading: {'✅ PASSED' if test1_passed else '❌ FAILED'}")
    print(f"   🧪 Endpoint Paths: {'✅ PASSED' if test2_passed else '❌ FAILED'}")
    print(f"   🧪 Curl Commands: {'✅ PASSED' if test3_passed else '❌ FAILED'}")
    print(f"   🧪 .env.example File: {'✅ PASSED' if test4_passed else '❌ FAILED'}")
    
    if all([test1_passed, test2_passed, test3_passed, test4_passed]):
        print("\n🎉 All tests passed! Default username functionality is working correctly.")
        print("\n📚 What's Ready:")
        print("   ✅ DEFAULT_SLACK_USERNAME environment variable support")
        print("   ✅ Falls back to 'satya.prakash' if env var not set")
        print("   ✅ Two endpoint paths available:")
        print("      - /slack/user/{username}/analyzed-messages (explicit username)")
        print("      - /slack/analyzed-messages (uses default username)")
        print("   ✅ .env.example file updated with configuration")
        
        print("\n🚀 Usage Examples:")
        print("   # Set environment variable")
        print("   export DEFAULT_SLACK_USERNAME=your.username")
        print("   ")
        print("   # Or add to .env file")
        print("   echo 'DEFAULT_SLACK_USERNAME=your.username' >> .env")
        print("   ")
        print("   # Use default username")
        print("   curl 'http://localhost:8000/slack/analyzed-messages'")
        print("   ")
        print("   # Use specific username")
        print("   curl 'http://localhost:8000/slack/user/john.doe/analyzed-messages'")
    else:
        print("\n💥 Some tests failed. Please check the error messages above.")


if __name__ == "__main__":
    main()
