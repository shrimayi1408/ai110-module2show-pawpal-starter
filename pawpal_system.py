"""PawPal+ logic layer: backend classes for pets, owners, tasks, and scheduling."""

from dataclasses import dataclass, field, replace
from datetime import date, datetime, time, timedelta
from typing import List, Optional, Tuple


@dataclass
class Task:
    description: str
    time: time
    frequency: str = "once"  # "once", "daily", or "weekly"
    priority: str = "medium"  # "high", "medium", or "low"
    weekday: Optional[int] = None  # for weekly tasks: 0=Monday..6=Sunday (defaults to today's weekday)
    duration: int = 15  # minutes
    due_date: Optional[date] = None  # the day this occurrence is due (defaults to today, or the next `weekday` for a new weekly task)
    completed_on: Optional[date] = None  # set when this occurrence is done
    pet: Optional["Pet"] = field(default=None, init=False, repr=False, compare=False)  # set by Pet.add_task

    def __post_init__(self) -> None:
        if self.frequency == "weekly" and self.weekday is None:
            self.weekday = date.today().weekday()
        if self.due_date is None:
            today = date.today()
            if self.frequency == "weekly":
                self.due_date = today + timedelta(days=(self.weekday - today.weekday()) % 7)
            else:
                self.due_date = today

    def is_due(self, day: Optional[date] = None) -> bool:
        """Return True if this occurrence belongs on the schedule for the given day (default today).

        A finished occurrence only shows on the day it was completed; an unfinished one shows from its
        due date onward (so a missed task carries over, as overdue, until it is done)."""
        day = day or date.today()
        if self.completed_on is not None:
            return day == self.completed_on
        return day >= self.due_date

    def next_occurrence(self) -> Optional["Task"]:
        """Return a fresh, incomplete copy of this task for its next due date, or None for one-off tasks.

        Daily tasks come back 1 day after completion, weekly tasks 7 days after (date + timedelta handles
        month and year rollovers). The copy keeps the description, time, priority and duration."""
        if self.frequency == "once":
            return None
        done = self.completed_on or date.today()
        next_due = done + timedelta(days=1 if self.frequency == "daily" else 7)
        return replace(self, due_date=next_due, completed_on=None)

    @property
    def start_minute(self) -> int:
        """Minutes since midnight when the task starts."""
        return self.time.hour * 60 + self.time.minute

    @property
    def end_minute(self) -> int:
        """Minutes since midnight when the task ends."""
        return self.start_minute + self.duration

    def overlaps(self, other: "Task") -> bool:
        """Return True if the two tasks' time ranges overlap (back-to-back tasks do not).

        Two half-open ranges [start, end) overlap exactly when each one starts before the other ends."""
        return self.start_minute < other.end_minute and other.start_minute < self.end_minute

    def is_overdue(self, now: Optional[datetime] = None) -> bool:
        """Return True if the task is due today, its start time has passed, and it isn't done.

        Args:
            now: the moment to check against (default: the current time; pass one in for tests).

        A task carried over from an earlier due date counts as overdue regardless of the time of day."""
        now = now or datetime.now()
        if not self.is_due(now.date()) or self.is_completed():
            return False
        return self.due_date < now.date() or self.time < now.time()

    def mark_complete(self) -> Optional["Task"]:
        """Mark this task done today. A daily/weekly task automatically adds a new instance for its next
        occurrence to the same pet.

        Returns:
            The new task, or None if there is no next occurrence (one-off task), the task was already
            completed (so calling it twice never adds a duplicate), or it isn't attached to a pet."""
        if self.is_completed():
            return None
        self.completed_on = date.today()
        upcoming = self.next_occurrence()
        if upcoming is not None and self.pet is not None:
            self.pet.add_task(upcoming)
        return upcoming

    def is_completed(self) -> bool:
        """Return True if this occurrence has been completed."""
        return self.completed_on is not None


