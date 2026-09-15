from __future__ import annotations

import importlib.util
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from analysis_engine import (
    EXPECTED_EVENTS,
    EXPECTED_TESTBENCHES,
    analyze_trace,
)


# ============================================================
# AUTOMOTIVE RTOS ANALYZER
# MASTER ANALYSIS & VALIDATION PIPELINE
# PHASE 5.3.3
# ============================================================


PROJECT_NAME = "AUTOMOTIVE RTOS ANALYZER"
VERSION = "5.3.3"

BASE_DIR = Path(__file__).resolve().parent

TRACE_FILE = BASE_DIR / "rtos_trace.csv"

OUTPUT_DIR = BASE_DIR / "outputs"

REPORT_FILE = (
    OUTPUT_DIR
    / "rtos_performance_report.txt"
)

SUMMARY_FILE = (
    OUTPUT_DIR
    / "analysis_summary.txt"
)

DASHBOARD_FILE = (
    BASE_DIR
    / "app.py"
)


# ------------------------------------------------------------
# Required Python packages
# ------------------------------------------------------------

REQUIRED_PACKAGES = {
    "pandas": "pandas",
    "numpy": "numpy",
    "plotly": "plotly",
    "streamlit": "streamlit",
}


# ============================================================
# TERMINAL FORMATTING
# ============================================================

RESET = "\033[0m"
BOLD = "\033[1m"

GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
CYAN = "\033[96m"


def print_header(title: str):
    print()
    print("=" * 78)
    print(title)
    print("=" * 78)


def print_ok(message: str):
    print(
        f"{GREEN}[PASS]{RESET} {message}"
    )


def print_warning(message: str):
    print(
        f"{YELLOW}[WARN]{RESET} {message}"
    )


def print_error(message: str):
    print(
        f"{RED}[FAIL]{RESET} {message}"
    )


def print_info(message: str):
    print(
        f"{CYAN}[INFO]{RESET} {message}"
    )


# ============================================================
# PACKAGE CHECK
# ============================================================

def check_python_environment() -> bool:

    print_header(
        "1. PYTHON ENVIRONMENT CHECK"
    )

    print_info(
        f"Python version: "
        f"{sys.version.split()[0]}"
    )

    if sys.version_info < (3, 9):

        print_error(
            "Python 3.9 or newer is recommended."
        )

        return False

    print_ok(
        "Python version is supported."
    )

    return True


def check_required_packages() -> bool:

    print_header(
        "2. DEPENDENCY CHECK"
    )

    all_available = True

    for package_name, module_name in (
        REQUIRED_PACKAGES.items()
    ):

        if importlib.util.find_spec(
            module_name
        ) is not None:

            print_ok(
                f"{package_name} installed"
            )

        else:

            print_error(
                f"{package_name} is NOT installed"
            )

            all_available = False

    return all_available


# ============================================================
# FILE CHECK
# ============================================================

def check_project_files() -> bool:

    print_header(
        "3. PROJECT FILE CHECK"
    )

    files_to_check = [
        TRACE_FILE,
        DASHBOARD_FILE,
        BASE_DIR / "analysis_engine.py",
        BASE_DIR / "report_generator.py",
    ]

    all_available = True

    for file_path in files_to_check:

        if file_path.exists():

            print_ok(
                f"{file_path.name} found"
            )

        else:

            print_error(
                f"{file_path.name} missing"
            )

            all_available = False

    return all_available


# ============================================================
# TRACE ANALYSIS
# ============================================================

def analyze_project_trace():

    print_header(
        "4. RTOS TRACE ANALYSIS"
    )

    print_info(
        f"Trace file: {TRACE_FILE}"
    )

    print_info(
        f"File size: "
        f"{TRACE_FILE.stat().st_size:,} bytes"
    )

    results = analyze_trace(
        str(TRACE_FILE)
    )

    system = results["system"]

    print_ok(
        f"Trace loaded successfully"
    )

    print_info(
        f"Records: {system['records']:,}"
    )

    print_info(
        f"Tasks: {system['tasks']}"
    )

    print_info(
        f"Capture duration: "
        f"{system['duration_ms']:.3f} ms"
    )

    print_info(
        f"Execution occupancy: "
        f"{system['execution_occupancy']:.2f}%"
    )

    return results


# ============================================================
# TESTBENCH VALIDATION
# ============================================================

