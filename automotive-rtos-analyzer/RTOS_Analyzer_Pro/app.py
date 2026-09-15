from __future__ import annotations

import io
from pathlib import Path
from typing import Dict, Tuple

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ============================================================
# AUTOMOTIVE RTOS PERFORMANCE ANALYZER
# UI: professional automotive / dark telemetry console
# DATA: actual rtos_trace.csv only; no synthetic dashboard values
# ============================================================
st.set_page_config(
    page_title="Automotive RTOS Performance Analyzer",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_TRACE = BASE_DIR / "rtos_trace.csv"
OUTPUT_DIR = BASE_DIR / "outputs"
OUTPUT_DIR.mkdir(exist_ok=True)

# Plotly graph toolbar used by every graph in the dashboard.
# Keeps the existing graph design/data while enabling download, zoom, pan,
# box/lasso selection, autoscale and reset controls.
PLOTLY_CONFIG = {
    "displayModeBar": True,
    "displaylogo": False,
    "responsive": True,
    "scrollZoom": True,
    "modeBarButtonsToAdd": [
        "drawline",
        "drawopenpath",
        "eraseshape",
    ],
    "toImageButtonOptions": {
        "format": "png",
        "filename": "rtos_analyzer_graph",
        "height": 900,
        "width": 1600,
        "scale": 2,
    },
}

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
# DESIGN SYSTEM
# ------------------------------------------------------------
st.markdown(
    """
<style>
:root{
  --bg:#050b13;
  --bg2:#07111d;
  --panel:#091522;
  --panel2:#0c1928;
  --panel3:#0f2032;
  --border:#1a3048;
  --border2:#23425f;
  --text:#edf5ff;
  --muted:#8294aa;
  --blue:#1597ff;
  --blue2:#3578ff;
  --violet:#7657ff;
  --purple:#b047ff;
  --cyan:#39d9ff;
  --green:#2fdb93;
  --amber:#ffb22e;
  --red:#ff5367;
}

.stApp{
  background:
    radial-gradient(circle at 78% 0%,rgba(70,75,255,.11),transparent 25%),
    radial-gradient(circle at 15% 12%,rgba(0,145,255,.08),transparent 23%),
    linear-gradient(180deg,#040a12 0%,#06101a 48%,#040a12 100%);
  color:var(--text);
}
.block-container{max-width:1660px;padding:1.0rem 1.4rem 3rem}
#MainMenu,footer{visibility:hidden}
header[data-testid="stHeader"]{background:transparent}

/* Sidebar */
section[data-testid="stSidebar"]{
  background:
    radial-gradient(circle at 90% 0%,rgba(78,70,255,.14),transparent 25%),
    linear-gradient(180deg,#06101a 0%,#07111c 55%,#050c15 100%);
  border-right:1px solid #172b40;
}
section[data-testid="stSidebar"] > div{padding:0.8rem .7rem 1rem}
section[data-testid="stSidebar"] *{color:#d8e5f3}
section[data-testid="stSidebar"] hr{border-color:#172b40;margin:.8rem 0}

.side-brand{padding:8px 8px 17px;border-bottom:1px solid #17283b;margin-bottom:13px}
.side-brand-row{display:flex;align-items:center;gap:9px}
.side-bolt{
  width:28px;height:32px;display:flex;align-items:center;justify-content:center;
  font-size:22px;filter:drop-shadow(0 0 8px rgba(255,91,177,.45));
}
.side-title{font-size:18px;font-weight:900;letter-spacing:.02em;line-height:1}
.side-title span{color:#62bfff}
.side-sub{font-size:9px;color:#72869d;margin:9px 0 0 37px;line-height:1.45}

.side-label{font-size:9px;font-weight:900;letter-spacing:.14em;color:#71859c!important;margin:13px 4px 7px;text-transform:uppercase}
.side-info{
  border:1px solid #183149;border-radius:10px;padding:10px 11px;margin-top:8px;
  background:linear-gradient(135deg,rgba(17,40,62,.72),rgba(8,19,32,.82));
}
.side-info .k{font-size:8px;color:#63809b;text-transform:uppercase;letter-spacing:.11em}
.side-info .v{font-size:11px;color:#e4effb;font-weight:800;margin-top:3px}

/* Sidebar file uploader */
section[data-testid="stSidebar"] [data-testid="stFileUploader"]{
  background:transparent;border:0;padding:0;
}
section[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"]{
  min-height:116px!important;
  border:1px dashed #314b68!important;border-radius:11px!important;
  background:linear-gradient(180deg,#0a1725,#08121e)!important;
}
section[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] button{
  background:#edf2f7!important;color:#718398!important;border:0!important;border-radius:8px!important;
  font-weight:800!important;
}

/* Hero */
.hero{
  position:relative;overflow:hidden;min-height:154px;
  border:1px solid #19334d;border-radius:15px;
  background:
    radial-gradient(circle at 82% 25%,rgba(73,88,255,.18),transparent 22%),
    radial-gradient(circle at 74% 80%,rgba(167,45,255,.10),transparent 25%),
    linear-gradient(135deg,#081521 0%,#071321 58%,#0a1120 100%);
  box-shadow:0 18px 55px rgba(0,0,0,.25),inset 0 1px 0 rgba(255,255,255,.025);
  padding:25px 28px;margin-bottom:12px;
}
.hero:after{content:"";position:absolute;left:0;bottom:0;width:61%;height:2px;background:linear-gradient(90deg,#139aff,#695bff,#c047ff,transparent)}
.hero-grid{display:grid;grid-template-columns:1fr auto;gap:20px;align-items:center;position:relative;z-index:2}
.hero-eyebrow{font-size:9px;font-weight:900;letter-spacing:.19em;color:#3ba7ff;text-transform:uppercase;margin-bottom:8px}
.hero-title{font-size:31px;font-weight:950;letter-spacing:-.035em;line-height:1.08;color:#f5f8fc}
.hero-title .grad{background:linear-gradient(90deg,#fff,#d8e5ff 45%,#9b79ff 78%,#d25dff);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.hero-sub{font-size:11px;color:#8295aa;margin-top:7px}
.hero-pills{display:flex;gap:7px;flex-wrap:wrap;margin-top:15px}
.pill{border:1px solid #1d3853;border-radius:8px;padding:6px 10px;background:rgba(7,18,30,.78);font-size:9px;font-weight:800;color:#a8bdd2}
.pill.blue{color:#55b9ff}.pill.green{color:#53e1a6}.pill.purple{color:#d279ff}
.hero-actions{display:flex;flex-direction:column;align-items:flex-end;gap:9px}
.trace-live{border:1px solid #164f45;background:rgba(7,36,31,.65);border-radius:9px;padding:8px 12px;font-size:9px;color:#42e7a2;font-weight:900;letter-spacing:.06em}
.hero-car{font-size:54px;opacity:.86;filter:drop-shadow(0 0 18px rgba(77,98,255,.32));margin-right:10px}

/* KPI cards */
.kpi-grid{display:grid;grid-template-columns:repeat(5,1fr);gap:8px;margin:0 0 12px}
.kpi{
  position:relative;overflow:hidden;min-height:104px;padding:15px 15px 13px;
  border:1px solid #19334c;border-radius:12px;
  background:linear-gradient(145deg,#0a1724,#08131f 70%,#0a1624);
  box-shadow:0 10px 28px rgba(0,0,0,.17),inset 0 1px 0 rgba(255,255,255,.025);
}
.kpi:before{content:"";position:absolute;left:0;top:0;width:100%;height:2px;background:linear-gradient(90deg,#1c9bff,#625fff,#bb4bff)}
.kpi .icon{font-size:21px;float:left;margin-right:9px;margin-top:2px}
.kpi .label{font-size:8px;color:#74879e;font-weight:900;letter-spacing:.10em}
.kpi .value{font-size:21px;font-weight:950;color:#f1f6fd;margin-top:5px;letter-spacing:-.025em}
.kpi .desc{font-size:8.5px;color:#74889e;margin-top:4px;line-height:1.35}
.kpi.health .value{color:#39df9a}.kpi.warn .value{color:#ffba45}.kpi.danger .value{color:#ff5e72}

/* Section */
.section{display:flex;align-items:end;justify-content:space-between;margin:19px 2px 8px;padding:0 2px}
.section h3{font-size:14px;margin:0;color:#eaf2fb;font-weight:900;letter-spacing:.01em}
.section p{font-size:9px;color:#647991;margin:3px 0 0}
.section-line{height:1px;background:linear-gradient(90deg,#1d3b57,rgba(29,59,87,0));margin-top:6px}

/* Panels */
.panel{
  border:1px solid #19334b;border-radius:12px;background:linear-gradient(180deg,#091622,#07121e);
  box-shadow:0 10px 28px rgba(0,0,0,.16);padding:12px 13px 10px;height:100%;
}
.panel-title{font-size:10px;font-weight:900;color:#d9e6f3;letter-spacing:.08em;text-transform:uppercase;margin-bottom:3px}
.panel-caption{font-size:8px;color:#667b92;margin-bottom:4px}
[data-testid="stPlotlyChart"]{background:transparent!important;border:0!important;padding:0!important}

/* Streamlit elements */
.stButton > button,.stDownloadButton > button{
  border:1px solid #235db1!important;border-radius:8px!important;
  background:linear-gradient(90deg,#0e8fff,#5a5fff 58%,#a94bff)!important;
  color:#fff!important;font-weight:850!important;font-size:10px!important;
  box-shadow:0 8px 22px rgba(51,88,255,.16)!important;
}
.stButton > button:hover,.stDownloadButton > button:hover{border-color:#8d76ff!important;transform:translateY(-1px)}
[data-baseweb="select"] > div,[data-testid="stTextInput"] input{background:#091622!important;border-color:#203b55!important;color:#e8f0f8!important}
[data-testid="stDataFrame"]{border:1px solid #19334c;border-radius:10px;overflow:hidden}
.stAlert{border-radius:9px!important}

/* Health */
.health-strip{display:flex;align-items:center;gap:13px;border:1px solid #1d3d3b;border-radius:11px;padding:11px 13px;background:linear-gradient(90deg,rgba(8,44,38,.55),rgba(7,20,29,.8))}
.health-dot{width:10px;height:10px;border-radius:50%;background:#31df96;box-shadow:0 0 13px #31df96}
.health-name{font-size:9px;color:#7590a4;font-weight:900;letter-spacing:.11em}
.health-state{font-size:18px;font-weight:950;color:#35df9a}
.health-reason{font-size:9px;color:#8195a8}
.evidence{font-size:8px;color:#5f758b;margin-top:6px}

/* Scheduling + coverage */
.coverage-row{display:flex;align-items:center;gap:7px;padding:4px 2px;border-bottom:1px solid rgba(27,52,76,.45);font-size:8px;min-width:0}
.coverage-check{width:15px;height:15px;border-radius:4px;display:inline-flex;align-items:center;justify-content:center;font-weight:950;flex:0 0 15px}
.coverage-check.captured{background:rgba(47,219,147,.16);color:#38df98;border:1px solid rgba(47,219,147,.34)}
.coverage-check.missing{background:rgba(255,83,103,.10);color:#ff6174;border:1px solid rgba(255,83,103,.28)}
.coverage-name{color:#cbd9e6;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;flex:1}
.coverage-count{color:#657b92;font-size:7.5px;white-space:nowrap}
.coverage-total{margin-top:7px;padding:7px 8px;border-radius:7px;background:linear-gradient(90deg,rgba(47,219,147,.08),rgba(50,86,112,.06));border:1px solid #19384b;color:#8195a8;font-size:8px;text-align:center}
.coverage-total b{color:#35df9a;font-size:12px;margin-right:4px}

/* Responsive */
@media(max-width:1050px){.kpi-grid{grid-template-columns:repeat(2,1fr)}.hero-grid{grid-template-columns:1fr}.hero-actions{align-items:flex-start}.hero-car{display:none}}

/* Added: responsive graph/page behavior across desktop, laptop and mobile */
.stPlotlyChart, [data-testid="stPlotlyChart"]{
  width:100%!important;
  max-width:100%!important;
  overflow:hidden!important;
}
[data-testid="stPlotlyChart"] > div,
[data-testid="stPlotlyChart"] .js-plotly-plot,
[data-testid="stPlotlyChart"] .plot-container{
  width:100%!important;
  max-width:100%!important;
}
@media(max-width:1200px){
  .block-container{padding-left:1rem;padding-right:1rem}
  .hero-title{font-size:27px}
  .panel{padding:11px}
}
@media(max-width:900px){
  .kpi-grid{grid-template-columns:repeat(2,1fr)}
  .hero{padding:20px 18px}
  .hero-title{font-size:23px}
  [data-testid="stHorizontalBlock"]{gap:.65rem}
}
@media(max-width:640px){
  .block-container{padding:.7rem .65rem 2rem}
  .kpi-grid{grid-template-columns:1fr}
  .kpi{min-height:88px}
  .hero-title{font-size:20px}
  .hero-sub{font-size:10px}
  .section h3{font-size:12px}
  .panel-title{font-size:9px}
  [data-testid="stPlotlyChart"]{min-height:250px!important}
  [data-testid="stPlotlyChart"] .plotly{width:100%!important}
}

</style>
""",
    unsafe_allow_html=True,
)

# ------------------------------------------------------------
# DATA FUNCTIONS
# ------------------------------------------------------------
def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [str(c).strip() for c in df.columns]
    normalized = {str(c).lower().strip().replace(" ", "_").replace("-", "_"): c for c in df.columns}
    aliases = {
        "timestamp": "timestamp_ns",
        "time": "timestamp_ns",
        "task": "task_id",
        "taskid": "task_id",
        "execution_time": "execution_time_ns",
        "execution": "execution_time_ns",
        "deadline": "deadline_ns",
        "temperature": "temperature_c",
        "temp": "temperature_c",
    }
    rename = {}
    for alias, target in aliases.items():
        if alias in normalized and target not in df.columns:
            rename[normalized[alias]] = target
    if rename:
        df = df.rename(columns=rename)
    return df


@st.cache_data(show_spinner=False)
def load_trace(file_bytes: bytes) -> pd.DataFrame:
    df = normalize_columns(pd.read_csv(io.BytesIO(file_bytes)))
    required = ["timestamp_ns", "task_id", "event", "execution_time_ns", "deadline_ns"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError("Missing required columns: " + ", ".join(missing))
    if "testbench" not in df.columns:
        df["testbench"] = "UNSPECIFIED"
    if "temperature_c" not in df.columns:
        df["temperature_c"] = np.nan
    for c in ["timestamp_ns", "task_id", "execution_time_ns", "deadline_ns", "temperature_c"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df["event"] = df["event"].astype(str).str.strip().str.upper()
    df["testbench"] = df["testbench"].astype(str).str.strip()
    df = df.dropna(subset=["timestamp_ns", "task_id"]).sort_values("timestamp_ns").reset_index(drop=True)
    return df


def get_trace() -> Tuple[pd.DataFrame | None, str]:
    uploaded = st.session_state.get("uploaded_trace_bytes")
    if uploaded:
        return load_trace(uploaded), "Uploaded trace"
    if DEFAULT_TRACE.exists():
        return load_trace(DEFAULT_TRACE.read_bytes()), DEFAULT_TRACE.name
    return None, "No trace"


def build_intervals(df: pd.DataFrame) -> pd.DataFrame:
    active: Dict[tuple, list] = {}
    rows = []
    for r in df.itertuples(index=False):
        key = (str(r.testbench), int(r.task_id))
        if r.event == "START":
            active.setdefault(key, []).append(float(r.timestamp_ns))
        elif r.event == "END" and active.get(key):
            start = active[key].pop(0)
            end = float(r.timestamp_ns)
            measured = end - start
            supplied = float(r.execution_time_ns) if pd.notna(r.execution_time_ns) and r.execution_time_ns >= 0 else measured
            if supplied < 0:
                continue
            deadline = float(r.deadline_ns) if pd.notna(r.deadline_ns) and r.deadline_ns > 0 else 0.0
            rows.append({
                "testbench": str(r.testbench),
                "task_id": int(r.task_id),
                "start_ns": start,
                "end_ns": end,
                "execution_ns": supplied,
                "execution_ms": supplied / 1e6,
                "deadline_ns": deadline,
                "deadline_ms": deadline / 1e6 if deadline else np.nan,
            })
    return pd.DataFrame(rows)


def calculate_jitter(df: pd.DataFrame) -> pd.DataFrame:
    starts = df[df.event == "START"].copy()
    if starts.empty:
        return pd.DataFrame()
    starts = starts.sort_values(["testbench", "task_id", "timestamp_ns"])
    starts["activation_ms"] = starts.groupby(["testbench", "task_id"])["timestamp_ns"].diff() / 1e6
    out = starts.dropna(subset=["activation_ms"]).groupby(["testbench", "task_id"], as_index=False)["activation_ms"].agg(
        samples="count", mean_period_ms="mean", jitter_ms="std", min_period_ms="min", max_period_ms="max"
    )
    out["jitter_ms"] = out["jitter_ms"].fillna(0)
    return out


def analyze(df: pd.DataFrame, intervals: pd.DataFrame) -> dict:
    if df.empty:
        return {"records": 0, "health": "ERROR", "health_reason": "Trace contains no usable records."}

    duration_ns = float(df.timestamp_ns.max() - df.timestamp_ns.min())
    ends = df[df.event == "END"].copy()
    ends["execution_time_ns"] = pd.to_numeric(ends.execution_time_ns, errors="coerce").fillna(0).clip(lower=0)
    deadline_rows = ends[ends.deadline_ns > 0]

    explicit = int((df.event == "DEADLINE_MISS").sum())
    calculated = int((deadline_rows.execution_time_ns > deadline_rows.deadline_ns).sum()) if not deadline_rows.empty else 0
    misses = explicit + calculated

    # Health is evidence-based. Coverage never changes health.
    if duration_ns <= 0:
        health, reason = "ERROR", "Trace has no positive capture duration."
    elif misses > 0:
        health, reason = "WARNING", f"{misses:,} deadline violation(s) detected in the trace."
    else:
        health, reason = "HEALTHY", "Valid capture with no recorded or calculated deadline violations."

    temps = df.loc[df.event == "TEMPERATURE", "temperature_c"].dropna()
    aggregate_ns = float(ends.execution_time_ns.sum())
    aggregate_load = aggregate_ns / duration_ns * 100 if duration_ns > 0 else np.nan

    present = [x for x in EXPECTED_TESTBENCHES if x in set(df.testbench)]
    missing = [x for x in EXPECTED_TESTBENCHES if x not in set(df.testbench)]

    return {
        "records": len(df),
        "tasks": df[["testbench", "task_id"]].drop_duplicates().shape[0],
        "duration_ms": duration_ns / 1e6,
        "duration_s": duration_ns / 1e9,
        "health": health,
        "health_reason": reason,
        "explicit_misses": explicit,
        "calculated_misses": calculated,
        "deadline_misses": misses,
        "deadline_checked": len(deadline_rows),
        "aggregate_load": aggregate_load,
        "avg_execution_ms": float(ends.execution_time_ns.mean() / 1e6) if not ends.empty else np.nan,
        "min_execution_ms": float(ends.execution_time_ns.min() / 1e6) if not ends.empty else np.nan,
        "max_execution_ms": float(ends.execution_time_ns.max() / 1e6) if not ends.empty else np.nan,
        "context_events": int((df.event == "CONTEXT_SWITCH").sum()),
        "temperature_samples": len(temps),
        "temp_min": float(temps.min()) if not temps.empty else np.nan,
        "temp_avg": float(temps.mean()) if not temps.empty else np.nan,
        "temp_max": float(temps.max()) if not temps.empty else np.nan,
        "present": present,
        "missing": missing,
        "coverage": len(present) / len(EXPECTED_TESTBENCHES) * 100,
    }


def safe(v, fmt="{:.2f}") -> str:
    try:
        return fmt.format(float(v)) if pd.notna(v) else "—"
    except Exception:
        return "—"


def chart_base(fig: go.Figure, height: int = 300) -> go.Figure:
    fig.update_layout(
        template="plotly_dark",
        height=height,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#07121e",
        margin=dict(l=48, r=18, t=35, b=42),
        font=dict(family="Inter, Segoe UI, Arial", size=10, color="#aab9ca"),
        title=None,
        showlegend=True,
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(size=9), orientation="h", y=1.08, x=0),
        hoverlabel=dict(bgcolor="#0c1a2a", bordercolor="#31506e", font_color="#f4f8ff"),
    )
    fig.update_xaxes(showgrid=True, gridcolor="#12283d", zeroline=False, linecolor="#1b344c", ticks="outside", tickfont=dict(size=9))
    fig.update_yaxes(showgrid=True, gridcolor="#12283d", zeroline=False, linecolor="#1b344c", tickfont=dict(size=9))
    return fig


def panel_title(title: str, caption: str = ""):
    html = f'<div class="panel-title">{title}</div>'
    if caption:
        html += f'<div class="panel-caption">{caption}</div>'
    st.markdown(html, unsafe_allow_html=True)


def section(title: str, caption: str = ""):
    st.markdown(
        f'<div class="section"><div><h3>{title}</h3><p>{caption}</p></div></div><div class="section-line"></div>',
        unsafe_allow_html=True,
    )


# ------------------------------------------------------------
# SIDEBAR
# ------------------------------------------------------------
with st.sidebar:
    st.markdown(
        '<div class="side-brand"><div class="side-brand-row"><div class="side-bolt">⚡</div><div class="side-title">RTOS<br><span>ANALYZER</span></div></div><div class="side-sub">Automotive real-time performance console</div></div>',
        unsafe_allow_html=True,
    )

    st.markdown('<div class="side-label">Trace Input</div>', unsafe_allow_html=True)
    uploaded = st.file_uploader("Upload trace CSV", type=["csv"], label_visibility="collapsed", help="Upload an rtos_trace.csv capture.")
    if uploaded is not None:
        st.session_state["uploaded_trace_bytes"] = uploaded.getvalue()
        st.session_state["uploaded_trace_name"] = uploaded.name
    if st.button("↻  Reset to Local Trace", use_container_width=True):
        st.session_state.pop("uploaded_trace_bytes", None)
        st.session_state.pop("uploaded_trace_name", None)
        st.rerun()

    # Added: refresh/recalculate every graph from the current trace.
    # This does not modify the trace or any analysis logic.
    if st.button("⟳  Refresh All Graphs", use_container_width=True, help="Reload the current trace and recalculate every dashboard graph."):
        st.cache_data.clear()
        st.rerun()

    st.markdown('<div class="side-label">Navigation</div>', unsafe_allow_html=True)
    nav = st.radio(
        "Navigation",
        ["Dashboard", "Overview", "Testbenches", "Performance", "Timeline", "Jitter Analysis", "Temperature", "Context Switches", "Events Explorer", "Reports", "Export Data"],
        label_visibility="collapsed",
    )

    st.markdown('<div class="side-label">System Info</div>', unsafe_allow_html=True)
    for k, v in [("QNX Version", "8.0.0"), ("Platform", "Raspberry Pi 4"), ("Testbenches", "11"), ("Trace File", "rtos_trace.csv")]:
        st.markdown(f'<div class="side-info"><div class="k">{k}</div><div class="v">{v}</div></div>', unsafe_allow_html=True)

    st.markdown('<div class="side-label">Trace Events</div>', unsafe_allow_html=True)
    st.markdown('<div class="side-info"><div class="v" style="font-size:9px;color:#86a2bb">START · END<br>DEADLINE_MISS<br>CONTEXT_SWITCH<br>TEMPERATURE</div></div>', unsafe_allow_html=True)

    st.markdown('<div style="height:14px"></div>', unsafe_allow_html=True)
    st.caption("RTOS Analyzer · Automotive Performance Monitoring System")

# ------------------------------------------------------------
# LOAD TRACE
# ------------------------------------------------------------
try:
    df, source_name = get_trace()
except Exception as exc:
    st.error(f"Trace loading error: {exc}")
    st.stop()

if df is None:
    st.markdown(
        '<div class="hero"><div class="hero-grid"><div><div class="hero-eyebrow">AUTOMOTIVE · REAL-TIME · TRACE ANALYSIS</div><div class="hero-title">AUTOMOTIVE <span class="grad">RTOS PERFORMANCE ANALYZER</span></div><div class="hero-sub">Load the actual rtos_trace.csv generated by your QNX testbench system to begin analysis.</div><div class="hero-pills"><div class="pill blue">QNX 8.0.0</div><div class="pill green">Raspberry Pi 4</div><div class="pill purple">11 Testbenches</div></div></div><div class="hero-car">🚘</div></div></div>',
        unsafe_allow_html=True,
    )
    st.info("No trace file found. Place rtos_trace.csv beside this app.py or upload a CSV from the sidebar.")
    st.stop()

intervals = build_intervals(df)
jitter = calculate_jitter(df)
m = analyze(df, intervals)

# ------------------------------------------------------------
# HERO
# ------------------------------------------------------------
health_class = "health" if m["health"] == "HEALTHY" else ("warn" if m["health"] == "WARNING" else "danger")
st.markdown(
    f'<div class="hero"><div class="hero-grid"><div><div class="hero-eyebrow">AUTOMOTIVE · REAL-TIME · PERFORMANCE TELEMETRY</div><div class="hero-title">AUTOMOTIVE <span class="grad">RTOS PERFORMANCE ANALYZER</span></div><div class="hero-sub">Real-time scheduling, latency, deadline, jitter and thermal performance monitoring</div><div class="hero-pills"><div class="pill blue">▣ QNX 8.0.0</div><div class="pill green">◉ Raspberry Pi 4</div><div class="pill purple">▥ 11 Testbenches</div></div></div><div class="hero-actions"><div class="trace-live">● TRACE LOADED</div><div class="hero-car">🚘</div></div></div></div>',
    unsafe_allow_html=True,
)

# ------------------------------------------------------------
# KPI ROW
# ------------------------------------------------------------
st.markdown('<div class="kpi-grid">', unsafe_allow_html=True)
kpis = [
    ("💚", "SYSTEM HEALTH", m["health"], m["health_reason"], health_class),
    ("▤", "TRACE RECORDS", f'{m["records"]:,}', "Total events captured", ""),
    ("◎", "TESTBENCH COVERAGE", f'{len(m["present"])} / 11', f'{m["coverage"]:.0f}% expected testbenches captured', ""),
    ("◉", "AGGREGATE TASK LOAD", safe(m["aggregate_load"], "{:.2f}") + "%", "Trace execution time ÷ capture window", ""),
    ("⚠", "DEADLINE MISSES", f'{m["deadline_misses"]:,}', f'{m["explicit_misses"]:,} explicit / {m["calculated_misses"]:,} calculated', "danger" if m["deadline_misses"] else ""),
]
for icon, label, value, desc, cls in kpis:
    st.markdown(f'<div class="kpi {cls}"><div class="icon">{icon}</div><div class="label">{label}</div><div class="value">{value}</div><div class="desc">{desc}</div></div>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# ------------------------------------------------------------
# HEALTH EVIDENCE STRIP
# ------------------------------------------------------------
health_color = "#35df9a" if m["health"] == "HEALTHY" else ("#ffb943" if m["health"] == "WARNING" else "#ff5e72")
st.markdown(
    f'<div class="health-strip"><div class="health-dot" style="background:{health_color};box-shadow:0 0 13px {health_color}"></div><div><div class="health-name">TRACE HEALTH DECISION</div><div class="health-state" style="color:{health_color}">{m["health"]}</div></div><div class="health-reason">{m["health_reason"]}<div class="evidence">Evidence checked: {m["records"]:,} records · {m["deadline_checked"]:,} deadline-tagged END records · {m["explicit_misses"]:,} explicit miss events · {m["calculated_misses"]:,} calculated misses</div></div></div>',
    unsafe_allow_html=True,
)

# ------------------------------------------------------------
# PERFORMANCE
# ------------------------------------------------------------
section("Performance Overview", "Actual START/END execution records reconstructed from the loaded trace")
if not intervals.empty:
    perf = intervals.groupby("testbench", as_index=False).agg(
        executions=("execution_ms", "count"),
        avg_ms=("execution_ms", "mean"),
        min_ms=("execution_ms", "min"),
        max_ms=("execution_ms", "max"),
    ).sort_values("avg_ms", ascending=True)
    c1, c2 = st.columns(2)
    with c1:
        with st.container(border=True):
            panel_title("Average Execution Time", "Mean measured execution time per testbench")
            fig = px.bar(perf, x="avg_ms", y="testbench", orientation="h", text="avg_ms")
            fig.update_traces(marker_color="#238cff", texttemplate="%{text:.3f} ms", textposition="outside", cliponaxis=False)
            fig.update_xaxes(title="Execution time (ms)")
            fig.update_yaxes(title="", categoryorder="array", categoryarray=perf.testbench.tolist())
            st.plotly_chart(chart_base(fig, 340), use_container_width=True, config=PLOTLY_CONFIG)
    with c2:
        with st.container(border=True):
            panel_title("Execution-Time Distribution", "Actual reconstructed execution intervals")
            fig = px.box(intervals, x="execution_ms", y="testbench", points=False)
            fig.update_traces(marker_color="#a64cff", line_color="#b65bff")
            fig.update_xaxes(title="Execution time (ms)")
            fig.update_yaxes(title="")
            st.plotly_chart(chart_base(fig, 340), use_container_width=True, config=PLOTLY_CONFIG)

    with st.expander("View execution statistics"):
        st.dataframe(perf.round(4), use_container_width=True, hide_index=True)
else:
    st.warning("No START/END execution pairs could be reconstructed from this trace.")

# ------------------------------------------------------------
# DEADLINE + EVENT DISTRIBUTION
# ------------------------------------------------------------
section("Deadline & Event Analysis", "Deadline compliance and actual event composition")
c1, c2 = st.columns(2)
with c1:
    with st.container(border=True):
        panel_title("Deadline Performance", "Execution time compared with recorded deadline")
        dl = intervals[intervals.deadline_ns > 0].copy() if not intervals.empty else pd.DataFrame()
        if not dl.empty:
            dl["margin_ms"] = dl["deadline_ms"] - dl["execution_ms"]
            dl["status"] = np.where(dl["margin_ms"] < 0, "MISS", "PASS")
            misses = int((dl.status == "MISS").sum()) + m["explicit_misses"]
            compliance = max(0, (len(dl) - int((dl.status == "MISS").sum())) / len(dl) * 100)
            g = go.Figure(go.Indicator(
                mode="gauge+number",
                value=compliance,
                number={"suffix":"%", "font":{"size":28,"color":"#35df9a" if misses == 0 else "#ffb943"}},
                gauge={"axis":{"range":[0,100],"tickcolor":"#657d94"},"bar":{"color":"#2fdb93" if misses == 0 else "#ffb22e"},"bgcolor":"#0a1724","borderwidth":0},
                domain={"x":[0,.52],"y":[0,1]},
            ))
            g.add_annotation(x=.26,y=.25,text="COMPLIANCE",showarrow=False,font=dict(size=10,color="#8aa0b5"))
            g.add_annotation(x=.76,y=.75,text=f"{len(dl):,}",showarrow=False,font=dict(size=19,color="#f0f6fd"))
            g.add_annotation(x=.76,y=.58,text="checked",showarrow=False,font=dict(size=9,color="#71879d"))
            g.add_annotation(x=.76,y=.38,text=f"{int((dl.status == 'MISS').sum()) + m['explicit_misses']:,} total misses",showarrow=False,font=dict(size=10,color="#ff6173" if misses else "#35df9a"))
            g.update_layout(height=260,paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",margin=dict(l=8,r=8,t=5,b=5),font=dict(family="Inter, Segoe UI",color="#b8c8d9"))
            st.plotly_chart(g,use_container_width=True,config=PLOTLY_CONFIG)
        else:
            st.info("No positive deadline values are available on END records.")

with c2:
    with st.container(border=True):
        panel_title("Event Distribution", "Only event types present in the original CSV")
        ec = df.event.value_counts().rename_axis("Event").reset_index(name="Records")
        fig = px.pie(ec, names="Event", values="Records", hole=.60)
        fig.update_traces(textinfo="percent", textposition="inside", marker=dict(line=dict(color="#07121e", width=2)))
        fig.update_layout(showlegend=True, legend=dict(orientation="v", x=.72, y=.5, font=dict(size=9)))
        st.plotly_chart(chart_base(fig, 300), use_container_width=True, config=PLOTLY_CONFIG)

# ------------------------------------------------------------
# JITTER + TEMPERATURE
# ------------------------------------------------------------
section("Jitter & Thermal Monitoring", "Repeated activation interval variation and temperature samples")
c1, c2 = st.columns(2)
with c1:
    with st.container(border=True):
        panel_title("Jitter Analysis", "Standard deviation of repeated START-to-START intervals")
        if not jitter.empty:
            j = jitter.copy()
            j["task"] = j.testbench + " / T" + j.task_id.astype(int).astype(str)
            j = j.sort_values("jitter_ms", ascending=True)
            fig = px.bar(j, x="jitter_ms", y="task", orientation="h")
            fig.update_traces(marker_color="#b247ff", hovertemplate="%{y}<br>Jitter: %{x:.4f} ms<extra></extra>")
            fig.update_xaxes(title="Jitter (ms)")
            fig.update_yaxes(title="")
            st.plotly_chart(chart_base(fig, 330), use_container_width=True, config=PLOTLY_CONFIG)
            st.caption(f"Average measured jitter: {safe(jitter.jitter_ms.mean(), '{:.4f}')} ms · Samples: {int(jitter.samples.sum()):,}")
        else:
            st.info("Repeated START events are unavailable; jitter cannot be calculated.")

with c2:
    with st.container(border=True):
        panel_title("Temperature Monitoring", "Actual TEMPERATURE events from the trace")
        temp = df[df.event == "TEMPERATURE"].copy()
        temp["temperature_c"] = pd.to_numeric(temp.temperature_c, errors="coerce")
        temp = temp.dropna(subset=["temperature_c"])
        if not temp.empty:
            base = float(df.timestamp_ns.min())
            temp["time_s"] = (temp.timestamp_ns - base) / 1e9
            fig = px.line(temp, x="time_s", y="temperature_c")
            fig.update_traces(line=dict(color="#ffb22e", width=2.2), fill="tozeroy", fillcolor="rgba(255,178,46,.08)")
            fig.update_xaxes(title="Trace time (s)")
            fig.update_yaxes(title="Temperature (°C)")
            st.plotly_chart(chart_base(fig, 250), use_container_width=True, config=PLOTLY_CONFIG)
            a,b,c = st.columns(3)
            a.metric("MIN", f"{temp.temperature_c.min():.2f} °C")
            b.metric("AVG", f"{temp.temperature_c.mean():.2f} °C")
            c.metric("MAX", f"{temp.temperature_c.max():.2f} °C")
        else:
            st.info("No valid TEMPERATURE samples were captured.")

# ------------------------------------------------------------
# TIMELINE + COVERAGE
# ------------------------------------------------------------
section("Scheduling Timeline & Testbench Coverage", "Execution intervals and actual capture coverage")
c1, c2 = st.columns([1.38, 0.92], gap="small")

with c1:
    with st.container(border=True):
        panel_title("Scheduling Timeline — Gantt View", "Actual START → END execution intervals reconstructed from the trace")

        if not intervals.empty:
            tl = intervals.copy()
            base = float(df.timestamp_ns.min())
            tl["start_s"] = (tl.start_ns - base) / 1e9
            tl["end_s"] = (tl.end_ns - base) / 1e9
            tl = tl[(tl.end_s >= tl.start_s) & (tl.end_s > 0)].copy()
            tl["task_id"] = pd.to_numeric(tl["task_id"], errors="coerce").fillna(0).astype(int)
            tl["testbench"] = tl["testbench"].astype(str)

            # Keep the task rows compact.  The trace itself determines which
            # tasks and intervals are displayed; nothing is fabricated.
            task_ids = sorted(tl.task_id.unique().tolist())
            task_labels = [f"Task {x}" for x in task_ids]
            y_map = {task: i for i, task in enumerate(task_ids)}

            # High-contrast automotive palette.  Each captured testbench gets
            # one stable color for the whole timeline and legend.
            palette = [
                "#1E90FF",  # electric blue
                "#20D391",  # emerald
                "#FFB52E",  # amber
                "#A970FF",  # violet
                "#22D3EE",  # cyan
                "#F052D0",  # magenta
                "#6B7CFF",  # indigo
                "#FF647C",  # red-pink
                "#8BD450",  # lime
                "#FF7A2F",  # orange
                "#35D6C2",  # teal
            ]
            tb_names = sorted(tl["testbench"].unique().tolist(), key=lambda x: EXPECTED_TESTBENCHES.index(x) if x in EXPECTED_TESTBENCHES else 999)
            tb_color = {name: palette[i % len(palette)] for i, name in enumerate(tb_names)}

            # Use thick horizontal Scatter segments instead of overlaid bars.
            # This is a much clearer Gantt representation for very short RTOS
            # execution intervals: colors remain visible even at small widths,
            # while the x-position and duration remain trace-derived.
            fig = go.Figure()
            for name in tb_names:
                part = tl[tl["testbench"] == name]
                xs, ys, hover = [], [], []
                for row in part.itertuples(index=False):
                    xs.extend([float(row.start_s), float(row.end_s), None])
                    ys.extend([f"Task {int(row.task_id)}", f"Task {int(row.task_id)}", None])
                fig.add_trace(go.Scatter(
                    x=xs,
                    y=ys,
                    mode="lines",
                    line=dict(color=tb_color[name], width=11),
                    name=name,
                    connectgaps=False,
                    hoverinfo="skip",
                ))

            # Transparent point traces carry exact interval hover details while
            # leaving the thick, readable Gantt segments visible.
            hover_rows = tl.copy()
            fig.add_trace(go.Scatter(
                x=hover_rows["start_s"],
                y=[f"Task {int(x)}" for x in hover_rows["task_id"]],
                mode="markers",
                marker=dict(size=10, color="rgba(0,0,0,0)"),
                customdata=np.column_stack([
                    hover_rows["testbench"].to_numpy(),
                    hover_rows["end_s"].to_numpy(),
                    hover_rows["execution_ms"].to_numpy(),
                ]),
                hovertemplate=(
                    "<b>%{y}</b><br>"
                    "Testbench: %{customdata[0]}<br>"
                    "Start: %{x:.4f} s<br>"
                    "End: %{customdata[1]:.4f} s<br>"
                    "Execution: %{customdata[2]:.4f} ms<extra></extra>"
                ),
                showlegend=False,
            ))

            max_time = max(float(tl.end_s.max()), 0.1)
            fig.update_layout(
                height=305,
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="#06121E",
                margin=dict(l=52, r=14, t=10, b=86),
                font=dict(family="Inter, Segoe UI, Arial", size=9, color="#B8C9DA"),
                showlegend=True,
                legend=dict(
                    orientation="h",
                    y=-0.25,
                    x=0,
                    xanchor="left",
                    bgcolor="rgba(0,0,0,0)",
                    borderwidth=0,
                    font=dict(size=8, color="#B7C9DA"),
                    traceorder="normal",
                ),
                hovermode="closest",
            )
            fig.update_xaxes(
                title="Trace time (s)",
                range=[0, max_time * 1.01],
                showgrid=True,
                gridcolor="#17324A",
                zeroline=False,
                linecolor="#23425E",
                tickfont=dict(size=8, color="#AFC1D3"),
                title_font=dict(size=9, color="#AFC1D3"),
                ticks="outside",
            )
            fig.update_yaxes(
                title="",
                categoryorder="array",
                categoryarray=task_labels[::-1],
                showgrid=True,
                gridcolor="#0D2234",
                zeroline=False,
                linecolor="#23425E",
                tickfont=dict(size=8, color="#D2DFEA"),
                fixedrange=True,
            )
            st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CONFIG)
            st.caption(
                f"{len(tl):,} execution intervals · {len(task_ids)} task rows · "
                "colors identify the captured testbench; hover a segment for exact timing."
            )
        else:
            st.info("Scheduling timeline is unavailable because the trace contains no valid START → END execution pairs.")

with c2:
    with st.container(border=True):
        panel_title("Testbench Coverage", "Expected 11 testbenches versus actual trace capture")

        coverage_df = pd.DataFrame({
            "Testbench": EXPECTED_TESTBENCHES,
            "Records": [int((df.testbench == x).sum()) for x in EXPECTED_TESTBENCHES],
        })
        coverage_df["Captured"] = coverage_df["Records"] > 0
        captured = int(coverage_df["Captured"].sum())
        coverage_pct = captured / len(EXPECTED_TESTBENCHES) * 100

        # Green completion ring with a neutral remainder.  The value comes
        # directly from the trace's testbench names.
        fig = go.Figure(go.Pie(
            labels=["Captured", "Not captured"],
            values=[captured, len(EXPECTED_TESTBENCHES) - captured],
            hole=0.72,
            sort=False,
            direction="clockwise",
            marker=dict(
                colors=["#20D391", "#172C3F"],
                line=dict(color="#07131F", width=3),
            ),
            textinfo="none",
            hovertemplate="%{label}: %{value} testbenches<extra></extra>",
        ))
        fig.add_annotation(
            x=0.5, y=0.55,
            text=f"<b>{captured}</b>",
            showarrow=False,
            font=dict(size=27, color="#36E5A0", family="Inter, Segoe UI, Arial"),
        )
        fig.add_annotation(
            x=0.5, y=0.40,
            text=f"of {len(EXPECTED_TESTBENCHES)}",
            showarrow=False,
            font=dict(size=10, color="#9FB3C5", family="Inter, Segoe UI, Arial"),
        )
        fig.update_layout(
            height=175,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=2, r=2, t=2, b=2),
            showlegend=False,
        )
        st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CONFIG)

        # Exact 11-item list. Captured rows use green checks; missing rows use
        # a clear red state. Record counts are real values from the CSV.
        for row in coverage_df.itertuples(index=False):
            if row.Captured:
                icon, cls = "✓", "captured"
                detail = f"{int(row.Records):,} records"
            else:
                icon, cls = "–", "missing"
                detail = "not captured"
            st.markdown(
                f'<div class="coverage-row">'
                f'<span class="coverage-check {cls}">{icon}</span>'
                f'<span class="coverage-name">{row.Testbench}</span>'
                f'<span class="coverage-count">{detail}</span>'
                f'</div>',
                unsafe_allow_html=True,
            )

        st.markdown(
            f'<div class="coverage-total"><b>{coverage_pct:.0f}%</b> captured · '
            f'{captured}/{len(EXPECTED_TESTBENCHES)} testbenches present in the trace</div>',
            unsafe_allow_html=True,
        )
        st.caption("Coverage is independent of System Health; it describes what was captured, not whether the RTOS passed or failed.")

# ------------------------------------------------------------
# CONTEXT EVENTS
# ------------------------------------------------------------
section("Context-Switch Activity", "Application-level CONTEXT_SWITCH events captured by the instrumentation")
ctx = df[df.event == "CONTEXT_SWITCH"].copy()
if not ctx.empty:
    cc = ctx.groupby(["testbench","task_id"],as_index=False).size().rename(columns={"size":"events"})
    cc["task"] = cc.testbench + " / T" + cc.task_id.astype(int).astype(str)
    fig = px.bar(cc.sort_values("events",ascending=True), x="events", y="task", orientation="h")
    fig.update_traces(marker_color="#ff9f2f")
    fig.update_xaxes(title="Recorded CONTEXT_SWITCH events")
    fig.update_yaxes(title="")
    st.plotly_chart(chart_base(fig, 300), use_container_width=True, config=PLOTLY_CONFIG)
    st.caption("Important: these are application-level instrumentation events around scheduling activity (for example sched_yield); they are not a kernel-confirmed context-switch counter.")
else:
    st.info("No CONTEXT_SWITCH events were captured in this trace.")

# ------------------------------------------------------------
# EVENT EXPLORER
# ------------------------------------------------------------
section("Trace Event Explorer", "Inspect the original records and export filtered data")
f1,f2,f3,f4 = st.columns([1.3,1,1,.7])
with f1:
    selected_tb = st.selectbox("Testbench", ["All"] + sorted(df.testbench.dropna().unique().tolist()))
with f2:
    selected_event = st.selectbox("Event", ["All"] + sorted(df.event.dropna().unique().tolist()))
with f3:
    tasks = sorted(df.task_id.dropna().astype(int).unique().tolist())
    selected_task = st.selectbox("Task ID", ["All"] + tasks)
with f4:
    max_rows = st.selectbox("Rows", [50,100,250,500,1000], index=0)

filtered = df.copy()
if selected_tb != "All": filtered = filtered[filtered.testbench == selected_tb]
if selected_event != "All": filtered = filtered[filtered.event == selected_event]
if selected_task != "All": filtered = filtered[filtered.task_id == int(selected_task)]

view = filtered.head(max_rows).copy()
view["timestamp_s"] = (view.timestamp_ns - float(df.timestamp_ns.min())) / 1e9
view["execution_ms"] = view.execution_time_ns / 1e6
view["deadline_ms"] = view.deadline_ns / 1e6
cols = ["timestamp_s","testbench","task_id","event","execution_ms","deadline_ms","temperature_c"]
st.dataframe(view[cols].round(4), use_container_width=True, hide_index=True)
st.download_button("⇩  Export Filtered CSV", filtered.to_csv(index=False).encode("utf-8"), "rtos_filtered_trace.csv", "text/csv")

# ------------------------------------------------------------
# FINAL SYSTEM STATUS + REPORT SUMMARY
# ------------------------------------------------------------
section("System Summary", "Trace-derived values suitable for your final project report")
s1,s2,s3,s4,s5 = st.columns(5)
s1.metric("AVG EXECUTION", safe(m["avg_execution_ms"], "{:.3f}") + " ms")
s2.metric("MIN EXECUTION", safe(m["min_execution_ms"], "{:.3f}") + " ms")
s3.metric("MAX EXECUTION", safe(m["max_execution_ms"], "{:.3f}") + " ms")
s4.metric("CAPTURE WINDOW", safe(m["duration_s"], "{:.3f}") + " s")
s5.metric("CONTEXT EVENTS", f'{m["context_events"]:,}')

if m["health"] == "HEALTHY":
    st.success(f"SYSTEM HEALTH: HEALTHY — {m['health_reason']}")
elif m["health"] == "WARNING":
    st.warning(f"SYSTEM HEALTH: WARNING — {m['health_reason']}")
else:
    st.error(f"SYSTEM HEALTH: ERROR — {m['health_reason']}")

st.markdown(
    f'<div class="panel"><div class="panel-title">TRACE INTEGRITY</div><div class="panel-caption">Source: {source_name} · {m["records"]:,} records · {m["tasks"]:,} task/testbench combinations · {m["duration_s"]:.3f} s capture window</div><div class="evidence">Aggregate Task Load is a trace-derived execution-time ratio, not a physical CPU utilization measurement. System Health is not inferred from testbench coverage.</div></div>',
    unsafe_allow_html=True,
)

st.markdown('<div style="height:20px"></div><div style="text-align:center;color:#4f657c;font-size:8px;letter-spacing:.13em;border-top:1px solid #13263a;padding-top:15px">AUTOMOTIVE RTOS ANALYZER · QNX 8.0.0 · RASPBERRY PI · TRACE-BASED PERFORMANCE MONITORING</div>', unsafe_allow_html=True)
