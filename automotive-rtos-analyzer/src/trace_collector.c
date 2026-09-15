#define _POSIX_C_SOURCE 200112L

#include "trace_collector.h"

#include <stdio.h>
#include <stdint.h>
#include <stddef.h>
#include <string.h>
#include <time.h>
#include <pthread.h>


/* =========================================================
 * TRACE STORAGE
 * =========================================================
 */

static trace_record_t
trace_records[MAX_TRACE_RECORDS];

static size_t
trace_record_count = 0;


/*
 * Multiple test threads can generate trace events
 * simultaneously, so protect the trace buffer.
 */
static pthread_mutex_t trace_mutex =
    PTHREAD_MUTEX_INITIALIZER;


/*
 * Current testbench name.
 */
static char current_testbench[
    TRACE_TESTBENCH_NAME_LEN] =
    "UNSPECIFIED";


/* =========================================================
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
        ((uint64_t)ts.tv_sec *
         1000000000ULL)
        +
        (uint64_t)ts.tv_nsec;
}


/* =========================================================
 * EVENT NAME
 * =========================================================
 */

static const char *get_event_name(
    trace_event_type_t event_type)
{
    switch (event_type)
    {
        case TRACE_EVENT_START:
            return "START";

        case TRACE_EVENT_END:
            return "END";

        case TRACE_EVENT_DEADLINE_MISS:
            return "DEADLINE_MISS";

        case TRACE_EVENT_CONTEXT_SWITCH:
            return "CONTEXT_SWITCH";

        case TRACE_EVENT_TEMPERATURE:
            return "TEMPERATURE";

        default:
            return "UNKNOWN";
    }
}


/* =========================================================
 * INITIALIZATION
 * =========================================================
 */

void trace_collector_init(void)
{
    pthread_mutex_lock(&trace_mutex);

    trace_record_count = 0;

    strncpy(
        current_testbench,
        "UNSPECIFIED",
        TRACE_TESTBENCH_NAME_LEN - 1);

    current_testbench[
        TRACE_TESTBENCH_NAME_LEN - 1] =
        '\0';

    pthread_mutex_unlock(&trace_mutex);

    printf("\n");
    printf("============================================\n");
    printf("          TRACE COLLECTOR INIT\n");
    printf("============================================\n");
    printf(
        "Maximum records : %d\n",
        MAX_TRACE_RECORDS);
    printf(
        "Current records : %zu\n",
        trace_record_count);
    printf(
        "Collector status: READY\n");
    printf("============================================\n");
}


/* =========================================================
 * TESTBENCH NAME
 * =========================================================
 */

void trace_set_testbench(
    const char *testbench_name)
{
    pthread_mutex_lock(&trace_mutex);

    if (testbench_name == NULL ||
        testbench_name[0] == '\0')
    {
        strncpy(
            current_testbench,
            "UNSPECIFIED",
            TRACE_TESTBENCH_NAME_LEN - 1);
    }
    else
    {
        strncpy(
            current_testbench,
            testbench_name,
            TRACE_TESTBENCH_NAME_LEN - 1);
    }

    current_testbench[
        TRACE_TESTBENCH_NAME_LEN - 1] =
        '\0';

    pthread_mutex_unlock(&trace_mutex);
}


const char *trace_get_testbench(void)
{
    return current_testbench;
}


/* =========================================================
 * INTERNAL RECORD FUNCTION
 * =========================================================
 */

static int store_record(
    int task_id,
    trace_event_type_t event_type,
    uint64_t execution_time_ns,
    uint64_t deadline_ns,
    double temperature_c)
{
    trace_record_t *record;

    pthread_mutex_lock(&trace_mutex);

    /*
     * Prevent buffer overflow.
     */
    if (trace_record_count >=
        MAX_TRACE_RECORDS)
    {
        pthread_mutex_unlock(&trace_mutex);

        printf(
            "WARNING: TRACE BUFFER FULL - "
            "EVENT DROPPED\n");

        return -1;
    }

    record =
        &trace_records[
            trace_record_count];

    /*
     * Timestamp.
     */
    record->timestamp_ns =
        get_timestamp_ns();

    /*
     * Testbench.
     */
    strncpy(
        record->testbench,
        current_testbench,
        TRACE_TESTBENCH_NAME_LEN - 1);

    record->testbench[
        TRACE_TESTBENCH_NAME_LEN - 1] =
        '\0';

    /*
     * Task.
     */
    record->task_id =
        task_id;

    /*
     * Event.
     */
    record->event_type =
        event_type;

    /*
     * Execution time.
     */
    record->execution_time_ns =
        execution_time_ns;

    /*
     * Deadline.
     */
    record->deadline_ns =
        deadline_ns;

    /*
     * Temperature.
     */
    record->temperature_c =
        temperature_c;

    /*
     * Increase record count.
     */
    trace_record_count++;

    pthread_mutex_unlock(&trace_mutex);

    return 0;
}