def validate_testbenches(results) -> bool:

    print_header(
        "5. TESTBENCH COVERAGE VALIDATION"
    )

    coverage = results[
        "coverage"
    ]

    present = coverage[
        "present_testbenches"
    ]

    missing = coverage[
        "missing_testbenches"
    ]

    print(
        f"Expected testbenches : "
        f"{coverage['expected']}"
    )

    print(
        f"Captured testbenches : "
        f"{coverage['present']}"
    )

    print(
        f"Coverage             : "
        f"{coverage['coverage_percent']:.2f}%"
    )

    print()

    for testbench in EXPECTED_TESTBENCHES:

        if testbench in present:

            print_ok(
                testbench
            )

        else:

            print_error(
                f"{testbench} - NOT FOUND"
            )

    if missing:

        print_warning(
            f"{len(missing)} testbench(es) "
            f"are missing."
        )

        return False

    print_ok(
        "All 11 testbenches are present."
    )

    return True


# ============================================================
# EVENT VALIDATION
# ============================================================

def validate_events(results) -> bool:

    print_header(
        "6. EVENT VALIDATION"
    )

    events = results[
        "events"
    ]

    event_counts = dict(
        zip(
            events["Event"],
            events["Count"]
        )
    )

    all_ok = True

    for event in EXPECTED_EVENTS:

        count = int(
            event_counts.get(
                event,
                0
            )
        )

        if count > 0:

            print_ok(
                f"{event}: "
                f"{count:,} records"
            )

        else:

            if event == "DEADLINE_MISS":

                print_info(
                    f"{event}: 0 "
                    f"(no deadline violations detected)"
                )

            elif event == "TEMPERATURE":

                print_warning(
                    f"{event}: 0 "
                    f"(thermal sensor data unavailable)"
                )

            else:

                print_warning(
                    f"{event}: 0 records"
                )

    return all_ok


# ============================================================
# DEADLINE VALIDATION
# ============================================================

def validate_deadlines(results):

    print_header(
        "7. DEADLINE ANALYSIS"
    )

    deadline = results[
        "deadline"
    ]

    checked = deadline[
        "checked"
    ]

    met = deadline[
        "met"
    ]

    missed = deadline[
        "missed"
    ]

    if checked == 0:

        print_warning(
            "No deadline measurements found."
        )

        return

    print_info(
        f"Deadline checks : {checked}"
    )

    print_info(
        f"Deadlines met   : {met}"
    )

    print_info(
        f"Deadlines missed: {missed}"
    )

    success_rate = (
        deadline[
            "success_rate"
        ]
    )

    if success_rate is not None:

        print_info(
            f"Deadline success rate: "
            f"{success_rate:.2f}%"
        )

    if missed > 0:

        print_warning(
            "Deadline violations detected."
        )

    else:

        print_ok(
            "No deadline violations detected."
        )


# ============================================================
# CONTEXT SWITCH VALIDATION
# ============================================================

def validate_context_switches(results):

    print_header(
        "8. CONTEXT-SWITCH INSTRUMENTATION"
    )

    count = results[
        "system"
    ][
        "context_switches"
    ]

    if count > 0:

        print_ok(
            f"Context-switch/yield "
            f"instrumentation events: "
            f"{count:,}"
        )

        print_info(
            "These records represent "
            "instrumented sched_yield() "
            "opportunities, not kernel-"
            "confirmed context switches."
        )

    else:

        print_warning(
            "No context-switch instrumentation "
            "events detected."
        )


# ============================================================
# TEMPERATURE VALIDATION
# ============================================================

def validate_temperature(results):

    print_header(
        "9. TEMPERATURE MONITORING"
    )

    temperature = results[
        "temperature"
    ]

    if not temperature[
        "available"
    ]:

        print_warning(
            "No temperature samples available."
        )

        print_info(
            "This normally means the QNX "
            "thermal sensor path did not "
            "provide readable data."
        )

        return

    print_ok(
        f"Temperature samples: "
        f"{temperature['samples']}"
    )

    print_info(
        f"Minimum: "
        f"{temperature['minimum_c']:.2f} °C"
    )

    print_info(
        f"Maximum: "
        f"{temperature['maximum_c']:.2f} °C"
    )

    print_info(
        f"Average: "
        f"{temperature['average_c']:.2f} °C"
    )

    print_info(
        f"Change: "
        f"{temperature['change_c']:.2f} °C"
    )


# ============================================================
# REPORT GENERATION
# ============================================================

def generate_performance_report():

    print_header(
        "10. PERFORMANCE REPORT GENERATION"
    )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    try:

        from report_generator import (
            generate_report
        )

        report_path = generate_report()

        print_ok(
            f"Performance report generated: "
            f"{report_path}"
        )

        return report_path

    except Exception as error:

        print_error(
            f"Report generation failed: "
            f"{error}"
        )

        return None