@dataclass
class Pet:
    name: str
    species: str
    age: int
    tasks: List[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Add a task to this pet (the pet must already be added to its owner, or the Scheduler won't see it)."""
        task.pet = self
        self.tasks.append(task)


@dataclass
class Owner:
    name: str
    pets: List[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Register a pet with this owner; raises ValueError if the owner already has a pet with that name."""
        if any(p.name.strip().lower() == pet.name.strip().lower() for p in self.pets):
            raise ValueError(f"{self.name} already has a pet named {pet.name}")
        self.pets.append(pet)

    def add_task(self, pet: Pet, task: Task) -> None:
        """Add a task to a pet, registering the pet with this owner if needed."""
        if pet not in self.pets:
            self.add_pet(pet)
        pet.add_task(task)

    def get_all_tasks(self) -> List[Tuple[Pet, Task]]:
        """Return every task across all of this owner's pets as (pet, task) pairs."""
        return [(pet, task) for pet in self.pets for task in pet.tasks]


PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}


@dataclass
class Scheduler:
    owners: List[Owner]

    def get_daily_schedule(self, now: Optional[datetime] = None) -> List[Tuple[Pet, Task]]:
        """Return today's due tasks across every pet, in the order the owner should do them.

        Args:
            now: the moment to build the schedule for (default: the current time).

        Collects each owner's due (pet, task) pairs, then orders them with sort_tasks(): overdue first,
        then high priority first, then earliest time."""
        now = now or datetime.now()
        due = [(pet, task) for owner in self.owners for pet, task in owner.get_all_tasks() if task.is_due(now.date())]
        return self.sort_tasks(due, now)

    def get_upcoming(self, day: date, frequency: Optional[str] = None) -> List[Tuple[Pet, Task]]:
        """Return unfinished tasks whose due date is exactly `day` (e.g. tomorrow), ordered by priority then time.

        Args:
            day: the due date to look for.
            frequency: if given ("once", "daily" or "weekly"), only tasks of that frequency are returned.

        Tasks carried over from earlier days are not included; they appear on today's schedule instead."""
        upcoming = [
            (pet, task)
            for owner in self.owners
            for pet, task in owner.get_all_tasks()
            if task.due_date == day and not task.is_completed() and (frequency is None or task.frequency == frequency)
        ]
        return self.sort_tasks(upcoming)

    def sort_by_time(self, tasks: List[Tuple[Pet, Task]]) -> List[Tuple[Pet, Task]]:
        """Return the (pet, task) pairs ordered by task time, earliest first.

        Uses sorted() with a lambda key that reaches into each pair for task.time. datetime.time values
        compare chronologically, and the sort is stable, so tasks at the same time keep their input order."""
        return sorted(tasks, key=lambda pair: pair[1].time)

    def sort_tasks(self, tasks: List[Tuple[Pet, Task]], now: Optional[datetime] = None) -> List[Tuple[Pet, Task]]:
        """Order (pet, task) pairs: overdue tasks first, then by priority (high first), then time (earliest first).

        Args:
            tasks: the (pet, task) pairs to order; the input list is not modified.
            now: the moment used to decide which tasks are overdue (default: the current time).

        The sort key is a tuple, so Python compares overdue-ness first and falls back to priority, then
        time, only on ties. `not is_overdue` is False (sorts first) for overdue tasks."""
        now = now or datetime.now()
        return sorted(
            tasks,
            key=lambda pair: (not pair[1].is_overdue(now), PRIORITY_ORDER.get(pair[1].priority, 1), pair[1].time),
        )

    def pet_label(self, pet: Pet) -> str:
        """Return the pet's name, or 'Name (Owner)' if another owner has a pet with the same name.

        Names are compared case-insensitively. A single owner can't have duplicate names, so the owner
        is only added when the clash is across owners."""
        owner = next(o for o in self.owners if pet in o.pets)
        clash = any(
            p is not pet and p.name.strip().lower() == pet.name.strip().lower()
            for o in self.owners
            for p in o.pets
        )
        return f"{pet.name} ({owner.name})" if clash else pet.name

    def filter_tasks(self, pet_name: Optional[str] = None, completed: Optional[bool] = None) -> List[Tuple[Pet, Task]]:
        """Return every task, optionally filtered by pet name (case-insensitive) and/or completion status.

        Args:
            pet_name: only tasks belonging to pets with this name; None means any pet.
            completed: True for finished tasks, False for unfinished ones; None means both.

        Filters combine with AND, and results stay in the order the tasks were added."""
        result = [pair for owner in self.owners for pair in owner.get_all_tasks()]
        if pet_name is not None:
            result = [(p, t) for p, t in result if p.name.strip().lower() == pet_name.strip().lower()]
        if completed is not None:
            result = [(p, t) for p, t in result if t.is_completed() == completed]
        return result

    def detect_conflicts(self, day: Optional[date] = None) -> List[Tuple[Pet, Task, Task]]:
        """Return (pet, task, task) triples where one pet has two due tasks whose time ranges overlap.

        Args:
            day: the day to check (default: today); only tasks due that day are considered.

        For each pet, sorts its due tasks by start time and compares each task with the ones after it,
        stopping as soon as a later task starts at or after the current one ends, since every task after
        that starts even later. That's O(n log n) in the common case instead of comparing every pair."""
        conflicts = []
        for owner in self.owners:
            for pet in owner.pets:
                due = sorted((t for t in pet.tasks if t.is_due(day)), key=lambda t: t.start_minute)
                for i, a in enumerate(due):
                    for b in due[i + 1:]:
                        if b.start_minute >= a.end_minute:
                            break  # sorted by start, so nothing later can overlap a either
                        conflicts.append((pet, a, b))
        return conflicts

    def detect_owner_conflicts(self, day: Optional[date] = None) -> List[Tuple[Owner, Pet, Task, Pet, Task]]:
        """Return overlaps between tasks of *different* pets of the same owner (one person can't do both).

        Args:
            day: the day to check (default: today).

        Uses the same sorted sweep as detect_conflicts, but across all of one owner's pets. Overlaps within
        a single pet are skipped here because detect_conflicts already reports them."""
        conflicts = []
        for owner in self.owners:
            due = sorted(
                ((pet, t) for pet, t in owner.get_all_tasks() if t.is_due(day)),
                key=lambda pair: pair[1].start_minute,
            )
            for i, (pet_a, a) in enumerate(due):
                for pet_b, b in due[i + 1:]:
                    if b.start_minute >= a.end_minute:
                        break
                    if pet_a is not pet_b:
                        conflicts.append((owner, pet_a, a, pet_b, b))
        return conflicts

    def suggest_free_slot(
        self, pet: Pet, task: Task, day: Optional[date] = None, owner_wide: bool = False, step: int = 5
    ) -> Optional[time]:
        """Return the earliest start time for `task` that doesn't overlap other due tasks, or None.

        Args:
            pet: the pet the task belongs to.
            task: the task to place; it is ignored when checking for clashes.
            day: the day to check (default: today).
            owner_wide: if True, avoid every task of the pet's owner (one person can't do two things at
                once); otherwise only avoid this pet's other tasks.
            step: how many minutes to advance per attempt.

        Starts at task.time and tries each `step`-minute start in turn until the whole task fits before
        midnight without overlapping a busy task. Returns None if it can't fit anywhere later today."""
        if owner_wide:
            owner = next(o for o in self.owners if pet in o.pets)
            others = [t for _, t in owner.get_all_tasks()]
        else:
            others = pet.tasks
        busy = [t for t in others if t is not task and t.is_due(day)]
        start = task.start_minute
        while start + task.duration <= 24 * 60:
            if not any(start < t.end_minute and t.start_minute < start + task.duration for t in busy):
                return time(start // 60, start % 60)
            start += step
        return None
