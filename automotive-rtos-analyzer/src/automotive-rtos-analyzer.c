/*
 * =========================================================
 * AUTOMOTIVE RTOS PERFORMANCE ANALYZER
 *
 * MAIN PROGRAM
 *
 * Shared Memory + CAN + MCP2515 SPI Integration
 *
 * Master Workflow - Step 12.4
 * =========================================================
 */

#include <stdio.h>
#include <stdlib.h>

#include "testbench.h"
#include "trace_collector.h"
#include "trace_analyzer.h"
#include "performance_report.h"
#include "shared_memory.h"
#include "can_interface.h"
#include "mcp2515_spi_test.h"


/*
 * =========================================================
 * SYNCHRONIZE TRACE DATA TO SHARED MEMORY
 * =========================================================
 */

static void sync_trace_to_shared_memory(void)
{
    const trace_record_t *records;
    size_t record_count;
    size_t i;

    records = trace_get_records();
    record_count = trace_get_record_count();

    if (records == NULL)
    {
        printf("ERROR: Trace records unavailable.\n");
        return;
    }

    printf("\n");
    printf("============================================\n");
    printf("      TRACE -> SHARED MEMORY SYNC\n");
    printf("============================================\n");

    printf("Records to synchronize : %zu\n",
           record_count);

    /*
     * Process every trace record.
     */
    for (i = 0; i < record_count; i++)
    {
        const trace_record_t *record =
            &records[i];

        /*
         * Priority is not available in the
         * trace record, therefore 0 is used.
         */
        shared_memory_register_task(
            record->task_id,
            0);

        /*
         * END event.
         */
        if (record->event_type ==
            TRACE_EVENT_END)
        {
            shared_memory_update_task(
                record->task_id,
                record->execution_time_ns,
                0,
                record->timestamp_ns,
                record->deadline_ns,
                0);
        }

        /*
         * DEADLINE MISS event.
         */
        else if (record->event_type ==
                 TRACE_EVENT_DEADLINE_MISS)
        {
            shared_memory_increment_deadline_miss();

            shared_memory_increment_event_count();
        }

        /*
         * CONTEXT SWITCH event.
         */
        else if (record->event_type ==
                 TRACE_EVENT_CONTEXT_SWITCH)
        {
            shared_memory_increment_context_switch();

            shared_memory_increment_event_count();
        }

        /*
         * START and TEMPERATURE events.
         */
        else
        {
            shared_memory_increment_event_count();
        }
    }

    printf("Synchronization complete.\n");

    printf("============================================\n");
}


/*
 * =========================================================
 * DISPLAY SHARED MEMORY STATUS
 * =========================================================
 */

static void display_shared_memory_status(void)
{
    printf("\n");

    printf("====================================================\n");
    printf("          SHARED MEMORY DATA READY\n");
    printf("====================================================\n");

    shared_memory_print();

    printf("====================================================\n");
}


/*
 * =========================================================
 * CAN INTERFACE INITIALIZATION
 * =========================================================
 */

static int initialize_can_interface(void)
{
    int result;

    printf("\n");

    printf("====================================================\n");
    printf("              CAN INTERFACE SETUP\n");
    printf("====================================================\n");

    /*
     * Initialize CAN interface.
     */
    result = can_interface_init();

    if (result != CAN_STATUS_OK)
    {
        printf(
            "CAN initialization returned status: %d\n",
            result);

        printf(
            "CAN module will remain in software-ready mode.\n");

        printf(
            "RTOS analyzer execution will continue.\n");

        printf("====================================================\n");

        return 0;
    }

    /*
     * Run CAN software self-test.
     */
    result = can_run_self_test();

    if (result != CAN_STATUS_OK)
    {
        printf(
            "CAN self-test returned status: %d\n",
            result);

        printf(
            "Continuing with RTOS analyzer.\n");
    }
    else
    {
        printf(
            "CAN software self-test completed successfully.\n");
    }

    /*
     * Display CAN status.
     */
    can_interface_print_status();

    printf("====================================================\n");

    return 0;
}


/*
 * =========================================================
 * MAIN
 * =========================================================
 */

