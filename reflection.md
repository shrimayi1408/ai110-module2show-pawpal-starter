# PawPal+ Project Reflection

## 1. System Design
- Add a pet
- Generate a user plan based on owner preferences/info
- Add tasks

**a. Initial design**

- Briefly describe your initial UML design.
I split PawPal+ into three kinds of classes. Data classes hold information. A scheduler holds the logic. Output classes hold the result. This keeps the owner and pet classes simple, and all the "when does each task happen" reasoning lives in one place.

- What classes did you include, and what responsibilities did you assign to each?
Class	Responsibility
Owner: Represents the person. Holds their name, available time windows, preferences and list of pets. Lets you add pets, add tasks, list every task across all pets, and set available times.
    Pet: Represents one animal (name, species, age). Owns that pet's list of care tasks and can add or remove tasks and return its daily schedule.
Task: One care activity such as a walk, feeding or grooming. Stores title, type, duration, priority, preferred time and completed status. Can mark itself complete and check whether it fits in a time window.
    TimeWindow: A block of time when the owner is free (start and end). Reports its duration and whether a given time falls inside it.
Scheduler: The "brain". Takes an owner, sorts tasks by priority, fits them into the owner's available windows, explains why each task was placed where it was, and produces the daily plan.
    ScheduledTask: A task that has been placed in the day. Pairs a Task and Pet with a start time, end time and the reason for the choice.
DailyPlan: The final output for one date. Holds the scheduled tasks and the tasks that didn't fit, can total the minutes planned, and can display the plan as text.
    TaskType (enum): The allowed kinds of task: walk, feeding, grooming, medication, play.
Priority (enum)	The allowed priority levels: low, medium, high.

How they connect:
    An Owner has many Pets and many TimeWindows.
    A Pet has many Tasks.
    The Scheduler reads an Owner and creates a DailyPlan.
    A DailyPlan contains many ScheduledTasks.

**b. Design changes**

- Did your design change during implementation?
Definitely
- If yes, describe at least one change and why you made it.
I made so many changes: 1 example

## Missing relationships
Tasks can be added for a pet the owner doesn't manage.

Owner.add_task(pet, task) takes any Pet.
If that pet isn't in owner.pets, get_all_tasks() never sees it, so the task silently vanishes from the schedule.
Fix: have add_task add the pet if it's missing, or raise an error.
detect_conflicts() returns (Task, Task) pairs.

It can't say which pets are involved, which is the interesting part when one owner is double-booked.
It should return (pet, task) pairs like the other methods.
Pet names aren't unique.

filter_tasks(pet_name=...) is ambiguous with two pets named "Max".
Reject duplicate names in add_pet, or filter by Pet object.
## Logic bottlenecks
is_completed() resets daily, even for "once" tasks.

A one-time task finished yesterday would show as undone today and reappear on the schedule.
The reset should apply only to recurring tasks. For "once", any completed_on value should mean done.
"weekly" has no way to say which day.

There is no weekday or start date on Task, so get_daily_schedule() can't tell whether a weekly task is due today.
Add a weekday or start_date field, or drop "weekly" for now.
Conflict detection is limited to identical times.

A Task has a start time but no duration, so you can only catch exact matches.
A walk at 8:00 and a feeding at 8:15 can't be flagged as overlapping.
Decide whether that's acceptable, or add a duration_minutes field.
frequency is an unchecked string.

A typo like "dailly" would behave like an unknown value.
Validate it in Task (for example in __post_init__), or use a small enum later.
Minor: the field time: time has the same name as its type. It works today, but it breaks if you ever give it a default value. Renaming it to due_time avoids that.

The first two logic problems matter most, because they produce wrong schedules rather than just awkward code. Do you want me to apply fixes for items 1 and 2 in the relationships list and the first two bottlenecks?

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
Design brainstorming, adding classes and methods most appropriate. choosing how to make my schedule was the least straight-forward.
- What kinds of prompts or questions were most helpful?
The most helpful ones were when i asked it what i wanted to do, and what are all teh changes i needed to make. so this would give me just text, no actual code changes so i can review and understand on my own. I rejected the over-engineered ones and I still have yet to resolve some differences like daily schedule being about the owner and not the individual pet schedule. I have accepted all the known gaps as of now and plan on changing it later, focusing on code structure and coherent relationships.

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?


## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?

---

## 6. Reflect on AI Strategy

**Which AI coding assistant features were most effective for building the scheduler?**

The most useful pattern was asking the assistant to review my design in plain text before it touched any code. When I asked "what do I want to do, and what changes do I need to make?", I got a list of gaps (tasks for pets the owner doesn't manage, `once` tasks resetting daily, weekly tasks with no day, conflict detection that only catches identical times). I could read, question and prioritize those myself instead of reviewing a pile of diffs. Once the design was settled, letting the assistant generate the class skeletons from the UML, then the sorting/filtering/conflict logic and the pytest suite, saved the most time. It was also good at drafting edge-case tests (recurrence, back-to-back tasks, empty schedules) that I then checked against the behavior I actually wanted.

**One suggestion I rejected or modified to keep the design clean**

The assistant offered more elaborate options than the project needed, such as extra fields and validation layers on `Task`. I rejected those and kept the three-part split: data classes (`Owner`, `Pet`, `Task`), one `Scheduler` that holds all the "when does it happen" logic, and `DailyPlan`/`ScheduledTask` as output. I also accepted a few known gaps on purpose, such as the daily schedule being owner-level rather than per-pet, and noted them to fix later. I chose to keep the code structure and the relationships between classes coherent rather than patch every edge case at once.

**How separate chat sessions for different phases helped**

Using a fresh session per phase (design/UML, implementation, then testing and documentation) kept each conversation focused on one question. The design session didn't get cluttered with debugging output, and the testing session started from the finished code rather than half-formed ideas. Each session began with a short summary of the previous result, which also forced me to state my decisions clearly. It was easier to tell which suggestions belonged to which phase, and I wasn't fighting stale context from an earlier design that had since changed.
