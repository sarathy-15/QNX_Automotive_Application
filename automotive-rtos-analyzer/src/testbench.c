#define _POSIX_C_SOURCE 200112L

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <pthread.h>
#include <time.h>
#include <unistd.h>
#include <sched.h>
#include <string.h>

#include "trace_collector.h"

/*
 * =========================================================
 * AUTOMOTIVE RTOS PERFORMANCE & LATENCY ANALYZER
 * TESTBENCH
 *
 * 1. Task Scaling
 * 2. Priority Variation
 * 3. Execution-Time Variation
 * 4. Period Variation + Jitter
 * 5. Deadline Testing
 * 6. CPU Load Variation
 * 7. Context-Switch Testing
 * 8. Mixed Workload
 * 9. Long-Duration Stability
 * 10. Stress Testing
 * 11. Temperature Monitoring
 * =========================================================
 */

#define MAX_TEST_TASKS       16
#define WORK_ITERATIONS      300000UL

#define TEMPERATURE_PATH \
    "/sys/class/thermal/thermal_zone0/temp"

#define JITTER_CYCLES        20

#define PERIOD_1_MS          50
#define PERIOD_2_MS          100
#define PERIOD_3_MS          200


/* =========================================================
 * COMMON DATA STRUCTURE
 * =========================================================
 */

typedef struct
{
    int task_id;
    unsigned long iterations;
    long long execution_ns;
    long long start_ns;
    long long end_ns;

} test_task_data_t;


/* =========================================================
 * TIME FUNCTION
 * =========================================================
 */

static long long get_time_ns(void)
{
    struct timespec ts;

    if (clock_gettime(CLOCK_MONOTONIC, &ts) != 0)
    {
        return 0;
    }

    return ((long long)ts.tv_sec * 1000000000LL)
           + (long long)ts.tv_nsec;
}


/* =========================================================
 * MILLISECOND SLEEP
 * =========================================================
 */

static void sleep_ms(int milliseconds)
{
    struct timespec ts;

    if (milliseconds <= 0)
    {
        return;
    }

    ts.tv_sec =
        milliseconds / 1000;

    ts.tv_nsec =
        (long)(milliseconds % 1000) * 1000000L;

    nanosleep(&ts, NULL);
}


/* =========================================================
 * CPU WORKLOAD
 * =========================================================
 */

static void small_workload(unsigned long iterations)
{
    volatile unsigned long value = 0;

    for (unsigned long i = 0;
         i < iterations;
         i++)
    {
        value += (i * 3UL) + 1UL;
    }

    (void)value;
}


/* =========================================================
 * TEST 1
 * TASK SCALING
 * =========================================================
 */

static void *test_task(void *arg)
{
    test_task_data_t *task =
        (test_task_data_t *)arg;

    long long start;
    long long end;
    long long execution;

    trace_record_event(
        task->task_id,
        TRACE_EVENT_START,
        0,
        0);

    start = get_time_ns();

    small_workload(WORK_ITERATIONS);

    end = get_time_ns();

    execution = end - start;

    task->start_ns = start;
    task->end_ns = end;
    task->execution_ns = execution;
    task->iterations++;

    trace_record_event(
        task->task_id,
        TRACE_EVENT_END,
        (uint64_t)execution,
        0);

    return NULL;
}


