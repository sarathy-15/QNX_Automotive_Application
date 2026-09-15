/*
 * =========================================================
 * AUTOMOTIVE RTOS PERFORMANCE & LATENCY ANALYZER
 *
 * SHARED MEMORY MODULE
 *
 * Master Workflow - Step 9
 *
 * QNX POSIX Shared Memory Implementation
 * =========================================================
 */

#include "shared_memory.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <fcntl.h>
#include <sys/mman.h>
#include <sys/stat.h>
#include <unistd.h>
#include <pthread.h>
#include <time.h>


/*
 * =========================================================
 * INTERNAL STATE
 * =========================================================
 */

static int shared_memory_fd = -1;

static rtos_shared_memory_t *shared_memory_ptr = NULL;

static pthread_mutex_t shared_memory_mutex =
    PTHREAD_MUTEX_INITIALIZER;


/*
 * =========================================================
 * TIMESTAMP
 * =========================================================
 */

static uint64_t get_timestamp_ns(void)
{
    struct timespec ts;

    if (clock_gettime(
            CLOCK_MONOTONIC,
            &ts) != 0)
    {
        return 0;
    }

    return
        ((uint64_t)ts.tv_sec * 1000000000ULL)
        +
        (uint64_t)ts.tv_nsec;
}


/*
 * =========================================================
 * FIND TASK
 * =========================================================
 */

static int find_task_index(int task_id)
{
    uint32_t i;

    if (shared_memory_ptr == NULL)
    {
        return -1;
    }

    for (i = 0;
         i < shared_memory_ptr->task_count;
         i++)
    {
        if (shared_memory_ptr->tasks[i].task_id ==
            task_id)
        {
            return (int)i;
        }
    }

    return -1;
}


/*
 * =========================================================
 * INITIALIZATION
 * =========================================================
 */

int shared_memory_init(void)
{
    size_t shared_memory_size;

    shared_memory_size =
        sizeof(rtos_shared_memory_t);


    /*
     * Already initialized.
     */
    if (shared_memory_ptr != NULL)
    {
        return 0;
    }


    /*
     * Create/open POSIX shared-memory object.
     */
    shared_memory_fd =
        shm_open(
            RTOS_SHARED_MEMORY_NAME,
            O_CREAT | O_RDWR,
            0666);


    if (shared_memory_fd == -1)
    {
        perror(
            "ERROR: shm_open failed");

        return -1;
    }


    /*
     * Set shared-memory size.
     */
    if (ftruncate(
            shared_memory_fd,
            (off_t)shared_memory_size) == -1)
    {
        perror(
            "ERROR: ftruncate failed");

        close(shared_memory_fd);

        shared_memory_fd = -1;

        return -1;
    }


    /*
     * Map shared memory.
     */
    shared_memory_ptr =
        mmap(
            NULL,
            shared_memory_size,
            PROT_READ | PROT_WRITE,
            MAP_SHARED,
            shared_memory_fd,
            0);


    if (shared_memory_ptr == MAP_FAILED)
    {
        perror(
            "ERROR: mmap failed");

        shared_memory_ptr = NULL;

        close(shared_memory_fd);

        shared_memory_fd = -1;

        return -1;
    }


    /*
     * Initialize contents.
     */
    pthread_mutex_lock(
        &shared_memory_mutex);


    memset(
        shared_memory_ptr,
        0,
        sizeof(rtos_shared_memory_t));


    shared_memory_ptr->version =
        SHM_VERSION;

    shared_memory_ptr->initialized =
        1;

    shared_memory_ptr->task_count =
        0;

    shared_memory_ptr->total_events =
        0;

    shared_memory_ptr->total_deadline_misses =
        0;

    shared_memory_ptr->total_context_switches =
        0;

    shared_memory_ptr->last_update_timestamp_ns =
        get_timestamp_ns();


    pthread_mutex_unlock(
        &shared_memory_mutex);


    printf("\n");
    printf("============================================\n");
    printf("          SHARED MEMORY INIT\n");
    printf("============================================\n");

    printf(
        "Object       : %s\n",
        RTOS_SHARED_MEMORY_NAME);

    printf(
        "Size         : %zu bytes\n",
        sizeof(rtos_shared_memory_t));

    printf(
        "Version      : %u\n",
        shared_memory_ptr->version);

    printf(
        "Status       : READY\n");

    printf(
        "============================================\n");


    return 0;
}


