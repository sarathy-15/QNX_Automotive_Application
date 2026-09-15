#ifndef TRACE_COLLECTOR_H
#define TRACE_COLLECTOR_H

#include <stdint.h>
#include <stddef.h>

/*
 * =========================================================
 * AUTOMOTIVE RTOS PERFORMANCE & LATENCY ANALYZER
 *
 * TRACE COLLECTOR
 * Phase 5.3.1 - Instrumentation Upgrade
 * =========================================================
 */

/*
 * Increased because Long-Duration and Context-Switch
 * tests can generate many trace records.
 */
#define MAX_TRACE_RECORDS 100000

/*
 * Maximum testbench-name length.
 */
#define TRACE_TESTBENCH_NAME_LEN 64


/* =========================================================
 * TRACE EVENT TYPES
 * =========================================================
 */

typedef enum
{
    TRACE_EVENT_START = 0,

    TRACE_EVENT_END,

    TRACE_EVENT_DEADLINE_MISS,

    TRACE_EVENT_CONTEXT_SWITCH,

    TRACE_EVENT_TEMPERATURE

} trace_event_type_t;


/* =========================================================
 * TRACE RECORD
 * =========================================================
 */

typedef struct
{
    /*
     * Monotonic timestamp.
     */
    uint64_t timestamp_ns;

    /*
     * Testbench that generated this event.
     *
     * Example:
     * Task Scaling
     * Deadline Testing
     * Stress Testing
     */
    char testbench[
        TRACE_TESTBENCH_NAME_LEN];

    /*
     * Task identifier.
     */
    int task_id;

    /*
     * Event type.
     */
    trace_event_type_t event_type;

    /*
     * Execution time when applicable.
     */
    uint64_t execution_time_ns;

    /*
     * Deadline when applicable.
     */
    uint64_t deadline_ns;

    /*
     * CPU temperature in degrees Celsius.
     *
     * Used only for:
     * TRACE_EVENT_TEMPERATURE
     */
    double temperature_c;

} trace_record_t;


/* =========================================================
 * INITIALIZATION
 * =========================================================
 */

void trace_collector_init(void);


/* =========================================================
 * TESTBENCH IDENTIFICATION
 * =========================================================
 */

/*
 * Set the currently running testbench.
 *
 * Every event recorded after this call automatically
 * receives this testbench name.
 */
void trace_set_testbench(
    const char *testbench_name);


/*
 * Return currently selected testbench.
 */
const char *trace_get_testbench(void);


/* =========================================================
 * NORMAL EVENT RECORDING
 * =========================================================
 */

int trace_record_event(
    int task_id,
    trace_event_type_t event_type,
    uint64_t execution_time_ns,
    uint64_t deadline_ns);


/* =========================================================
 * TEMPERATURE EVENT RECORDING
 * =========================================================
 */

int trace_record_temperature(
    int task_id,
    double temperature_c);


/* =========================================================
 * TRACE ACCESS
 * =========================================================
 */

size_t trace_get_record_count(void);

const trace_record_t *
trace_get_records(void);


/* =========================================================
 * TRACE BUFFER MANAGEMENT
 * =========================================================
 */

void trace_collector_clear(void);


/* =========================================================
 * TRACE DISPLAY
 * =========================================================
 */

void trace_collector_print(void);


/* =========================================================
 * CSV EXPORT
 * =========================================================
 */

int trace_collector_export_csv(
    const char *filename);


#endif