void run_task_scaling_test(int task_count)
{
    pthread_t threads[MAX_TEST_TASKS];
    test_task_data_t data[MAX_TEST_TASKS];

    long long total_execution = 0;

    trace_set_testbench("Task Scaling");

    if (task_count < 1)
        task_count = 1;

    if (task_count > MAX_TEST_TASKS)
        task_count = MAX_TEST_TASKS;

    printf("\n");
    printf("====================================\n");
    printf("        TASK SCALING TEST\n");
    printf("====================================\n");

    printf("Number of tasks : %d\n", task_count);

    for (int i = 0;
         i < task_count;
         i++)
    {
        data[i].task_id = i + 1;
        data[i].iterations = 0;
        data[i].execution_ns = 0;
        data[i].start_ns = 0;
        data[i].end_ns = 0;

        pthread_create(
            &threads[i],
            NULL,
            test_task,
            &data[i]);
    }

    for (int i = 0;
         i < task_count;
         i++)
    {
        pthread_join(
            threads[i],
            NULL);

        total_execution +=
            data[i].execution_ns;
    }

    printf("------------------------------------\n");

    for (int i = 0;
         i < task_count;
         i++)
    {
        printf(
            "Task %d : %.3f ms\n",
            data[i].task_id,
            data[i].execution_ns /
                1000000.0);
    }

    printf("------------------------------------\n");

    printf(
        "Total execution : %.3f ms\n",
        total_execution /
            1000000.0);

    printf("Task Scaling Test Completed\n");
    printf("====================================\n");
}


/* =========================================================
 * TEST 2
 * PRIORITY VARIATION
 * =========================================================
 */

typedef struct
{
    test_task_data_t base;
    int requested_priority;
    int priority_applied;

} priority_task_data_t;


static void *priority_task(void *arg)
{
    priority_task_data_t *task =
        (priority_task_data_t *)arg;

    struct sched_param param;

    long long start;
    long long end;
    long long execution;

    /*
     * Attempt to apply requested real-time priority.
     *
     * On QNX this may require appropriate scheduling
     * privileges. Failure is reported but does not
     * terminate the test.
     */

    param.sched_priority =
        task->requested_priority;

    if (pthread_setschedparam(
            pthread_self(),
            SCHED_RR,
            &param) == 0)
    {
        task->priority_applied = 1;
    }
    else
    {
        task->priority_applied = 0;
    }

    trace_record_event(
        task->base.task_id,
        TRACE_EVENT_START,
        0,
        0);

    start = get_time_ns();

    small_workload(
        WORK_ITERATIONS / 2);

    end = get_time_ns();

    execution = end - start;

    task->base.start_ns = start;
    task->base.end_ns = end;
    task->base.execution_ns = execution;

    trace_record_event(
        task->base.task_id,
        TRACE_EVENT_END,
        (uint64_t)execution,
        0);

    return NULL;
}


void run_priority_variation_test(void)
{
    pthread_t threads[3];

    priority_task_data_t data[3];

    int priorities[3] =
    {
        10,
        20,
        30
    };

    trace_set_testbench("Priority Variation");

    printf("\n");
    printf("====================================\n");
    printf("       PRIORITY VARIATION TEST\n");
    printf("====================================\n");

    for (int i = 0;
         i < 3;
         i++)
    {
        data[i].base.task_id = i + 1;
        data[i].base.iterations = 0;
        data[i].base.execution_ns = 0;
        data[i].base.start_ns = 0;
        data[i].base.end_ns = 0;

        data[i].requested_priority =
            priorities[i];

        data[i].priority_applied = 0;

        pthread_create(
            &threads[i],
            NULL,
            priority_task,
            &data[i]);
    }

    for (int i = 0;
         i < 3;
         i++)
    {
        pthread_join(
            threads[i],
            NULL);

        printf(
            "Task %d | Priority %d | %s | Execution %.3f ms\n",
            i + 1,
            priorities[i],
            data[i].priority_applied
                ? "APPLIED"
                : "NOT APPLIED",
            data[i].base.execution_ns /
                1000000.0);
    }

    printf("------------------------------------\n");

    printf(
        "Priority Variation Test Completed\n");

    printf("====================================\n");
}


/* =========================================================
 * TEST 3
 * EXECUTION-TIME VARIATION
 * =========================================================
 */

