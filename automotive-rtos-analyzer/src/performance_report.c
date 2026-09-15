/*
 * =========================================================
 * AUTOMOTIVE RTOS PERFORMANCE ANALYZER
 *
 * PERFORMANCE REPORT
 *
 * Phase 3.10
 * =========================================================
 */

#include "performance_report.h"

#include <stdio.h>


/* =========================================================
 * GENERATE PERFORMANCE REPORT
 * ========================================================= */

void performance_report_generate(
    const trace_analysis_result_t *analysis)
{
    FILE *file;

    if (analysis == NULL)
    {
        printf(
            "ERROR: Invalid analysis data.\n");

        return;
    }


    file = fopen(
        "rtos_performance_report.txt",
        "w");


    if (file == NULL)
    {
        printf(
            "ERROR: Cannot create performance report.\n");

        return;
    }


    fprintf(
        file,
        "====================================================\n");

    fprintf(
        file,
        "       AUTOMOTIVE RTOS PERFORMANCE REPORT\n");

    fprintf(
        file,
        "====================================================\n\n");


    fprintf(
        file,
        "TRACE INFORMATION\n");

    fprintf(
        file,
        "-----------------\n");

    fprintf(
        file,
        "Total records          : %zu\n",
        analysis->total_records);

    fprintf(
        file,
        "START events           : %zu\n",
        analysis->start_events);

    fprintf(
        file,
        "END events             : %zu\n",
        analysis->end_events);

    fprintf(
        file,
        "Completed tasks        : %zu\n",
        analysis->completed_tasks);


    fprintf(
        file,
        "\nEXECUTION TIME\n");

    fprintf(
        file,
        "--------------\n");

    fprintf(
        file,
        "Total execution time   : %llu ns\n",
        (unsigned long long)
        analysis->total_execution_time_ns);

    fprintf(
        file,
        "Minimum execution time : %llu ns\n",
        (unsigned long long)
        analysis->minimum_execution_time_ns);

    fprintf(
        file,
        "Maximum execution time : %llu ns\n",
        (unsigned long long)
        analysis->maximum_execution_time_ns);

    fprintf(
        file,
        "Average execution time : %.2f ns\n",
        analysis->average_execution_time_ns);


    fprintf(
        file,
        "\nLATENCY\n");

    fprintf(
        file,
        "-------\n");

    fprintf(
        file,
        "Minimum latency        : %llu ns\n",
        (unsigned long long)
        analysis->minimum_latency_ns);

    fprintf(
        file,
        "Maximum latency        : %llu ns\n",
        (unsigned long long)
        analysis->maximum_latency_ns);

    fprintf(
        file,
        "Average latency        : %.2f ns\n",
        analysis->average_latency_ns);


    fprintf(
        file,
        "\nJITTER\n");

    fprintf(
        file,
        "------\n");

    fprintf(
        file,
        "Minimum jitter         : %llu ns\n",
        (unsigned long long)
        analysis->minimum_jitter_ns);

    fprintf(
        file,
        "Maximum jitter         : %llu ns\n",
        (unsigned long long)
        analysis->maximum_jitter_ns);

    fprintf(
        file,
        "Average jitter         : %.2f ns\n",
        analysis->average_jitter_ns);


    fprintf(
        file,
        "\nRTOS EVENTS\n");

    fprintf(
        file,
        "-----------\n");

    fprintf(
        file,
        "Deadline misses        : %zu\n",
        analysis->deadline_misses);

    fprintf(
        file,
        "Context switches       : %zu\n",
        analysis->context_switches);


    fprintf(
        file,
        "\n====================================================\n");

    fprintf(
        file,
        "                REPORT COMPLETED\n");

    fprintf(
        file,
        "====================================================\n");


    fclose(file);


    printf("\n");
    printf(
        "Performance report generated successfully.\n");

    printf(
        "File: rtos_performance_report.txt\n");
}


/* =========================================================
 * PRINT PERFORMANCE REPORT
 * ========================================================= */

void performance_report_print(
    const trace_analysis_result_t *analysis)
{
    if (analysis == NULL)
    {
        return;
    }


    printf("\n");

    printf(
        "====================================================\n");

    printf(
        "       AUTOMOTIVE RTOS PERFORMANCE REPORT\n");

    printf(
        "====================================================\n");


    printf("\nTRACE INFORMATION\n");

    printf(
        "Total records          : %zu\n",
        analysis->total_records);

    printf(
        "Completed tasks        : %zu\n",
        analysis->completed_tasks);


    printf("\nEXECUTION TIME\n");

    printf(
        "Minimum                : %llu ns\n",
        (unsigned long long)
        analysis->minimum_execution_time_ns);

    printf(
        "Maximum                : %llu ns\n",
        (unsigned long long)
        analysis->maximum_execution_time_ns);

    printf(
        "Average                : %.2f ns\n",
        analysis->average_execution_time_ns);


    printf("\nLATENCY\n");

    printf(
        "Minimum                : %llu ns\n",
        (unsigned long long)
        analysis->minimum_latency_ns);

    printf(
        "Maximum                : %llu ns\n",
        (unsigned long long)
        analysis->maximum_latency_ns);

    printf(
        "Average                : %.2f ns\n",
        analysis->average_latency_ns);


    printf("\nJITTER\n");

    printf(
        "Minimum                : %llu ns\n",
        (unsigned long long)
        analysis->minimum_jitter_ns);

    printf(
        "Maximum                : %llu ns\n",
        (unsigned long long)
        analysis->maximum_jitter_ns);

    printf(
        "Average                : %.2f ns\n",
        analysis->average_jitter_ns);


    printf("\nRTOS EVENTS\n");

    printf(
        "Deadline misses        : %zu\n",
        analysis->deadline_misses);

    printf(
        "Context switches       : %zu\n",
        analysis->context_switches);


    printf(
        "\n====================================================\n");
}
