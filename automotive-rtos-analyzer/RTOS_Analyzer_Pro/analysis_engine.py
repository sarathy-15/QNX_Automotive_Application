from __future__ import annotations

from pathlib import Path
from typing import Dict, Tuple

import numpy as np
import pandas as pd


# ============================================================
# AUTOMOTIVE RTOS ANALYZER
# PHASE 5.3.3
# PYTHON ANALYSIS ENGINE
# ============================================================


# ------------------------------------------------------------
# REQUIRED CSV FORMAT
# ------------------------------------------------------------

REQUIRED_COLUMNS = [
    "timestamp_ns",
    "task_id",
    "event",
    "execution_time_ns",
    "deadline_ns",
]


OPTIONAL_COLUMNS = [
    "testbench",
    "temperature_c",
]


# ------------------------------------------------------------
# EXPECTED TESTBENCHES
# ------------------------------------------------------------

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


# ------------------------------------------------------------
# EXPECTED EVENTS
# ------------------------------------------------------------

EXPECTED_EVENTS = [
    "START",
    "END",
    "DEADLINE_MISS",
    "CONTEXT_SWITCH",
    "TEMPERATURE",
]


# ============================================================
# 1. LOAD TRACE
# ============================================================

def load_trace(path: str = "rtos_trace.csv") -> pd.DataFrame:
    """
    Load and normalize the QNX RTOS trace CSV.

    Supports both:
      - New trace format with testbench + temperature_c
      - Older trace format without those columns
    """

    csv_path = Path(path)

    if not csv_path.exists():
        raise FileNotFoundError(
            f"Trace file not found: {csv_path}"
        )

    df = pd.read_csv(csv_path)

    # --------------------------------------------------------
    # Check required columns
    # --------------------------------------------------------

    missing = [
        column
        for column in REQUIRED_COLUMNS
        if column not in df.columns
    ]

    if missing:
        raise ValueError(
            "Missing required columns: "
            + ", ".join(missing)
        )

    # --------------------------------------------------------
    # Add optional columns when using old CSV
    # --------------------------------------------------------

    if "testbench" not in df.columns:
        df["testbench"] = "UNKNOWN"

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
        .fillna("UNKNOWN")
        .astype(str)
        .str.strip()
    )

    # --------------------------------------------------------
    # Remove unusable records
    # --------------------------------------------------------

    df = df.dropna(
        subset=[
            "timestamp_ns",
            "task_id",
            "event",
        ]
    ).copy()

    # --------------------------------------------------------
    # Integer conversion
    # --------------------------------------------------------

    df["timestamp_ns"] = (
        df["timestamp_ns"]
        .astype(np.int64)
    )

    df["task_id"] = (
        df["task_id"]
        .astype(int)
    )

    df["execution_time_ns"] = (
        df["execution_time_ns"]
        .fillna(0)
        .astype(np.int64)
    )

    df["deadline_ns"] = (
        df["deadline_ns"]
        .fillna(0)
        .astype(np.int64)
    )

    # --------------------------------------------------------
    # Sort by timestamp
    # --------------------------------------------------------

    df = (
        df.sort_values(
            "timestamp_ns"
        )
        .reset_index(drop=True)
    )

    # --------------------------------------------------------
    # Relative time
    # --------------------------------------------------------

    if not df.empty:

        base_timestamp = int(
            df["timestamp_ns"].min()
        )

        df["time_ms"] = (
            df["timestamp_ns"]
            - base_timestamp
        ) / 1_000_000.0

    else:

        df["time_ms"] = pd.Series(
            dtype=float
        )

    # --------------------------------------------------------
    # Convenience columns
    # --------------------------------------------------------

    df["execution_time_ms"] = (
        df["execution_time_ns"]
        / 1_000_000.0
    )

    df["deadline_ms"] = (
        df["deadline_ns"]
        / 1_000_000.0
    )

    return df


# ============================================================
# 2. PAIR START / END EXECUTIONS
# ============================================================

