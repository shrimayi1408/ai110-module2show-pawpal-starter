# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

## 🖥️ Sample Output

Paste a sample of your app's CLI or Streamlit output here so a reader can see what a generated plan looks like:

```
# e.g.:
# Daily plan for Biscuit (Golden Retriever):
#   08:00 — Morning walk (30 min) [priority: high]
#   09:00 — Feeding (10 min) [priority: high]
#   ...
```
Plans are built around each pet's tasks (`python main.py`):

```
Today's Schedule for Jordan
----------------------------------------
[ ] 07:30  Buddy: Morning walk (daily, medium, 15 min)
[ ] 08:00  Whiskers: Breakfast (daily, medium, 15 min)
[ ] 12:15  Whiskers: Playtime (once, medium, 15 min)
[ ] 18:00  Buddy: Evening grooming (weekly, medium, 15 min)
```

In the Streamlit app (`streamlit run app.py`) the schedule is a persistent area at the top of the page, with a "Mark complete" button per task.

## ✨ Features

- **Sorting by time**: `sort_by_time()` orders tasks earliest first using `sorted()` with a `datetime.time` key, so `9:00` correctly comes before `10:00`. The sort is stable, so equal times keep their input order.
- **Smart daily schedule**: `get_daily_schedule()` collects today's due tasks across every owner's pets and orders them overdue first, then by priority (high, medium, low), then by time.
- **Filtering**: `filter_tasks()` narrows tasks by pet name (case-insensitive), completion status, or both.
- **Conflict warnings**: `detect_conflicts()` flags overlapping tasks for the same pet by comparing start and end times (duration-aware, so back-to-back tasks are fine). It sorts by start time and stops early, so it is O(n log n) in the common case. `detect_owner_conflicts()` adds an optional check across different pets of one owner.
- **Free-slot suggestions**: `suggest_free_slot()` scans forward in 5-minute steps for the first time a task fits without overlapping, or reports that none is left today.
- **Daily and weekly recurrence**: completing a daily or weekly task adds the next copy (+1 or +7 days, using `timedelta`, so month, year and leap-year rollovers just work). Completing twice never duplicates, and one-off tasks create nothing.
- **Overdue carry-over**: an unfinished task stays on the schedule after its due date and is marked overdue until it is done.
- **Multi-owner, multi-pet**: duplicate pet names are rejected within an owner and labelled `Rex (Ann)` across owners.

## Implementation Summary

The logic layer lives in `pawpal_system.py` and is built from four dataclasses. `main.py` is a small demo script and `app.py` is the Streamlit UI.

- **`Task`**: one care activity: description, time of day, `duration` (minutes), `frequency` (once/daily/weekly), `priority` (high/medium/low), and `weekday` (for weekly tasks). `due_date` and `is_due(day)` decide whether it belongs on a given day, `next_occurrence()` builds the next daily/weekly copy, `overlaps(other)` compares time ranges, `is_overdue(now)` flags missed tasks, and `is_completed()` is true once it has been marked done.
- **`Pet`**: a pet's details plus its own list of tasks, with `add_task()`. `Task.mark_complete()` automatically adds the next occurrence to the pet.
- **`Owner`**: manages multiple pets. `add_pet()` rejects a duplicate pet name (case-insensitive) for the same owner. `add_task(pet, task)` registers the pet if needed, and `get_all_tasks()` returns every pet's tasks as `(pet, task)` pairs.
- **`Scheduler`**: the "brain". It holds a list of `Owner`s and builds one schedule across all their pets.

**How they work together:** `Owner` has many `Pet`s, each `Pet` has many `Task`s, and `Scheduler` reads across all of them through the owners. A pet must be added to its owner before its tasks are visible to the scheduler.

## 🧪 Testing PawPal+

```bash
# Run the full test suite (from the project root, with the venv active):
python -m pytest
```

### What the tests cover

The 49 tests in `tests/test_pawpal.py` exercise the logic layer in `pawpal_system.py` (no UI):

- **Sorting correctness**: tasks come back in chronological order across the whole day (`00:00`, `09:00`, `10:00`, `23:59`), equal times keep their input order, empty input is fine, the input list isn't mutated, and the daily schedule orders overdue first, then priority, then time.
- **Recurrence logic**: completing a daily task creates a fresh task for the next day (weekly: 7 days later) on the same pet, one-off tasks create nothing, completing twice never duplicates, and month, year and leap-year rollovers land on the right date.
- **Conflict detection**: overlapping and duplicate start times are flagged for the same pet, different pets of one owner are flagged as owner conflicts, containment and three-way overlaps are caught, and back-to-back tasks are not conflicts.
- **Other**: overdue boundaries, weekly due dates, the free-slot suggestion, filtering, duplicate pet names, and empty owners/pets not crashing.

### Test results