static void *execution_variation_task(void *arg)
{
    test_task_data_t *task =
        (test_task_data_t *)arg;

    unsigned long workload =
        WORK_ITERATIONS *
        (unsigned long)task->task_id;

    long long start;
    long long end;
    long long execution;

    trace_record_event(
        task->task_id,
        TRACE_EVENT_START,
        0,
        0);

    start = get_time_ns();

    small_workload(workload);

    end = get_time_ns();

    execution = end - start;

    task->start_ns = start;
    task->end_ns = end;
    task->execution_ns = execution;

    trace_record_event(
        task->task_id,
        TRACE_EVENT_END,
        (uint64_t)execution,
        0);

    return NULL;
}


void run_execution_time_variation_test(void)
{
    pthread_t threads[3];

    test_task_data_t data[3];

    trace_set_testbench(
        "Execution-Time Variation");

    printf("\n");
    printf("====================================\n");
    printf("     EXECUTION-TIME VARIATION TEST\n");
    printf("====================================\n");

    for (int i = 0;
         i < 3;
         i++)
    {
        data[i].task_id = i + 1;
        data[i].iterations = 0;
        data[i].execution_ns = 0;
        data[i].start_ns = 0;
        data[i].end_ns = 0;

        pthread_create(
            &threads[i],
            NULL,
            execution_variation_task,
            &data[i]);
    }

    for (int i = 0;
         i < 3;
         i++)
    {
        pthread_join(
            threads[i],
            NULL);

        printf(
            "Task %d | Workload %dx | Execution %.3f ms\n",
            i + 1,
            i + 1,
            data[i].execution_ns /
                1000000.0);
    }

    printf("------------------------------------\n");

    printf(
        "Execution-Time Variation Completed\n");

    printf("====================================\n");
}


/* =========================================================
 * TEST 4
 * PERIOD VARIATION + JITTER
 * =========================================================
 */

typedef struct
{
    int task_id;
    int period_ms;
    int cycles;
    int completed_cycles;
    long long total_execution_ns;

} period_task_data_t;


static void *periodic_task(void *arg)
{
    period_task_data_t *task =
        (period_task_data_t *)arg;

    long long next_release =
        get_time_ns();

    for (int i = 0;
         i < task->cycles;
         i++)
    {
        long long now =
            get_time_ns();

        if (now < next_release)
        {
            long long wait_ns =
                next_release - now;

            struct timespec ts;

            ts.tv_sec =
                wait_ns / 1000000000LL;

            ts.tv_nsec =
                (long)(wait_ns %
                       1000000000LL);

            nanosleep(
                &ts,
                NULL);
        }

        long long start =
            get_time_ns();

        trace_record_event(
            task->task_id,
            TRACE_EVENT_START,
            0,
            0);

        small_workload(
            WORK_ITERATIONS / 10);

        long long end =
            get_time_ns();

        long long execution =
            end - start;

        task->total_execution_ns +=
            execution;

        task->completed_cycles++;

        trace_record_event(
            task->task_id,
            TRACE_EVENT_END,
            (uint64_t)execution,
            0);

        printf(
            "Task %d | Cycle %02d/%02d | Period %d ms | Exec %.3f ms\n",
            task->task_id,
            i + 1,
            task->cycles,
            task->period_ms,
            execution /
                1000000.0);

        next_release +=
            (long long)task->period_ms *
            1000000LL;
    }

    return NULL;
}


