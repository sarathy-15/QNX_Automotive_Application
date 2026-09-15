#ifndef TESTBENCH_H
#define TESTBENCH_H

void run_task_scaling_test(int task_count);

void run_priority_variation_test(void);

void run_execution_time_variation_test(void);

void run_period_variation_test(void);

void run_deadline_test(void);

void run_cpu_load_test(int load_level);

void run_context_switch_test(int task_count);

void run_mixed_workload_test(void);

void run_long_duration_test(int duration_seconds);

void run_stress_test(void);

void run_temperature_test(int duration_seconds);

#endif
