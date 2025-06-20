# Running Tests

## Basic Usage

```bash
# Run all tests
that

# Run specific file
that test_user.py

# Run specific directory
that tests/unit/

# Run multiple files
that test_user.py test_orders.py

# Run with pattern
that tests/unit/test_*.py
```

## Command Line Options

### Verbosity

```bash
# Verbose output (shows stack traces on failure)
that -v

# Quiet mode (only show failures)
that -q
```

### Filtering

```bash
# Run specific suite
that -s "User Management"

# Pattern matching on test names
that -k "email"
that -k "user.*validation"

# Multiple patterns
that -k "email" -k "password"
```

### Output Control

```bash
# Disable colored output
that --no-color

# Focus mode (only show failures with full context)
that --focus
```

### Test Discovery

```bash
# Custom test directory
that --test-dir my_tests/

# Custom file pattern
that --pattern "*_tests.py"

# Show discovered tests without running
that --collect-only
```

## Configuration

Create `pyproject.toml` to configure default behavior:

```toml
[tool.that]
test_dir = "tests"
pattern = "test_*.py"
verbose = false
color = true
```

## Examples

### Development Workflow

```bash
# Quick feedback during development
that tests/unit/

# Run specific test while debugging
that tests/unit/test_models.py -v

# Run tests matching current feature
that -k "user_signup"
```

### CI/CD Pipeline

```bash
# Run all tests with verbose output
that -v

# Run only fast tests first
that tests/unit/

# Then run integration tests
that tests/integration/

# Focus on failures in CI
that --focus --no-color
```

### Specific Use Cases

```bash
# Test a specific component
that -s "Database" -v

# Find tests related to authentication
that -k "auth" --collect-only

# Run all email-related tests
that -k "email"

# Debug a failing test
that tests/unit/test_models.py::test_user_validation -v
```

## Exit Codes

- `0` - All tests passed
- `1` - Some tests failed
- `2` - Error in test execution (syntax error, import error, etc.)

## Performance Tips

### Organize by Speed

```
tests/
├── unit/        # Fast tests (< 1ms each)
├── integration/ # Medium tests (< 100ms each)  
└── e2e/        # Slow tests (> 100ms each)
```

### Development Commands

```bash
# Fast feedback loop
that tests/unit/

# Before committing
that tests/unit/ tests/integration/

# Before deploying
that
```

### Parallel Execution

Currently, That runs tests sequentially. For very large test suites, you can run different directories in parallel:

```bash
# Terminal 1
that tests/unit/

# Terminal 2  
that tests/integration/

# Terminal 3
that tests/e2e/
```

## Debugging Failed Tests

### Verbose Mode

```bash
# See full stack traces
that -v
```

### Focus Mode

```bash
# Only show failing tests with context
that --focus
```

### Run Single Test

```bash
# Run just the failing test
that tests/unit/test_models.py -k "specific_test_name"
```

### Add Debug Prints

```python
@test("debug example")
def test_with_debug():
    result = complex_calculation()
    print(f"DEBUG: result = {result}")  # Will show in -v mode
    that(result).equals(expected)
```

## Integration with IDEs

### VS Code

Add to `.vscode/settings.json`:

```json
{
    "python.testing.pytestEnabled": false,
    "python.testing.unittestEnabled": false,
    "python.defaultInterpreterPath": "./venv/bin/python",
    "terminal.integrated.env.osx": {
        "PYTHONPATH": "${workspaceFolder}"
    }
}
```

Run tests from terminal:
```bash
that tests/unit/test_models.py -v
```

### PyCharm

Set up external tool:
- Program: `that`
- Arguments: `$FilePath$ -v`
- Working directory: `$ProjectFileDir$`

Or use the built-in integration:
```bash
that --setup-pycharm
```

## Continuous Integration

### GitHub Actions

```yaml
name: Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        pip install -e .
    
    - name: Run unit tests
      run: that tests/unit/ -v
    
    - name: Run integration tests  
      run: that tests/integration/ -v
```

### Other CI Systems

```bash
# Generic CI command
pip install -e . && that -v --no-color
```

## Watch Mode (Future Feature)

Coming soon:
```bash
# Re-run tests when files change
that --watch

# Watch specific directory
that tests/unit/ --watch
```

## Common Workflows

### TDD Cycle

```bash
# 1. Write failing test
that tests/unit/test_new_feature.py -v

# 2. Implement feature
# ... code ...

# 3. Run test again
that tests/unit/test_new_feature.py -v

# 4. Refactor and run all related tests
that -k "new_feature" -v
```

### Pre-commit Hook

```bash
#!/bin/sh
# .git/hooks/pre-commit
that tests/unit/ || exit 1
```

### Release Testing

```bash
# Full test suite
that -v

# Performance check (if you have timing tests)
that -k "performance" -v

# Smoke tests
that tests/smoke/ -v
```