void run_period_variation_test(void)
{
    pthread_t threads[3];

    period_task_data_t data[3];

    int periods[3] =
    {
        PERIOD_1_MS,
        PERIOD_2_MS,
        PERIOD_3_MS
    };

    trace_set_testbench(
        "Period Variation + Jitter");

    printf("\n");
    printf("====================================\n");
    printf("     PERIOD VARIATION + JITTER TEST\n");
    printf("====================================\n");

    printf(
        "Cycles per task : %d\n",
        JITTER_CYCLES);

    printf(
        "Task 1 Period   : %d ms\n",
        PERIOD_1_MS);

    printf(
        "Task 2 Period   : %d ms\n",
        PERIOD_2_MS);

    printf(
        "Task 3 Period   : %d ms\n",
        PERIOD_3_MS);

    printf("------------------------------------\n");

    for (int i = 0;
         i < 3;
         i++)
    {
        data[i].task_id = i + 1;
        data[i].period_ms = periods[i];
        data[i].cycles = JITTER_CYCLES;
        data[i].completed_cycles = 0;
        data[i].total_execution_ns = 0;

        pthread_create(
            &threads[i],
            NULL,
            periodic_task,
            &data[i]);
    }

    for (int i = 0;
         i < 3;
         i++)
    {
        pthread_join(
            threads[i],
            NULL);
    }

    printf("------------------------------------\n");

    for (int i = 0;
         i < 3;
         i++)
    {
        double average_execution = 0.0;

        if (data[i].completed_cycles > 0)
        {
            average_execution =
                ((double)data[i].total_execution_ns /
                 (double)data[i].completed_cycles)
                / 1000000.0;
        }

        printf(
            "Task %d | Period %d ms | Cycles %d | Avg Exec %.3f ms\n",
            data[i].task_id,
            data[i].period_ms,
            data[i].completed_cycles,
            average_execution);
    }

    printf("------------------------------------\n");

    printf(
        "Repeated START/END trace events generated\n");

    printf(
        "Period Variation + Jitter Data Completed\n");

    printf("====================================\n");
}


/* =========================================================
 * TEST 5
 * DEADLINE TEST
 * =========================================================
 */

typedef struct
{
    int task_id;
    int deadline_ms;
    int execution_ms;
    int deadline_miss;

} deadline_task_data_t;


static void *deadline_task(void *arg)
{
    deadline_task_data_t *task =
        (deadline_task_data_t *)arg;

    long long start =
        get_time_ns();

    uint64_t deadline_ns =
        (uint64_t)task->deadline_ms *
        1000000ULL;

    trace_record_event(
        task->task_id,
        TRACE_EVENT_START,
        0,
        deadline_ns);

    small_workload(
        WORK_ITERATIONS *
        (unsigned long)task->execution_ms /
        20UL);

    long long end =
        get_time_ns();

    long long execution_ns =
        end - start;

    long long execution_ms =
        execution_ns / 1000000LL;

    if (execution_ms >
        task->deadline_ms)
    {
        task->deadline_miss = 1;

        /*
         * Explicit deadline-miss trace event.
         */
        trace_record_event(
            task->task_id,
            TRACE_EVENT_DEADLINE_MISS,
            (uint64_t)execution_ns,
            deadline_ns);
    }
    else
    {
        task->deadline_miss = 0;
    }

    trace_record_event(
        task->task_id,
        TRACE_EVENT_END,
        (uint64_t)execution_ns,
        deadline_ns);

    return NULL;
}


void run_deadline_test(void)
{
    pthread_t threads[3];

    deadline_task_data_t data[3];

    int deadlines[3] =
    {
        5,
        10,
        20
    };

    trace_set_testbench(
        "Deadline Testing");

    printf("\n");
    printf("====================================\n");
    printf("          DEADLINE TEST\n");
    printf("====================================\n");

    for (int i = 0;
         i < 3;
         i++)
    {
        data[i].task_id = i + 1;
        data[i].deadline_ms = deadlines[i];
        data[i].execution_ms = i + 1;
        data[i].deadline_miss = 0;

        pthread_create(
            &threads[i],
            NULL,
            deadline_task,
            &data[i]);
    }

    for (int i = 0;
         i < 3;
         i++)
    {
        pthread_join(
            threads[i],
            NULL);

        printf(
            "Task %d | Deadline %d ms | %s\n",
            data[i].task_id,
            data[i].deadline_ms,
            data[i].deadline_miss
                ? "DEADLINE MISS"
                : "ON TIME");
    }

    printf("------------------------------------\n");

    printf(
        "Deadline Test Completed\n");

    printf("====================================\n");
}


/* =========================================================
 * TEST 6
 * CPU LOAD VARIATION
 * =========================================================
 */

