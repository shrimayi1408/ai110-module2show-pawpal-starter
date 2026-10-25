"""PawPal+ logic layer: backend classes for pets, owners, tasks, and scheduling."""

from dataclasses import dataclass, field
from datetime import date, time
from typing import List, Optional, Tuple


@dataclass
class Task:
    description: str
    time: time
    frequency: str = "once"  # "once", "daily", or "weekly"
    completed_on: Optional[date] = None  # resets itself: only "done" if completed today

    def mark_complete(self) -> None:
        """Record that this task was completed today."""
        self.completed_on = date.today()

    def is_completed(self) -> bool:
        """Return True if this task was completed today."""
        return self.completed_on == date.today()


@dataclass
class Pet:
    name: str
    species: str
    age: int
    tasks: List[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Add a task to this pet (the pet must already be added to its owner, or the Scheduler won't see it)."""
        self.tasks.append(task)


@dataclass
class Owner:
    name: str
    pets: List[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Register a pet with this owner."""
        self.pets.append(pet)

    def add_task(self, pet: Pet, task: Task) -> None:
        """Add a task to a pet, registering the pet with this owner if needed."""
        if pet not in self.pets:
            self.add_pet(pet)
        pet.add_task(task)

    def get_all_tasks(self) -> List[Tuple[Pet, Task]]:
        """Return every task across all of this owner's pets as (pet, task) pairs."""
        return [(pet, task) for pet in self.pets for task in pet.tasks]


@dataclass
class Scheduler:
    owner: Owner

    def get_daily_schedule(self) -> List[Tuple[Pet, Task]]:
        """Return all of the owner's tasks across every pet, sorted by time."""
        return self.sort_by_time(self.owner.get_all_tasks())

    def sort_by_time(self, tasks: List[Tuple[Pet, Task]]) -> List[Tuple[Pet, Task]]:
        """Return the (pet, task) pairs ordered by task time, earliest first."""
        return sorted(tasks, key=lambda pair: pair[1].time)

    def filter_tasks(self, pet_name: Optional[str] = None, completed: Optional[bool] = None) -> List[Tuple[Pet, Task]]:
        """Return tasks filtered by pet name and/or completion status (not yet implemented)."""
        pass

    def detect_conflicts(self) -> List[Tuple[Task, Task]]:
        """Return pairs of tasks scheduled at conflicting times (not yet implemented)."""
        pass
