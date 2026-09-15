AUTOMOTIVE RTOS ANALYZER - PROFESSIONAL UI

1. Copy your latest rtos_trace.csv into this folder.
2. Open PowerShell in this folder.
3. Install packages once:

   python -m pip install -r requirements.txt

4. Run the complete system:

   python run_all_analysis.py

   OR double-click:
   run_dashboard.bat

The system generates:
outputs/rtos_performance_report.txt

The dashboard contains:
- KPI cards
- task execution statistics
- execution-share visualization
- deadline compliance
- Gantt-style task timeline
- jitter analysis
- detailed data tables
- trace filters
- uploaded CSV support

IMPORTANT:
"Execution Occupancy" is trace-based workload occupancy, not a true hardware
per-core CPU utilization metric. Accurate per-core CPU utilization requires
separate CPU instrumentation on QNX.