int main(void)
{
    trace_analysis_result_t analysis;
    int spi_test_result;

    /*
     * =====================================================
     * PROGRAM START
     * =====================================================
     */

    printf("\n");

    printf("====================================================\n");
    printf("        AUTOMOTIVE RTOS PERFORMANCE ANALYZER\n");
    printf("====================================================\n");

    printf("\n");

    printf("Starting RTOS Testbench...\n");


    /*
     * =====================================================
     * TRACE COLLECTOR INITIALIZATION
     * =====================================================
     */

    trace_collector_init();


    /*
     * =====================================================
     * SHARED MEMORY INITIALIZATION
     * =====================================================
     */

    printf("\n");

    printf("Initializing shared memory...\n");

    if (shared_memory_init() != 0)
    {
        printf(
            "ERROR: Shared memory initialization failed.\n");

        return EXIT_FAILURE;
    }

    printf(
        "Shared memory initialization successful.\n");


    /*
     * =====================================================
     * CAN INTERFACE INITIALIZATION
     * =====================================================
     */

    initialize_can_interface();


    /*
     * =====================================================
     * TEST 1
     * =====================================================
     */

    printf("\n");

    printf(">>> TEST 1: TASK SCALING\n");

    run_task_scaling_test(4);


    /*
     * =====================================================
     * TEST 2
     * =====================================================
     */

    printf("\n");

    printf(">>> TEST 2: PRIORITY VARIATION\n");

    run_priority_variation_test();


    /*
     * =====================================================
     * TEST 3
     * =====================================================
     */

    printf("\n");

    printf(">>> TEST 3: EXECUTION-TIME VARIATION\n");

    run_execution_time_variation_test();


    /*
     * =====================================================
     * TEST 4
     * =====================================================
     */

    printf("\n");

    printf(">>> TEST 4: PERIOD VARIATION\n");

    run_period_variation_test();


    /*
     * =====================================================
     * TEST 5
     * =====================================================
     */

    printf("\n");

    printf(">>> TEST 5: DEADLINE TESTING\n");

    run_deadline_test();


    /*
     * =====================================================
     * TEST 6
     * =====================================================
     */

    printf("\n");

    printf(">>> TEST 6: CPU LOAD VARIATION\n");

    run_cpu_load_test(50);


    /*
     * =====================================================
     * TEST 7
     * =====================================================
     */

    printf("\n");

    printf(">>> TEST 7: CONTEXT-SWITCH TESTING\n");

    run_context_switch_test(4);


    /*
     * =====================================================
     * TEST 8
     * =====================================================
     */

    printf("\n");

    printf(">>> TEST 8: MIXED WORKLOAD\n");

    run_mixed_workload_test();


    /*
     * =====================================================
     * TEST 9
     * =====================================================
     */

    printf("\n");

    printf(">>> TEST 9: LONG-DURATION STABILITY\n");

    run_long_duration_test(10);


    /*
     * =====================================================
     * TEST 10
     * =====================================================
     */

    printf("\n");

    printf(">>> TEST 10: STRESS TESTING\n");

    run_stress_test();


    /*
     * =====================================================
     * TEST 11
     * =====================================================
     */

    printf("\n");

    printf(">>> TEST 11: TEMPERATURE MONITORING\n");

    run_temperature_test(10);


    /*
     * =====================================================
     * TESTBENCH COMPLETED
     * =====================================================
     */

    printf("\n");

    printf("====================================================\n");
    printf("              TESTBENCH COMPLETED\n");
    printf("====================================================\n");


    /*
     * =====================================================
     * MCP2515 SPI HARDWARE TEST
     * =====================================================
     *
     * This test is performed after the RTOS measurements
     * so that SPI activity does not disturb the timing
     * measurements of the 11 testbenches.
     */

    printf("\n");

    printf("====================================================\n");
    printf("              MCP2515 SPI TEST\n");
    printf("====================================================\n");

    printf(
        "Testing MCP2515 through SPI0 / dev0...\n");

    spi_test_result = mcp2515_spi_test();

    if (spi_test_result == 0)
    {
        printf("\n");

        printf(
            "[SPI] MCP2515 SPI TEST PASSED.\n");

        printf(
            "[SPI] MCP2515 responded correctly.\n");
    }
    else
    {
        printf("\n");

        printf(
            "[SPI] MCP2515 SPI TEST FAILED.\n");

        printf(
            "[SPI] Result code: %d\n",
            spi_test_result);

        printf(
            "[SPI] Check MCP2515 wiring, power and SPI configuration.\n");

        printf(
            "[SPI] RTOS analyzer will continue.\n");
    }

    printf("====================================================\n");


    /*
     * =====================================================
     * CAN TEST MESSAGE
     * =====================================================
     */

    printf("\n");

    printf(
        "[CAN] Sending CAN test message...\n");

    if (can_send_test_message() == CAN_STATUS_OK)
    {
        printf(
            "[CAN] CAN test message sent successfully.\n");
    }
    else
    {
        printf(
            "[CAN] CAN test message is not available yet.\n");

        printf(
            "[CAN] This is expected while MCP2515 CAN TX integration is pending.\n");
    }


    /*
     * =====================================================
     * SHARED MEMORY SYNCHRONIZATION
     * =====================================================
     */

    sync_trace_to_shared_memory();


    /*
     * =====================================================
     * DISPLAY SHARED MEMORY DATA
     * =====================================================
     */

    display_shared_memory_status();


    /*
     * =====================================================
     * PRINT TRACE
     * =====================================================
     */

    trace_collector_print();


    /*
     * =====================================================
     * EXPORT CSV
     * =====================================================
     */

    printf("\n");

    printf(
        "Exporting trace data to CSV...\n");

    if (trace_collector_export_csv(
            "rtos_trace.csv") != 0)
    {
        printf(
            "ERROR: CSV export failed.\n");
    }
    else
    {
        printf(
            "CSV export successful.\n");

        printf(
            "File: rtos_trace.csv\n");
    }


    /*
     * =====================================================
     * TRACE ANALYSIS
     * =====================================================
     */

    printf("\n");

    printf("====================================================\n");
    printf("                  TRACE ANALYSIS\n");
    printf("====================================================\n");

    trace_analyzer_init();

    if (trace_analyze(&analysis) == 0)
    {
        trace_analysis_print(&analysis);
    }
    else
    {
        printf(
            "ERROR: Trace analysis failed.\n");

        shared_memory_close();

        return EXIT_FAILURE;
    }


    /*
     * =====================================================
     * PERFORMANCE REPORT
     * =====================================================
     */

    printf("\n");

    printf("====================================================\n");
    printf("               PERFORMANCE REPORT\n");
    printf("====================================================\n");

    performance_report_print(
        &analysis);

    performance_report_generate(
        &analysis);


    /*
     * =====================================================
     * FINAL CAN STATUS
     * =====================================================
     */

    printf("\n");

    printf("====================================================\n");
    printf("                    FINAL CAN STATUS\n");
    printf("====================================================\n");

    can_interface_print_status();


    /*
     * =====================================================
     * CAN CLEANUP
     * =====================================================
     */

    can_interface_close();


    /*
     * =====================================================
     * SHARED MEMORY CLEANUP
     * =====================================================
     */

    shared_memory_close();


    /*
     * =====================================================
     * FINAL STATUS
     * =====================================================
     */

    printf("\n");

    printf("====================================================\n");
    printf("        AUTOMOTIVE RTOS ANALYZER FINISHED\n");
    printf("====================================================\n");

    printf("\n");

    printf("Generated files:\n");

    printf(
        "  1. rtos_trace.csv\n");

    printf(
        "  2. rtos_performance_report.txt\n");

    printf("\n");

    printf(
        "RTOS Test Benches  : 11 COMPLETED\n");

    printf(
        "Performance Analysis : COMPLETED\n");

    printf(
        "Performance Report : COMPLETED\n");

    if (spi_test_result == 0)
    {
        printf(
            "MCP2515 SPI Test   : PASSED\n");
    }
    else
    {
        printf(
            "MCP2515 SPI Test   : FAILED / CHECK HARDWARE\n");
    }

    printf("\n");

    printf(
        "====================================================\n");

    return EXIT_SUCCESS;
}
