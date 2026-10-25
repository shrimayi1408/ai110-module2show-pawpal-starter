"""PawPal+ logic layer: backend classes for pets, owners, tasks, and scheduling."""

import datetime
from dataclasses import dataclass, field
from datetime import date, time
from enum import Enum
from typing import Dict, List, Optional, Tuple

#enum classes for task types and priority levels
class TaskType(Enum):
    WALK = "walk"
    FEEDING = "feeding"
    GROOMING = "grooming"
    MEDICATION = "medication"
    PLAY = "play"
class Priority(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3


@dataclass
class TimeWindow:
    start: time
    end: time

    def duration(self) -> int:
        pass

    def contains(self, t: time) -> bool:
        pass


@dataclass
class Task:
    title: str
    task_type: TaskType
    duration_minutes: int  # time preference: the task should not run longer than this
    priority: Priority
    preferred_time: Optional[time] = None  # time preference: when in the day (e.g. morning, evening)
    completed_on: Optional[date] = None  # resets itself: only "done" if completed today

    def mark_complete(self) -> None:
        pass

    def is_completed(self) -> bool:
        pass

    def fits_in(self, window: TimeWindow) -> bool:
        pass


# eq=False keeps Pet hashable (identity-based) so it can be a dict key in Owner.tasks
@dataclass(eq=False)
class Pet:
    name: str
    species: str
    age: int


@dataclass
class Owner:
    name: str
    available_times: List[TimeWindow] = field(default_factory=list)
    tasks: Dict[Pet, List[Task]] = field(default_factory=dict)  # pet -> that pet's tasks

    def add_pet(self, pet: Pet) -> None:
        pass

    def add_task(self, pet: Pet, task: Task) -> None:
        pass

    def get_all_tasks(self) -> List[Tuple[Pet, Task]]:
        pass

    def set_available_time(self, window: TimeWindow) -> None:
        pass


@dataclass
class ScheduledTask:
    task: Task
    start_time: time
    end_time: time
    reason: str


@dataclass
class DailyPlan:
    owner: Owner
    pet: Pet
    date: datetime.date = field(init=False, default_factory=datetime.date.today)  # filled in automatically
    scheduled: List[ScheduledTask] = field(default_factory=list)
    unscheduled: List[Task] = field(default_factory=list)

    def total_minutes(self) -> int:
        pass

    def display(self) -> str:
        pass


@dataclass
class Scheduler:
    owner: Owner

    def get_daily_schedule(self, pet: Pet) -> List[Task]:
        pass

    def generate_daily_plan(self, pet: Pet) -> DailyPlan:
        pass

    def sort_by_priority(self, tasks: List[Task]) -> List[Task]:
        pass

    def fit_to_availability(self, tasks: List[Task]) -> List[ScheduledTask]:
        pass

    def explain_choice(self, task: Task) -> str:
        pass
