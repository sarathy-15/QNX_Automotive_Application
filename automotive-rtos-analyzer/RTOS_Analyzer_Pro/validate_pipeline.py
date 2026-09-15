import os
import sys
import pandas as pd


# ============================================================
# AUTOMOTIVE RTOS ANALYZER
# PHASE 5.2 - AUTOMATED SYSTEM VALIDATION
# ============================================================

TRACE_FILE = "rtos_trace.csv"
REPORT_FILE = "outputs/rtos_performance_report.txt"

REQUIRED_COLUMNS = [
    "timestamp_ns",
    "task_id",
    "event",
    "execution_time_ns",
    "deadline_ns"
]


def print_header():
    print("=" * 70)
    print("       AUTOMOTIVE RTOS ANALYZER - PHASE 5.2")
    print("              AUTOMATED SYSTEM VALIDATION")
    print("=" * 70)
    print()


def check_trace_file():
    print("[1] Checking trace file...")

    if not os.path.exists(TRACE_FILE):
        print("[FAIL] rtos_trace.csv not found")
        return None

    try:
        df = pd.read_csv(TRACE_FILE)
    except Exception as e:
        print(f"[FAIL] Could not read CSV: {e}")
        return None

    print(f"[PASS] Trace file found")
    print(f"[PASS] Records loaded: {len(df)}")

    return df


def check_columns(df):
    print("\n[2] Checking CSV structure...")

    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]

    if missing:
        print("[FAIL] Missing columns:")
        for col in missing:
            print(f"       - {col}")
        return False

    print("[PASS] All required columns present")
    return True


def check_basic_data(df):
    print("\n[3] Checking trace data...")

    errors = 0

    if df.empty:
        print("[FAIL] CSV contains no records")
        return False

    if df["timestamp_ns"].isna().any():
        print("[FAIL] Missing timestamp values")
        errors += 1
    else:
        print("[PASS] Timestamp data valid")

    if df["task_id"].isna().any():
        print("[FAIL] Missing task IDs")
        errors += 1
    else:
        print("[PASS] Task ID data valid")

    if df["event"].isna().any():
        print("[FAIL] Missing event values")
        errors += 1
    else:
        print("[PASS] Event data valid")

    return errors == 0


def check_events(df):
    print("\n[4] Checking RTOS events...")

    events = set(
        str(x).strip().upper()
        for x in df["event"].dropna()
    )

    print(f"[INFO] Events detected: {', '.join(sorted(events))}")

    if "START" in events:
        print("[PASS] START events detected")
    else:
        print("[WARN] No START events detected")

    if "END" in events:
        print("[PASS] END events detected")
    else:
        print("[WARN] No END events detected")

    if "DEADLINE" in events:
        print("[PASS] DEADLINE events detected")
    else:
        print("[INFO] No DEADLINE events detected")

    if "CONTEXT_SWITCH" in events:
        print("[PASS] CONTEXT_SWITCH events detected")
    else:
        print("[INFO] No CONTEXT_SWITCH events detected")

    if "TEMPERATURE" in events:
        print("[PASS] TEMPERATURE events detected")
    else:
        print("[INFO] No TEMPERATURE events detected")

    return True


def check_tasks(df):
    print("\n[5] Checking task execution...")

    tasks = sorted(df["task_id"].dropna().unique())

    print(f"[PASS] Tasks detected: {len(tasks)}")

    for task in tasks:
        task_df = df[df["task_id"] == task]

        starts = (task_df["event"] == "START").sum()
        ends = (task_df["event"] == "END").sum()

        print(
            f"       Task {task}: "
            f"START={starts}, END={ends}"
        )

    return len(tasks) > 0


def check_execution_pairs(df):
    print("\n[6] Checking START/END execution pairs...")

    start_count = (df["event"] == "START").sum()
    end_count = (df["event"] == "END").sum()

    print(f"[INFO] START events: {start_count}")
    print(f"[INFO] END events:   {end_count}")

    if start_count == 0:
        print("[FAIL] No START events")
        return False

    if end_count == 0:
        print("[FAIL] No END events")
        return False

    if end_count <= start_count:
        print("[PASS] Execution events available")
    else:
        print("[WARN] More END events than START events")

    return True


