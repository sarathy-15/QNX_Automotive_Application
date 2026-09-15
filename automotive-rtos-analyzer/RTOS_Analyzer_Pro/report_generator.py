from __future__ import annotations

"""
============================================================
AUTOMOTIVE RTOS PERFORMANCE ANALYZER
REPORT GENERATOR
Phase 5.3.3

Purpose:
    Generate a professional text performance report from
    the actual QNX RTOS trace CSV.

Important:
    SYSTEM HEALTH is derived only from trace evidence.
    Testbench coverage is reported separately.

CSV schema:
    timestamp_ns
    testbench
    task_id
    event
    execution_time_ns
    deadline_ns
    temperature_c
============================================================
"""

from pathlib import Path
from datetime import datetime
import sys

import numpy as np
import pandas as pd


# ============================================================
# PATH CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

DEFAULT_TRACE = BASE_DIR / "rtos_trace.csv"

OUTPUT_DIR = BASE_DIR / "outputs"
OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)

DEFAULT_REPORT = (
    OUTPUT_DIR /
    "rtos_performance_report.txt"
)


# ============================================================
# EXPECTED TESTBENCHES
# ============================================================

EXPECTED_TESTBENCHES = [
    "Task Scaling",
    "Priority Variation",
    "Execution-Time Variation",
    "Period Variation + Jitter",
    "Deadline Testing",
    "CPU Load Variation",
    "Context-Switch Testing",
    "Mixed Workload",
    "Long-Duration Stability",
    "Stress Testing",
    "Temperature Monitoring",
]


# ============================================================
# REQUIRED TRACE COLUMNS
# ============================================================

REQUIRED_COLUMNS = [
    "timestamp_ns",
    "task_id",
    "event",
]


OPTIONAL_COLUMNS = [
    "testbench",
    "execution_time_ns",
    "deadline_ns",
    "temperature_c",
]


# ============================================================
# TRACE LOADING
# ============================================================

