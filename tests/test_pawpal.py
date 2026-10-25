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
