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

    # Whether this task has been completed today
    completed: bool = False

    def edit(
        self,
        task_type: Optional[str] = None,
        duration: Optional[int] = None,
        priority: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> None:
        """Update one or more fields on this task in place."""
        # Only overwrite a field when a new value was actually passed in;
        # None means "leave this field unchanged."
        if task_type is not None:
            self.task_type = task_type
        if duration is not None:
            self.duration = duration
        if priority is not None:
            self.priority = priority
        if notes is not None:
            self.notes = notes

    def mark_complete(self) -> None:
        """Mark this task as completed."""
        self.completed = True

    def mark_incomplete(self) -> None:
        """Mark this task as not yet completed."""
        self.completed = False


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
        """Add a task to this pet's task list."""
        self.tasks.append(task)

    def remove_task(self, task_name: str) -> None:
        """Remove a task by matching its type."""
        self.tasks = [t for t in self.tasks if t.task_type != task_name]


# ---------------------------------------------------------------------------
# Owner
# Represents the pet owner. Holds contact details and a list of their pets.
# A regular class (not dataclass) because it has richer behaviour.
# ---------------------------------------------------------------------------

class Owner:
    def __init__(self, name: str, email: str = "", phone: str = "") -> None:
        """Initialize an owner with contact information."""
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
        # input() blocks until the user presses Enter; .strip() removes
        # accidental leading/trailing whitespace from copy-paste.
        name = input("Owner name: ").strip()
        email = input("Email (press Enter to skip): ").strip()
        phone = input("Phone (press Enter to skip): ").strip()
        return cls(name=name, email=email, phone=phone)

    def add_pet(self, pet: Pet) -> None:
        """Register a pet under this owner."""
        self.pets.append(pet)

    def get_all_tasks(self) -> list[tuple["Pet", Task]]:
        """Return all (pet, task) pairs across all pets."""
        return [(pet, task) for pet in self.pets for task in pet.tasks]


# ---------------------------------------------------------------------------
# Scheduler
# Core planning engine. Takes an owner + pet, then builds and explains
# a daily care schedule that fits within the available time budget.
# ---------------------------------------------------------------------------

# Maps priority label → sort key so "high" always comes before "medium"/"low".
_PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}