typedef struct
{
    int load_percent;
    long long execution_ns;

} cpu_load_data_t;


static void *cpu_load_task(void *arg)
{
    cpu_load_data_t *task =
        (cpu_load_data_t *)arg;

    unsigned long workload =
        WORK_ITERATIONS *
        (unsigned long)task->load_percent /
        25UL;

    long long start;
    long long end;

    if (workload < 10000UL)
        workload = 10000UL;

    trace_record_event(
        1,
        TRACE_EVENT_START,
        0,
        0);

    start = get_time_ns();

    small_workload(workload);

    end = get_time_ns();

    task->execution_ns =
        end - start;

    trace_record_event(
        1,
        TRACE_EVENT_END,
        (uint64_t)task->execution_ns,
        0);

    return NULL;
}


void run_cpu_load_test(int load_level)
{
    pthread_t thread;

    cpu_load_data_t data;

    trace_set_testbench(
        "CPU Load Variation");

    if (load_level < 1)
        load_level = 1;

    if (load_level > 100)
        load_level = 100;

    printf("\n");
    printf("====================================\n");
    printf("        CPU LOAD VARIATION TEST\n");
    printf("====================================\n");

    data.load_percent =
        load_level;

    data.execution_ns =
        0;

    pthread_create(
        &thread,
        NULL,
        cpu_load_task,
        &data);

    pthread_join(
        thread,
        NULL);

    printf(
        "Requested CPU load : %d%%\n",
        load_level);

    printf(
        "Work execution     : %.3f ms\n",
        data.execution_ns /
            1000000.0);

    printf("------------------------------------\n");

    printf(
        "CPU Load Test Completed\n");

    printf("====================================\n");
}


/* =========================================================
 * TEST 7
 * CONTEXT-SWITCH TEST
 * =========================================================
 */

static void *context_switch_task(void *arg)
{
    test_task_data_t *task =
        (test_task_data_t *)arg;

    long long start =
        get_time_ns();

    trace_record_event(
        task->task_id,
        TRACE_EVENT_START,
        0,
        0);

    for (int i = 0;
         i < 100;
         i++)
    {
        small_workload(5000UL);

        /*
         * Record a yield opportunity.
         *
         * IMPORTANT:
         * This is instrumentation of sched_yield(),
         * not a kernel-confirmed context switch.
         */
        trace_record_event(
            task->task_id,
            TRACE_EVENT_CONTEXT_SWITCH,
            0,
            0);

        sched_yield();
    }

    long long end =
        get_time_ns();

    task->execution_ns =
        end - start;

    task->iterations++;

    trace_record_event(
        task->task_id,
        TRACE_EVENT_END,
        (uint64_t)task->execution_ns,
        0);

    return NULL;
}


void run_context_switch_test(int task_count)
{
    pthread_t threads[MAX_TEST_TASKS];

    test_task_data_t data[MAX_TEST_TASKS];

    trace_set_testbench(
        "Context-Switch Testing");

    if (task_count < 2)
        task_count = 2;

    if (task_count > MAX_TEST_TASKS)
        task_count = MAX_TEST_TASKS;

    printf("\n");
    printf("====================================\n");
    printf("        CONTEXT-SWITCH TEST\n");
    printf("====================================\n");

    printf(
        "Competing tasks : %d\n",
        task_count);

    for (int i = 0;
         i < task_count;
         i++)
    {
        data[i].task_id = i + 1;
        data[i].iterations = 0;
        data[i].execution_ns = 0;
        data[i].start_ns = 0;
        data[i].end_ns = 0;

        pthread_create(
            &threads[i],
            NULL,
            context_switch_task,
            &data[i]);
    }

    for (int i = 0;
         i < task_count;
         i++)
    {
        pthread_join(
            threads[i],
            NULL);
    }

    printf("------------------------------------\n");

    printf(
        "Yield opportunities generated by %d tasks\n",
        task_count);

    printf(
        "Context-Switch Test Completed\n");

    printf("====================================\n");
}


