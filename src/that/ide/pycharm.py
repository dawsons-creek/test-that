"""
PyCharm integration for the That testing library.

This module provides PyCharm IDE integration through pytest compatibility.
PyCharm recognizes pytest as a test framework, so we create a compatibility
layer that makes That tests discoverable and runnable through pytest.
"""

import sys
from pathlib import Path
from typing import Dict, List, Any


def setup_pycharm_integration():
    """Set up PyCharm integration for the current project."""
    
    # Create .idea directory if it doesn't exist
    idea_dir = Path('.idea')
    idea_dir.mkdir(exist_ok=True)
    
    # Create workspace.xml with pytest configuration
    workspace_file = idea_dir / 'workspace.xml'
    workspace_content = '''<?xml version="1.0" encoding="UTF-8"?>
<project version="4">
  <component name="TestRunnerService">
    <option name="PROJECT_TEST_RUNNER" value="pytest" />
  </component>
  <component name="PropertiesComponent">
    <property name="settings.editor.selected.configurable" value="com.jetbrains.python.configuration.PyActiveSdkModuleConfigurable" />
  </component>
</project>'''
    
    with open(workspace_file, 'w') as f:
        f.write(workspace_content)
    
    # Create pytest.ini configuration
    pytest_ini_content = '''[tool:pytest]
testpaths = tests
python_files = test_*.py *_test.py
python_functions = 
python_classes = 
addopts = -v --tb=short
markers =
    that_test: mark test as a That framework test
    slow: marks tests as slow
    integration: marks tests as integration tests
    unit: marks tests as unit tests
'''
    
    with open('pytest.ini', 'w') as f:
        f.write(pytest_ini_content)
    
    # Create conftest.py in project root to enable That discovery
    conftest_content = '''"""
Project conftest.py - enables That test discovery through pytest.
"""

# Import the pytest compatibility hooks directly
from that.ide.pytest_compat import (
    pytest_collect_file,
    pytest_configure,
    pytest_collection_modifyitems,
    pytest_pycollect_makemodule
)
'''
    
    with open('conftest.py', 'w') as f:
        f.write(conftest_content)
    
    print("PyCharm integration setup complete!")
    print("\nTo use:")
    print("1. Restart PyCharm")
    print("2. Go to Settings > Tools > Python Integrated Tools")
    print("3. Set 'Default test runner' to 'pytest'")
    print("4. That tests will now be discoverable through pytest")
    print("5. Right-click on test files to run individual tests")
    print("\nFiles created:")
    print("- .idea/workspace.xml (PyCharm configuration)")
    print("- pytest.ini (pytest configuration)")
    print("- conftest.py (That-pytest integration)")


class ThatPyCharmPlugin:
    """PyCharm plugin for That testing framework."""
    
    @staticmethod
    def get_test_framework_name() -> str:
        """Return the name of this test framework."""
        return "That"
    
    @staticmethod
    def is_test_file(file_path: str) -> bool:
        """Check if a file contains That tests."""
        if not file_path.endswith('.py'):
            return False
        
        # Check if file starts with test_ or is in tests directory
        path = Path(file_path)
        if path.name.startswith('test_'):
            return True
        
        # Check if file is in tests directory
        if 'tests' in path.parts:
            return True
        
        # Check file content for That imports
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read(1000)  # Read first 1000 chars
                return 'from that import' in content or 'import that' in content
        except (IOError, UnicodeDecodeError):
            return False
    
    @staticmethod
    def discover_tests_in_file(file_path: str) -> List[Dict[str, Any]]:
        """Discover tests in a specific file."""
        from .pytest_compat import ThatTestCollector
        
        collector = ThatTestCollector()
        tests = collector.collect_tests(file_path)
        
        return [{
            'name': test.name,
            'location': {
                'file': test.file_path,
                'line': test.line_number
            },
            'suite': test.suite_name,
            'id': test.nodeid
        } for test in tests]
    
    @staticmethod
    def run_test(test_id: str, **kwargs) -> Dict[str, Any]:
        """Run a specific test."""
        from .pytest_compat import get_pycharm_runner
        
        runner = get_pycharm_runner()
        return runner.run_test(test_id)
    
    @staticmethod
    def get_test_runner_command(test_path: str = None, test_name: str = None) -> List[str]:
        """Get command to run tests from command line."""
        cmd = [sys.executable, '-m', 'that']
        
        if test_path:
            if test_name:
                cmd.append(f"{test_path}::{test_name}")
            else:
                cmd.append(test_path)
        
        return cmd