def pair_executions(
    df: pd.DataFrame
) -> pd.DataFrame:
    """
    Pair START and END events.

    IMPORTANT:
    Tasks are identified using:

        testbench + task_id

    because task IDs are reused between testbenches.
    """

    output_columns = [
        "Testbench",
        "task_id",
        "Task",
        "start_ms",
        "end_ms",
        "duration_ms",
        "execution_time_ms",
        "deadline_ms",
        "deadline_missed",
    ]

    if df.empty:
        return pd.DataFrame(
            columns=output_columns
        )

    base = int(
        df["timestamp_ns"].min()
    )

    # --------------------------------------------------------
    # START event queues
    # --------------------------------------------------------

    starts: Dict[
        Tuple[str, int],
        list[int]
    ] = {}

    rows = []

    # --------------------------------------------------------
    # Process events
    # --------------------------------------------------------

    for _, record in df.iterrows():

        testbench = str(
            record["testbench"]
        )

        task_id = int(
            record["task_id"]
        )

        event = str(
            record["event"]
        )

        key = (
            testbench,
            task_id
        )

        timestamp = int(
            record["timestamp_ns"]
        )

        # ----------------------------------------------------
        # START
        # ----------------------------------------------------

        if event == "START":

            starts.setdefault(
                key,
                []
            ).append(timestamp)

        # ----------------------------------------------------
        # END
        # ----------------------------------------------------

        elif event == "END":

            queue = starts.get(
                key,
                []
            )

            if not queue:
                continue

            start_ns = queue.pop(0)

            end_ns = timestamp

            execution_ns = int(
                record["execution_time_ns"]
            )

            deadline_ns = int(
                record["deadline_ns"]
            )

            deadline_missed = (
                deadline_ns > 0
                and execution_ns > deadline_ns
            )

            rows.append(
                {
                    "Testbench": testbench,

                    "task_id": task_id,

                    "Task":
                        f"{testbench} / T{task_id}",

                    "start_ms":
                        (
                            start_ns - base
                        ) / 1_000_000.0,

                    "end_ms":
                        (
                            end_ns - base
                        ) / 1_000_000.0,

                    "duration_ms":
                        max(
                            0,
                            end_ns - start_ns
                        ) / 1_000_000.0,

                    "execution_time_ms":
                        execution_ns
                        / 1_000_000.0,

                    "deadline_ms":
                        deadline_ns
                        / 1_000_000.0,

                    "deadline_missed":
                        bool(
                            deadline_missed
                        ),
                }
            )

    return pd.DataFrame(
        rows,
        columns=output_columns
    )


# ============================================================
# 3. TASK STATISTICS
# ============================================================

def task_statistics(
    df: pd.DataFrame
) -> pd.DataFrame:
    """
    Calculate execution statistics for each
    testbench/task combination.
    """

    output_columns = [
        "Testbench",
        "Task",
        "Executions",
        "Average (ms)",
        "Minimum (ms)",
        "Maximum (ms)",
        "Total (ms)",
        "Execution Share (%)",
    ]

    ends = df[
        df["event"] == "END"
    ].copy()

    if ends.empty:
        return pd.DataFrame(
            columns=output_columns
        )

    ends["exec_ms"] = (
        ends["execution_time_ns"]
        / 1_000_000.0
    )

    grouped = (
        ends
        .groupby(
            [
                "testbench",
                "task_id",
            ],
            dropna=False
        )["exec_ms"]
    )

    rows = []

    for (
        (testbench, task_id),
        values
    ) in grouped:

        rows.append(
            {
                "Testbench":
                    str(testbench),

                "Task":
                    f"{testbench} / T{int(task_id)}",

                "Executions":
                    int(values.count()),

                "Average (ms)":
                    float(values.mean()),

                "Minimum (ms)":
                    float(values.min()),

                "Maximum (ms)":
                    float(values.max()),

                "Total (ms)":
                    float(values.sum()),
            }
        )

    out = pd.DataFrame(rows)

    if out.empty:
        out["Execution Share (%)"] = []
        return out

    total_execution = float(
        out["Total (ms)"].sum()
    )

    if total_execution > 0:

        out["Execution Share (%)"] = (
            out["Total (ms)"]
            / total_execution
            * 100.0
        )

    else:

        out["Execution Share (%)"] = 0.0

    return out[output_columns]


# ============================================================
# 4. JITTER ANALYSIS
# ============================================================