```
============================= test session starts ==============================
platform darwin -- Python 3.9.6, pytest-8.4.2, pluggy-1.6.0
rootdir: /Users/shrimayisinkar/personalProj/ai-course/ai110-module2show-pawpal-starter
collected 49 items

tests/test_pawpal.py .................................................   [100%]

============================== 49 passed in 0.02s ==============================
```

## 📐 Smarter Scheduling

All of this lives in `pawpal_system.py`. `Scheduler` works across every owner's pets, and `main.py` demos each feature in the terminal.

### Sorting

- **`Scheduler.sort_by_time(tasks)`** orders `(pet, task)` pairs by time of day, earliest first. It uses `sorted()` with a lambda key, `key=lambda pair: pair[1].time`.
- **`Scheduler.sort_tasks(tasks, now)`** is the order used for the daily schedule. The key is a tuple: overdue tasks first, then priority (high, medium, low), then time.
- **`Scheduler.get_daily_schedule(now)`** collects today's due tasks across all pets and runs them through `sort_tasks()`.

### Filtering

- **`Scheduler.filter_tasks(pet_name, completed)`** returns `(pet, task)` pairs filtered by pet name (case-insensitive), completion status, or both. A `None` argument means "don't filter on this".
- **`Scheduler.get_upcoming(day, frequency)`** returns unfinished tasks due on an exact day, optionally of one frequency. The app uses it for the "Tomorrow's daily tasks" panel.

### Conflict detection

- **`Task.overlaps(other)`** compares two time ranges (start plus `duration`). Back-to-back tasks, such as 08:00-08:30 and 08:30-08:40, are not a conflict.
- **`Scheduler.detect_conflicts(day)`** finds overlapping tasks for the *same pet*. It sorts each pet's due tasks by start time and stops comparing as soon as a later task starts after the current one ends.
- **`Scheduler.detect_owner_conflicts(day)`** finds overlaps between *different pets* of the same owner, since one person can't do both. It is optional (a checkbox in the app).
- **`Scheduler.suggest_free_slot(pet, task, day, owner_wide)`** returns the next start time (in 5-minute steps) where the task fits without overlapping, or `None` if it can't fit today. The app shows it as a "Try moving..." hint.
- Conflicts are warnings only. Nothing is moved or blocked automatically.

### Recurring tasks

- Each task has a **`due_date`**. New tasks default to today (a new weekly task defaults to its chosen weekday).
- **`Task.mark_complete()`** marks a task done and, for daily or weekly tasks, adds a new copy to the same pet automatically. It returns the new task, or `None` for one-off tasks. Calling it twice never adds a duplicate.
- **`Task.next_occurrence()`** builds that copy: `due_date` is the completion date plus `timedelta(days=1)` for daily and `timedelta(days=7)` for weekly.
- **`Task.is_due(day)`** decides what appears on a given day. An unfinished task shows from its due date onward (a missed one carries over as overdue). A finished task shows only on the day it was completed, so tomorrow's copy waits until tomorrow.
- **`Task.is_overdue(now)`** is true for an unfinished task whose due date has passed, or whose time has passed today.

### Other

| Feature             | Method(s)                                   |  Notes                                                       |
|---------------------|---------------------------------------------|--------------------------------------------------------------|
| Duplicate pet names | `Owner.add_pet()`, `Scheduler.pet_label()` | Same owner: rejected. Different owners: shown as `Rex (Ann)`. |

## 📸 Demo Walkthrough

### The app (`streamlit run app.py`)

**What you can do**
- Add owners and pets (name, species, age), and add tasks to a pet with a time, duration, priority, and frequency (once, daily or weekly, with a weekday for weekly).
- See **Today's Schedule** pinned at the top of the page, with summary counts, a "Mark complete" button per task, and a "Tomorrow's daily tasks" panel.
- Open **All tasks (sort and filter)** to view every task in a table, filtered by pet and by pending or done.
- Tick the checkbox to also warn when one owner has overlapping tasks for different pets.

**Example workflow**
1. Add a pet, for example "Mochi" (dog, age 2).
2. Add a task: "Morning walk" at 08:00 for 30 minutes, priority high, daily.
3. Add a second task: "Medication" at 08:15 for 10 minutes. Because it overlaps the walk, a warning appears at the top of the schedule naming both tasks, showing their time ranges, and suggesting a free time such as 08:30.
4. Fix the clash by re-adding the task at the suggested time. The banner switches to a green "No scheduling conflicts" message.
5. Click **Mark complete** on the walk. It stays on today's list as done, and tomorrow's walk appears in "Tomorrow's daily tasks".

**Scheduler behaviors on display**
- **Sorting**: today's list is ordered overdue first, then priority, then time.
- **Conflict warnings**: `st.warning` messages with the pet, both tasks, their time ranges and a suggested fix. They never move or block anything.
- **Recurrence**: completing a daily or weekly task queues its next occurrence automatically.
- **Filtering**: the all-tasks table can be narrowed by pet and by status.

