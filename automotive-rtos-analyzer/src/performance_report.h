#ifndef PERFORMANCE_REPORT_H
#define PERFORMANCE_REPORT_H

#include "trace_analyzer.h"

void performance_report_generate(
    const trace_analysis_result_t *analysis);

void performance_report_print(
    const trace_analysis_result_t *analysis);

#endif