def jitter_statistics(
    df: pd.DataFrame
):
    """
    Calculate periodic START-to-START jitter.

    Grouping is done using:

        testbench + task_id
    """

    summary_columns = [
        "Testbench",
        "Task",
        "Samples",
        "Average Period (ms)",
        "Average Jitter (ms)",
        "Maximum Jitter (ms)",
        "Minimum Jitter (ms)",
    ]

    sample_columns = [
        "Testbench",
        "Task",
        "Sample",
        "Period (ms)",
        "Jitter (ms)",
    ]

    starts = df[
        df["event"] == "START"
    ].copy()

    summary_rows = []
    sample_rows = []

    if starts.empty:

        return (
            pd.DataFrame(
                columns=summary_columns
            ),
            pd.DataFrame(
                columns=sample_columns
            ),
        )

    for (
        (testbench, task_id),
        group
    ) in starts.groupby(
        [
            "testbench",
            "task_id",
        ]
    ):

        timestamps = np.sort(
            group[
                "timestamp_ns"
            ].to_numpy(
                dtype=np.int64
            )
        )

        if len(timestamps) < 2:
            continue

        intervals = (
            np.diff(timestamps)
            / 1_000_000.0
        )

        average_period = float(
            intervals.mean()
        )

        jitter = np.abs(
            intervals
            - average_period
        )

        task_name = (
            f"{testbench} / T{int(task_id)}"
        )

        summary_rows.append(
            {
                "Testbench":
                    str(testbench),

                "Task":
                    task_name,

                "Samples":
                    int(len(intervals)),

                "Average Period (ms)":
                    average_period,

                "Average Jitter (ms)":
                    float(jitter.mean()),

                "Maximum Jitter (ms)":
                    float(jitter.max()),

                "Minimum Jitter (ms)":
                    float(jitter.min()),
            }
        )

        for index, (
            period,
            jitter_value
        ) in enumerate(
            zip(
                intervals,
                jitter
            ),
            start=1
        ):

            sample_rows.append(
                {
                    "Testbench":
                        str(testbench),

                    "Task":
                        task_name,

                    "Sample":
                        index,

                    "Period (ms)":
                        float(period),

                    "Jitter (ms)":
                        float(jitter_value),
                }
            )

    return (
        pd.DataFrame(
            summary_rows,
            columns=summary_columns
        ),
        pd.DataFrame(
            sample_rows,
            columns=sample_columns
        ),
    )


# ============================================================
# 5. DEADLINE ANALYSIS
# ============================================================

def deadline_statistics(
    df: pd.DataFrame
):
    """
    Analyze deadline performance.

    Supports both:

        DEADLINE_MISS events

    and:

        END execution_time > deadline_time
    """

    detail_columns = [
        "Testbench",
        "Task",
        "task_id",
        "Execution (ms)",
        "Deadline (ms)",
        "Status",
        "Source",
    ]

    # --------------------------------------------------------
    # Explicit deadline miss events
    # --------------------------------------------------------

    explicit_misses = df[
        df["event"] == "DEADLINE_MISS"
    ].copy()

    # --------------------------------------------------------
    # END events with deadlines
    # --------------------------------------------------------

    deadline_ends = df[
        (
            df["event"] == "END"
        )
        &
        (
            df["deadline_ns"] > 0
        )
    ].copy()

    detail_rows = []

    # --------------------------------------------------------
    # Analyze END events
    # --------------------------------------------------------

    for _, record in deadline_ends.iterrows():

        testbench = str(
            record["testbench"]
        )

        task_id = int(
            record["task_id"]
        )

        execution_ns = int(
            record["execution_time_ns"]
        )

        deadline_ns = int(
            record["deadline_ns"]
        )

        missed = (
            execution_ns
            > deadline_ns
        )

        detail_rows.append(
            {
                "Testbench":
                    testbench,

                "Task":
                    f"{testbench} / T{task_id}",

                "task_id":
                    task_id,

                "Execution (ms)":
                    execution_ns
                    / 1_000_000.0,

                "Deadline (ms)":
                    deadline_ns
                    / 1_000_000.0,

                "Status":
                    "MISSED"
                    if missed
                    else "MET",

                "Source":
                    "END comparison",
            }
        )

    # --------------------------------------------------------
    # Explicit miss events
    # --------------------------------------------------------

    for _, record in explicit_misses.iterrows():

        testbench = str(
            record["testbench"]
        )

        task_id = int(
            record["task_id"]
        )

        execution_ns = int(
            record["execution_time_ns"]
        )

        deadline_ns = int(
            record["deadline_ns"]
        )

        detail_rows.append(
            {
                "Testbench":
                    testbench,

                "Task":
                    f"{testbench} / T{task_id}",

                "task_id":
                    task_id,

                "Execution (ms)":
                    execution_ns
                    / 1_000_000.0,

                "Deadline (ms)":
                    deadline_ns
                    / 1_000_000.0,

                "Status":
                    "MISSED",

                "Source":
                    "Explicit DEADLINE_MISS",
            }
        )

    # --------------------------------------------------------
    # No deadline information
    # --------------------------------------------------------

    if not detail_rows:

        return (
            {
                "checked": 0,
                "met": 0,
                "missed": 0,
                "success_rate": None,
                "explicit_misses": 0,
            },

            pd.DataFrame(
                columns=detail_columns
            ),
        )

    detail = pd.DataFrame(
        detail_rows,
        columns=detail_columns
    )

    checked = int(
        len(deadline_ends)
        + len(explicit_misses)
    )

    missed = int(
        (detail["Status"] == "MISSED")
        .sum()
    )

    met = max(
        0,
        checked - missed
    )

    return (
        {
            "checked":
                checked,

            "met":
                met,

            "missed":
                missed,

            "success_rate":
                (
                    met
                    / checked
                    * 100.0
                )
                if checked > 0
                else None,

            "explicit_misses":
                int(
                    len(explicit_misses)
                ),
        },

        detail,
    )