### The terminal demo (`python main.py`)

Sample output (dates depend on the day you run it):

```

As added (unsorted)
------------------------------------------------------------
[ ] 18:00  Buddy: Evening grooming (daily, low, 20 min)
[ ] 07:30  Buddy: Morning walk (daily, high, 30 min)
[ ] 16:00  Buddy: Bath (weekly, low, 30 min)
[ ] 07:45  Buddy: Medication (daily, high, 5 min)
[ ] 12:15  Whiskers: Playtime (once, medium, 15 min)
[ ] 08:00  Whiskers: Breakfast (daily, high, 10 min)

sort_by_time()
------------------------------------------------------------
[ ] 07:30  Buddy: Morning walk (daily, high, 30 min)
[ ] 07:45  Buddy: Medication (daily, high, 5 min)
[ ] 08:00  Whiskers: Breakfast (daily, high, 10 min)
[ ] 12:15  Whiskers: Playtime (once, medium, 15 min)
[ ] 16:00  Buddy: Bath (weekly, low, 30 min)
[ ] 18:00  Buddy: Evening grooming (daily, low, 20 min)

Daily schedule (overdue, then priority, then time)
------------------------------------------------------------
[ ] 07:30  Buddy: Morning walk (daily, high, 30 min)
[ ] 07:45  Buddy: Medication (daily, high, 5 min)
[ ] 08:00  Whiskers: Breakfast (daily, high, 10 min)
[ ] 12:15  Whiskers: Playtime (once, medium, 15 min)
[ ] 16:00  Buddy: Bath (weekly, low, 30 min)
[ ] 18:00  Buddy: Evening grooming (daily, low, 20 min)

filter_tasks(pet_name='Buddy')
------------------------------------------------------------
[ ] 18:00  Buddy: Evening grooming (daily, low, 20 min)
[x] 07:30  Buddy: Morning walk (daily, high, 30 min)
[ ] 16:00  Buddy: Bath (weekly, low, 30 min)
[ ] 07:45  Buddy: Medication (daily, high, 5 min)
[ ] 07:30  Buddy: Morning walk (daily, high, 30 min)

filter_tasks(completed=True)
------------------------------------------------------------
[x] 07:30  Buddy: Morning walk (daily, high, 30 min)
[x] 08:00  Whiskers: Breakfast (daily, high, 10 min)

filter_tasks(completed=False)
------------------------------------------------------------
[ ] 18:00  Buddy: Evening grooming (daily, low, 20 min)
[ ] 16:00  Buddy: Bath (weekly, low, 30 min)
[ ] 07:45  Buddy: Medication (daily, high, 5 min)
[ ] 07:30  Buddy: Morning walk (daily, high, 30 min)
[ ] 12:15  Whiskers: Playtime (once, medium, 15 min)
[ ] 08:00  Whiskers: Breakfast (daily, high, 10 min)

filter_tasks(pet_name='Buddy', completed=False)
------------------------------------------------------------
[ ] 18:00  Buddy: Evening grooming (daily, low, 20 min)
[ ] 16:00  Buddy: Bath (weekly, low, 30 min)
[ ] 07:45  Buddy: Medication (daily, high, 5 min)
[ ] 07:30  Buddy: Morning walk (daily, high, 30 min)

Recurring tasks: completing a task queues its next occurrence
------------------------------------------------------------
Buddy: Evening grooming (daily) done -> next due Mon 2026-10-26
Buddy: Bath (weekly) done -> next due Sun 2026-11-01
Whiskers: Playtime (once) done -> no next occurrence

Schedule today (finished tasks stay visible, next occurrences wait)
------------------------------------------------------------
[ ] 07:45  Buddy: Medication (daily, high, 5 min)
[x] 07:30  Buddy: Morning walk (daily, high, 30 min)
[x] 08:00  Whiskers: Breakfast (daily, high, 10 min)
[x] 12:15  Whiskers: Playtime (once, medium, 15 min)
[x] 16:00  Buddy: Bath (weekly, low, 30 min)
[x] 18:00  Buddy: Evening grooming (daily, low, 20 min)

filter_tasks(completed=False): includes the queued next occurrences
------------------------------------------------------------
[ ] 07:45  Buddy: Medication (daily, high, 5 min)
[ ] 07:30  Buddy: Morning walk (daily, high, 30 min)
[ ] 18:00  Buddy: Evening grooming (daily, low, 20 min)
[ ] 16:00  Buddy: Bath (weekly, low, 30 min)
[ ] 08:00  Whiskers: Breakfast (daily, high, 10 min)

Conflicts
------------------------------------------------------------
Buddy: Morning walk overlaps Medication; try Medication at 08:00
```
