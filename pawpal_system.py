"""
pawpal_system.py
----------------
Logic layer for PawPal+. All backend classes live here.
The Streamlit UI (app.py) imports from this module to drive the app.

Class overview:
  Task      -- a single pet care task (dataclass)
  Pet       -- a pet and its list of tasks (dataclass)
  Owner     -- the pet owner with contact info and a list of pets
  Scheduler -- builds and explains a daily care plan
"""

from dataclasses import dataclass, field
from typing import Optional


# ---------------------------------------------------------------------------
# Task
# A single care task (e.g. "morning walk", "feeding", "meds").
# Using a dataclass so Python auto-generates __init__, __repr__, etc.
# ---------------------------------------------------------------------------

@dataclass
class Task:
    # What kind of care this task involves (e.g. "walk", "feed", "groom")
    task_type: str

    # How long the task takes, in minutes
    duration: int

    # Scheduling priority — expected values: "low", "medium", "high"
    priority: str

    # Any extra details the owner wants to track (optional)
    notes: Optional[str] = None

    def edit(
        self,
        task_type: Optional[str] = None,
        duration: Optional[int] = None,
        priority: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> None:
        """Update one or more fields on this task in place."""
        pass


# ---------------------------------------------------------------------------
# Pet
# Represents a pet and the care tasks associated with it.
# Also a dataclass; tasks default to an empty list per pet instance.
# ---------------------------------------------------------------------------

@dataclass
class Pet:
    # The pet's name (e.g. "Mochi")
    name: str

    # Breed or species description (e.g. "Golden Retriever", "tabby cat")
    breed: str

    # All tasks registered for this pet; populated via add_task()
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Append a Task to this pet's task list."""
        pass

    def remove_task(self, task_name: str) -> None:
        """Remove a task from the list by matching its type/name."""
        pass


# ---------------------------------------------------------------------------
# Owner
# Represents the pet owner. Holds contact details and a list of their pets.
# A regular class (not dataclass) because it has richer behaviour.
# ---------------------------------------------------------------------------

class Owner:
    def __init__(self, name: str, email: str = "", phone: str = "") -> None:
        # Owner's display name
        self.name: str = name

        # Contact email (optional but useful for notifications)
        self.email: str = email

        # Contact phone number (optional)
        self.phone: str = phone

        # All pets this owner has registered
        self.pets: list[Pet] = []

    @classmethod
    def ask_info(cls) -> "Owner":
        """
        Prompt the user for owner details and return a new Owner instance.
        Used in CLI / non-Streamlit contexts.
        """
        pass

    def add_pet(self, pet: Pet) -> None:
        """Register a new pet under this owner."""
        pass


# ---------------------------------------------------------------------------
# Scheduler
# Core planning engine. Takes an owner + pet, then builds and explains
# a daily care schedule that fits within the available time budget.
# ---------------------------------------------------------------------------

class Scheduler:
    def __init__(self, owner: Owner, pet: Pet, available_minutes: int) -> None:
        # The owner whose preferences guide the schedule
        self.owner: Owner = owner

        # The specific pet being scheduled for today
        self.pet: Pet = pet

        # Total minutes the owner has free today (hard cap for the plan)
        self.available_minutes: int = available_minutes

        # Filled in by arrange_tasks(); holds the ordered task list for the day
        self._scheduled_tasks: list[Task] = []

    def collect_owner_info(self) -> Owner:
        """
        Interactively gather owner details and return an Owner object.
        Delegates to Owner.ask_info() in CLI mode; override for Streamlit.
        """
        pass

    def record_task(self, task: Task) -> None:
        """Add a task to the pet's task list via the pet's own add_task()."""
        pass

    def arrange_tasks(self) -> list[Task]:
        """
        Sort and filter the pet's tasks to fit within available_minutes.
        High-priority tasks come first; tasks that push over the time budget
        are dropped. Stores the result in _scheduled_tasks and returns it.
        """
        pass

    def generate_plan(self) -> str:
        """
        Build a human-readable daily schedule string.
        Calls arrange_tasks() internally if _scheduled_tasks is empty.
        Returns something like:
            Daily plan for Mochi:
              08:00 — Morning walk (20 min) [high]
              08:20 — Feeding (10 min) [high]
              ...
        """
        pass

    def explain_plan(self) -> str:
        """
        Return a plain-English explanation of *why* each task was chosen
        (or skipped), so the owner understands the reasoning behind the plan.
        """
        pass
