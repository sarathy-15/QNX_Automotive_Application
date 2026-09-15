# 🚗 Automotive RTOS Performance & Latency Analyzer

> **A QNX-based real-time workload measurement and analysis platform for studying scheduling behavior, execution timing, latency, jitter, deadline compliance, and context switching on Raspberry Pi 4.**

---

## 📌 Project Overview

Real-time automotive software is expected to execute tasks within predictable timing limits. A workload may appear to run correctly while still experiencing scheduling delays, execution-time variation, jitter, or deadline violations.

The **Automotive RTOS Performance & Latency Analyzer** was developed to make these timing behaviors measurable and visible.

Instead of relying only on console output, the system follows a complete measurement pipeline:

**Generate workload → Execute on QNX → Capture trace → Store timing data → Analyze → Validate → Visualize → Generate report**

The project combines a **native QNX/C measurement layer** with a **Python-based analysis and visualization layer**.

---

## 🎯 Project Objective

The main objective is to measure and analyze the behavior of real-time workloads running on **QNX Neutrino RTOS**.

The system focuses on:

* Task execution timing
* Scheduling behavior
* Task latency
* Timing jitter
* Deadline compliance
* Context-switch activity
* Workload scaling
* CPU/workload occupancy
* Trace-based performance analysis
* Long-duration and stress behavior

---

## 🧠 What Makes This Project Different?

This project is designed as a **measurement-to-analysis pipeline**, rather than simply running RTOS tasks.

### Traditional approach

```text
Create Task
    ↓
Run Task
    ↓
Print Result
```

### Proposed approach

```text
        QNX Workload
             │
             ▼
     ┌───────────────┐
     │ Testbench     │
     │ Workloads     │
     └───────┬───────┘
             │
             ▼
     ┌───────────────┐
     │ Trace         │
     │ Collector     │
     └───────┬───────┘
             │
             ▼
        rtos_trace.csv
             │
             ▼
     ┌───────────────┐
     │ Analysis      │
     │ Engine        │
     └───────┬───────┘
             │
       ┌─────┴─────┐
       ▼           ▼
   Reports      Dashboard
```

This separation allows the workload execution and the performance analysis to be developed independently.

---

# 🏗️ System Architecture

```text
                    ┌─────────────────────────┐
                    │     Automotive /        │
                    │    Infotainment         │
                    │      Workloads          │
                    └────────────┬────────────┘
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │     QNX Neutrino RTOS   │
                    │                         │
                    │  • Task Scheduling      │
                    │  • Priorities           │
                    │  • Timing               │
                    │  • Synchronization      │
                    └────────────┬────────────┘
                                 │
             ┌───────────────────┼───────────────────┐
             │                   │                   │
             ▼                   ▼                   ▼
      ┌────────────┐      ┌────────────┐      ┌────────────┐
      │ Testbench  │      │ CAN / SPI  │      │ Shared     │
      │ Workloads  │      │ Interface  │      │ Memory     │
      └─────┬──────┘      └────────────┘      └─────┬──────┘
            │                                         │
            └──────────────────┬──────────────────────┘
                               ▼
                    ┌─────────────────────────┐
                    │    Trace Collector      │
                    │                         │
                    │ START / END events     │
                    │ Timing measurements     │
                    └────────────┬────────────┘
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │      CSV Trace          │
                    │    rtos_trace.csv       │
                    └────────────┬────────────┘
                                 │
                                 ▼
              ┌─────────────────────────────────────┐
              │        Python Analysis Layer        │
              │                                     │
              │  • Trace Processing                 │
              │  • Latency                           │
              │  • Jitter                            │
              │  • Deadline Analysis                 │
              │  • Task Statistics                   │
              │  • Validation                        │
              └───────────────┬─────────────────────┘
                              │
                 ┌────────────┴─────────────┐
                 ▼                          ▼
       ┌──────────────────┐       ┌──────────────────┐
       │ Performance      │       │ Interactive      │
       │ Reports          │       │ Dashboard        │
       └──────────────────┘       └──────────────────┘
```

---

# 🛠️ Technology Stack

| Layer              | Technology                       |
| ------------------ | -------------------------------- |
| RTOS               | QNX Neutrino                     |
| Target             | Raspberry Pi 4 Model B           |
| Native Development | C                                |
| Build Environment  | QNX Momentics                    |
| Compiler           | QNX `qcc`                        |
| Analysis           | Python                           |
| Data Processing    | Pandas / NumPy                   |
| Visualization      | Matplotlib / dashboard framework |
| Trace Format       | CSV                              |
| Hardware Interface | CAN / SPI support                |
| Communication      | Shared Memory                    |
| Dashboard          | Python application               |