# ============================================================
# 6. TESTBENCH STATISTICS
# ============================================================

def testbench_statistics(
    df: pd.DataFrame
) -> pd.DataFrame:
    """
    Generate one summary row for every testbench.
    """

    columns = [
        "Testbench",
        "Records",
        "START",
        "END",
        "Deadline Misses",
        "Context Switches",
        "Temperature Events",
        "Executions",
        "Average Execution (ms)",
        "Maximum Execution (ms)",
    ]

    rows = []

    for testbench in EXPECTED_TESTBENCHES:

        subset = df[
            df["testbench"]
            == testbench
        ]

        ends = subset[
            subset["event"] == "END"
        ]

        rows.append(
            {
                "Testbench":
                    testbench,

                "Records":
                    int(len(subset)),

                "START":
                    int(
                        (
                            subset["event"]
                            == "START"
                        ).sum()
                    ),

                "END":
                    int(
                        (
                            subset["event"]
                            == "END"
                        ).sum()
                    ),

                "Deadline Misses":
                    int(
                        (
                            subset["event"]
                            == "DEADLINE_MISS"
                        ).sum()
                    ),

                "Context Switches":
                    int(
                        (
                            subset["event"]
                            == "CONTEXT_SWITCH"
                        ).sum()
                    ),

                "Temperature Events":
                    int(
                        (
                            subset["event"]
                            == "TEMPERATURE"
                        ).sum()
                    ),

                "Executions":
                    int(len(ends)),

                "Average Execution (ms)":
                    (
                        float(
                            ends[
                                "execution_time_ns"
                            ].mean()
                        )
                        / 1_000_000.0
                    )
                    if not ends.empty
                    else 0.0,

                "Maximum Execution (ms)":
                    (
                        float(
                            ends[
                                "execution_time_ns"
                            ].max()
                        )
                        / 1_000_000.0
                    )
                    if not ends.empty
                    else 0.0,
            }
        )

    return pd.DataFrame(
        rows,
        columns=columns
    )


# ============================================================
# 7. TESTBENCH COVERAGE
# ============================================================

def testbench_coverage(
    df: pd.DataFrame
) -> dict:
    """
    Determine how many expected testbenches
    are actually present in the trace.
    """

    present = sorted(
        set(
            df["testbench"]
            .dropna()
            .astype(str)
        )
        & set(EXPECTED_TESTBENCHES)
    )

    missing = [
        testbench
        for testbench in EXPECTED_TESTBENCHES
        if testbench not in present
    ]

    total_expected = len(
        EXPECTED_TESTBENCHES
    )

    total_present = len(
        present
    )

    percentage = (
        total_present
        / total_expected
        * 100.0
    )

    return {
        "expected":
            total_expected,

        "present":
            total_present,

        "missing":
            len(missing),

        "coverage_percent":
            percentage,

        "present_testbenches":
            present,

        "missing_testbenches":
            missing,
    }


