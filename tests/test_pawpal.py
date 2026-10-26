from datetime import time

from pawpal_system import Owner, Pet, Task


def test_mark_complete_changes_status():
    task = Task("Morning walk", time(7, 30))
    assert not task.is_completed()

    task.mark_complete()

    assert task.is_completed()


def test_adding_task_increases_pet_task_count():
    owner = Owner("Jordan")
    pet = Pet("Buddy", "dog", 4)
    owner.add_pet(pet)
    assert len(pet.tasks) == 0

    owner.add_task(pet, Task("Breakfast", time(8, 0)))

    assert len(pet.tasks) == 1


# --- scheduling behavior ---

from datetime import date, datetime, time as dtime, timedelta

import pytest

from pawpal_system import Scheduler

# a fixed Monday, 10:00, so overdue / weekly logic is deterministic
NOW = datetime(2030, 1, 7, 10, 0)


def make(tasks, pet_name="Buddy"):
    owner = Owner("Jordan")
    pet = Pet(pet_name, "dog", 4)
    owner.add_pet(pet)
    for t in tasks:
        owner.add_task(pet, t)
    return owner, pet, Scheduler([owner])


def test_sort_by_time_orders_earliest_first():
    owner, pet, sched = make([Task("b", dtime(9, 0)), Task("a", dtime(7, 30)), Task("c", dtime(18, 0))])
    ordered = sched.sort_by_time(owner.get_all_tasks())
    assert [t.description for _, t in ordered] == ["a", "b", "c"]


def test_high_priority_comes_first_then_time():
    _, _, sched = make(
        [
            Task("low early", dtime(11, 0), priority="low"),
            Task("high late", dtime(20, 0), priority="high"),
            Task("high early", dtime(12, 0), priority="high"),
            Task("medium", dtime(11, 30)),
        ]
    )
    names = [t.description for _, t in sched.get_daily_schedule(NOW)]
    assert names == ["high early", "high late", "medium", "low early"]


def test_weekly_task_not_due_before_its_due_date_but_carries_over_after():
    task = Task("Grooming", dtime(18, 0), "weekly", weekday=0, due_date=date(2030, 1, 7))  # Monday
    assert not task.is_due(date(2030, 1, 6))
    assert task.is_due(date(2030, 1, 7))
    assert task.is_due(date(2030, 1, 8))  # missed -> carries over (as overdue) until completed


def test_weekly_defaults_to_creation_weekday_and_is_due_today():
    task = Task("Bath", dtime(9, 0), "weekly")
    assert task.weekday == date.today().weekday()
    assert task.due_date == date.today()


def test_weekly_due_date_is_next_matching_weekday():
    other = (date.today().weekday() + 3) % 7
    task = Task("Bath", dtime(9, 0), "weekly", weekday=other)
    assert task.due_date == date.today() + timedelta(days=3)
    assert task.due_date.weekday() == other


def test_weekly_task_missing_from_schedule_before_due_date():
    _, _, sched = make([Task("Grooming", dtime(18, 0), "weekly", weekday=2, due_date=date(2030, 1, 9))])
    assert sched.get_daily_schedule(NOW) == []  # NOW is Monday 2030-01-07


def test_completed_task_only_shows_on_completion_day():
    task = Task("Walk", dtime(8, 0), "daily", due_date=date(2030, 1, 7))
    task.completed_on = date(2030, 1, 7)
    assert task.is_completed()
    assert task.is_due(date(2030, 1, 7))
    assert not task.is_due(date(2030, 1, 8))


def test_daily_completion_creates_next_day_task():
    owner, pet, _ = make([])
    walk = Task("Walk", dtime(8, 0), "daily", priority="high", duration=30)
    owner.add_task(pet, walk)

    upcoming = walk.mark_complete()

    assert walk.is_completed()
    assert upcoming is not None and upcoming is not walk
    assert upcoming.due_date == date.today() + timedelta(days=1)
    assert not upcoming.is_completed()
    assert (upcoming.description, upcoming.time, upcoming.priority, upcoming.duration) == ("Walk", dtime(8, 0), "high", 30)
    assert pet.tasks == [walk, upcoming]


def test_weekly_completion_creates_task_seven_days_later():
    owner, pet, _ = make([])
    task = Task("Bath", dtime(9, 0), "weekly", weekday=date.today().weekday())
    owner.add_task(pet, task)

    upcoming = task.mark_complete()

    assert upcoming.due_date == date.today() + timedelta(days=7)
    assert upcoming.weekday == task.weekday


def test_one_off_task_has_no_next_occurrence():
    owner, pet, _ = make([])
    task = Task("Vet visit", dtime(9, 0), "once")
    owner.add_task(pet, task)
    assert task.mark_complete() is None
    assert pet.tasks == [task]


