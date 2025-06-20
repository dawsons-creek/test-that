# PyCharm Integration

The "That" testing library provides full integration with PyCharm IDE, allowing you to run and debug tests directly from the IDE with all the benefits of PyCharm's testing interface.

## Quick Setup

1. **Install the library with PyCharm support**:
   ```bash
   pip install test-that[pycharm]
   ```

2. **Set up PyCharm integration**:
   ```bash
   that --setup-pycharm
   ```

3. **Configure PyCharm**:
   - Go to **Settings** → **Tools** → **Python Integrated Tools**
   - Set **Default test runner** to "pytest"
   - Click **OK**

4. **Restart PyCharm** for changes to take effect

**Note**: That tests work through pytest compatibility, so you select "pytest" as the test runner, not "That".

## Features

### ✅ Test Discovery
- PyCharm automatically discovers all `@test` decorated functions
- Tests are organized by suites in the test tree
- Line numbers and file locations are tracked

### ✅ Run Individual Tests
- Right-click on any test function → **Run 'test_name'**
- Right-click on test files → **Run 'test_file.py'**
- Right-click on test directories → **Run tests in 'directory'**

### ✅ Debug Tests
- Set breakpoints in test code
- Right-click → **Debug 'test_name'**
- Full debugging support with variable inspection

### ✅ Test Results
- Green/red indicators for pass/fail
- Detailed failure messages with intelligent diffs
- Click on failures to jump to the failing line

### ✅ Test Tree View
- Hierarchical view of all tests
- Suite grouping
- Filter by status (passed/failed/all)

## Usage Examples

### Running Tests from PyCharm

1. **Single Test**: Right-click on a test function and select "Run"
2. **Test File**: Right-click on a test file and select "Run"
3. **Test Suite**: Tests are automatically grouped by suite
4. **All Tests**: Use the run configuration or right-click on the tests directory

### Test Configuration

PyCharm will automatically create run configurations for your tests. You can also create custom configurations:

1. Go to **Run** → **Edit Configurations**
2. Click **+** → **Python**
3. Set:
   - **Script path**: `-m`
   - **Parameters**: `that [options]`
   - **Working directory**: Your project root

### Debugging Tests

1. Set breakpoints in your test code
2. Right-click on the test → **Debug 'test_name'**
3. Use PyCharm's debugger features:
   - Step through code
   - Inspect variables
   - Evaluate expressions
   - View call stack

## Advanced Configuration

### Custom Test Patterns

If you use custom test file patterns, update your `pyproject.toml`:

```toml
[tool.that]
test_dir = "tests"
pattern = "test_*.py"  # or your custom pattern
```

### Test Runner Options

You can pass additional options to the test runner:

1. Edit your run configuration
2. Add parameters like:
   - `--verbose` for detailed output
   - `--focus` for failure-focused output
   - `--include-tags=unit` for tag filtering

### Integration with Other Tools

The PyCharm integration works alongside:
- **Coverage.py**: Use PyCharm's coverage runner
- **Profiling**: Use PyCharm's profiler with test runs
- **Version Control**: Test results are integrated with VCS

## Troubleshooting

### Tests Not Discovered

1. **Check test runner setting**:
   - Settings → Tools → Python Integrated Tools
   - Ensure "Default test runner" is set to "That"

2. **Verify test file patterns**:
   - Files should start with `test_` or be in a `tests` directory
   - Files should contain `from that import` statements

3. **Restart PyCharm** after configuration changes

### Run Configuration Issues

1. **Check Python interpreter**:
   - Settings → Project → Python Interpreter
   - Ensure the correct environment is selected

2. **Verify working directory**:
   - Run configurations should use project root as working directory

3. **Check module path**:
   - Ensure `that` module is installed in the selected interpreter

### Debug Issues

1. **Breakpoints not hit**:
   - Ensure you're using "Debug" not "Run"
   - Check that breakpoints are on executable lines

2. **Variables not showing**:
   - Use PyCharm's "Variables" panel in debug mode
   - Check "Show variables" option in debugger settings

## Command Line Integration

You can still use command line features alongside PyCharm:

```bash
# Run all tests
that

# Run specific file
that tests/test_example.py

# Run with tags
that --include-tags=unit

# Focus mode for failures
that --focus
```

## Best Practices

1. **Use descriptive test names** - they appear in PyCharm's test tree
2. **Organize tests in suites** - creates clear hierarchy in IDE
3. **Use tags for filtering** - easily run subsets of tests
4. **Set up run configurations** - for common test scenarios
5. **Use debugging features** - step through failing tests to understand issues

## Migration from pytest

If you're migrating from pytest:

1. **Keep existing test structure** - "That" works with similar patterns
2. **Update imports**: Change `import pytest` to `from that import test, that`
3. **Update decorators**: Change `def test_*()` to `@test("description")`
4. **Update assertions**: Change `assert` to `that().equals()`
5. **Run setup**: `that --setup-pycharm`

The PyCharm integration makes "That" a first-class testing framework in your IDE, providing all the benefits of the improved error messages and readable API with the full power of PyCharm's testing tools.