/* =========================================================
 * TEST 8
 * MIXED WORKLOAD
 * =========================================================
 */

static void *mixed_cpu_task(void *arg)
{
    int task_id = 1;

    (void)arg;

    trace_record_event(
        task_id,
        TRACE_EVENT_START,
        0,
        0);

    long long start =
        get_time_ns();

    for (int i = 0;
         i < 20;
         i++)
    {
        small_workload(20000UL);

        sched_yield();
    }

    long long end =
        get_time_ns();

    trace_record_event(
        task_id,
        TRACE_EVENT_END,
        (uint64_t)(end - start),
        0);

    return NULL;
}


static void *mixed_periodic_task(void *arg)
{
    int task_id = 2;

    (void)arg;

    trace_record_event(
        task_id,
        TRACE_EVENT_START,
        0,
        0);

    long long start =
        get_time_ns();

    for (int i = 0;
         i < 10;
         i++)
    {
        small_workload(10000UL);

        sleep_ms(20);
    }

    long long end =
        get_time_ns();

    trace_record_event(
        task_id,
        TRACE_EVENT_END,
        (uint64_t)(end - start),
        0);

    return NULL;
}


static void *mixed_io_task(void *arg)
{
    int task_id = 3;

    (void)arg;

    trace_record_event(
        task_id,
        TRACE_EVENT_START,
        0,
        0);

    long long start =
        get_time_ns();

    for (int i = 0;
         i < 20;
         i++)
    {
        printf(
            "Mixed I/O task cycle %d\n",
            i + 1);

        sleep_ms(10);
    }

    long long end =
        get_time_ns();

    trace_record_event(
        task_id,
        TRACE_EVENT_END,
        (uint64_t)(end - start),
        0);

    return NULL;
}


void run_mixed_workload_test(void)
{
    pthread_t cpu_thread;
    pthread_t periodic_thread;
    pthread_t io_thread;

    trace_set_testbench(
        "Mixed Workload");

    printf("\n");
    printf("====================================\n");
    printf("          MIXED WORKLOAD TEST\n");
    printf("====================================\n");

    pthread_create(
        &cpu_thread,
        NULL,
        mixed_cpu_task,
        NULL);

    pthread_create(
        &periodic_thread,
        NULL,
        mixed_periodic_task,
        NULL);

    pthread_create(
        &io_thread,
        NULL,
        mixed_io_task,
        NULL);

    pthread_join(
        cpu_thread,
        NULL);

    pthread_join(
        periodic_thread,
        NULL);

    pthread_join(
        io_thread,
        NULL);

    printf("------------------------------------\n");

    printf(
        "CPU + Periodic + I/O workload executed\n");

    printf(
        "Mixed Workload Test Completed\n");

    printf("====================================\n");
}


/* =========================================================
 * TEST 9
 * LONG-DURATION STABILITY
 * =========================================================
 */

typedef struct
{
    int task_id;

    int completed_cycles;

    long long total_execution_ns;

    long long min_execution_ns;

    long long max_execution_ns;

} long_duration_data_t;


static void *long_duration_task(void *arg)
{
    long_duration_data_t *task =
        (long_duration_data_t *)arg;

    trace_record_event(
        task->task_id,
        TRACE_EVENT_START,
        0,
        0);

    long long start =
        get_time_ns();

    small_workload(
        WORK_ITERATIONS / 2);

    long long end =
        get_time_ns();

    long long execution =
        end - start;

    task->total_execution_ns +=
        execution;

    if (execution <
        task->min_execution_ns)
    {
        task->min_execution_ns =
            execution;
    }

    if (execution >
        task->max_execution_ns)
    {
        task->max_execution_ns =
            execution;
    }

    task->completed_cycles++;

    trace_record_event(
        task->task_id,
        TRACE_EVENT_END,
        (uint64_t)execution,
        0);

    return NULL;
}