def test_completing_twice_does_not_duplicate_next_occurrence():
    owner, pet, _ = make([])
    walk = Task("Walk", dtime(8, 0), "daily")
    owner.add_task(pet, walk)
    walk.mark_complete()
    assert walk.mark_complete() is None
    assert len(pet.tasks) == 2


def test_next_occurrence_not_on_todays_schedule():
    owner, pet, sched = make([])
    walk = Task("Walk", dtime(8, 0), "daily")
    owner.add_task(pet, walk)
    walk.mark_complete()
    today_tasks = sched.get_daily_schedule()
    assert today_tasks == [(pet, walk)]  # the finished one shows (as done); tomorrow's waits


def test_same_owner_cannot_have_duplicate_pet_names():
    owner = Owner("Jordan")
    owner.add_pet(Pet("Rex", "dog", 1))
    with pytest.raises(ValueError):
        owner.add_pet(Pet("  rex ", "dog", 2))
    assert len(owner.pets) == 1


def test_same_pet_name_across_owners_gets_owner_label():
    a, b = Owner("Ann"), Owner("Ben")
    rex_a, rex_b, solo = Pet("Rex", "dog", 1), Pet("rex", "dog", 2), Pet("Mia", "cat", 3)
    a.add_pet(rex_a)
    a.add_pet(solo)
    b.add_pet(rex_b)
    sched = Scheduler([a, b])
    assert sched.pet_label(rex_a) == "Rex (Ann)"
    assert sched.pet_label(rex_b) == "rex (Ben)"
    assert sched.pet_label(solo) == "Mia"


def test_overlap_detects_partial_overlap_but_not_back_to_back():
    walk = Task("Walk", dtime(8, 0), duration=30)
    feed = Task("Feed", dtime(8, 15), duration=10)
    after = Task("Play", dtime(8, 30), duration=10)
    assert walk.overlaps(feed)
    assert not walk.overlaps(after)


def test_conflict_detected_for_same_pet_overlap():
    _, pet, sched = make([Task("Walk", dtime(8, 0), duration=30), Task("Feed", dtime(8, 15), duration=10)])
    conflicts = sched.detect_conflicts(NOW.date())
    assert len(conflicts) == 1
    assert conflicts[0][0] is pet


def test_no_conflict_when_tasks_do_not_overlap():
    _, _, sched = make([Task("Walk", dtime(8, 0), duration=30), Task("Feed", dtime(8, 30), duration=10)])
    assert sched.detect_conflicts(NOW.date()) == []


def test_different_pets_same_time_is_not_a_pet_conflict_but_is_an_owner_conflict():
    owner = Owner("Jordan")
    dog, cat = Pet("Buddy", "dog", 4), Pet("Whiskers", "cat", 2)
    owner.add_task(dog, Task("Walk", dtime(8, 0), duration=30))
    owner.add_task(cat, Task("Groom", dtime(8, 10), duration=20))
    sched = Scheduler([owner])
    assert sched.detect_conflicts(NOW.date()) == []
    conflicts = sched.detect_owner_conflicts(NOW.date())
    assert len(conflicts) == 1
    assert {conflicts[0][1].name, conflicts[0][3].name} == {"Buddy", "Whiskers"}


def test_owner_conflicts_ignore_same_pet_pairs():
    _, _, sched = make([Task("Walk", dtime(8, 0), duration=30), Task("Feed", dtime(8, 15), duration=10)])
    assert sched.detect_owner_conflicts(NOW.date()) == []


def test_suggest_free_slot_skips_past_overlap():
    _, pet, sched = make([Task("Walk", dtime(8, 0), duration=30)])
    feed = Task("Feed", dtime(8, 15), duration=10)
    pet.add_task(feed)
    assert sched.suggest_free_slot(pet, feed, NOW.date()) == dtime(8, 30)


def test_suggest_free_slot_returns_none_when_day_is_full():
    _, pet, sched = make([Task("Marathon", dtime(0, 0), duration=24 * 60)])
    late = Task("Late", dtime(23, 0), duration=30)
    pet.add_task(late)
    assert sched.suggest_free_slot(pet, late, NOW.date()) is None


def test_suggest_free_slot_owner_wide_avoids_other_pets():
    owner = Owner("Jordan")
    dog, cat = Pet("Buddy", "dog", 4), Pet("Whiskers", "cat", 2)
    owner.add_task(dog, Task("Walk", dtime(8, 0), duration=30))
    groom = Task("Groom", dtime(8, 10), duration=20)
    owner.add_task(cat, groom)
    sched = Scheduler([owner])
    assert sched.suggest_free_slot(cat, groom, NOW.date()) == dtime(8, 10)
    assert sched.suggest_free_slot(cat, groom, NOW.date(), owner_wide=True) == dtime(8, 30)