---

# 🧪 Testbench Suite

The analyzer contains **11 workload testbenches** designed to study different dimensions of real-time behavior.

|  # | Testbench                | Purpose                                                      |
| -: | ------------------------ | ------------------------------------------------------------ |
| 01 | Task Scaling             | Studies behavior as the number of active tasks increases     |
| 02 | Priority Variation       | Examines scheduling behavior under different task priorities |
| 03 | Execution-Time Variation | Measures the effect of changing workload execution time      |
| 04 | Period Variation         | Studies task behavior with different execution periods       |
| 05 | Deadline Testing         | Checks whether workloads complete within their deadlines     |
| 06 | CPU Load Variation       | Evaluates performance under different workload loads         |
| 07 | Context-Switch Testing   | Measures context-switch activity                             |
| 08 | Mixed Workload           | Combines different workload characteristics                  |
| 09 | Long-Duration Stability  | Observes timing behavior during extended execution           |
| 10 | Stress Testing           | Evaluates behavior under heavy workload conditions           |
| 11 | Temperature Monitoring   | Provides a platform-level thermal observation point          |

### Why 11 testbenches?

Each testbench changes a different workload parameter. This makes it possible to distinguish whether a timing problem is related to:

* Task count
* Priority
* Execution time
* Period
* Deadline
* System load
* Scheduling activity
* Combined workload conditions
* Extended execution
* Stress conditions
* Thermal behavior

---

# 📡 Trace Collection

The QNX application records task timing information into a trace dataset.

The primary trace format is:

```text
timestamp_ns,
task_id,
event,
execution_time_ns,
deadline_ns
```

Example:

```text
timestamp_ns,task_id,event,execution_time_ns,deadline_ns
...
```

The trace collector records events such as:

* `START`
* `END`
* Context-switch information
* Timing-related measurements

The resulting CSV becomes the interface between the QNX measurement system and the Python analysis system.

---

# 🐍 Python Analysis Engine

The `RTOS_Analyzer_Pro` directory contains the analysis layer.

### Main components

```text
RTOS_Analyzer_Pro/
│
├── analysis_engine.py
├── app.py
├── report_generator.py
├── run_all_analysis.py
├── testbench_validation.py
├── validate_pipeline.py
│
├── rtos_trace.csv
├── rtos_trace_DEMO.csv
│
├── outputs/
│   ├── analysis_summary.txt
│   └── rtos_performance_report.txt
│
└── requirements.txt
```

### Analysis flow

```text
CSV Trace
   │
   ▼
Load & Validate
   │
   ▼
Pair START / END Events
   │
   ▼
Calculate Timing Metrics
   │
   ├── Execution Time
   ├── Latency
   ├── Jitter
   ├── Deadline Status
   └── Context Switches
   │
   ▼
Generate Report
   │
   ▼
Display Dashboard
```

---

# 📊 Measured Performance Metrics

## 1. Execution Time

Measures the time taken by a workload execution.

```text
Execution Time = END Timestamp - START Timestamp
```

The analyzer calculates:

* Minimum
* Maximum
* Average
* Total execution time

---

## 2. Latency

Latency represents the measured timing delay associated with workload execution.

The analyzer reports minimum, maximum, and average latency values.

---

## 3. Jitter

Jitter represents variation in timing behavior across repeated executions.

A low and stable jitter indicates more predictable timing behavior.

The analyzer calculates:

* Minimum jitter
* Maximum jitter
* Average jitter

---

## 4. Deadline Compliance

The analyzer compares measured execution behavior against configured deadlines.

```text
Execution Time ≤ Deadline
        │
        ├── PASS → Deadline met
        │
        └── FAIL → Deadline miss
```

---

## 5. Context Switching

Context-switch activity is measured to understand scheduling overhead and task switching behavior.

---

# 📈 Interactive Dashboard

The Python dashboard provides a visual interface for exploring the collected trace.

The dashboard includes:

* KPI cards
* Task execution statistics
* Execution-share visualization
* Deadline compliance
* Gantt-style task timeline
* Jitter analysis
* Detailed data tables
* Trace filtering
* CSV upload support

This makes the analyzer suitable for **debugging, performance investigation, and project demonstrations**.

---

# 📋 Example Performance Result

The included trace analysis produced:

