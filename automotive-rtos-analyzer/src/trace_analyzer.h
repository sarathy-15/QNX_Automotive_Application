#ifndef TRACE_ANALYZER_H
#define TRACE_ANALYZER_H

#include <stddef.h>
#include <stdint.h>

#include "trace_collector.h"


/* =========================================================
 * TRACE ANALYSIS RESULT
 * ========================================================= */

typedef struct
{
    /* Basic trace information */

    size_t total_records;

    size_t start_events;

    size_t end_events;

    size_t deadline_misses;

    size_t context_switches;


    /* Execution-time statistics */

    uint64_t total_execution_time_ns;

    uint64_t minimum_execution_time_ns;

    uint64_t maximum_execution_time_ns;

    double average_execution_time_ns;


    /* Latency statistics */

    uint64_t minimum_latency_ns;

    uint64_t maximum_latency_ns;

    double average_latency_ns;


    /* Jitter statistics */

    uint64_t minimum_jitter_ns;

    uint64_t maximum_jitter_ns;

    double average_jitter_ns;


    /* Number of completed task pairs */

    size_t completed_tasks;

} trace_analysis_result_t;


/* =========================================================
 * FUNCTIONS
 * ========================================================= */

void trace_analyzer_init(void);


int trace_analyze(
    trace_analysis_result_t *result);


void trace_analysis_print(
    const trace_analysis_result_t *result);


#endif
