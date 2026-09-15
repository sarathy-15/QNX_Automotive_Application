/*
 * =========================================================
 * AUTOMOTIVE RTOS PERFORMANCE ANALYZER
 *
 * TRACE ANALYZER
 *
 * Phase 3.9
 * Latency and Jitter Calculation
 * =========================================================
 */

#include "trace_analyzer.h"

#include <stdio.h>
#include <stdint.h>
#include <stddef.h>


/* =========================================================
 * INITIALIZATION
 * ========================================================= */

void trace_analyzer_init(void)
{
    printf("\n");

    printf("============================================\n");
    printf("           TRACE ANALYZER INIT\n");
    printf("============================================\n");

    printf("Analyzer status: READY\n");

    printf("============================================\n");
}


/* =========================================================
 * TRACE ANALYSIS
 * ========================================================= */

int trace_analyze(
    trace_analysis_result_t *result)
{
    const trace_record_t *records;

    size_t count;
    size_t i;

    uint64_t previous_execution_time = 0;

    uint64_t total_jitter = 0;

    size_t jitter_count = 0;

    size_t execution_count = 0;


    /*
     * Validate result pointer.
     */

    if (result == NULL)
    {
        return -1;
    }


    /*
     * Clear all results.
     */

    result->total_records = 0;

    result->start_events = 0;

    result->end_events = 0;

    result->deadline_misses = 0;

    result->context_switches = 0;


    result->total_execution_time_ns = 0;

    result->minimum_execution_time_ns = 0;

    result->maximum_execution_time_ns = 0;

    result->average_execution_time_ns = 0.0;


    result->minimum_latency_ns = 0;

    result->maximum_latency_ns = 0;

    result->average_latency_ns = 0.0;


    result->minimum_jitter_ns = 0;

    result->maximum_jitter_ns = 0;

    result->average_jitter_ns = 0.0;


    result->completed_tasks = 0;


    /*
     * Get trace records.
     */

    records =
        trace_get_records();

    count =
        trace_get_record_count();


    result->total_records =
        count;


    /*
     * No records.
     */

    if (records == NULL || count == 0)
    {
        return 0;
    }


    /* =====================================================
     * ANALYZE RECORDS
     * ===================================================== */

    for (i = 0;
         i < count;
         i++)
    {
        const trace_record_t *record =
            &records[i];


        /* ---------------------------------------------
         * START EVENT
         * --------------------------------------------- */

        if (record->event_type ==
            TRACE_EVENT_START)
        {
            result->start_events++;
        }


        /* ---------------------------------------------
         * END EVENT
         * --------------------------------------------- */

        else if (record->event_type ==
                 TRACE_EVENT_END)
        {
            result->end_events++;


            /*
             * Execution time.
             */

            if (record->execution_time_ns > 0)
            {
                uint64_t execution =
                    record->execution_time_ns;


                result->total_execution_time_ns +=
                    execution;


                execution_count++;


                /*
                 * Minimum execution time.
                 */

                if (result->minimum_execution_time_ns == 0 ||
                    execution <
                    result->minimum_execution_time_ns)
                {
                    result->minimum_execution_time_ns =
                        execution;
                }


                /*
                 * Maximum execution time.
                 */

                if (execution >
                    result->maximum_execution_time_ns)
                {
                    result->maximum_execution_time_ns =
                        execution;
                }


                /*
                 * Jitter.
                 *
                 * Difference between consecutive
                 * execution times.
                 */

                if (previous_execution_time > 0)
                {
                    uint64_t jitter;


                    if (execution >=
                        previous_execution_time)
                    {
                        jitter =
                            execution -
                            previous_execution_time;
                    }
                    else
                    {
                        jitter =
                            previous_execution_time -
                            execution;
                    }


                    total_jitter +=
                        jitter;

                    jitter_count++;


                    /*
                     * Minimum jitter.
                     */

                    if (result->minimum_jitter_ns == 0 ||
                        jitter <
                        result->minimum_jitter_ns)
                    {
                        result->minimum_jitter_ns =
                            jitter;
                    }


                    /*
                     * Maximum jitter.
                     */

                    if (jitter >
                        result->maximum_jitter_ns)
                    {
                        result->maximum_jitter_ns =
                            jitter;
                    }
                }


                previous_execution_time =
                    execution;
            }


            result->completed_tasks++;
        }


        /* ---------------------------------------------
         * DEADLINE MISS
         * --------------------------------------------- */

        else if (record->event_type ==
                 TRACE_EVENT_DEADLINE_MISS)
        {
            result->deadline_misses++;
        }


        /* ---------------------------------------------
         * CONTEXT SWITCH
         * --------------------------------------------- */

        else if (record->event_type ==
                 TRACE_EVENT_CONTEXT_SWITCH)
        {
            result->context_switches++;
        }
    }


    /* =====================================================
     * AVERAGE EXECUTION TIME
     * ===================================================== */

    if (execution_count > 0)
    {
        result->average_execution_time_ns =
            (double)
            result->total_execution_time_ns /
            (double)
            execution_count;
    }


    /* =====================================================
     * LATENCY
     *
     * For this project, the recorded execution duration
     * is used as the measured task latency.
     * ===================================================== */

    if (execution_count > 0)
    {
        result->minimum_latency_ns =
            result->minimum_execution_time_ns;

        result->maximum_latency_ns =
            result->maximum_execution_time_ns;

        result->average_latency_ns =
            result->average_execution_time_ns;
    }


    /* =====================================================
     * AVERAGE JITTER
     * ===================================================== */

    if (jitter_count > 0)
    {
        result->average_jitter_ns =
            (double)
            total_jitter /
            (double)
            jitter_count;
    }


    return 0;
}