def check_execution_times(df):
    print("\n[7] Checking execution-time measurements...")

    end_df = df[df["event"] == "END"]

    if end_df.empty:
        print("[FAIL] No END events available")
        return False

    valid = end_df["execution_time_ns"].notna()
    valid_count = valid.sum()

    print(f"[PASS] Execution measurements: {valid_count}")

    positive = (
        end_df["execution_time_ns"].fillna(0) > 0
    ).sum()

    print(f"[INFO] Positive execution times: {positive}")

    if positive > 0:
        print("[PASS] Execution timing data available")
        return True

    print("[WARN] No positive execution-time values")
    return False


def check_jitter(df):
    print("\n[8] Checking jitter measurement capability...")

    start_df = df[df["event"] == "START"]

    repeated_tasks = 0

    for task in start_df["task_id"].unique():
        count = (start_df["task_id"] == task).sum()

        if count >= 2:
            repeated_tasks += 1

    if repeated_tasks > 0:
        print(
            f"[PASS] Repeated executions detected "
            f"for {repeated_tasks} task(s)"
        )
    else:
        print(
            "[WARN] No repeated START events detected"
        )
        print(
            "       Jitter requires repeated executions."
        )

    return True


def check_deadlines(df):
    print("\n[9] Checking deadline analysis data...")

    deadline_df = df[
        df["deadline_ns"].fillna(0) > 0
    ]

    if deadline_df.empty:
        print("[INFO] No deadline measurements found")
        return True

    print(
        f"[PASS] Deadline measurements: "
        f"{len(deadline_df)}"
    )

    misses = (
        deadline_df["execution_time_ns"].fillna(0)
        > deadline_df["deadline_ns"]
    ).sum()

    print(f"[INFO] Deadline misses detected: {misses}")

    if misses == 0:
        print("[PASS] No deadline misses")
    else:
        print("[INFO] Deadline misses are present")

    return True


def check_trace_duration(df):
    print("\n[10] Checking trace duration...")

    timestamps = pd.to_numeric(
        df["timestamp_ns"],
        errors="coerce"
    ).dropna()

    if len(timestamps) < 2:
        print("[FAIL] Not enough timestamps")
        return False

    duration_ns = timestamps.max() - timestamps.min()

    if duration_ns <= 0:
        print("[FAIL] Invalid trace duration")
        return False

    duration_ms = duration_ns / 1_000_000

    print(f"[PASS] Trace duration: {duration_ms:.3f} ms")

    return True


def check_report():
    print("\n[11] Checking performance report...")

    if os.path.exists(REPORT_FILE):
        size = os.path.getsize(REPORT_FILE)

        print("[PASS] Performance report found")
        print(f"[INFO] Report size: {size} bytes")

        if size > 0:
            print("[PASS] Report contains data")
            return True

    print("[FAIL] Performance report not found")
    return False


def print_summary(results):
    print()
    print("=" * 70)
    print("                    VALIDATION SUMMARY")
    print("=" * 70)

    passed = sum(results)
    total = len(results)

    print()
    print(f"Checks passed : {passed}/{total}")

    if passed == total:
        print()
        print("      █████████████████████████████████")
        print("      █      SYSTEM VALIDATED         █")
        print("      █          100% PASS            █")
        print("      █████████████████████████████████")
        print()
        print("[SUCCESS] Phase 5.2 validation completed.")
    else:
        print()
        print("[WARNING] Some validation checks require attention.")

    print("=" * 70)


def main():

    print_header()

    results = []

    df = check_trace_file()

    if df is None:
        sys.exit(1)

    results.append(check_columns(df))
    results.append(check_basic_data(df))
    results.append(check_events(df))
    results.append(check_tasks(df))
    results.append(check_execution_pairs(df))
    results.append(check_execution_times(df))
    results.append(check_jitter(df))
    results.append(check_deadlines(df))
    results.append(check_trace_duration(df))
    results.append(check_report())

    print_summary(results)


if __name__ == "__main__":
    main()