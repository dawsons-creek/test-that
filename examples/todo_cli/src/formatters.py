"""Output formatters for todo display."""

from datetime import datetime
from typing import List

from .models import Todo, Status, Priority


class TodoFormatter:
    """Format todos for display."""
    
    @staticmethod
    def format_todo(todo: Todo, detailed: bool = False) -> str:
        """Format a single todo for display."""
        status_icon = "✓" if todo.status == Status.COMPLETED else "○"
        priority_icon = {
            Priority.HIGH: "!!!",
            Priority.MEDIUM: "!!",
            Priority.LOW: "!"
        }[todo.priority]
        
        # Basic format
        parts = [f"{status_icon} [{todo.id[:8]}] {todo.title} {priority_icon}"]
        
        if todo.tags:
            tags_str = " ".join(f"#{tag}" for tag in todo.tags)
            parts.append(f"  Tags: {tags_str}")
        
        if detailed:
            if todo.description:
                parts.append(f"  Description: {todo.description}")
            parts.append(f"  Created: {todo.created_at.strftime('%Y-%m-%d %H:%M')}")
            if todo.completed_at:
                parts.append(f"  Completed: {todo.completed_at.strftime('%Y-%m-%d %H:%M')}")
        
        return "\n".join(parts)
    
    @staticmethod
    def format_list(todos: List[Todo], detailed: bool = False) -> str:
        """Format a list of todos for display."""
        if not todos:
            return "No todos found."
        
        # Group by status
        pending = [t for t in todos if t.status == Status.PENDING]
        completed = [t for t in todos if t.status == Status.COMPLETED]
        
        lines = []
        
        if pending:
            lines.append("=== PENDING ===")
            for todo in sorted(pending, key=lambda t: (t.priority.value, t.created_at)):
                lines.append(TodoFormatter.format_todo(todo, detailed))
                if detailed:
                    lines.append("")  # Empty line between detailed todos
        
        if completed:
            if pending:
                lines.append("\n=== COMPLETED ===")
            else:
                lines.append("=== COMPLETED ===")
            for todo in sorted(completed, key=lambda t: t.completed_at, reverse=True):
                lines.append(TodoFormatter.format_todo(todo, detailed))
                if detailed:
                    lines.append("")
        
        # Summary
        lines.append(f"\nTotal: {len(todos)} ({len(pending)} pending, {len(completed)} completed)")
        
        return "\n".join(lines)
    
    @staticmethod
    def format_stats(todos: List[Todo]) -> str:
        """Format statistics about todos."""
        total = len(todos)
        if total == 0:
            return "No todos to analyze."
        
        completed = sum(1 for t in todos if t.status == Status.COMPLETED)
        pending = total - completed
        
        high_priority = sum(1 for t in todos if t.priority == Priority.HIGH)
        medium_priority = sum(1 for t in todos if t.priority == Priority.MEDIUM)
        low_priority = sum(1 for t in todos if t.priority == Priority.LOW)
        
        # Calculate completion rate
        completion_rate = (completed / total) * 100 if total > 0 else 0
        
        # Get all unique tags
        all_tags = set()
        for todo in todos:
            all_tags.update(todo.tags)
        
        lines = [
            "=== TODO STATISTICS ===",
            f"Total todos: {total}",
            f"Completed: {completed} ({completion_rate:.1f}%)",
            f"Pending: {pending}",
            "",
            "By Priority:",
            f"  High: {high_priority}",
            f"  Medium: {medium_priority}",
            f"  Low: {low_priority}",
        ]
        
        if all_tags:
            lines.extend([
                "",
                f"Tags in use: {', '.join(sorted(all_tags))}"
            ])
        
        return "\n".join(lines)