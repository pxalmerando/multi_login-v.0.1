## 1. Initialization and Concurrency Control

- The application instantiates `ConcurrentTaskExecutor` with a specific `max_concurrency` integer.
- An `asyncio.Semaphore` is immediately created with this limit. This semaphore acts as a gatekeeper, ensuring that no more than $N$ tasks access resources simultaneously.

## 2. Batch Task Submission

- The caller invokes `execute_batch`, passing a list of raw data `items` and a `processor_func` (the logic to apply to each item).
- **Task Wrapping**: The executor internally wraps the `processor_func` inside a new async function.
  - This wrapper attempts to acquire the `semaphore` before running.
  - If the limit is reached, it waits until a slot is freed by a completing task.

## 3. Execution and Aggregation

- **Gathering**: The executor generates a list of these wrapped coroutines and schedules them using `asyncio.gather`.
- **Logging**: It logs the total number of tasks and the concurrency limit for observability.
- **Completion**:
  - The system waits for *all* tasks to finish, regardless of success or failure (`return_exceptions=True`).
  - It returns a unified list containing both successful results and exception objects to the caller for final processing.