```text
Total records          : 53174
START events           : 26387
END events             : 26387
Completed tasks        : 26387

Minimum execution time : 86148 ns
Maximum execution time : 10000236112 ns
Average execution time : 1300516.92 ns

Minimum latency        : 86148 ns
Maximum latency        : 10000236112 ns
Average latency        : 1300516.92 ns

Minimum jitter         : 37 ns
Maximum jitter         : 9931493168 ns
Average jitter         : 416822.76 ns

Deadline misses        : 0
Context switches       : 400
```

### Interpretation

The captured workload completed **26,387 task executions** with matching START/END events. The analyzed trace reported **zero deadline misses** and recorded **400 context switches**.

> **Note:** The execution-occupancy visualization in this project is trace-based workload occupancy. It should not be interpreted as true per-core hardware CPU utilization. Accurate per-core CPU utilization requires dedicated CPU instrumentation on QNX.

---

# 🔌 CAN / SPI Support

The native layer contains CAN-related interface code and an MCP2515 SPI test component.

Relevant files include:

```text
src/can_interface.c
src/can_interface.h

src/mcp2515_spi_test.c
src/mcp2515_spi_test.h
```

This provides a foundation for integrating external automotive-style events into the workload measurement system.

For example:

```text
External CAN Event
       │
       ▼
CAN Interface
       │
       ▼
QNX Workload Trigger
       │
       ▼
Trace Collection
```

---

# 🧩 Native QNX Components

The main C implementation is organized into dedicated modules:

```text
src/
│
├── automotive-rtos-analyzer.c
│
├── testbench.c
├── testbench.h
│
├── trace_collector.c
├── trace_collector.h
│
├── trace_analyzer.c
├── trace_analyzer.h
│
├── performance_report.c
├── performance_report.h
│
├── shared_memory.c
├── shared_memory.h
│
├── can_interface.c
├── can_interface.h
│
├── mcp2515_spi_test.c
└── mcp2515_spi_test.h
```

### Module responsibilities

| Module                       | Responsibility                |
| ---------------------------- | ----------------------------- |
| `automotive-rtos-analyzer.c` | Main application              |
| `testbench.c`                | Workload/testbench execution  |
| `trace_collector.c`          | Timing-event collection       |
| `trace_analyzer.c`           | Native trace analysis         |
| `performance_report.c`       | Performance reporting         |
| `shared_memory.c`            | Shared-memory communication   |
| `can_interface.c`            | CAN interface support         |
| `mcp2515_spi_test.c`         | MCP2515/SPI interface testing |

---

# 🚀 Getting Started

## Prerequisites

### Target side

* Raspberry Pi 4 Model B
* QNX Neutrino RTOS
* QNX Momentics development environment
* QNX toolchain
* Network connection between host and target

### Analysis side

* Python 3.x
* Required Python packages

Install the analysis dependencies:

```bash
python -m pip install -r RTOS_Analyzer_Pro/requirements.txt
```

---

# ▶️ Running the QNX Application

Build the project using the QNX Momentics environment with the appropriate target configuration.

The project contains the QNX build configuration:

```text
aarch64le-debug
```

The generated target executable is:

```text
automotive-rtos-analyzer
```

Deploy the executable to the Raspberry Pi 4 running QNX and execute it on the target.

The application generates the trace data required for the analysis stage.

---

# ▶️ Running the Analysis Pipeline

Navigate to:

```text
RTOS_Analyzer_Pro
```

Run:

```bash
python run_all_analysis.py
```

The pipeline performs the analysis and generates the performance results.

A dashboard can also be started using:

```text
run_dashboard.bat
```

---

# 📁 Output

The analysis generates reports inside:

```text
RTOS_Analyzer_Pro/outputs/
```

Important output:

```text
rtos_performance_report.txt
```

The complete trace is stored as:

```text
rtos_trace.csv
```

A smaller demonstration dataset is also included:

```text
rtos_trace_DEMO.csv
```

---

# 🔍 Validation

The project includes dedicated validation utilities:

```text
testbench_validation.py
validate_pipeline.py
```

These help verify:

* Trace structure
* START/END event consistency
* Analysis pipeline behavior
* Generated performance information

This adds an additional validation layer instead of assuming that every generated trace is automatically valid.

---

# 💡 Engineering Workflow

The complete project workflow can be summarized as:

