from datetime import time

from pawpal_system import Owner, Pet, Scheduler, Task


def main() -> None:
    owner = Owner(name="Jordan")
    buddy = Pet(name="Buddy", species="dog", age=4)
    whiskers = Pet(name="Whiskers", species="cat", age=2)
    owner.add_pet(buddy)
    owner.add_pet(whiskers)

    owner.add_task(buddy, Task("Morning walk", time(7, 30), "daily"))
    owner.add_task(whiskers, Task("Breakfast", time(8, 0), "daily"))
    owner.add_task(buddy, Task("Evening grooming", time(18, 0), "weekly"))
    owner.add_task(whiskers, Task("Playtime", time(12, 15)))

    scheduler = Scheduler(owner)

    print(f"Today's Schedule for {owner.name}")
    print("-" * 40)
    for pet, task in scheduler.get_daily_schedule():
        status = "x" if task.is_completed() else " "
        print(f"[{status}] {task.time:%H:%M}  {pet.name}: {task.description} ({task.frequency})")


if __name__ == "__main__":
    main()