/* =========================================================
 * NORMAL EVENT
 * =========================================================
 */

int trace_record_event(
    int task_id,
    trace_event_type_t event_type,
    uint64_t execution_time_ns,
    uint64_t deadline_ns)
{
    return store_record(
        task_id,
        event_type,
        execution_time_ns,
        deadline_ns,
        0.0);
}


/* =========================================================
 * TEMPERATURE EVENT
 * =========================================================
 */

int trace_record_temperature(
    int task_id,
    double temperature_c)
{
    return store_record(
        task_id,
        TRACE_EVENT_TEMPERATURE,
        0,
        0,
        temperature_c);
}


/* =========================================================
 * RECORD COUNT
 * =========================================================
 */

size_t trace_get_record_count(void)
{
    size_t count;

    pthread_mutex_lock(&trace_mutex);

    count =
        trace_record_count;

    pthread_mutex_unlock(&trace_mutex);

    return count;
}


/* =========================================================
 * RECORD ACCESS
 * =========================================================
 */

const trace_record_t *
trace_get_records(void)
{
    return trace_records;
}


/* =========================================================
 * CLEAR TRACE
 * =========================================================
 */

void trace_collector_clear(void)
{
    pthread_mutex_lock(&trace_mutex);

    trace_record_count = 0;

    pthread_mutex_unlock(&trace_mutex);

    printf(
        "Trace buffer cleared.\n");
}


/* =========================================================
 * PRINT TRACE
 * =========================================================
 */

void trace_collector_print(void)
{
    size_t i;

    pthread_mutex_lock(&trace_mutex);

    printf("\n");
    printf("============================================\n");
    printf("             TRACE RECORDS\n");
    printf("============================================\n");

    printf(
        "Total records: %zu\n",
        trace_record_count);

    printf("--------------------------------------------\n");

    for (i = 0;
         i < trace_record_count;
         i++)
    {
        const trace_record_t *record =
            &trace_records[i];

        printf(
            "Record %zu\n",
            i + 1);

        printf(
            "  Testbench     : %s\n",
            record->testbench);

        printf(
            "  Task ID       : %d\n",
            record->task_id);

        printf(
            "  Event         : %s\n",
            get_event_name(
                record->event_type));

        printf(
            "  Timestamp     : %llu ns\n",
            (unsigned long long)
                record->timestamp_ns);

        printf(
            "  Execution     : %llu ns\n",
            (unsigned long long)
                record->execution_time_ns);

        printf(
            "  Deadline      : %llu ns\n",
            (unsigned long long)
                record->deadline_ns);

        if (record->event_type ==
            TRACE_EVENT_TEMPERATURE)
        {
            printf(
                "  Temperature   : %.2f C\n",
                record->temperature_c);
        }

        printf(
            "--------------------------------------------\n");
    }

    printf(
        "============================================\n");

    pthread_mutex_unlock(&trace_mutex);
}


/* =========================================================
 * CSV EXPORT
 * =========================================================
 */

int trace_collector_export_csv(
    const char *filename)
{
    FILE *file;
    size_t i;

    if (filename == NULL)
        return -1;

    file = fopen(
        filename,
        "w");

    if (file == NULL)
    {
        printf(
            "ERROR: Cannot create %s\n",
            filename);

        return -1;
    }

    pthread_mutex_lock(&trace_mutex);

    /*
     * NEW CSV HEADER
     */
    fprintf(
        file,
        "timestamp_ns,"
        "testbench,"
        "task_id,"
        "event,"
        "execution_time_ns,"
        "deadline_ns,"
        "temperature_c\n");

    /*
     * Write records.
     */
    for (i = 0;
         i < trace_record_count;
         i++)
    {
        const trace_record_t *record =
            &trace_records[i];

        fprintf(
            file,
            "%llu,%s,%d,%s,%llu,%llu,%.3f\n",

            (unsigned long long)
                record->timestamp_ns,

            record->testbench,

            record->task_id,

            get_event_name(
                record->event_type),

            (unsigned long long)
                record->execution_time_ns,

            (unsigned long long)
                record->deadline_ns,

            record->temperature_c);
    }

    pthread_mutex_unlock(&trace_mutex);

    fclose(file);

    printf("\n");
    printf("============================================\n");
    printf("          TRACE EXPORT COMPLETE\n");
    printf("============================================\n");

    printf(
        "File    : %s\n",
        filename);

    printf(
        "Records : %zu\n",
        trace_record_count);

    printf(
        "============================================\n");

    return 0;
}