/*
 * =========================================================
 * GET SHARED MEMORY POINTER
 * =========================================================
 */

rtos_shared_memory_t *shared_memory_get(void)
{
    return shared_memory_ptr;
}


/*
 * =========================================================
 * REGISTER TASK
 * =========================================================
 */

int shared_memory_register_task(
    int task_id,
    int priority)
{
    uint32_t index;


    if (shared_memory_ptr == NULL)
    {
        return -1;
    }


    pthread_mutex_lock(
        &shared_memory_mutex);


    /*
     * Check whether task already exists.
     */
    if (find_task_index(task_id) >= 0)
    {
        pthread_mutex_unlock(
            &shared_memory_mutex);

        return 0;
    }


    /*
     * Check capacity.
     */
    if (shared_memory_ptr->task_count >=
        SHM_MAX_TASKS)
    {
        pthread_mutex_unlock(
            &shared_memory_mutex);

        printf(
            "WARNING: Shared memory task table full.\n");

        return -1;
    }


    index =
        shared_memory_ptr->task_count;


    /*
     * Initialize task record.
     */
    shared_memory_ptr->tasks[index].task_id =
        task_id;

    shared_memory_ptr->tasks[index].priority =
        priority;

    shared_memory_ptr->tasks[index].execution_time_ns =
        0;

    shared_memory_ptr->tasks[index].deadline_ns =
        0;

    shared_memory_ptr->tasks[index].start_timestamp_ns =
        0;

    shared_memory_ptr->tasks[index].end_timestamp_ns =
        0;

    shared_memory_ptr->tasks[index].execution_count =
        0;

    shared_memory_ptr->tasks[index].deadline_miss_count =
        0;


    shared_memory_ptr->task_count++;


    shared_memory_ptr->last_update_timestamp_ns =
        get_timestamp_ns();


    pthread_mutex_unlock(
        &shared_memory_mutex);


    return 0;
}


/*
 * =========================================================
 * UPDATE TASK
 * =========================================================
 */

int shared_memory_update_task(
    int task_id,
    uint64_t execution_time_ns,
    uint64_t start_timestamp_ns,
    uint64_t end_timestamp_ns,
    uint64_t deadline_ns,
    int deadline_missed)
{
    int index;


    if (shared_memory_ptr == NULL)
    {
        return -1;
    }


    pthread_mutex_lock(
        &shared_memory_mutex);


    index =
        find_task_index(task_id);


    /*
     * Automatically create the task
     * if it has not been registered.
     */
    if (index < 0)
    {
        if (shared_memory_ptr->task_count >=
            SHM_MAX_TASKS)
        {
            pthread_mutex_unlock(
                &shared_memory_mutex);

            return -1;
        }


        index =
            (int)shared_memory_ptr->task_count;


        shared_memory_ptr->tasks[index].task_id =
            task_id;

        shared_memory_ptr->tasks[index].priority =
            0;

        shared_memory_ptr->task_count++;
    }


    /*
     * Update performance data.
     */
    shared_memory_ptr->tasks[index]
        .execution_time_ns =
        execution_time_ns;

    shared_memory_ptr->tasks[index]
        .start_timestamp_ns =
        start_timestamp_ns;

    shared_memory_ptr->tasks[index]
        .end_timestamp_ns =
        end_timestamp_ns;

    shared_memory_ptr->tasks[index]
        .deadline_ns =
        deadline_ns;

    shared_memory_ptr->tasks[index]
        .execution_count++;


    if (deadline_missed)
    {
        shared_memory_ptr->tasks[index]
            .deadline_miss_count++;

        shared_memory_ptr
            ->total_deadline_misses++;
    }


    shared_memory_ptr->total_events++;


    shared_memory_ptr->last_update_timestamp_ns =
        get_timestamp_ns();


    pthread_mutex_unlock(
        &shared_memory_mutex);


    return 0;
}


/*
 * =========================================================
 * EVENT COUNT
 * =========================================================
 */

