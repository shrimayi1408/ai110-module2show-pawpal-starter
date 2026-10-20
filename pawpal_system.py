"""PawPal+ logic layer: backend classes for pets, owners, tasks, and scheduling."""

from dataclasses import dataclass, field
from datetime import date, time
from enum import Enum
from typing import Dict, List


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
    duration_minutes: int
    priority: Priority
    preferred_time: str
    completed: bool = False

    def mark_complete(self) -> None:
        pass

    def fits_in(self, window: TimeWindow) -> bool:
        pass


@dataclass
class Pet:
    name: str
    species: str
    age: int
    tasks: List[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        pass

    def remove_task(self, task: Task) -> None:
        pass

    def get_daily_schedule(self) -> List[Task]:
        pass


@dataclass
class Owner:
    name: str
    available_times: List[TimeWindow] = field(default_factory=list)
    preferences: Dict = field(default_factory=dict)
    pets: List[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        pass

    def add_task(self, pet: Pet, task: Task) -> None:
        pass

    def get_all_tasks(self) -> List[Task]:
        pass

    def set_available_time(self, window: TimeWindow) -> None:
        pass


@dataclass
class ScheduledTask:
    task: Task
    pet: Pet
    start_time: time
    end_time: time
    reason: str


@dataclass
class DailyPlan:
    date: date
    scheduled: List[ScheduledTask] = field(default_factory=list)
    unscheduled: List[Task] = field(default_factory=list)

    def total_minutes(self) -> int:
        pass

    def display(self) -> str:
        pass


@dataclass
class Scheduler:
    owner: Owner

    def generate_daily_plan(self) -> DailyPlan:
        pass

    def sort_by_priority(self, tasks: List[Task]) -> List[Task]:
        pass

    def fit_to_availability(self, tasks: List[Task]) -> List[ScheduledTask]:
        pass

    def explain_choice(self, task: Task) -> str:
        pass
