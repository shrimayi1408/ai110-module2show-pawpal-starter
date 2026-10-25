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
Owner tasks: Owner.tasks is a Dict[Pet, List[Task]]. I removed Owner.pets because the dict's keys are the pets. add_pet registers a pet with an empty list. add_task(pet, task) adds to that pet's list, and get_all_tasks() returns (pet, task) pairs.

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
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

---

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