def test_overdue_only_when_past_and_incomplete():
    task = Task("Walk", dtime(8, 0), "daily", due_date=NOW.date())
    assert task.is_overdue(NOW)
    assert not Task("Later", dtime(18, 0), "daily", due_date=NOW.date()).is_overdue(NOW)
    assert Task("Missed yesterday", dtime(23, 0), "daily", due_date=NOW.date() - timedelta(days=1)).is_overdue(NOW)
    task.completed_on = date.today()
    assert not task.is_overdue(datetime.now().replace(hour=23, minute=59))


def test_overdue_tasks_sort_to_top():
    _, _, sched = make(
        [
            Task("upcoming high", dtime(18, 0), priority="high", due_date=NOW.date()),
            Task("overdue low", dtime(7, 0), priority="low", due_date=NOW.date()),
            Task("overdue high", dtime(9, 0), priority="high", due_date=NOW.date()),
        ]
    )
    names = [t.description for _, t in sched.get_daily_schedule(NOW)]
    assert names == ["overdue high", "overdue low", "upcoming high"]


def test_filter_tasks_by_pet_and_completion():
    owner = Owner("Jordan")
    dog, cat = Pet("Buddy", "dog", 4), Pet("Whiskers", "cat", 2)
    walk, feed = Task("Walk", dtime(8, 0)), Task("Feed", dtime(9, 0))
    owner.add_task(dog, walk)
    owner.add_task(dog, feed)
    owner.add_task(cat, Task("Play", dtime(10, 0)))
    walk.mark_complete()
    sched = Scheduler([owner])

    assert [t.description for _, t in sched.filter_tasks(pet_name="buddy")] == ["Walk", "Feed"]
    assert [t.description for _, t in sched.filter_tasks(completed=True)] == ["Walk"]
    assert [t.description for _, t in sched.filter_tasks(pet_name="Buddy", completed=False)] == ["Feed"]
    assert len(sched.filter_tasks()) == 3


def test_mark_complete_on_daily_task_adds_next_occurrence_to_its_pet():
    owner, pet, _ = make([])
    walk = Task("Walk", dtime(8, 0), "daily")
    owner.add_task(pet, walk)

    upcoming = walk.mark_complete()

    assert pet.tasks == [walk, upcoming]
    assert upcoming.due_date == date.today() + timedelta(days=1)
    assert upcoming.pet is pet
    assert walk.mark_complete() is None  # no duplicate on a second call
    assert len(pet.tasks) == 2


def test_mark_complete_on_weekly_task_adds_next_week():
    owner, pet, _ = make([])
    bath = Task("Bath", dtime(9, 0), "weekly", weekday=date.today().weekday())
    owner.add_task(pet, bath)
    assert bath.mark_complete().due_date == date.today() + timedelta(days=7)


def test_mark_complete_on_one_off_task_adds_nothing():
    owner, pet, _ = make([Task("Vet", dtime(9, 0), "once")])
    assert pet.tasks[0].mark_complete() is None
    assert len(pet.tasks) == 1


def test_get_upcoming_lists_tomorrows_daily_tasks_only():
    owner, pet, sched = make([])
    walk = Task("Walk", dtime(8, 0), "daily")
    bath = Task("Bath", dtime(9, 0), "weekly", weekday=date.today().weekday())
    owner.add_task(pet, walk)
    owner.add_task(pet, bath)
    walk.mark_complete()
    bath.mark_complete()
    tomorrow = date.today() + timedelta(days=1)

    assert [t.description for _, t in sched.get_upcoming(tomorrow, frequency="daily")] == ["Walk"]
    assert [t.description for _, t in sched.get_upcoming(tomorrow)] == ["Walk"]  # the bath is a week out
    assert sched.get_upcoming(date.today() + timedelta(days=7))[0][1].description == "Bath"


# --- required coverage: sorting, recurrence, conflict detection (plus edge cases) ---


def test_sort_by_time_is_chronological_across_the_whole_day():
    # 9:00 vs 10:00 would sort wrongly as strings ("10:00" < "9:00"); midnight and 23:59 are the extremes
    owner, _, sched = make(
        [Task("late", dtime(23, 59)), Task("ten", dtime(10, 0)), Task("midnight", dtime(0, 0)), Task("nine", dtime(9, 0))]
    )
    ordered = sched.sort_by_time(owner.get_all_tasks())
    assert [t.description for _, t in ordered] == ["midnight", "nine", "ten", "late"]


def test_sort_by_time_is_stable_for_equal_times_and_handles_empty_input():
    owner, _, sched = make([Task("first", dtime(8, 0)), Task("second", dtime(8, 0))])
    ordered = sched.sort_by_time(owner.get_all_tasks())
    assert [t.description for _, t in ordered] == ["first", "second"]
    assert sched.sort_by_time([]) == []


