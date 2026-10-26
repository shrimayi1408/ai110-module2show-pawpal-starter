from datetime import datetime, time, timedelta

import streamlit as st

from pawpal_system import Owner, Pet, Scheduler, Task

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")

WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

if "owners" not in st.session_state:
    st.session_state.owners = [Owner(name="Jordan")]
owners = st.session_state.owners

# Reserve the top of the page for the schedule; it is filled in at the end of the script
# so it always reflects whatever changed during this run, and stays until the page is refreshed.
schedule_area = st.container()

st.divider()

st.subheader("Owners and Pets")

new_owner = st.columns([3, 1])
new_owner_name = new_owner[0].text_input("New owner name", label_visibility="collapsed", placeholder="New owner name")
if new_owner[1].button("Add owner"):
    name = new_owner_name.strip()
    if not name:
        st.warning("Enter an owner name first.")
    elif any(o.name.lower() == name.lower() for o in owners):
        st.warning(f"There is already an owner named {name}.")
    else:
        owners.append(Owner(name=name))

owner_index = st.selectbox("Owner", range(len(owners)), format_func=lambda i: owners[i].name)
owner = owners[owner_index]

col1, col2, col3 = st.columns(3)
with col1:
    pet_name = st.text_input("Pet name", value="Mochi")
with col2:
    species = st.selectbox("Species", ["dog", "cat", "other"])
with col3:
    age = st.number_input("Age", min_value=0, max_value=40, value=2)

if st.button("Add pet"):
    if not pet_name.strip():
        st.warning("Enter a pet name first.")
    else:
        try:
            owner.add_pet(Pet(name=pet_name.strip(), species=species, age=int(age)))
        except ValueError:
            st.warning(f"{owner.name} already has a pet named {pet_name.strip()}.")

if owner.pets:
    st.write(f"{owner.name}'s pets: " + ", ".join(f"{p.name} ({p.species})" for p in owner.pets))
else:
    st.info(f"{owner.name} has no pets yet. Add one above.")

st.markdown("### Tasks")

if owner.pets:
    col1, col2 = st.columns(2)
    with col1:
        # selectbox returns a copy of object options, so select by index and look up the real Pet
        pet_index = st.selectbox("Pet", range(len(owner.pets)), format_func=lambda i: owner.pets[i].name)
        task_pet = owner.pets[pet_index]
    with col2:
        description = st.text_input("Task description", value="Morning walk")

    col1, col2, col3 = st.columns(3)
    with col1:
        task_time = st.time_input("Time", value=time(8, 0))
    with col2:
        duration = st.number_input("Duration (min)", min_value=1, max_value=600, value=30, step=5)
    with col3:
        priority = st.selectbox("Priority", ["high", "medium", "low"], index=1)

    col1, col2 = st.columns(2)
    with col1:
        frequency = st.selectbox("Frequency", ["once", "daily", "weekly"])
    with col2:
        weekday = st.selectbox("Day", range(7), format_func=lambda i: WEEKDAYS[i], disabled=frequency != "weekly")

    if st.button("Add task"):
        owner.add_task(
            task_pet,
            Task(
                description=description,
                time=task_time,
                frequency=frequency,
                priority=priority,
                weekday=weekday if frequency == "weekly" else None,
                duration=int(duration),
            ),
        )

st.divider()
owner_wide = st.checkbox(
    "Also warn when one owner has overlapping tasks for different pets",
    help="One person can't walk the dog and groom the cat at the same time.",
)

# Rendered last, into the container at the top of the page.
with schedule_area:
    scheduler = Scheduler(owners)
    now = datetime.now()
    st.subheader("Today's Schedule")

    schedule = scheduler.get_daily_schedule(now)
    if not schedule:
        st.info("Nothing scheduled today. Add tasks below.")
    else:
        for pet, first, second in scheduler.detect_conflicts(now.date()):
            slot = scheduler.suggest_free_slot(pet, second, now.date())
            hint = f" Try moving {second.description} to {slot:%H:%M}." if slot else ""
            st.warning(
                f"{scheduler.pet_label(pet)}: {first.description} ({first.time:%H:%M}, {first.duration} min) "
                f"overlaps {second.description} ({second.time:%H:%M}, {second.duration} min).{hint}"
            )
        if owner_wide:
            for conflict_owner, pet_a, a, pet_b, b in scheduler.detect_owner_conflicts(now.date()):
                st.warning(
                    f"{conflict_owner.name} can't do both: {scheduler.pet_label(pet_a)}'s {a.description} "
                    f"({a.time:%H:%M}) and {scheduler.pet_label(pet_b)}'s {b.description} ({b.time:%H:%M}) overlap."
                )

        widths = [1, 1.5, 2, 3, 1.5, 2.5]
        for col, title in zip(st.columns(widths), ["Done", "Time", "Pet", "Task", "Priority", ""]):
            col.markdown(f"**{title}**")

        for pet, task in schedule:
            row = st.columns(widths)
            overdue = task.is_overdue(now)
            row[0].write("✅" if task.is_completed() else "⬜")
            row[1].write(f"{task.time:%H:%M} ({task.duration}m)")
            row[2].write(scheduler.pet_label(pet))
            label = task.description + ("" if task.frequency == "once" else f" ({task.frequency})")
            row[3].write(f"⏰ **Overdue:** {label}" if overdue else label)
            row[4].write(task.priority)
            if not task.is_completed():
                if row[5].button("Mark complete", key=f"done-{id(task)}"):
                    task.mark_complete()  # also adds the next daily/weekly occurrence
                    st.rerun()

    tomorrow = now.date() + timedelta(days=1)
    coming_up = scheduler.get_upcoming(tomorrow, frequency="daily")
    with st.expander(f"Tomorrow's daily tasks ({len(coming_up)})", expanded=True):
        if coming_up:
            for pet, task in coming_up:
                st.write(f"{task.time:%H:%M} ({task.duration}m) · {scheduler.pet_label(pet)} · {task.description} · {task.priority}")
        else:
            st.caption("Nothing queued yet. Daily tasks you complete today show up here for tomorrow.")
