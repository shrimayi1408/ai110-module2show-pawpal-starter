from datetime import time

from pawpal_system import Owner, Pet, Scheduler, Task


def show(title, scheduler, pairs):
    print(f"\n{title}")
    print("-" * 60)
    if not pairs:
        print("(none)")
    for pet, task in pairs:
        status = "x" if task.is_completed() else " "
        print(
            f"[{status}] {task.time:%H:%M}  {scheduler.pet_label(pet)}: {task.description} "
            f"({task.frequency}, {task.priority}, {task.duration} min)"
        )


def main() -> None:
    owner = Owner(name="Jordan")
    buddy = Pet(name="Buddy", species="dog", age=4)
    whiskers = Pet(name="Whiskers", species="cat", age=2)
    owner.add_pet(buddy)
    owner.add_pet(whiskers)

    # tasks deliberately added out of time/priority order
    owner.add_task(buddy, Task("Evening grooming", time(18, 0), "daily", priority="low", duration=20))
    owner.add_task(whiskers, Task("Playtime", time(12, 15), "once", priority="medium", duration=15))
    owner.add_task(buddy, Task("Morning walk", time(7, 30), "daily", priority="high", duration=30))
    owner.add_task(whiskers, Task("Breakfast", time(8, 0), "daily", priority="high", duration=10))
    owner.add_task(buddy, Task("Bath", time(16, 0), "weekly", priority="low", duration=30))
    owner.add_task(buddy, Task("Medication", time(7, 45), "daily", priority="high", duration=5))  # overlaps the walk

    scheduler = Scheduler([owner])

    show("As added (unsorted)", scheduler, owner.get_all_tasks())
    show("sort_by_time()", scheduler, scheduler.sort_by_time(owner.get_all_tasks()))
    show("Daily schedule (overdue, then priority, then time)", scheduler, scheduler.get_daily_schedule())

    # complete a couple so the completion filter has something to show (daily tasks queue a next occurrence)
    buddy.tasks[1].mark_complete()  # Morning walk
    whiskers.tasks[1].mark_complete()  # Breakfast

    show("filter_tasks(pet_name='Buddy')", scheduler, scheduler.filter_tasks(pet_name="Buddy"))
    show("filter_tasks(completed=True)", scheduler, scheduler.filter_tasks(completed=True))
    show("filter_tasks(completed=False)", scheduler, scheduler.filter_tasks(completed=False))
    show(
        "filter_tasks(pet_name='Buddy', completed=False)",
        scheduler,
        scheduler.filter_tasks(pet_name="Buddy", completed=False),
    )

    print("\nRecurring tasks: completing a task queues its next occurrence")
    print("-" * 60)
    for pet, task in [(buddy, buddy.tasks[0]), (buddy, buddy.tasks[2]), (whiskers, whiskers.tasks[0])]:
        upcoming = task.mark_complete()
        if upcoming:
            print(f"{pet.name}: {task.description} ({task.frequency}) done -> next due {upcoming.due_date:%a %Y-%m-%d}")
        else:
            print(f"{pet.name}: {task.description} ({task.frequency}) done -> no next occurrence")
    show("Schedule today (finished tasks stay visible, next occurrences wait)", scheduler, scheduler.get_daily_schedule())
    show("filter_tasks(completed=False): includes the queued next occurrences", scheduler, scheduler.filter_tasks(completed=False))

    print("\nConflicts")
    print("-" * 60)
    for pet, a, b in scheduler.detect_conflicts():
        slot = scheduler.suggest_free_slot(pet, b)
        print(f"{pet.name}: {a.description} overlaps {b.description}; try {b.description} at {slot:%H:%M}")


if __name__ == "__main__":
    main()
