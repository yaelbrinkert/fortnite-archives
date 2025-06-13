#!/usr/bin/env python3
import unittest
import sys
import os

# Add project root to sys.path so navigator package can be imported
script_path = os.path.abspath(__file__)
project_root = os.path.dirname(os.path.dirname(script_path))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

def run_tests():
    """Discover and run all tests in the tests directory."""
    # Get the directory containing this script
    tests_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tests')
    
    # Discover and run tests
    test_suite = unittest.defaultTestLoader.discover(tests_dir, pattern='test_*.py')
    test_runner = unittest.TextTestRunner(verbosity=2)
    result = test_runner.run(test_suite)
    
    # Return non-zero exit code if tests failed
    return 0 if result.wasSuccessful() else 1

if __name__ == '__main__':
    sys.exit(run_tests())