/* =========================================================
 * PRINT ANALYSIS
 * ========================================================= */

void trace_analysis_print(
    const trace_analysis_result_t *result)
{
    if (result == NULL)
    {
        return;
    }


    printf("\n");

    printf("============================================\n");
    printf("             TRACE ANALYSIS\n");
    printf("============================================\n");


    /* Basic information */

    printf(
        "Total records          : %zu\n",
        result->total_records);

    printf(
        "START events           : %zu\n",
        result->start_events);

    printf(
        "END events             : %zu\n",
        result->end_events);

    printf(
        "Completed tasks        : %zu\n",
        result->completed_tasks);

    printf(
        "Deadline misses        : %zu\n",
        result->deadline_misses);

    printf(
        "Context switches       : %zu\n",
        result->context_switches);


    printf("--------------------------------------------\n");


    /* Execution time */

    printf(
        "Total execution time   : %llu ns\n",
        (unsigned long long)
        result->total_execution_time_ns);

    printf(
        "Minimum execution time : %llu ns\n",
        (unsigned long long)
        result->minimum_execution_time_ns);

    printf(
        "Maximum execution time : %llu ns\n",
        (unsigned long long)
        result->maximum_execution_time_ns);

    printf(
        "Average execution time : %.2f ns\n",
        result->average_execution_time_ns);


    printf("--------------------------------------------\n");


    /* Latency */

    printf(
        "Minimum latency        : %llu ns\n",
        (unsigned long long)
        result->minimum_latency_ns);

    printf(
        "Maximum latency        : %llu ns\n",
        (unsigned long long)
        result->maximum_latency_ns);

    printf(
        "Average latency        : %.2f ns\n",
        result->average_latency_ns);


    printf("--------------------------------------------\n");


    /* Jitter */

    printf(
        "Minimum jitter         : %llu ns\n",
        (unsigned long long)
        result->minimum_jitter_ns);

    printf(
        "Maximum jitter         : %llu ns\n",
        (unsigned long long)
        result->maximum_jitter_ns);

    printf(
        "Average jitter         : %.2f ns\n",
        result->average_jitter_ns);


    printf("============================================\n");
}