# ============================================================
# 8. EVENT STATISTICS
# ============================================================

def event_statistics(
    df: pd.DataFrame
) -> pd.DataFrame:
    """
    Count every event type.
    """

    counts = (
        df["event"]
        .value_counts()
        .reindex(
            EXPECTED_EVENTS,
            fill_value=0
        )
    )

    return pd.DataFrame(
        {
            "Event": counts.index,
            "Count": counts.values,
        }
    ).reset_index(
        drop=True
    )


# ============================================================
# 9. TEMPERATURE ANALYSIS
# ============================================================

def temperature_statistics(
    df: pd.DataFrame
) -> dict:
    """
    Analyze TEMPERATURE events.
    """

    temperature_rows = df[
        (
            df["event"]
            == "TEMPERATURE"
        )
        &
        (
            df["temperature_c"]
            .notna()
        )
    ].copy()

    if temperature_rows.empty:

        return {
            "available": False,
            "samples": 0,
            "minimum_c": None,
            "maximum_c": None,
            "average_c": None,
            "first_c": None,
            "last_c": None,
            "change_c": None,
            "data": pd.DataFrame(),
        }

    values = (
        temperature_rows[
            "temperature_c"
        ]
        .astype(float)
    )

    first_value = float(
        values.iloc[0]
    )

    last_value = float(
        values.iloc[-1]
    )

    return {
        "available": True,

        "samples":
            int(len(values)),

        "minimum_c":
            float(values.min()),

        "maximum_c":
            float(values.max()),

        "average_c":
            float(values.mean()),

        "first_c":
            first_value,

        "last_c":
            last_value,

        "change_c":
            last_value - first_value,

        "data":
            temperature_rows[
                [
                    "timestamp_ns",
                    "time_ms",
                    "testbench",
                    "task_id",
                    "temperature_c",
                ]
            ].copy(),
    }


# ============================================================
# 10. SYSTEM SUMMARY
# ============================================================

def system_summary(
    df: pd.DataFrame
) -> dict:
    """
    Generate high-level system performance summary.
    """

    if df.empty:

        return {
            "records": 0,
            "tasks": 0,
            "testbenches": 0,
            "testbench_coverage": 0.0,
            "duration_ms": 0.0,
            "context_switches": 0,
            "temperature_events": 0,
            "deadline_misses": 0,
            "execution_occupancy": 0.0,
            "health": "NO DATA",
        }

    # --------------------------------------------------------
    # Capture duration
    # --------------------------------------------------------

    duration_ns = int(
        df["timestamp_ns"].max()
        - df["timestamp_ns"].min()
    )

    duration_ms = (
        duration_ns
        / 1_000_000.0
    )

    # --------------------------------------------------------
    # END execution
    # --------------------------------------------------------

    end_rows = df[
        df["event"] == "END"
    ]

    total_execution_ns = int(
        end_rows[
            "execution_time_ns"
        ].sum()
    )

    # --------------------------------------------------------
    # Deadline
    # --------------------------------------------------------

    deadline, _ = deadline_statistics(
        df
    )

    # --------------------------------------------------------
    # Testbench coverage
    # --------------------------------------------------------

    coverage = testbench_coverage(
        df
    )

    # --------------------------------------------------------
    # Context switch
    # --------------------------------------------------------

    context_switches = int(
        (
            df["event"]
            == "CONTEXT_SWITCH"
        ).sum()
    )

    # --------------------------------------------------------
    # Temperature
    # --------------------------------------------------------

    temperature_events = int(
        (
            df["event"]
            == "TEMPERATURE"
        ).sum()
    )

    # --------------------------------------------------------
    # Execution occupancy
    # --------------------------------------------------------

    if duration_ns > 0:

        occupancy = (
            total_execution_ns
            / duration_ns
            * 100.0
        )

    else:

        occupancy = 0.0

    # --------------------------------------------------------
    # Health
    # --------------------------------------------------------

    if deadline["missed"] > 0:

        health = "ATTENTION"

    elif coverage["present"] < coverage["expected"]:

        health = "INCOMPLETE"

    else:

        health = "HEALTHY"

    return {
        "records":
            int(len(df)),

        "tasks":
            int(df["task_id"].nunique()),

        "testbenches":
            int(coverage["present"]),

        "testbench_coverage":
            float(
                coverage[
                    "coverage_percent"
                ]
            ),

        "duration_ms":
            duration_ms,

        "context_switches":
            context_switches,

        "temperature_events":
            temperature_events,

        "deadline_misses":
            int(
                deadline["missed"]
            ),

        "execution_occupancy":
            occupancy,

        "health":
            health,
    }