```text
┌──────────────────────┐
│ Define RTOS Workload │
└──────────┬───────────┘
           ↓
┌──────────────────────┐
│ Configure Testbench  │
└──────────┬───────────┘
           ↓
┌──────────────────────┐
│ Execute on QNX       │
│ Raspberry Pi 4       │
└──────────┬───────────┘
           ↓
┌──────────────────────┐
│ Capture Timing Trace │
└──────────┬───────────┘
           ↓
┌──────────────────────┐
│ Store CSV Trace      │
└──────────┬───────────┘
           ↓
┌──────────────────────┐
│ Validate Trace       │
└──────────┬───────────┘
           ↓
┌──────────────────────┐
│ Analyze Performance  │
└──────────┬───────────┘
           ↓
      ┌────┴────┐
      ↓         ↓
   Report    Dashboard
```

---

# 🏎️ Automotive Relevance

The architecture is intended to represent the type of timing investigation that is important in real-time automotive computing.

Potential workload categories include:

* Infotainment processing
* Sensor-related tasks
* Communication handling
* Periodic control-style workloads
* Background processing
* Mixed-priority workloads

The project does **not** claim to be an automotive-certified system. Instead, it provides a practical platform for studying real-time scheduling and workload timing behavior.

---

# ⚠️ Important Measurement Consideration

The analyzer distinguishes between **trace-based workload occupancy** and actual hardware CPU utilization.

The current dashboard's occupancy metric is derived from captured trace events.

For true CPU utilization measurements, additional QNX-specific per-core CPU instrumentation would be required.

This distinction is important when interpreting the results.

---

# 🔮 Future Enhancements

Possible extensions include:

* Per-core CPU utilization
* More detailed QNX scheduling instrumentation
* Hardware GPIO timing markers
* Live CAN-triggered workload generation
* Automated comparison between testbench runs
* Historical performance database
* Regression detection
* Automated performance thresholds
* Real-time dashboard updates
* Multi-core scheduling visualization
* Temperature/performance correlation
* Export to engineering-oriented report formats

---

# 📌 Project Highlights

### Measurement

**Real QNX workload execution**
rather than purely simulated timing data.

### Experimentation

**11 independent testbench scenarios**
to investigate different scheduling conditions.

### Traceability

**Timestamped START/END trace records**
provide measurable execution information.

### Analysis

**Python-based automated analysis pipeline**
converts raw trace data into engineering metrics.

### Visualization

**Interactive dashboard + Gantt-style timeline**
makes timing behavior easier to inspect.

### Reporting

**Automatically generated performance reports**
provide a repeatable analysis output.

---

# 📂 Repository Structure

```text
automotive-rtos-analyzer/
│
├── src/
│   ├── automotive-rtos-analyzer.c
│   ├── testbench.c
│   ├── testbench.h
│   ├── trace_collector.c
│   ├── trace_collector.h
│   ├── trace_analyzer.c
│   ├── trace_analyzer.h
│   ├── performance_report.c
│   ├── performance_report.h
│   ├── shared_memory.c
│   ├── shared_memory.h
│   ├── can_interface.c
│   ├── can_interface.h
│   ├── mcp2515_spi_test.c
│   └── mcp2515_spi_test.h
│
├── RTOS_Analyzer_Pro/
│   ├── analysis_engine.py
│   ├── app.py
│   ├── report_generator.py
│   ├── run_all_analysis.py
│   ├── testbench_validation.py
│   ├── validate_pipeline.py
│   ├── requirements.txt
│   ├── rtos_trace.csv
│   ├── rtos_trace_DEMO.csv
│   └── outputs/
│
├── Makefile
├── .project
└── .cproject
```

---

# 🧪 Project Status

| Component                 | Status                               |
| ------------------------- | ------------------------------------ |
| QNX workload application  | ✅ Completed                          |
| RTOS testbench suite      | ✅ Completed                          |
| Trace collection          | ✅ Completed                          |
| Trace analysis            | ✅ Completed                          |
| Performance analysis      | ✅ Completed                          |
| Performance reporting     | ✅ Completed                          |
| Dashboard                 | ✅ Implemented                        |
| Validation pipeline       | ✅ Implemented                        |
| CAN/SPI interface support | 🔧 Available / integration dependent |

---

# 📜 License

This project is intended for educational, research, and engineering demonstration purposes.

Add your preferred open-source license before publishing the repository if required.

---

# 👨‍💻 Author

**Parthasarathy Mohan**

Engineering Student | Embedded Systems | RTOS | PCB Design

---

## ⭐ Project Summary

**Automotive RTOS Performance & Latency Analyzer** turns raw real-time workload execution into measurable performance information.

