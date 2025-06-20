# Installation Guide

Get Test That up and running in under 2 minutes.

## Quick Install

```bash
pip install test-that
```

That's it! Test That works out of the box with zero configuration.

## Verify Installation

Create a simple test to verify everything works:

```python title="test_hello.py"
from that import that, test

@test("hello world works")
def test_hello():
    greeting = "Hello, World!"
    that(greeting).contains("World")
```

Run it:

```bash
that
```

You should see:
```
✓ hello world works (0.001s)

1 test passed in 0.001s
```

## Installation Options

### Using pip (Recommended)

```bash
# Latest stable version
pip install test-that

# Specific version
pip install test-that==0.2.0

# With development dependencies
pip install test-that[dev]
```

### Using uv (Fast Python Package Manager)

```bash
# Add to project
uv add test-that

# Install globally
uv tool install test-that
```

### Using Poetry

```bash
poetry add test-that
```

### Using Conda

```bash
conda install -c conda-forge test-that
```

## System Requirements

- **Python**: 3.8 or higher
- **Operating Systems**: Windows, macOS, Linux
- **Dependencies**: None (pure Python)

## Development Installation

If you want to contribute to Test That:

```bash
# Clone the repository
git clone https://github.com/dawsons-creek/test-that.git
cd test-that

# Install in development mode
pip install -e .

# Install development dependencies
pip install -e .[dev]
```

## IDE Integration

### VS Code

Install the Python extension and Test That will work automatically:

1. Install [Python extension](https://marketplace.visualstudio.com/items?itemName=ms-python.python)
2. Open your project folder
3. Create test files starting with `test_`
4. Use `Ctrl+Shift+P` → "Python: Run Tests" or run `that` in terminal

### PyCharm

Test That integrates with PyCharm's test runner:

1. Go to **Settings** → **Tools** → **Python Integrated Tools**
2. Set **Default test runner** to "pytest" (Test That is compatible)
3. Right-click test files to run individual tests

### Other Editors

Test That works with any editor since it's a command-line tool:

```bash
# Run all tests
that

# Run specific file
that test_user.py

# Run with verbose output
that -v
```

## Project Setup

### Basic Project Structure

```
my-project/
├── src/
│   └── myapp/
│       ├── __init__.py
│       └── user.py
├── tests/
│   ├── test_user.py
│   └── test_integration.py
├── requirements.txt
└── README.md
```

### Configuration File (Optional)

Create `pyproject.toml` for project configuration:

```toml title="pyproject.toml"
[tool.that]
test_directory = "tests"
pattern = "test_*.py"
verbose = false
color = true
```

## Common Issues

### "that: command not found"

If you get this error, ensure Test That is installed in your active Python environment:

```bash
# Check if installed
pip list | grep test-that

# Reinstall if needed
pip install --force-reinstall test-that
```

### Import Errors

If you get import errors, check your Python path:

```python
import sys
print(sys.path)

# Make sure your project directory is in the path
```

### Permission Issues

On some systems, you might need to use `--user`:

```bash
pip install --user test-that
```

## Next Steps

Now that Test That is installed:

1. **[Write Your First Test](first-test.md)** - Create your first test in 30 seconds
2. **[Quick Start Guide](quickstart.md)** - Learn the basics in 5 minutes
3. **[Why Test That?](why-test-that.md)** - See how it compares to other frameworks

## Getting Help

- **Documentation**: [https://test-that.dev](https://test-that.dev)
- **GitHub Issues**: [Report bugs or request features](https://github.com/dawsons-creek/test-that/issues)
- **Discussions**: [Ask questions and share tips](https://github.com/dawsons-creek/test-that/discussions)

## Troubleshooting

### Virtual Environments

If using virtual environments, make sure Test That is installed in the active environment:

```bash
# Activate your virtual environment first
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows

# Then install
pip install test-that
```

### Multiple Python Versions

If you have multiple Python versions, use the specific pip:

```bash
# Python 3.9
python3.9 -m pip install test-that

# Python 3.10
python3.10 -m pip install test-that
```

### Corporate Networks

If behind a corporate firewall:

```bash
# Use corporate proxy
pip install --proxy http://proxy.company.com:8080 test-that

# Or use trusted host
pip install --trusted-host pypi.org --trusted-host pypi.python.org test-that
```

Ready to write your first test? Let's go! → [First Test](first-test.md)