class Scheduler:
    def __init__(self, owner: Owner, pet: Optional[Pet] = None, available_minutes: int = 480) -> None:
        """Initialize a scheduler with an owner, optional pet, and time budget."""
        # The owner whose preferences guide the schedule
        self.owner: Owner = owner

        # The specific pet being scheduled for today; None means schedule all pets.
        self.pet: Optional[Pet] = pet

        # Total minutes the owner has free today (hard cap for the plan)
        self.available_minutes: int = available_minutes

        # Filled in by arrange_tasks(); holds the ordered task list for the day.
        # Each entry is (pet, task) to track which pet each task belongs to.
        self._scheduled_tasks: list[tuple[Pet, Task]] = []

        # Once generate_plan() is called, the plan is locked and won't change
        # when new pets/tasks are added. Only regenerate_plan() can unlock it.
        self._plan_locked: bool = False
        self._cached_plan_str: str = ""
        self._cached_explanation: str = ""

    def collect_owner_info(self) -> Owner:
        """Prompt for owner details and return an Owner object."""
        return Owner.ask_info()

    def record_task(self, task: Task) -> None:
        """Add a task to the scheduled pet's task list."""
        self.pet.add_task(task)

    def arrange_tasks(self) -> list[tuple[Pet, Task]]:
        """
        Collect and schedule tasks from the pet (or all pets if pet is None).
        High-priority tasks come first; tasks that push over the time budget
        are dropped. Schedule is sequential with no overlaps across pets.
        Stores the result in _scheduled_tasks and returns it.
        """
        # Determine which pets to schedule for.
        pets_to_schedule = [self.pet] if self.pet else self.owner.pets

        # Calculate per-pet budget. When scheduling multiple pets, divide the
        # available minutes evenly among them so individual plans match the combined plan.
        if not self.pet and len(pets_to_schedule) > 1:
            per_pet_budget = self.available_minutes // len(pets_to_schedule)
        else:
            per_pet_budget = self.available_minutes

        # Collect all tasks from all selected pets as (pet, task) pairs.
        all_tasks: list[tuple[Pet, Task]] = []
        for pet in pets_to_schedule:
            for task in pet.tasks:
                all_tasks.append((pet, task))

        # Sort by priority first (high → medium → low); unknown labels sink
        # to the bottom via the default value of 99.
        sorted_tasks = sorted(
            all_tasks,
            key=lambda pt: _PRIORITY_ORDER.get(pt[1].priority, 99),
        )

        # Greedy fit: add each (pet, task) pair in priority order until the
        # budget is full. Since we schedule sequentially, no two tasks overlap.
        # Also enforce per-pet budgets to keep individual plans consistent.
        scheduled = []
        minutes_used = 0
        pet_minutes_used = {id(pet): 0 for pet in pets_to_schedule}

        for pet, task in sorted_tasks:
            if (minutes_used + task.duration <= self.available_minutes and
                pet_minutes_used[id(pet)] + task.duration <= per_pet_budget):
                scheduled.append((pet, task))
                minutes_used += task.duration
                pet_minutes_used[id(pet)] += task.duration

        self._scheduled_tasks = scheduled
        return self._scheduled_tasks

    def generate_plan(self) -> str:
        """
        Build a human-readable daily schedule string.
        First call generates and locks the plan; subsequent calls return the cached version.
        To regenerate after adding pets/tasks, call regenerate_plan() explicitly.
        """
        # If plan is locked, return the cached version.
        if self._plan_locked:
            return self._cached_plan_str

        # Arrange tasks if not already done.
        if not self._scheduled_tasks:
            self.arrange_tasks()

        # Build the schedule string.
        if self.pet:
            # Single-pet mode: show just that pet's name.
            lines = [f"Daily plan for {self.pet.name}:"]
        else:
            # Multi-pet mode: show a consolidated schedule.
            lines = [f"Daily plan for {self.owner.name}'s pets:"]

        # Walk a running clock starting at 08:00, advancing by each task's duration.
        # Tasks are interleaved by global priority across all pets, so the owner
        # does one task at a time with no overlaps.
        hour, minute = 8, 0
        for pet, task in self._scheduled_tasks:
            time_str = f"{hour:02d}:{minute:02d}"
            lines.append(
                f"  {time_str} — {pet.name}: {task.task_type} ({task.duration} min) [{task.priority}]"
            )
            minute += task.duration
            hour += minute // 60   # carry overflow minutes into hours
            minute = minute % 60

        if not self._scheduled_tasks:
            lines.append("  (no tasks fit within the available time)")

        # Summary footer shows how much of the daily budget is consumed.
        total = sum(t[1].duration for t in self._scheduled_tasks)
        lines.append(f"\nTotal time: {total} min / {self.available_minutes} min available")

        plan_str = "\n".join(lines)

        # Lock the plan and cache it.
        self._plan_locked = True
        self._cached_plan_str = plan_str
        return self._cached_plan_str

    def generate_pet_plan(self, pet: "Pet") -> str:
        """
        Extract and display a specific pet's tasks from the consolidated schedule.
        Shows the pet's actual times as they appear in the combined plan.
        """
        if not self._scheduled_tasks:
            self.arrange_tasks()

        # Collect this pet's tasks and their times from the consolidated schedule.
        lines = [f"Daily plan for {pet.name}:"]
        hour, minute = 8, 0
        pet_total = 0

        for scheduled_pet, task in self._scheduled_tasks:
            if scheduled_pet.name == pet.name:
                time_str = f"{hour:02d}:{minute:02d}"
                lines.append(
                    f"  {time_str} — {pet.name}: {task.task_type} ({task.duration} min) [{task.priority}]"
                )
                pet_total += task.duration

            minute += task.duration
            hour += minute // 60
            minute = minute % 60

        if pet_total == 0:
            lines.append("  (no tasks scheduled for this pet)")

        lines.append(f"\nTotal time: {pet_total} min / {self.available_minutes} min available")
        return "\n".join(lines)

    def explain_pet_plan(self, pet: "Pet") -> str:
        """
        Explain why specific tasks were included or skipped for a pet
        in the consolidated schedule.
        """
        if not self._scheduled_tasks:
            self.arrange_tasks()

        scheduled_set = set(id(t) for _, t in self._scheduled_tasks if _.name == pet.name)

        lines = [f"Schedule explanation for {pet.name}:\n"]

        for task in pet.tasks:
            if id(task) in scheduled_set:
                reason = (
                    f"  INCLUDED — '{task.task_type}' ({task.duration} min, "
                    f"{task.priority} priority) fits within the consolidated plan."
                )
            else:
                reason = (
                    f"  SKIPPED  — '{task.task_type}' ({task.duration} min, "
                    f"{task.priority} priority) was left out of the consolidated plan "
                    f"due to budget constraints."
                )
            if task.notes:
                reason += f" Note: {task.notes}"
            lines.append(reason)

        return "\n".join(lines)

    def regenerate_plan(self) -> str:
        """
        Force unlock and regenerate the plan, discarding the old cached version.
        Use this after adding new pets or tasks to reflect the updated schedule.
        """
        # Unlock and clear the cache.
        self._plan_locked = False
        self._scheduled_tasks = []
        self._cached_plan_str = ""
        self._cached_explanation = ""
        # Regenerate and return the fresh plan.
        return self.generate_plan()

    def explain_plan(self) -> str:
        """
        Return a plain-English explanation of *why* each task was chosen
        (or skipped), so the owner understands the reasoning behind the plan.
        Plan is locked after first call; subsequent calls return the cached explanation.
        """
        # If plan is locked, return the cached explanation.
        if self._plan_locked:
            return self._cached_explanation

        if not self._scheduled_tasks:
            self.arrange_tasks()

        # Use object identity (id()) instead of name matching so two tasks
        # with the same type string are still treated as distinct entries.
        scheduled_set = set(id(t) for _, t in self._scheduled_tasks)

        # Determine which pets to explain.
        pets_to_explain = [self.pet] if self.pet else self.owner.pets

        lines = [f"Schedule explanation for {self.owner.name}:\n"]

        for pet in pets_to_explain:
            lines.append(f"\n{pet.name}:")
            for task in pet.tasks:
                if id(task) in scheduled_set:
                    reason = (
                        f"  INCLUDED — '{task.task_type}' ({task.duration} min, "
                        f"{task.priority} priority) fits within the time budget."
                    )
                else:
                    # Makes the budget cap explicit so the owner knows exactly why
                    # a task was left out rather than just seeing it missing.
                    reason = (
                        f"  SKIPPED  — '{task.task_type}' ({task.duration} min, "
                        f"{task.priority} priority) was left out because adding it "
                        f"would exceed the {self.available_minutes}-minute limit."
                    )
                if task.notes:
                    reason += f" Note: {task.notes}"
                lines.append(reason)

        explanation = "\n".join(lines)

        # Lock the explanation and cache it.
        self._plan_locked = True
        self._cached_explanation = explanation
        return self._cached_explanation