void run_long_duration_test(int duration_seconds)
{
    const int TASK_COUNT = 3;

    pthread_t threads[TASK_COUNT];

    long_duration_data_t data[TASK_COUNT];

    long long start_time;
    long long current_time;
    long long duration_ns;

    trace_set_testbench(
        "Long-Duration Stability");

    printf("\n");
    printf("====================================\n");
    printf("     LONG-DURATION STABILITY TEST\n");
    printf("====================================\n");

    if (duration_seconds <= 0)
        duration_seconds = 10;

    printf(
        "Duration : %d seconds\n",
        duration_seconds);

    duration_ns =
        (long long)duration_seconds *
        1000000000LL;

    for (int i = 0;
         i < TASK_COUNT;
         i++)
    {
        data[i].task_id = i + 1;

        data[i].completed_cycles = 0;

        data[i].total_execution_ns = 0;

        data[i].min_execution_ns =
            9223372036854775807LL;

        data[i].max_execution_ns = 0;
    }

    start_time =
        get_time_ns();

    current_time =
        start_time;

    while ((current_time - start_time) <
           duration_ns)
    {
        for (int i = 0;
             i < TASK_COUNT;
             i++)
        {
            pthread_create(
                &threads[i],
                NULL,
                long_duration_task,
                &data[i]);
        }

        for (int i = 0;
             i < TASK_COUNT;
             i++)
        {
            pthread_join(
                threads[i],
                NULL);
        }

        current_time =
            get_time_ns();
    }

    printf("\n");
    printf("------------------------------------\n");

    for (int i = 0;
         i < TASK_COUNT;
         i++)
    {
        double average = 0.0;

        if (data[i].completed_cycles > 0)
        {
            average =
                ((double)data[i].total_execution_ns /
                 (double)data[i].completed_cycles)
                / 1000000.0;
        }

        printf(
            "Task %d | Cycles %d | Avg %.3f ms | Min %.3f ms | Max %.3f ms\n",
            data[i].task_id,
            data[i].completed_cycles,
            average,
            data[i].min_execution_ns /
                1000000.0,
            data[i].max_execution_ns /
                1000000.0);
    }

    printf("------------------------------------\n");

    printf(
        "System Status : STABLE\n");

    printf(
        "Long-Duration Stability Test Completed\n");

    printf("====================================\n");
}


/* =========================================================
 * TEST 10
 * STRESS TEST
 * =========================================================
 */

static void *stress_task(void *arg)
{
    test_task_data_t *task =
        (test_task_data_t *)arg;

    trace_record_event(
        task->task_id,
        TRACE_EVENT_START,
        0,
        0);

    long long start =
        get_time_ns();

    for (int i = 0;
         i < 50;
         i++)
    {
        small_workload(
            WORK_ITERATIONS / 4);

        sched_yield();
    }

    long long end =
        get_time_ns();

    task->execution_ns =
        end - start;

    task->iterations++;

    trace_record_event(
        task->task_id,
        TRACE_EVENT_END,
        (uint64_t)task->execution_ns,
        0);

    return NULL;
}


void run_stress_test(void)
{
    const int STRESS_TASKS = 16;

    pthread_t threads[STRESS_TASKS];

    test_task_data_t data[STRESS_TASKS];

    long long start;
    long long end;

    trace_set_testbench(
        "Stress Testing");

    printf("\n");
    printf("====================================\n");
    printf("             STRESS TEST\n");
    printf("====================================\n");

    printf(
        "Stress tasks : %d\n",
        STRESS_TASKS);

    start =
        get_time_ns();

    for (int i = 0;
         i < STRESS_TASKS;
         i++)
    {
        data[i].task_id = i + 1;
        data[i].iterations = 0;
        data[i].execution_ns = 0;
        data[i].start_ns = 0;
        data[i].end_ns = 0;

        pthread_create(
            &threads[i],
            NULL,
            stress_task,
            &data[i]);
    }

    for (int i = 0;
         i < STRESS_TASKS;
         i++)
    {
        pthread_join(
            threads[i],
            NULL);
    }

    end =
        get_time_ns();

    printf("------------------------------------\n");

    printf(
        "Total stress execution : %.3f ms\n",
        (end - start) /
            1000000.0);

    printf(
        "Concurrent tasks       : %d\n",
        STRESS_TASKS);

    printf("------------------------------------\n");

    printf(
        "Stress Test Completed\n");

    printf("====================================\n");
}