# ============================================================
# 11. COMPLETE ANALYSIS
# ============================================================

def analyze_trace(
    path: str = "rtos_trace.csv"
) -> dict:
    """
    Run all analysis modules in one call.
    """

    df = load_trace(path)

    executions = pair_executions(
        df
    )

    tasks = task_statistics(
        df
    )

    jitter, jitter_samples = (
        jitter_statistics(df)
    )

    deadline, deadline_detail = (
        deadline_statistics(df)
    )

    testbenches = (
        testbench_statistics(df)
    )

    coverage = (
        testbench_coverage(df)
    )

    events = (
        event_statistics(df)
    )

    temperature = (
        temperature_statistics(df)
    )

    system = (
        system_summary(df)
    )

    return {
        "trace": df,

        "executions":
            executions,

        "tasks":
            tasks,

        "jitter":
            jitter,

        "jitter_samples":
            jitter_samples,

        "deadline":
            deadline,

        "deadline_detail":
            deadline_detail,

        "testbenches":
            testbenches,

        "coverage":
            coverage,

        "events":
            events,

        "temperature":
            temperature,

        "system":
            system,
    }


# ============================================================
# 12. MODULE TEST
# ============================================================

if __name__ == "__main__":

    print("=" * 72)
    print("AUTOMOTIVE RTOS ANALYZER")
    print("PYTHON ANALYSIS ENGINE - PHASE 5.3.3")
    print("=" * 72)

    try:

        results = analyze_trace(
            "rtos_trace.csv"
        )

        system = results[
            "system"
        ]

        coverage = results[
            "coverage"
        ]

        temperature = results[
            "temperature"
        ]

        deadline = results[
            "deadline"
        ]

        print()
        print("TRACE ANALYSIS SUCCESSFUL")
        print("-" * 72)

        print(
            f"Records              : "
            f"{system['records']}"
        )

        print(
            f"Tasks                : "
            f"{system['tasks']}"
        )

        print(
            f"Testbenches          : "
            f"{coverage['present']}/"
            f"{coverage['expected']}"
        )

        print(
            f"Coverage             : "
            f"{coverage['coverage_percent']:.2f}%"
        )

        print(
            f"Duration             : "
            f"{system['duration_ms']:.3f} ms"
        )

        print(
            f"Context switches     : "
            f"{system['context_switches']}"
        )

        print(
            f"Temperature events   : "
            f"{system['temperature_events']}"
        )

        print(
            f"Deadline misses      : "
            f"{deadline['missed']}"
        )

        print(
            f"Execution occupancy  : "
            f"{system['execution_occupancy']:.2f}%"
        )

        print(
            f"System health        : "
            f"{system['health']}"
        )

        print()
        print("TESTBENCH COVERAGE")
        print("-" * 72)

        for testbench in (
            coverage[
                "present_testbenches"
            ]
        ):
            print(
                f"[PASS] {testbench}"
            )

        for testbench in (
            coverage[
                "missing_testbenches"
            ]
        ):
            print(
                f"[MISS] {testbench}"
            )

        print()
        print("TEMPERATURE")
        print("-" * 72)

        if temperature["available"]:

            print(
                f"Samples : "
                f"{temperature['samples']}"
            )

            print(
                f"Minimum : "
                f"{temperature['minimum_c']:.2f} °C"
            )

            print(
                f"Maximum : "
                f"{temperature['maximum_c']:.2f} °C"
            )

            print(
                f"Average : "
                f"{temperature['average_c']:.2f} °C"
            )

        else:

            print(
                "No temperature samples available."
            )

        print()
        print("=" * 72)

    except Exception as error:

        print()
        print("ANALYSIS FAILED")
        print("-" * 72)
        print(
            f"Error: {error}"
        )
        print("=" * 72)