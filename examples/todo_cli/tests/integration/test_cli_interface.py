"""Integration tests for the CLI interface."""

import subprocess
import sys
import tempfile
from pathlib import Path

from that import test, suite, that, tag, integration, mock


def run_cli(args, storage_file=None):
    """Helper to run CLI commands."""
    cmd = [sys.executable, "-m", "todo_cli.src.cli"]
    
    if storage_file:
        cmd.extend(["--storage-file", storage_file])
    
    cmd.extend(args)
    
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True
    )
    
    return result


with suite("CLI Add Command"):
    
    @test("adds todo via CLI")
    @tag("integration", "cli")
    def test_cli_add():
        with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as tmp:
            result = run_cli(["add", "Buy groceries"], tmp.name)
            
            that(result.returncode).equals(0)
            that(result.stdout).contains("Todo added:")
            that(result.stdout).contains("Buy groceries")
            
            # Verify by listing
            result = run_cli(["list"], tmp.name)
            that(result.stdout).contains("Buy groceries")
            
            Path(tmp.name).unlink()
    
    @test("adds todo with options")
    @tag("integration", "cli")
    def test_cli_add_with_options():
        with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as tmp:
            result = run_cli([
                "add", "Important task",
                "-d", "Very important",
                "-p", "high",
                "-t", "work", "urgent"
            ], tmp.name)
            
            that(result.returncode).equals(0)
            that(result.stdout).contains("Important task")
            that(result.stdout).contains("!!!")  # High priority indicator
            
            # List with verbose to see details
            result = run_cli(["list", "-v"], tmp.name)
            that(result.stdout).contains("Very important")
            that(result.stdout).contains("#work")
            that(result.stdout).contains("#urgent")
            
            Path(tmp.name).unlink()


with suite("CLI List Command"):
    
    @test("lists todos with filters")
    @tag("integration", "cli")
    def test_cli_list_filters():
        with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as tmp:
            # Add some todos
            run_cli(["add", "Work task", "-t", "work"], tmp.name)
            run_cli(["add", "Personal task", "-t", "personal"], tmp.name)
            run_cli(["add", "Another work task", "-t", "work"], tmp.name)
            
            # List all
            result = run_cli(["list"], tmp.name)
            that(result.stdout).contains("Work task")
            that(result.stdout).contains("Personal task")
            that(result.stdout).contains("Total: 3")
            
            # List by tag
            result = run_cli(["list", "-t", "work"], tmp.name)
            that(result.stdout).contains("Work task")
            that(result.stdout).contains("Another work task")
            that(result.stdout).does_not_contain("Personal task")
            that(result.stdout).contains("Total: 2")
            
            Path(tmp.name).unlink()
    
    @test("searches todos")
    @tag("integration", "cli")
    def test_cli_search():
        with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as tmp:
            run_cli(["add", "Fix login bug", "-d", "Users cannot login"], tmp.name)
            run_cli(["add", "Add logout feature"], tmp.name)
            run_cli(["add", "Update docs"], tmp.name)
            
            # Search
            result = run_cli(["list", "-q", "login"], tmp.name)
            that(result.stdout).contains("Fix login bug")
            that(result.stdout).contains("Add logout feature")
            that(result.stdout).does_not_contain("Update docs")
            
            Path(tmp.name).unlink()


with suite("CLI Complete Command"):
    
    @test("completes todo by ID prefix")
    @tag("integration", "cli")
    def test_cli_complete():
        with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as tmp:
            # Add a todo
            result = run_cli(["add", "Task to complete"], tmp.name)
            
            # Extract ID from output (first 8 chars)
            lines = result.stdout.strip().split('\n')
            id_line = lines[0]  # "Todo added: 12345678"
            todo_id = id_line.split(": ")[1]
            
            # Complete it
            result = run_cli(["complete", todo_id[:4]], tmp.name)  # Use prefix
            that(result.returncode).equals(0)
            that(result.stdout).contains("Completed: Task to complete")
            
            # Verify status
            result = run_cli(["list"], tmp.name)
            that(result.stdout).contains("✓")  # Completed indicator
            that(result.stdout).contains("=== COMPLETED ===")
            
            Path(tmp.name).unlink()