def test_sort_tasks_does_not_modify_its_input():
    owner, _, sched = make([Task("b", dtime(9, 0)), Task("a", dtime(7, 0))])
    pairs = owner.get_all_tasks()
    before = list(pairs)
    sched.sort_tasks(pairs, NOW)
    assert pairs == before


def test_overdue_low_priority_sorts_before_upcoming_high_priority():
    _, _, sched = make(
        [
            Task("high later", dtime(18, 0), priority="high", due_date=NOW.date()),
            Task("low missed", dtime(8, 0), priority="low", due_date=NOW.date()),
        ]
    )
    names = [t.description for _, t in sched.get_daily_schedule(NOW)]  # NOW is 10:00
    assert names == ["low missed", "high later"]


@pytest.mark.parametrize(
    "done, frequency, expected",
    [
        (date(2030, 1, 31), "daily", date(2030, 2, 1)),  # month rollover
        (date(2030, 12, 31), "daily", date(2031, 1, 1)),  # year rollover
        (date(2028, 2, 28), "daily", date(2028, 2, 29)),  # leap year
        (date(2030, 2, 28), "daily", date(2030, 3, 1)),  # non-leap year
        (date(2030, 12, 28), "weekly", date(2031, 1, 4)),  # weekly across the new year
    ],
)
def test_next_occurrence_handles_calendar_rollovers(done, frequency, expected):
    task = Task("Walk", dtime(8, 0), frequency, due_date=done)
    task.completed_on = done
    assert task.next_occurrence().due_date == expected


def test_next_occurrence_is_independent_of_the_original():
    owner, pet, _ = make([])
    walk = Task("Walk", dtime(8, 0), "daily")
    owner.add_task(pet, walk)
    upcoming = walk.mark_complete()
    assert upcoming.pet is pet
    upcoming.description = "Long walk"
    assert walk.description == "Walk"
    assert walk.is_completed() and not upcoming.is_completed()


def test_completing_the_next_occurrence_chains_another_day():
    owner, pet, _ = make([])
    walk = Task("Walk", dtime(8, 0), "daily")
    owner.add_task(pet, walk)
    second = walk.mark_complete()
    third = second.mark_complete()
    assert third.due_date == date.today() + timedelta(days=1)  # completion date drives the next due date
    assert len(pet.tasks) == 3


def test_duplicate_times_on_same_pet_are_flagged_as_a_conflict():
    _, pet, sched = make([Task("Walk", dtime(8, 0)), Task("Feed", dtime(8, 0))])
    conflicts = sched.detect_conflicts(NOW.date())
    assert len(conflicts) == 1
    flagged_pet, a, b = conflicts[0]
    assert flagged_pet is pet
    assert {a.description, b.description} == {"Walk", "Feed"}


def test_duplicate_times_across_pets_are_flagged_as_an_owner_conflict():
    owner = Owner("Jordan")
    owner.add_task(Pet("Buddy", "dog", 4), Task("Walk", dtime(8, 0)))
    owner.add_task(Pet("Whiskers", "cat", 2), Task("Feed", dtime(8, 0)))
    sched = Scheduler([owner])
    assert len(sched.detect_owner_conflicts(NOW.date())) == 1


def test_three_mutually_overlapping_tasks_give_three_conflict_pairs():
    _, _, sched = make([Task(n, dtime(8, 0), duration=30) for n in "abc"])
    assert len(sched.detect_conflicts(NOW.date())) == 3


def test_task_contained_inside_a_longer_task_is_a_conflict():
    _, _, sched = make([Task("Long", dtime(8, 0), duration=60), Task("Short", dtime(8, 20), duration=10)])
    assert len(sched.detect_conflicts(NOW.date())) == 1


def test_conflicts_only_consider_tasks_due_that_day():
    _, _, sched = make(
        [
            Task("Walk", dtime(8, 0), due_date=date(2030, 1, 7)),
            Task("Feed", dtime(8, 0), due_date=date(2030, 1, 9)),
        ]
    )
    assert sched.detect_conflicts(date(2030, 1, 7)) == []


def test_empty_scheduler_and_empty_pet_do_not_crash():
    assert Scheduler([]).get_daily_schedule(NOW) == []
    assert Scheduler([]).detect_conflicts(NOW.date()) == []
    _, _, sched = make([])
    assert sched.get_daily_schedule(NOW) == []
    assert sched.detect_conflicts(NOW.date()) == []
    assert sched.detect_owner_conflicts(NOW.date()) == []


def test_task_exactly_at_now_is_not_overdue():
    task = Task("Walk", dtime(10, 0), due_date=NOW.date())
    assert not task.is_overdue(NOW)
    assert Task("Walk", dtime(9, 59), due_date=NOW.date()).is_overdue(NOW)
