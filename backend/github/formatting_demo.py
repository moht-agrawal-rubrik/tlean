#!/usr/bin/env python3
"""
Demonstration of improved long_summary formatting.

This script shows the difference between the old single-line format
and the new multi-line format with proper newlines.
"""

import json

def show_formatting_comparison():
    """Show before/after comparison of long_summary formatting."""
    
    # Example of OLD formatting (single line)
    old_format = "Modified 10 files. (+212/-10 lines). - tests. Key changes: • polaris/src/rubrik/api-server/app/services/physicalhost/rbac/BUILD.bazel: Added dependencies on proto_deps and common-scala to the rkscala_library build target; • polaris/src/rubrik/sdk_internal/grpc/physicalhost_pb2_grpc.py: Updated docstring for BulkRegisterSecondaryHosts to remove TODO and add parameter description; • polaris/src/rubrik/api-server/test/app/services/physicalhost/rbac/BUILD.bazel: Added Bazel test build configuration for physicalhost RBAC Scala tests. Author: moht-agrawal-rubrik, State: open, Reviewers: 3"
    
    # Example of NEW formatting (multi-line with proper structure)
    new_format = """Modified 10 files. (+212/-10 lines). - tests

Key changes:
• polaris/src/rubrik/api-server/app/services/physicalhost/rbac/BUILD.bazel: Added dependencies on proto_deps and common-scala to the rkscala_library build target
• polaris/src/rubrik/sdk_internal/grpc/physicalhost_pb2_grpc.py: Modified BulkRegisterSecondaryHosts docstring to remove TODO and add parameter description
• polaris/src/rubrik/api-server/test/app/services/physicalhost/rbac/BUILD.bazel: Added Bazel test build configuration for physicalhost RBAC Scala tests

Author: moht-agrawal-rubrik, State: open, Reviewers: 3"""
    
    print("GitHub Long Summary Formatting Improvement")
    print("=" * 60)
    
    print("\n🔴 OLD FORMAT (single line, hard to read):")
    print("-" * 60)
    print(old_format)
    
    print("\n✅ NEW FORMAT (multi-line, well-structured):")
    print("-" * 60)
    print(new_format)
    
    print("\n" + "=" * 60)
    print("IMPROVEMENTS:")
    print("• Proper line breaks between sections")
    print("• Each file change on its own line")
    print("• Clear separation between overview, changes, and metadata")
    print("• Much more readable in JSON output")
    print("• Better for display in UIs and reports")
    
    # Show JSON representation
    example_json = {
        "old_format": {
            "long_summary": old_format,
            "readability": "Poor - all on one line",
            "newlines": old_format.count('\n')
        },
        "new_format": {
            "long_summary": new_format,
            "readability": "Excellent - well-structured",
            "newlines": new_format.count('\n')
        }
    }
    
    print(f"\nJSON representation saved to: formatting_comparison.json")
    with open("formatting_comparison.json", "w") as f:
        json.dump(example_json, f, indent=2)
    
    print(f"\nCharacter counts:")
    print(f"• Old format: {len(old_format)} characters, {old_format.count(chr(10))} newlines")
    print(f"• New format: {len(new_format)} characters, {new_format.count(chr(10))} newlines")


if __name__ == "__main__":
    show_formatting_comparison()