with suite("CLI Update Command"):
    
    @test("updates todo properties")
    @tag("integration", "cli")
    def test_cli_update():
        with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as tmp:
            # Add a todo
            result = run_cli(["add", "Original title", "-p", "low"], tmp.name)
            todo_id = result.stdout.strip().split('\n')[0].split(": ")[1]
            
            # Update it
            result = run_cli([
                "update", todo_id[:4],
                "-t", "Updated title",
                "-p", "high",
                "--add-tags", "urgent", "important"
            ], tmp.name)
            
            that(result.returncode).equals(0)
            that(result.stdout).contains("Updated:")
            that(result.stdout).contains("Updated title")
            that(result.stdout).contains("!!!")  # High priority
            that(result.stdout).contains("#urgent")
            that(result.stdout).contains("#important")
            
            Path(tmp.name).unlink()


with suite("CLI Error Handling"):
    
    @test("handles invalid commands")
    @tag("integration", "cli", "error-handling")
    def test_cli_invalid_command():
        result = run_cli(["invalid"])
        
        that(result.returncode).is_not_equal_to(0)
        that(result.stderr).contains("Error:")
    
    @test("handles missing arguments")
    @tag("integration", "cli", "error-handling")
    def test_cli_missing_args():
        result = run_cli(["add"])  # Missing title
        
        that(result.returncode).is_not_equal_to(0)
        that(result.stderr).contains("error")
    
    @test("handles non-existent todo")
    @tag("integration", "cli", "error-handling")
    def test_cli_nonexistent_todo():
        with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as tmp:
            result = run_cli(["complete", "fake-id"], tmp.name)
            
            that(result.returncode).is_not_equal_to(0)
            that(result.stderr).contains("Error:")
            that(result.stderr).contains("No todo found")
            
            Path(tmp.name).unlink()
    
    @test("handles ambiguous ID prefix")
    @tag("integration", "cli", "error-handling")  
    def test_cli_ambiguous_prefix():
        with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as tmp:
            # Add two todos with similar IDs (mock this scenario)
            # In practice, we'd need to mock UUID generation
            # For now, just test the concept
            
            result = run_cli(["add", "Task 1"], tmp.name)
            result = run_cli(["add", "Task 2"], tmp.name)
            
            # Try to complete with too short prefix (likely ambiguous)
            result = run_cli(["complete", ""], tmp.name)
            
            that(result.returncode).is_not_equal_to(0)
            
            Path(tmp.name).unlink()


with suite("CLI Statistics"):
    
    @test("shows statistics")
    @tag("integration", "cli")
    def test_cli_stats():
        with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as tmp:
            # Create diverse todos
            run_cli(["add", "High 1", "-p", "high"], tmp.name)
            run_cli(["add", "High 2", "-p", "high", "-t", "work"], tmp.name)
            run_cli(["add", "Medium", "-p", "medium", "-t", "work", "urgent"], tmp.name)
            run_cli(["add", "Low", "-p", "low"], tmp.name)
            
            # Complete one
            result = run_cli(["add", "Done task"], tmp.name)
            todo_id = result.stdout.strip().split('\n')[0].split(": ")[1]
            run_cli(["complete", todo_id[:4]], tmp.name)
            
            # Get stats
            result = run_cli(["stats"], tmp.name)
            
            that(result.stdout).contains("=== TODO STATISTICS ===")
            that(result.stdout).contains("Total todos: 5")
            that(result.stdout).contains("Completed: 1 (20.0%)")
            that(result.stdout).contains("Pending: 4")
            that(result.stdout).contains("High: 2")
            that(result.stdout).contains("Medium: 1")
            that(result.stdout).contains("Low: 1")
            that(result.stdout).contains("Tags in use:")
            that(result.stdout).contains("work")
            that(result.stdout).contains("urgent")
            
            Path(tmp.name).unlink()


with suite("CLI Help"):
    
    @test("shows help with no args")
    @tag("integration", "cli")
    def test_cli_help_no_args():
        result = run_cli([])
        
        that(result.returncode).equals(1)
        that(result.stdout).contains("usage:")
        that(result.stdout).contains("Available commands")
    
    @test("shows help for subcommands")
    @tag("integration", "cli")
    def test_cli_help_subcommand():
        result = run_cli(["add", "--help"])
        
        that(result.returncode).equals(0)
        that(result.stdout).contains("Add a new todo")
        that(result.stdout).contains("--description")
        that(result.stdout).contains("--priority")
        that(result.stdout).contains("--tags")