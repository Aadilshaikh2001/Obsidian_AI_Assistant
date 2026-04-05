"""
Test suite runner for Cornelius-Ollama
"""

import sys

import pytest


def run_tests():
    """Run the test suite."""
    exit_code = pytest.main([
        "-v",
        "--tb=short",
        "--strict-markers",
        os.path.dirname(os.path.abspath(__file__)),
    ])
    sys.exit(exit_code)


if __name__ == "__main__":
    run_tests()