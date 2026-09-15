import os
import pandas as pd


# ============================================================
# AUTOMOTIVE RTOS ANALYZER
# PHASE 5.3 - FINAL TESTBENCH VALIDATION
# ============================================================

TRACE_FILE = "rtos_trace.csv"


TESTBENCHES = [
    "Task Scaling",
    "Priority Variation",
    "Execution-Time Variation",
    "Period Variation",
    "Deadline Testing",
    "CPU Load Variation",
    "Context-Switch Testing",
    "Mixed Workload",
    "Long-Duration Stability",
    "Stress Testing",
    "Temperature Monitoring"
]


def header():
    print("=" * 78)
    print("        AUTOMOTIVE RTOS ANALYZER - PHASE 5.3")
    print("             FINAL TESTBENCH VALIDATION")
    print("=" * 78)
    print()


def load_trace():

    if not os.path.exists(TRACE_FILE):
        print("[FAIL] rtos_trace.csv not found")
        return None

    try:
        df = pd.read_csv(TRACE_FILE)
        print(f"[PASS] Trace loaded: {len(df)} records")
        return df

    except Exception as e:
        print(f"[FAIL] Unable to read trace: {e}")
        return None


def analyze_trace(df):

    print()
    print("-" * 78)
    print("TRACE ANALYSIS")
    print("-" * 78)

    events = set(
        str(x).strip().upper()
        for x in df["event"].dropna()
    )

    print(
        "[INFO] Events:",
        ", ".join(sorted(events))
    )

    tasks = sorted(
        df["task_id"].dropna().unique()
    )

    print(f"[INFO] Tasks detected: {len(tasks)}")

    start_count = (
        df["event"].astype(str).str.upper() == "START"
    ).sum()

    end_count = (
        df["event"].astype(str).str.upper() == "END"
    ).sum()

    print(f"[INFO] START events: {start_count}")
    print(f"[INFO] END events:   {end_count}")

    deadline_count = (
        pd.to_numeric(
            df["deadline_ns"],
            errors="coerce"
        ).fillna(0) > 0
    ).sum()

    print(
        f"[INFO] Deadline measurements: "
        f"{deadline_count}"
    )

    context_count = (
        df["event"].astype(str).str.upper()
        == "CONTEXT_SWITCH"
    ).sum()

    temperature_count = (
        df["event"].astype(str).str.upper()
        == "TEMPERATURE"
    ).sum()

    print(
        f"[INFO] Context-switch events: "
        f"{context_count}"
    )

    print(
        f"[INFO] Temperature events: "
        f"{temperature_count}"
    )


def print_matrix():

    print()
    print("=" * 78)
    print("                 11-TESTBENCH VALIDATION MATRIX")
    print("=" * 78)
    print()

    print(
        f"{'#':<4}"
        f"{'TESTBENCH':<32}"
        f"{'EXECUTION':<13}"
        f"{'TRACE':<10}"
        f"{'STATUS'}"
    )

    print("-" * 78)

    for i, name in enumerate(TESTBENCHES, 1):

        print(
            f"{i:<4}"
            f"{name:<32}"
            f"{'READY':<13}"
            f"{'CHECK':<10}"
            f"{'PENDING'}"
        )

    print()
    print("-" * 78)
    print("NOTE:")
    print("This matrix is the final validation checklist.")
    print("The existing QNX testbench code is NOT modified.")
    print("-" * 78)


def main():

    header()

    df = load_trace()

    if df is None:
        return

    required_columns = [
        "timestamp_ns",
        "task_id",
        "event",
        "execution_time_ns",
        "deadline_ns"
    ]

    missing = [
        c for c in required_columns
        if c not in df.columns
    ]

    if missing:

        print("[FAIL] Missing columns:")

        for column in missing:
            print("       ", column)

        return

    analyze_trace(df)

    print_matrix()

    print()
    print("=" * 78)
    print("PHASE 5.3 INITIAL VALIDATION READY")
    print("=" * 78)


if __name__ == "__main__":
    main()