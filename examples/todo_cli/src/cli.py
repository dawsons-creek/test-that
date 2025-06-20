"""Command-line interface for the todo application."""

import argparse
import sys
from pathlib import Path

from .commands import TodoCommands
from .storage import FileStorage, StorageError, TodoNotFoundError
from .formatters import TodoFormatter


def create_parser():
    """Create the argument parser for the CLI."""
    parser = argparse.ArgumentParser(
        description="A simple todo CLI application",
        prog="todo"
    )
    
    parser.add_argument(
        "--storage-file",
        default=str(Path.home() / ".todos.json"),
        help="Path to the todo storage file"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Add command
    add_parser = subparsers.add_parser("add", help="Add a new todo")
    add_parser.add_argument("title", help="Todo title")
    add_parser.add_argument("-d", "--description", default="", help="Todo description")
    add_parser.add_argument("-p", "--priority", choices=["low", "medium", "high"], 
                           default="medium", help="Todo priority")
    add_parser.add_argument("-t", "--tags", nargs="*", help="Tags for the todo")
    
    # List command
    list_parser = subparsers.add_parser("list", help="List todos")
    list_parser.add_argument("-s", "--status", choices=["pending", "completed"],
                            help="Filter by status")
    list_parser.add_argument("-t", "--tag", help="Filter by tag")
    list_parser.add_argument("-q", "--search", help="Search todos")
    list_parser.add_argument("-v", "--verbose", action="store_true",
                            help="Show detailed information")
    
    # Complete command
    complete_parser = subparsers.add_parser("complete", help="Mark a todo as completed")
    complete_parser.add_argument("todo_id", help="Todo ID (or prefix)")
    
    # Reopen command
    reopen_parser = subparsers.add_parser("reopen", help="Reopen a completed todo")
    reopen_parser.add_argument("todo_id", help="Todo ID (or prefix)")
    
    # Delete command
    delete_parser = subparsers.add_parser("delete", help="Delete a todo")
    delete_parser.add_argument("todo_id", help="Todo ID (or prefix)")
    
    # Update command
    update_parser = subparsers.add_parser("update", help="Update a todo")
    update_parser.add_argument("todo_id", help="Todo ID (or prefix)")
    update_parser.add_argument("-t", "--title", help="New title")
    update_parser.add_argument("-d", "--description", help="New description")
    update_parser.add_argument("-p", "--priority", choices=["low", "medium", "high"],
                              help="New priority")
    update_parser.add_argument("--add-tags", nargs="*", help="Tags to add")
    update_parser.add_argument("--remove-tags", nargs="*", help="Tags to remove")
    
    # Clear command
    clear_parser = subparsers.add_parser("clear", help="Clear completed todos")
    
    # Stats command
    stats_parser = subparsers.add_parser("stats", help="Show todo statistics")
    
    return parser


def find_todo_by_prefix(commands: TodoCommands, prefix: str) -> str:
    """Find a todo ID by prefix."""
    todos = commands.list_todos()
    matches = [t for t in todos if t.id.startswith(prefix)]
    
    if len(matches) == 0:
        raise TodoNotFoundError(f"No todo found with ID starting with '{prefix}'")
    elif len(matches) > 1:
        raise ValueError(f"Multiple todos found with ID starting with '{prefix}'. Be more specific.")
    
    return matches[0].id


def main():
    """Main entry point for the CLI."""
    parser = create_parser()
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Initialize storage and commands
    try:
        storage = FileStorage(args.storage_file)
        commands = TodoCommands(storage)
        formatter = TodoFormatter()
    except Exception as e:
        print(f"Error initializing: {e}", file=sys.stderr)
        return 1
    
    try:
        # Execute commands
        if args.command == "add":
            todo = commands.add(
                title=args.title,
                description=args.description,
                priority=args.priority,
                tags=args.tags
            )
            print(f"Todo added: {todo.id[:8]}")
            print(formatter.format_todo(todo))
        
        elif args.command == "list":
            todos = commands.list_todos(
                status=args.status,
                tag=args.tag,
                search=args.search
            )
            print(formatter.format_list(todos, detailed=args.verbose))
        
        elif args.command == "complete":
            todo_id = find_todo_by_prefix(commands, args.todo_id)
            todo = commands.complete(todo_id)
            print(f"Completed: {todo.title}")
        
        elif args.command == "reopen":
            todo_id = find_todo_by_prefix(commands, args.todo_id)
            todo = commands.reopen(todo_id)
            print(f"Reopened: {todo.title}")
        
        elif args.command == "delete":
            todo_id = find_todo_by_prefix(commands, args.todo_id)
            todo = commands.storage.get(todo_id)  # Get before delete for confirmation
            commands.delete(todo_id)
            print(f"Deleted: {todo.title}")
        
        elif args.command == "update":
            todo_id = find_todo_by_prefix(commands, args.todo_id)
            todo = commands.update(
                todo_id,
                title=args.title,
                description=args.description,
                priority=args.priority,
                add_tags=args.add_tags,
                remove_tags=args.remove_tags
            )
            print(f"Updated: {todo.id[:8]}")
            print(formatter.format_todo(todo, detailed=True))
        
        elif args.command == "clear":
            count = commands.clear_completed()
            print(f"Cleared {count} completed todo(s)")
        
        elif args.command == "stats":
            stats = commands.get_stats()
            todos = commands.list_todos()
            print(formatter.format_stats(todos))
        
        return 0
        
    except (StorageError, TodoNotFoundError, ValueError) as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\nCancelled", file=sys.stderr)
        return 130
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())