# ============================================================
# ANALYSIS SUMMARY FILE
# ============================================================

def save_analysis_summary(results):

    print_header(
        "11. SAVING ANALYSIS SUMMARY"
    )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    system = results[
        "system"
    ]

    coverage = results[
        "coverage"
    ]

    deadline = results[
        "deadline"
    ]

    temperature = results[
        "temperature"
    ]

    lines = []

    lines.append(
        "AUTOMOTIVE RTOS ANALYZER"
    )

    lines.append(
        "MASTER ANALYSIS SUMMARY"
    )

    lines.append(
        "=" * 60
    )

    lines.append(
        f"Generated: "
        f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )

    lines.append(
        f"Pipeline Version: {VERSION}"
    )

    lines.append("")

    lines.append(
        "SYSTEM"
    )

    lines.append(
        f"Records: {system['records']}"
    )

    lines.append(
        f"Tasks: {system['tasks']}"
    )

    lines.append(
        f"Duration (ms): "
        f"{system['duration_ms']:.3f}"
    )

    lines.append(
        f"Execution Occupancy (%): "
        f"{system['execution_occupancy']:.2f}"
    )

    lines.append(
        f"System Health: "
        f"{system['health']}"
    )

    lines.append("")

    lines.append(
        "TESTBENCH COVERAGE"
    )

    lines.append(
        f"Expected: "
        f"{coverage['expected']}"
    )

    lines.append(
        f"Present: "
        f"{coverage['present']}"
    )

    lines.append(
        f"Coverage: "
        f"{coverage['coverage_percent']:.2f}%"
    )

    lines.append("")

    lines.append(
        "DEADLINE"
    )

    lines.append(
        f"Checked: "
        f"{deadline['checked']}"
    )

    lines.append(
        f"Met: "
        f"{deadline['met']}"
    )

    lines.append(
        f"Missed: "
        f"{deadline['missed']}"
    )

    lines.append("")

    lines.append(
        "CONTEXT SWITCH"
    )

    lines.append(
        f"Events: "
        f"{system['context_switches']}"
    )

    lines.append("")

    lines.append(
        "TEMPERATURE"
    )

    if temperature[
        "available"
    ]:

        lines.append(
            f"Samples: "
            f"{temperature['samples']}"
        )

        lines.append(
            f"Minimum: "
            f"{temperature['minimum_c']:.2f} C"
        )

        lines.append(
            f"Maximum: "
            f"{temperature['maximum_c']:.2f} C"
        )

        lines.append(
            f"Average: "
            f"{temperature['average_c']:.2f} C"
        )

    else:

        lines.append(
            "No temperature samples available."
        )

    lines.append("")

    lines.append(
        "PRESENT TESTBENCHES"
    )

    for testbench in coverage[
        "present_testbenches"
    ]:

        lines.append(
            f"[PASS] {testbench}"
        )

    lines.append("")

    lines.append(
        "MISSING TESTBENCHES"
    )

    for testbench in coverage[
        "missing_testbenches"
    ]:

        lines.append(
            f"[MISS] {testbench}"
        )

    SUMMARY_FILE.write_text(
        "\n".join(lines),
        encoding="utf-8"
    )

    print_ok(
        f"Analysis summary saved: "
        f"{SUMMARY_FILE}"
    )


# ============================================================
# FINAL STATUS
# ============================================================

def calculate_final_status(
    results,
    testbench_ok: bool
):

    system = results[
        "system"
    ]

    coverage = results[
        "coverage"
    ]

    deadline = results[
        "deadline"
    ]

    print_header(
        "12. FINAL VALIDATION STATUS"
    )

    critical_checks = [
        (
            "Trace available",
            system["records"] > 0
        ),

        (
            "11-testbench coverage",
            testbench_ok
        ),

        (
            "Trace duration valid",
            system["duration_ms"] > 0
        ),

        (
            "Task data available",
            system["tasks"] > 0
        ),
    ]

    passed = 0

    for name, status in critical_checks:

        if status:

            print_ok(name)

            passed += 1

        else:

            print_error(name)

    total = len(
        critical_checks
    )

    score = (
        passed
        / total
        * 100.0
    )

    print()

    print(
        f"Validation Score: "
        f"{score:.0f}%"
    )

    if score == 100:

        print_ok(
            "SYSTEM VALIDATION PASSED"
        )

    elif score >= 75:

        print_warning(
            "SYSTEM VALIDATION PASSED "
            "WITH WARNINGS"
        )

    else:

        print_error(
            "SYSTEM VALIDATION FAILED"
        )

    if deadline["missed"] > 0:

        print_warning(
            f"Deadline misses detected: "
            f"{deadline['missed']}"
        )

    if coverage["missing"] > 0:

        print_warning(
            f"Missing testbenches: "
            f"{coverage['missing']}"
        )

    return score >= 75