def load_trace(trace_path: Path) -> pd.DataFrame:
    """
    Load and normalize the QNX trace CSV.
    """

    if not trace_path.exists():
        raise FileNotFoundError(
            f"Trace file not found:\n{trace_path}"
        )

    df = pd.read_csv(trace_path)

    # Normalize column names.
    df.columns = [
        str(column).strip()
        for column in df.columns
    ]

    # --------------------------------------------------------
    # Backward-compatible aliases
    # --------------------------------------------------------

    aliases = {
        "timestamp": "timestamp_ns",
        "task": "task_id",
        "execution_time": "execution_time_ns",
        "deadline": "deadline_ns",
        "temperature": "temperature_c",
    }

    rename_map = {}

    for column in df.columns:

        normalized = (
            str(column)
            .strip()
            .lower()
            .replace(" ", "_")
            .replace("-", "_")
        )

        if normalized in aliases:
            target = aliases[normalized]

            if column != target:
                rename_map[column] = target

    if rename_map:
        df = df.rename(
            columns=rename_map
        )

    # --------------------------------------------------------
    # Required fields
    # --------------------------------------------------------

    missing = [
        column
        for column in REQUIRED_COLUMNS
        if column not in df.columns
    ]

    if missing:
        raise ValueError(
            "Required trace columns missing: "
            + ", ".join(missing)
        )

    # --------------------------------------------------------
    # Optional fields
    # --------------------------------------------------------

    if "testbench" not in df.columns:
        df["testbench"] = "UNSPECIFIED"

    if "execution_time_ns" not in df.columns:
        df["execution_time_ns"] = np.nan

    if "deadline_ns" not in df.columns:
        df["deadline_ns"] = np.nan

    if "temperature_c" not in df.columns:
        df["temperature_c"] = np.nan

    # --------------------------------------------------------
    # Numeric conversion
    # --------------------------------------------------------

    numeric_columns = [
        "timestamp_ns",
        "task_id",
        "execution_time_ns",
        "deadline_ns",
        "temperature_c",
    ]

    for column in numeric_columns:
        df[column] = pd.to_numeric(
            df[column],
            errors="coerce"
        )

    # --------------------------------------------------------
    # Text normalization
    # --------------------------------------------------------

    df["event"] = (
        df["event"]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    df["testbench"] = (
        df["testbench"]
        .astype(str)
        .str.strip()
    )

    # --------------------------------------------------------
    # Remove invalid timestamp/task rows
    # --------------------------------------------------------

    df = df.dropna(
        subset=[
            "timestamp_ns",
            "task_id",
        ]
    ).copy()

    df["task_id"] = (
        df["task_id"]
        .astype(int)
    )

    df = df.sort_values(
        "timestamp_ns"
    ).reset_index(
        drop=True
    )

    return df


# ============================================================
# TRACE INTEGRITY
# ============================================================

def analyze_trace_integrity(
    df: pd.DataFrame
) -> dict:

    result = {
        "valid": False,
        "reason": "",
        "records": len(df),
        "duration_ns": 0,
    }

    if df.empty:
        result["reason"] = (
            "Trace contains no records."
        )
        return result

    timestamps = (
        df["timestamp_ns"]
        .dropna()
    )

    if timestamps.empty:
        result["reason"] = (
            "Trace contains no valid timestamps."
        )
        return result

    duration_ns = (
        float(timestamps.max())
        - float(timestamps.min())
    )

    result["duration_ns"] = duration_ns

    if duration_ns <= 0:
        result["reason"] = (
            "Trace duration is zero or invalid."
        )
        return result

    result["valid"] = True

    result["reason"] = (
        "Trace contains valid timestamp data "
        "with a positive capture duration."
    )

    return result


# ============================================================
# DEADLINE ANALYSIS
# ============================================================

def analyze_deadlines(
    df: pd.DataFrame
) -> dict:

    explicit_misses = int(
        (
            df["event"]
            == "DEADLINE_MISS"
        ).sum()
    )

    # --------------------------------------------------------
    # Evaluate END records where execution and deadline
    # are both available.
    # --------------------------------------------------------

    deadline_rows = df[
        (
            df["event"]
            == "END"
        )
        &
        df["execution_time_ns"].notna()
        &
        df["deadline_ns"].notna()
        &
        (
            df["deadline_ns"]
            > 0
        )
    ].copy()

    calculated_misses = int(
        (
            deadline_rows[
                "execution_time_ns"
            ]
            >
            deadline_rows[
                "deadline_ns"
            ]
        ).sum()
    )

    deadline_met = int(
        (
            deadline_rows[
                "execution_time_ns"
            ]
            <=
            deadline_rows[
                "deadline_ns"
            ]
        ).sum()
    )

    measurements = len(
        deadline_rows
    )

    # --------------------------------------------------------
    # Use strongest actual evidence.
    # --------------------------------------------------------

    total_misses = max(
        explicit_misses,
        calculated_misses,
    )

    if measurements > 0:
        compliance = (
            deadline_met
            / measurements
            * 100.0
        )
    else:
        compliance = None

    return {
        "explicit_misses":
            explicit_misses,

        "calculated_misses":
            calculated_misses,

        "deadline_misses":
            total_misses,

        "measurements":
            measurements,

        "deadline_met":
            deadline_met,

        "compliance_percent":
            compliance,
    }


# ============================================================
# SYSTEM HEALTH
# ============================================================

def determine_system_health(
    integrity: dict,
    deadline_info: dict
) -> dict:

    # --------------------------------------------------------
    # IMPORTANT:
    # Health is NEVER based on testbench coverage.
    # --------------------------------------------------------

    if not integrity["valid"]:

        return {
            "status": "ERROR",
            "reason": integrity["reason"],
        }

    if (
        deadline_info[
            "deadline_misses"
        ] > 0
    ):

        misses = (
            deadline_info[
                "deadline_misses"
            ]
        )

        return {
            "status": "WARNING",
            "reason": (
                f"{misses} deadline miss(es) "
                "were detected from the RTOS trace."
            ),
        }

    return {
        "status": "HEALTHY",
        "reason": (
            "Trace is valid and no deadline "
            "misses were recorded or calculated."
        ),
    }


# ============================================================
# TESTBENCH COVERAGE
# ============================================================

def analyze_testbench_coverage(
    df: pd.DataFrame
) -> dict:

    present = []

    for testbench in EXPECTED_TESTBENCHES:

        if testbench in set(
            df["testbench"]
            .dropna()
            .astype(str)
            .tolist()
        ):

            present.append(
                testbench
            )

    missing = [
        testbench
        for testbench in EXPECTED_TESTBENCHES
        if testbench not in present
    ]

    coverage_percent = (
        len(present)
        / len(EXPECTED_TESTBENCHES)
        * 100.0
    )

    return {
        "present":
            present,

        "missing":
            missing,

        "count":
            len(present),

        "total":
            len(EXPECTED_TESTBENCHES),

        "percent":
            coverage_percent,
    }


# ============================================================
# EXECUTION STATISTICS
# ============================================================

def analyze_execution(
    df: pd.DataFrame
) -> dict:

    end_rows = df[
        (
            df["event"]
            == "END"
        )
        &
        df["execution_time_ns"].notna()
    ].copy()

    if end_rows.empty:

        return {
            "count": 0,
            "average_ms": 0.0,
            "minimum_ms": 0.0,
            "maximum_ms": 0.0,
            "total_ms": 0.0,
        }

    execution_ns = (
        pd.to_numeric(
            end_rows[
                "execution_time_ns"
            ],
            errors="coerce"
        )
        .dropna()
        .clip(lower=0)
    )

    if execution_ns.empty:

        return {
            "count": 0,
            "average_ms": 0.0,
            "minimum_ms": 0.0,
            "maximum_ms": 0.0,
            "total_ms": 0.0,
        }

    return {
        "count":
            len(execution_ns),

        "average_ms":
            float(
                execution_ns.mean()
            )
            / 1_000_000.0,

        "minimum_ms":
            float(
                execution_ns.min()
            )
            / 1_000_000.0,

        "maximum_ms":
            float(
                execution_ns.max()
            )
            / 1_000_000.0,

        "total_ms":
            float(
                execution_ns.sum()
            )
            / 1_000_000.0,
    }


# ============================================================
# AGGREGATE TASK LOAD
# ============================================================

def calculate_aggregate_task_load(
    df: pd.DataFrame,
    integrity: dict
) -> dict:

    end_rows = df[
        (
            df["event"]
            == "END"
        )
        &
        df["execution_time_ns"].notna()
    ]

    execution_ns = (
        pd.to_numeric(
            end_rows[
                "execution_time_ns"
            ],
            errors="coerce"
        )
        .dropna()
        .clip(lower=0)
    )

    aggregate_execution_ns = float(
        execution_ns.sum()
    )

    duration_ns = float(
        integrity["duration_ns"]
    )

    if duration_ns <= 0:

        return {
            "execution_ms":
                aggregate_execution_ns
                / 1_000_000.0,

            "load_percent":
                None,
        }

    load_percent = (
        aggregate_execution_ns
        / duration_ns
        * 100.0
    )

    return {
        "execution_ms":
            aggregate_execution_ns
            / 1_000_000.0,

        "load_percent":
            load_percent,
    }


# ============================================================
# CONTEXT EVENTS
# ============================================================

def analyze_context_events(
    df: pd.DataFrame
) -> dict:

    context = df[
        df["event"]
        == "CONTEXT_SWITCH"
    ]

    count = len(context)

    by_testbench = (
        context[
            "testbench"
        ]
        .value_counts()
        .to_dict()
    )

    return {
        "count":
            count,

        "by_testbench":
            by_testbench,
    }


# ============================================================
# TEMPERATURE ANALYSIS
# ============================================================

def analyze_temperature(
    df: pd.DataFrame
) -> dict:

    temperature = df[
        df["event"]
        == "TEMPERATURE"
    ].copy()

    values = pd.to_numeric(
        temperature[
            "temperature_c"
        ],
        errors="coerce"
    ).dropna()

    if values.empty:

        return {
            "samples": 0,
            "minimum": None,
            "average": None,
            "maximum": None,
            "delta": None,
            "first": None,
            "last": None,
        }

    first = float(
        values.iloc[0]
    )

    last = float(
        values.iloc[-1]
    )

    return {
        "samples":
            len(values),

        "minimum":
            float(values.min()),

        "average":
            float(values.mean()),

        "maximum":
            float(values.max()),

        "delta":
            last - first,

        "first":
            first,

        "last":
            last,
    }


# ============================================================
# JITTER ANALYSIS
# ============================================================

def analyze_jitter(
    df: pd.DataFrame
) -> dict:

    starts = df[
        df["event"]
        == "START"
    ].copy()

    if starts.empty:

        return {
            "samples": 0,
            "average_ms": None,
            "minimum_ms": None,
            "maximum_ms": None,
            "jitter_ms": None,
        }

    starts = starts.sort_values(
        [
            "testbench",
            "task_id",
            "timestamp_ns",
        ]
    )

    starts[
        "interval_ns"
    ] = (
        starts
        .groupby(
            [
                "testbench",
                "task_id",
            ]
        )[
            "timestamp_ns"
        ]
        .diff()
    )

    intervals = (
        starts[
            "interval_ns"
        ]
        .dropna()
    )

    if intervals.empty:

        return {
            "samples": 0,
            "average_ms": None,
            "minimum_ms": None,
            "maximum_ms": None,
            "jitter_ms": None,
        }

    intervals_ms = (
        intervals
        / 1_000_000.0
    )

    return {
        "samples":
            len(intervals_ms),

        "average_ms":
            float(
                intervals_ms.mean()
            ),

        "minimum_ms":
            float(
                intervals_ms.min()
            ),

        "maximum_ms":
            float(
                intervals_ms.max()
            ),

        "jitter_ms":
            float(
                intervals_ms.std()
            )
            if len(intervals_ms) > 1
            else 0.0,
    }


# ============================================================
# TESTBENCH RECORD SUMMARY
# ============================================================

def testbench_summary(
    df: pd.DataFrame
) -> pd.DataFrame:

    summary = (
        df
        .groupby(
            "testbench",
            dropna=False
        )
        .agg(
            records=(
                "event",
                "size"
            ),

            start_events=(
                "event",
                lambda x:
                    int(
                        (
                            x == "START"
                        ).sum()
                    )
            ),

            end_events=(
                "event",
                lambda x:
                    int(
                        (
                            x == "END"
                        ).sum()
                    )
            ),

            deadline_misses=(
                "event",
                lambda x:
                    int(
                        (
                            x
                            == "DEADLINE_MISS"
                        ).sum()
                    )
            ),

            context_events=(
                "event",
                lambda x:
                    int(
                        (
                            x
                            == "CONTEXT_SWITCH"
                        ).sum()
                    )
            ),

            temperature_events=(
                "event",
                lambda x:
                    int(
                        (
                            x
                            == "TEMPERATURE"
                        ).sum()
                    )
            ),
        )
        .reset_index()
    )

    return summary


# ============================================================
# FORMATTERS
# ============================================================

def format_number(
    value,
    decimals=3
):

    if value is None:
        return "N/A"

    if isinstance(
        value,
        (float, np.floating)
    ):
        return f"{value:.{decimals}f}"

    return str(value)


def format_percent(
    value
):

    if value is None:
        return "N/A"

    return f"{value:.2f}%"


# ============================================================
# REPORT GENERATION
# ============================================================

def generate_report(
    df: pd.DataFrame,
    trace_path: Path
) -> str:

    integrity = (
        analyze_trace_integrity(
            df
        )
    )

    deadlines = (
        analyze_deadlines(
            df
        )
    )

    health = (
        determine_system_health(
            integrity,
            deadlines
        )
    )

    coverage = (
        analyze_testbench_coverage(
            df
        )
    )

    execution = (
        analyze_execution(
            df
        )
    )

    aggregate_load = (
        calculate_aggregate_task_load(
            df,
            integrity
        )
    )

    context = (
        analyze_context_events(
            df
        )
    )

    temperature = (
        analyze_temperature(
            df
        )
    )

    jitter = (
        analyze_jitter(
            df
        )
    )

    tb_summary = (
        testbench_summary(
            df
        )
    )

    # --------------------------------------------------------
    # Capture window
    # --------------------------------------------------------

    duration_ms = (
        integrity["duration_ns"]
        / 1_000_000.0
    )

    # --------------------------------------------------------
    # Unique task/testbench combinations
    # --------------------------------------------------------

    unique_tasks = (
        df[
            [
                "testbench",
                "task_id",
            ]
        ]
        .drop_duplicates()
        .shape[0]
    )

    # --------------------------------------------------------
    # Event counts
    # --------------------------------------------------------

    event_counts = (
        df["event"]
        .value_counts()
        .to_dict()
    )

    generated_at = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    # ========================================================
    # BUILD REPORT
    # ========================================================

    lines = []

    lines.append(
        "============================================================"
    )

    lines.append(
        "        AUTOMOTIVE RTOS PERFORMANCE ANALYZER"
    )

    lines.append(
        "                 PERFORMANCE REPORT"
    )

    lines.append(
        "============================================================"
    )

    lines.append("")

    lines.append(
        f"Generated          : {generated_at}"
    )

    lines.append(
        f"Trace File         : {trace_path.name}"
    )

    lines.append(
        f"Trace Records      : {len(df):,}"
    )

    lines.append(
        f"Unique Task Groups : {unique_tasks:,}"
    )

    lines.append(
        f"Capture Window     : {duration_ms:.3f} ms"
    )

    lines.append("")

    # ========================================================
    # SYSTEM HEALTH
    # ========================================================

    lines.append(
        "------------------------------------------------------------"
    )

    lines.append(
        "SYSTEM HEALTH"
    )

    lines.append(
        "------------------------------------------------------------"
    )

    lines.append(
        f"Status             : {health['status']}"
    )

    lines.append(
        f"Reason             : {health['reason']}"
    )

    lines.append(
        f"Deadline Misses    : "
        f"{deadlines['deadline_misses']}"
    )

    lines.append(
        f"Deadline Checked   : "
        f"{deadlines['measurements']}"
    )

    lines.append("")

    # ========================================================
    # TRACE INTEGRITY
    # ========================================================

    lines.append(
        "------------------------------------------------------------"
    )

    lines.append(
        "TRACE INTEGRITY"
    )

    lines.append(
        "------------------------------------------------------------"
    )

    lines.append(
        f"Valid Trace        : "
        f"{'YES' if integrity['valid'] else 'NO'}"
    )

    lines.append(
        f"Integrity Reason   : "
        f"{integrity['reason']}"
    )

    lines.append("")

    # ========================================================
    # TESTBENCH COVERAGE
    # ========================================================

    lines.append(
        "------------------------------------------------------------"
    )

    lines.append(
        "TESTBENCH COVERAGE"
    )

    lines.append(
        "------------------------------------------------------------"
    )

    lines.append(
        f"Coverage           : "
        f"{coverage['count']}/{coverage['total']}"
    )

    lines.append(
        f"Coverage Percent   : "
        f"{coverage['percent']:.2f}%"
    )

    lines.append("")

    lines.append(
        "Captured Testbenches:"
    )

    for testbench in coverage["present"]:
        lines.append(
            f"  [CAPTURED] {testbench}"
        )

    lines.append("")

    if coverage["missing"]:

        lines.append(
            "Not Present in This Trace:"
        )

        for testbench in coverage["missing"]:
            lines.append(
                f"  [NOT CAPTURED] {testbench}"
            )

    else:

        lines.append(
            "All 11 expected testbenches "
            "are present in the trace."
        )

    lines.append("")

    # ========================================================
    # EXECUTION PERFORMANCE
    # ========================================================

    lines.append(
        "------------------------------------------------------------"
    )

    lines.append(
        "EXECUTION PERFORMANCE"
    )

    lines.append(
        "------------------------------------------------------------"
    )

    lines.append(
        f"END Events         : "
        f"{execution['count']:,}"
    )

    lines.append(
        f"Average Execution  : "
        f"{execution['average_ms']:.3f} ms"
    )

    lines.append(
        f"Minimum Execution  : "
        f"{execution['minimum_ms']:.3f} ms"
    )

    lines.append(
        f"Maximum Execution  : "
        f"{execution['maximum_ms']:.3f} ms"
    )

    lines.append(
        f"Total Execution    : "
        f"{execution['total_ms']:.3f} ms"
    )

    lines.append("")

    # ========================================================
    # AGGREGATE TASK LOAD
    # ========================================================

    lines.append(
        "------------------------------------------------------------"
    )

    lines.append(
        "AGGREGATE TASK LOAD"
    )

    lines.append(
        "------------------------------------------------------------"
    )

    lines.append(
        f"Aggregate Execution: "
        f"{aggregate_load['execution_ms']:.3f} ms"
    )

    lines.append(
        f"Aggregate Task Load: "
        f"{format_percent(aggregate_load['load_percent'])}"
    )

    lines.append(
        "Definition         : Sum of recorded task execution "
        "time divided by wall-clock trace duration."
    )

    lines.append(
        "Note               : This is NOT physical CPU utilization."
    )

    lines.append("")

    # ========================================================
    # DEADLINE PERFORMANCE
    # ========================================================

    lines.append(
        "------------------------------------------------------------"
    )

    lines.append(
        "DEADLINE PERFORMANCE"
    )

    lines.append(
        "------------------------------------------------------------"
    )

    lines.append(
        f"Explicit Miss Events: "
        f"{deadlines['explicit_misses']}"
    )

    lines.append(
        f"Calculated Misses   : "
        f"{deadlines['calculated_misses']}"
    )

    lines.append(
        f"Total Misses        : "
        f"{deadlines['deadline_misses']}"
    )

    lines.append(
        f"Measurements       : "
        f"{deadlines['measurements']}"
    )

    lines.append(
        f"Deadlines Met      : "
        f"{deadlines['deadline_met']}"
    )

    lines.append(
        f"Compliance         : "
        f"{format_percent(deadlines['compliance_percent'])}"
    )

    lines.append("")

    # ========================================================
    # JITTER
    # ========================================================

    lines.append(
        "------------------------------------------------------------"
    )

    lines.append(
        "JITTER ANALYSIS"
    )

    lines.append(
        "------------------------------------------------------------"
    )

    lines.append(
        f"Interval Samples   : "
        f"{jitter['samples']}"
    )

    lines.append(
        f"Average Interval   : "
        f"{format_number(jitter['average_ms'])} ms"
    )

    lines.append(
        f"Minimum Interval   : "
        f"{format_number(jitter['minimum_ms'])} ms"
    )

    lines.append(
        f"Maximum Interval   : "
        f"{format_number(jitter['maximum_ms'])} ms"
    )

    lines.append(
        f"Jitter Std Dev     : "
        f"{format_number(jitter['jitter_ms'])} ms"
    )

    lines.append("")

    # ========================================================
    # CONTEXT EVENTS
    # ========================================================

    lines.append(
        "------------------------------------------------------------"
    )

    lines.append(
        "CONTEXT-SWITCH ACTIVITY"
    )

    lines.append(
        "------------------------------------------------------------"
    )

    lines.append(
        f"Context Events     : "
        f"{context['count']:,}"
    )

    lines.append(
        "Instrumentation    : sched_yield() testbench events"
    )

    lines.append(
        "Interpretation     : These are yield instrumentation "
        "records, not kernel-confirmed context-switch counts."
    )

    lines.append("")

    # ========================================================
    # TEMPERATURE
    # ========================================================

    lines.append(
        "------------------------------------------------------------"
    )

    lines.append(
        "TEMPERATURE MONITORING"
    )

    lines.append(
        "------------------------------------------------------------"
    )

    lines.append(
        f"Temperature Samples: "
        f"{temperature['samples']}"
    )

    if temperature["samples"] > 0:

        lines.append(
            f"First Temperature  : "
            f"{temperature['first']:.2f} °C"
        )

        lines.append(
            f"Minimum Temperature: "
            f"{temperature['minimum']:.2f} °C"
        )

        lines.append(
            f"Average Temperature: "
            f"{temperature['average']:.2f} °C"
        )

        lines.append(
            f"Maximum Temperature: "
            f"{temperature['maximum']:.2f} °C"
        )

        lines.append(
            f"Temperature Delta  : "
            f"{temperature['delta']:+.2f} °C"
        )

        lines.append(
            f"Last Temperature   : "
            f"{temperature['last']:.2f} °C"
        )

    else:

        lines.append(
            "Temperature Data   : "
            "No TEMPERATURE events were present."
        )

    lines.append("")

    # ========================================================
    # EVENT SUMMARY
    # ========================================================

    lines.append(
        "------------------------------------------------------------"
    )

    lines.append(
        "EVENT SUMMARY"
    )

    lines.append(
        "------------------------------------------------------------"
    )

    for event_name in sorted(
        event_counts.keys()
    ):

        lines.append(
            f"{event_name:<20}: "
            f"{event_counts[event_name]:,}"
        )

    lines.append("")

    # ========================================================
    # TESTBENCH DETAIL
    # ========================================================

    lines.append(
        "------------------------------------------------------------"
    )

    lines.append(
        "TESTBENCH DETAIL"
    )

    lines.append(
        "------------------------------------------------------------"
    )

    if tb_summary.empty:

        lines.append(
            "No testbench records available."
        )

    else:

        for row in tb_summary.itertuples(
            index=False
        ):

            lines.append(
                f"\n[{row.testbench}]"
            )

            lines.append(
                f"  Records           : "
                f"{row.records}"
            )

            lines.append(
                f"  START events      : "
                f"{row.start_events}"
            )

            lines.append(
                f"  END events        : "
                f"{row.end_events}"
            )

            lines.append(
                f"  Deadline misses   : "
                f"{row.deadline_misses}"
            )

            lines.append(
                f"  Context events    : "
                f"{row.context_events}"
            )

            lines.append(
                f"  Temperature events: "
                f"{row.temperature_events}"
            )

    lines.append("")

    # ========================================================
    # FINAL INTERPRETATION
    # ========================================================

    lines.append(
        "============================================================"
    )

    lines.append(
        "FINAL ANALYSIS"
    )

    lines.append(
        "============================================================"
    )

    lines.append(
        f"System Health      : "
        f"{health['status']}"
    )

    lines.append(
        f"Trace Valid        : "
        f"{'YES' if integrity['valid'] else 'NO'}"
    )

    lines.append(
        f"Deadline Misses    : "
        f"{deadlines['deadline_misses']}"
    )

    lines.append(
        f"Testbench Coverage : "
        f"{coverage['count']}/{coverage['total']}"
    )

    lines.append(
        f"Context Events     : "
        f"{context['count']}"
    )

    lines.append(
        f"Temperature Samples: "
        f"{temperature['samples']}"
    )

    lines.append("")

    lines.append(
        "IMPORTANT:"
    )

    lines.append(
        "System Health is derived from actual trace validity "
        "and deadline evidence."
    )

    lines.append(
        "Testbench coverage is reported independently and "
        "does not automatically change System Health."
    )

    lines.append(
        "Aggregate Task Load is a trace-based execution metric "
        "and must not be interpreted as physical CPU utilization."
    )

    lines.append("")

    lines.append(
        "============================================================"
    )

    lines.append(
        "                 END OF PERFORMANCE REPORT"
    )

    lines.append(
        "============================================================"
    )

    return "\n".join(lines)


# ============================================================
# WRITE REPORT
# ============================================================

def save_report(
    report: str,
    output_path: Path
):

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    output_path.write_text(
        report,
        encoding="utf-8"
    )

    return output_path


# ============================================================
# MAIN
# ============================================================

def main():

    # --------------------------------------------------------
    # Command-line trace path
    # --------------------------------------------------------

    if len(sys.argv) >= 2:

        trace_path = Path(
            sys.argv[1]
        )

        if not trace_path.is_absolute():

            trace_path = (
                BASE_DIR
                / trace_path
            )

    else:

        trace_path = (
            DEFAULT_TRACE
        )

    # --------------------------------------------------------
    # Optional output path
    # --------------------------------------------------------

    if len(sys.argv) >= 3:

        output_path = Path(
            sys.argv[2]
        )

        if not output_path.is_absolute():

            output_path = (
                BASE_DIR
                / output_path
            )

    else:

        output_path = (
            DEFAULT_REPORT
        )

    print("")
    print(
        "============================================================"
    )
    print(
        " AUTOMOTIVE RTOS PERFORMANCE ANALYZER"
    )
    print(
        " Report Generator"
    )
    print(
        "============================================================"
    )

    print(
        f"Trace : {trace_path}"
    )

    try:

        df = load_trace(
            trace_path
        )

        print(
            f"Records loaded : {len(df):,}"
        )

        report = generate_report(
            df,
            trace_path
        )

        save_report(
            report,
            output_path
        )

        print(
            f"Report saved   : {output_path}"
        )

        print(
            "Report generation completed successfully."
        )

        print("")

    except Exception as exc:

        print("")
        print(
            "REPORT GENERATION FAILED"
        )

        print(
            f"Reason: {exc}"
        )

        print("")

        raise


if __name__ == "__main__":
    main()