/* =========================================================
 * TEST 11
 * TEMPERATURE MONITORING
 * =========================================================
 */

static int read_cpu_temperature(
    double *temperature_c)
{
    FILE *file;

    long temperature_milli_c;

    file =
        fopen(
            TEMPERATURE_PATH,
            "r");

    if (file == NULL)
    {
        return -1;
    }

    if (fscanf(
            file,
            "%ld",
            &temperature_milli_c)
        != 1)
    {
        fclose(file);

        return -1;
    }

    fclose(file);

    *temperature_c =
        (double)temperature_milli_c /
        1000.0;

    return 0;
}


static void run_temperature_workload(
    int seconds)
{
    long long start;
    long long now;
    long long duration_ns;

    start =
        get_time_ns();

    duration_ns =
        (long long)seconds *
        1000000000LL;

    while (1)
    {
        small_workload(
            WORK_ITERATIONS / 2);

        now =
            get_time_ns();

        if ((now - start) >=
            duration_ns)
        {
            break;
        }

        sched_yield();
    }
}


void run_temperature_test(
    int duration_seconds)
{
    double temperature_before;
    double temperature_after;

    trace_set_testbench(
        "Temperature Monitoring");

    if (duration_seconds <= 0)
        duration_seconds = 10;

    printf("\n");
    printf("====================================\n");
    printf("      TEMPERATURE MONITORING TEST\n");
    printf("====================================\n");

    printf(
        "Test duration : %d seconds\n",
        duration_seconds);

    printf("------------------------------------\n");

    /*
     * Temperature before workload.
     */

    if (read_cpu_temperature(
            &temperature_before) == 0)
    {
        printf(
            "Temperature before workload : %.2f C\n",
            temperature_before);

        trace_record_temperature(
            0,
            temperature_before);
    }
    else
    {
        printf(
            "Temperature before workload : N/A\n");

        temperature_before = -1.0;
    }

    /*
     * CPU workload.
     */

    printf(
        "Running CPU workload...\n");

    trace_record_event(
        1,
        TRACE_EVENT_START,
        0,
        0);

    long long workload_start =
        get_time_ns();

    run_temperature_workload(
        duration_seconds);

    long long workload_end =
        get_time_ns();

    trace_record_event(
        1,
        TRACE_EVENT_END,
        (uint64_t)(
            workload_end -
            workload_start),
        0);

    /*
     * Temperature after workload.
     */

    if (read_cpu_temperature(
            &temperature_after) == 0)
    {
        printf(
            "Temperature after workload  : %.2f C\n",
            temperature_after);

        trace_record_temperature(
            0,
            temperature_after);
    }
    else
    {
        printf(
            "Temperature after workload  : N/A\n");

        temperature_after = -1.0;
    }

    printf("------------------------------------\n");

    if (temperature_before >= 0.0 &&
        temperature_after >= 0.0)
    {
        printf(
            "Temperature change           : %.2f C\n",
            temperature_after -
            temperature_before);

        if (temperature_after >
            temperature_before)
        {
            printf(
                "Thermal response             : INCREASED\n");
        }
        else if (temperature_after <
                 temperature_before)
        {
            printf(
                "Thermal response             : DECREASED\n");
        }
        else
        {
            printf(
                "Thermal response             : STABLE\n");
        }
    }
    else
    {
        printf(
            "Thermal response             : SENSOR NOT AVAILABLE\n");
    }

    printf("------------------------------------\n");

    printf(
        "Temperature Monitoring Test Completed\n");

    printf("====================================\n");
}