# ============================================================
# DASHBOARD
# ============================================================

def launch_dashboard():

    print_header(
        "13. LAUNCHING PROFESSIONAL DASHBOARD"
    )

    print_info(
        "Starting Streamlit dashboard..."
    )

    print_info(
        "Browser should open automatically."
    )

    print_info(
        "Press Ctrl+C to stop the dashboard."
    )

    print()

    try:

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "streamlit",
                "run",
                str(DASHBOARD_FILE),
            ],
            cwd=str(BASE_DIR)
        )

        return result.returncode

    except KeyboardInterrupt:

        print()

        print_info(
            "Dashboard stopped by user."
        )

        return 0

    except Exception as error:

        print_error(
            f"Dashboard failed to start: "
            f"{error}"
        )

        return 1


# ============================================================
# MAIN PIPELINE
# ============================================================

def main():

    start_time = datetime.now()

    print()
    print("=" * 78)
    print(
        f"{BOLD}{CYAN}"
        f"{PROJECT_NAME}"
        f"{RESET}"
    )
    print(
        f"MASTER ANALYSIS & VALIDATION PIPELINE"
    )
    print(
        f"Phase {VERSION}"
    )
    print("=" * 78)

    print_info(
        f"Started: "
        f"{start_time.strftime('%Y-%m-%d %H:%M:%S')}"
    )

    # --------------------------------------------------------
    # Environment
    # --------------------------------------------------------

    environment_ok = (
        check_python_environment()
    )

    if not environment_ok:
        return 1

    # --------------------------------------------------------
    # Dependencies
    # --------------------------------------------------------

    dependencies_ok = (
        check_required_packages()
    )

    if not dependencies_ok:

        print()
        print_error(
            "Missing Python dependencies."
        )

        print_info(
            "Run:"
        )

        print(
            "python -m pip install "
            "-r requirements.txt"
        )

        return 1

    # --------------------------------------------------------
    # Project files
    # --------------------------------------------------------

    files_ok = (
        check_project_files()
    )

    if not files_ok:
        return 1

    # --------------------------------------------------------
    # Trace analysis
    # --------------------------------------------------------

    try:

        results = (
            analyze_project_trace()
        )

    except Exception as error:

        print_error(
            f"Trace analysis failed: "
            f"{error}"
        )

        return 1

    # --------------------------------------------------------
    # Testbench
    # --------------------------------------------------------

    testbench_ok = (
        validate_testbenches(
            results
        )
    )

    # --------------------------------------------------------
    # Events
    # --------------------------------------------------------

    validate_events(
        results
    )

    # --------------------------------------------------------
    # Deadline
    # --------------------------------------------------------

    validate_deadlines(
        results
    )

    # --------------------------------------------------------
    # Context switch
    # --------------------------------------------------------

    validate_context_switches(
        results
    )

    # --------------------------------------------------------
    # Temperature
    # --------------------------------------------------------

    validate_temperature(
        results
    )

    # --------------------------------------------------------
    # Report
    # --------------------------------------------------------

    generate_performance_report()

    # --------------------------------------------------------
    # Summary
    # --------------------------------------------------------

    save_analysis_summary(
        results
    )

    # --------------------------------------------------------
    # Final validation
    # --------------------------------------------------------

    validation_ok = (
        calculate_final_status(
            results,
            testbench_ok
        )
    )

    finish_time = datetime.now()

    elapsed = (
        finish_time
        - start_time
    ).total_seconds()

    print()
    print("=" * 78)

    print(
        f"Pipeline execution time: "
        f"{elapsed:.2f} seconds"
    )

    print(
        f"Report: {REPORT_FILE}"
    )

    print(
        f"Summary: {SUMMARY_FILE}"
    )

    print("=" * 78)

    # --------------------------------------------------------
    # Launch dashboard
    # --------------------------------------------------------

    if validation_ok:

        return launch_dashboard()

    print()
    print_error(
        "Dashboard was not launched because "
        "critical validation checks failed."
    )

    print_info(
        "Fix the validation issues and "
        "run the pipeline again."
    )

    return 1


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    try:

        exit_code = main()

        sys.exit(
            exit_code
        )

    except KeyboardInterrupt:

        print()
        print_info(
            "Pipeline stopped by user."
        )

        sys.exit(0)

    except Exception as error:

        print()
        print_error(
            f"Unexpected pipeline error: "
            f"{error}"
        )

        sys.exit(1)