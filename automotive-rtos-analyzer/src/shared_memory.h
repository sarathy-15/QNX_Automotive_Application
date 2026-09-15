#ifndef SHARED_MEMORY_H
#define SHARED_MEMORY_H

/*
 * =========================================================
 * AUTOMOTIVE RTOS PERFORMANCE & LATENCY ANALYZER
 *
 * SHARED MEMORY MODULE
 *
 * Master Workflow - Step 9
 *
 * Purpose:
 *   Provide a QNX POSIX shared-memory area for exchanging
 *   RTOS performance information between processes/tasks.
 * =========================================================
 */

#include <stdint.h>
#include <stddef.h>

/*
 * Shared memory object name.
 *
 * POSIX shared-memory names must begin with '/'.
 */
#define RTOS_SHARED_MEMORY_NAME "/rtos_analyzer_shared"

/*
 * Maximum number of task records.
 */
#define SHM_MAX_TASKS 32

/*
 * Shared-memory version.
 */
#define SHM_VERSION 1

/*
 * =========================================================
 * TASK PERFORMANCE DATA
 * =========================================================
 */

typedef struct
{
    int task_id;

    int priority;

    uint64_t execution_time_ns;

    uint64_t deadline_ns;

    uint64_t start_timestamp_ns;

    uint64_t end_timestamp_ns;

    uint64_t execution_count;

    uint64_t deadline_miss_count;

} shm_task_data_t;


/*
 * =========================================================
 * SHARED MEMORY DATA
 * =========================================================
 */

typedef struct
{
    /*
     * Structure/version information.
     */
    uint32_t version;

    uint32_t initialized;

    /*
     * Number of valid task records.
     */
    uint32_t task_count;

    /*
     * Global counters.
     */
    uint64_t total_events;

    uint64_t total_deadline_misses;

    uint64_t total_context_switches;

    /*
     * Last update timestamp.
     */
    uint64_t last_update_timestamp_ns;

    /*
     * Task performance records.
     */
    shm_task_data_t tasks[SHM_MAX_TASKS];

} rtos_shared_memory_t;


/*
 * =========================================================
 * INITIALIZATION
 * =========================================================
 */

/*
 * Create/open the shared-memory object.
 *
 * Returns:
 *   0  = success
 *  -1  = failure
 */
int shared_memory_init(void);


/*
 * =========================================================
 * ACCESS
 * =========================================================
 */

/*
 * Get a pointer to the shared-memory data.
 *
 * Returns:
 *   pointer = success
 *   NULL    = failure/not initialized
 */
rtos_shared_memory_t *shared_memory_get(void);


/*
 * =========================================================
 * TASK DATA
 * =========================================================
 */

/*
 * Register a task in shared memory.
 *
 * Returns:
 *   0  = success
 *  -1  = failure
 */
int shared_memory_register_task(
    int task_id,
    int priority);


/*
 * Update task execution information.
 *
 * Returns:
 *   0  = success
 *  -1  = failure
 */
int shared_memory_update_task(
    int task_id,
    uint64_t execution_time_ns,
    uint64_t start_timestamp_ns,
    uint64_t end_timestamp_ns,
    uint64_t deadline_ns,
    int deadline_missed);


/*
 * =========================================================
 * EVENT COUNTERS
 * =========================================================
 */

void shared_memory_increment_event_count(void);

void shared_memory_increment_deadline_miss(void);

void shared_memory_increment_context_switch(void);


/*
 * =========================================================
 * DISPLAY
 * =========================================================
 */

/*
 * Print the current shared-memory contents.
 */
void shared_memory_print(void);


/*
 * =========================================================
 * CLEANUP
 * =========================================================
 */

/*
 * Unmap and close the shared-memory object.
 *
 * This does NOT unlink the object by default.
 */
void shared_memory_close(void);


/*
 * Permanently remove the named shared-memory object.
 */
void shared_memory_unlink(void);


#endif
