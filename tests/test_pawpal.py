"""
test_pawpal.py
--------------
Unit tests for PawPal+ system.
"""

import sys
# Add parent directory to path so we can import pawpal_system from tests/
sys.path.insert(0, "..")

from pawpal_system import Task, Pet


def test_task_completion():
    """Verify that calling mark_complete() changes the task's status."""
    task = Task(task_type="Feeding", duration=10, priority="high")
    assert task.completed is False

    task.mark_complete()

    assert task.completed is True


def test_task_addition():
    """Verify that adding a task to a Pet increases that pet's task count."""
    pet = Pet(name="Matcha", breed="Border Collie")
    initial_count = len(pet.tasks)

    task = Task(task_type="Morning walk", duration=30, priority="high")
    pet.add_task(task)

    assert len(pet.tasks) == initial_count + 1