void shared_memory_increment_event_count(void)
{
    if (shared_memory_ptr == NULL)
    {
        return;
    }


    pthread_mutex_lock(
        &shared_memory_mutex);


    shared_memory_ptr->total_events++;


    shared_memory_ptr->last_update_timestamp_ns =
        get_timestamp_ns();


    pthread_mutex_unlock(
        &shared_memory_mutex);
}


/*
 * =========================================================
 * DEADLINE MISS
 * =========================================================
 */

void shared_memory_increment_deadline_miss(void)
{
    if (shared_memory_ptr == NULL)
    {
        return;
    }


    pthread_mutex_lock(
        &shared_memory_mutex);


    shared_memory_ptr->total_deadline_misses++;


    shared_memory_ptr->last_update_timestamp_ns =
        get_timestamp_ns();


    pthread_mutex_unlock(
        &shared_memory_mutex);
}


/*
 * =========================================================
 * CONTEXT SWITCH
 * =========================================================
 */

void shared_memory_increment_context_switch(void)
{
    if (shared_memory_ptr == NULL)
    {
        return;
    }


    pthread_mutex_lock(
        &shared_memory_mutex);


    shared_memory_ptr->total_context_switches++;


    shared_memory_ptr->last_update_timestamp_ns =
        get_timestamp_ns();


    pthread_mutex_unlock(
        &shared_memory_mutex);
}


/*
 * =========================================================
 * PRINT SHARED MEMORY
 * =========================================================
 */

void shared_memory_print(void)
{
    uint32_t i;


    if (shared_memory_ptr == NULL)
    {
        printf(
            "Shared memory is not initialized.\n");

        return;
    }


    pthread_mutex_lock(
        &shared_memory_mutex);


    printf("\n");
    printf("============================================\n");
    printf("          SHARED MEMORY STATUS\n");
    printf("============================================\n");


    printf(
        "Object               : %s\n",
        RTOS_SHARED_MEMORY_NAME);

    printf(
        "Version              : %u\n",
        shared_memory_ptr->version);

    printf(
        "Initialized          : %u\n",
        shared_memory_ptr->initialized);

    printf(
        "Registered tasks     : %u\n",
        shared_memory_ptr->task_count);

    printf(
        "Total events         : %llu\n",
        (unsigned long long)
            shared_memory_ptr->total_events);

    printf(
        "Deadline misses      : %llu\n",
        (unsigned long long)
            shared_memory_ptr->total_deadline_misses);

    printf(
        "Context switches     : %llu\n",
        (unsigned long long)
            shared_memory_ptr->total_context_switches);


    printf("--------------------------------------------\n");


    for (i = 0;
         i < shared_memory_ptr->task_count;
         i++)
    {
        shm_task_data_t *task =
            &shared_memory_ptr->tasks[i];


        printf(
            "Task %d\n",
            task->task_id);

        printf(
            "  Priority          : %d\n",
            task->priority);

        printf(
            "  Execution         : %llu ns\n",
            (unsigned long long)
                task->execution_time_ns);

        printf(
            "  Deadline          : %llu ns\n",
            (unsigned long long)
                task->deadline_ns);

        printf(
            "  Executions        : %llu\n",
            (unsigned long long)
                task->execution_count);

        printf(
            "  Deadline misses   : %llu\n",
            (unsigned long long)
                task->deadline_miss_count);

        printf("--------------------------------------------\n");
    }


    printf(
        "============================================\n");


    pthread_mutex_unlock(
        &shared_memory_mutex);
}


/*
 * =========================================================
 * CLOSE
 * =========================================================
 */

void shared_memory_close(void)
{
    if (shared_memory_ptr != NULL)
    {
        munmap(
            shared_memory_ptr,
            sizeof(rtos_shared_memory_t));

        shared_memory_ptr = NULL;
    }


    if (shared_memory_fd != -1)
    {
        close(
            shared_memory_fd);

        shared_memory_fd = -1;
    }


    printf(
        "Shared memory closed.\n");
}


/*
 * =========================================================
 * UNLINK
 * =========================================================
 */

void shared_memory_unlink(void)
{
    if (shm_unlink(
            RTOS_SHARED_MEMORY_NAME) == -1)
    {
        perror(
            "WARNING: shm_unlink failed");

        return;
    }


    printf(
        "Shared memory object removed: %s\n",
        RTOS_SHARED_MEMORY_NAME);
}
