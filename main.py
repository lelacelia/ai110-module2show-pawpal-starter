"""
main.py
-------
Demo script for PawPal+. Creates an owner, two pets, and several tasks,
then prints today's care schedule to the terminal.
"""

from pawpal_system import Owner, Pet, Task, Scheduler


# ---------------------------------------------------------------------------
# 1. Create the owner
# ---------------------------------------------------------------------------
owner = Owner(name="Celia", email="celia@example.com", phone="555-0100")

# ---------------------------------------------------------------------------
# 2. Create two pets and register them with the owner
# ---------------------------------------------------------------------------
matcha = Pet(name="Matcha", breed="Border Collie")
luna   = Pet(name="Luna",   breed="Tabby Cat")

owner.add_pet(matcha)
owner.add_pet(luna)

# ---------------------------------------------------------------------------
# 3. Add tasks to each pet (different durations and priorities)
# ---------------------------------------------------------------------------

# Matcha's tasks
matcha.add_task(Task(task_type="Morning walk", duration=30, priority="high"))
matcha.add_task(Task(task_type="Feeding",      duration=10, priority="high"))
matcha.add_task(Task(task_type="Grooming",     duration=20, priority="medium",
                     notes="focus on ears and paws"))
matcha.add_task(Task(task_type="Playtime",     duration=15, priority="low"))

# Luna's tasks
luna.add_task(Task(task_type="Feeding",          duration=10, priority="high"))
luna.add_task(Task(task_type="Litter box",       duration=5,  priority="high"))
luna.add_task(Task(task_type="Brush coat",       duration=10, priority="medium"))
luna.add_task(Task(task_type="Interactive play", duration=20, priority="low"))

# ---------------------------------------------------------------------------
# 4. Build and print "Today's Schedule" for all pets (consolidated, no overlaps).
#    Tasks are scheduled sequentially across all pets so the owner can do one
#    task at a time. Once generated, the plan is locked and won't change if
#    new pets/tasks are added — call regenerate_plan() to rebuild it.
# ---------------------------------------------------------------------------
print("=" * 70)
print("           TODAY'S SCHEDULE — PawPal+")
print("=" * 70)

# Create a single scheduler for all pets with a 120-minute daily budget.
consolidated_scheduler = Scheduler(owner=owner, available_minutes=120)

print()
print(consolidated_scheduler.generate_plan())
print()
print(consolidated_scheduler.explain_plan())

print("\n" + "=" * 70)
print("           INDIVIDUAL PET SCHEDULES")
print("=" * 70)

# Extract each pet's tasks from the consolidated schedule for accurate timing.
for pet in owner.pets:
    print()
    print(consolidated_scheduler.generate_pet_plan(pet))
    print()
    print(consolidated_scheduler.explain_pet_plan(pet))
    print("-" * 70)
