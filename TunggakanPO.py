import os
import pandas as pd
import streamlit as st

# =========================
# PAGE CONFIG
# =========================
st.set_page_config(page_title="Tunggakan PO + PTJ", layout="wide")

st.markdown("""
<style>
/* =========================
   NICE TABLE (eAset theme)
   ========================= */
.table-wrap {
    max-height: 380px;                /* 10 rows-ish */
    overflow-y: auto;
    border-radius: 14px;
    border: 1px solid rgba(46,95,138,0.20);
    box-shadow: 0 8px 18px rgba(46,95,138,0.10);
    background: white;
    margin-top: 8px;
}

/* table base */
.table-wrap table {
    width: 100%;
    border-collapse: collapse;
    font-size: 14px;
}

/* header (FIX overlap when scroll) */
.table-wrap thead th{
    position: sticky;
    top: 0;
    z-index: 20;                       /* higher than body */
    background: rgba(110,198,197,0.95);/* more solid so rows won't show through */
    color: #1F3B57;
    font-weight: 700;
    text-align: left;
    padding: 10px 12px;
    border-bottom: 2px solid rgba(46,95,138,0.25);

    /* extra protection */
    background-clip: padding-box;
}

/* optional: keep header on its own layer */
.table-wrap thead{
    position: sticky;
    top: 0;
    z-index: 30;
}


/* body cells */
.table-wrap tbody td {
    padding: 9px 12px;
    border-bottom: 1px solid rgba(46,95,138,0.10);
    color: #111827;
}

/* zebra */
.table-wrap tbody tr:nth-child(even) td {
    background: rgba(247,249,252,0.85);
}

/* hover */
.table-wrap tbody tr:hover td {
    background: rgba(110,198,197,0.18);
}
</style>
""", unsafe_allow_html=True)


st.markdown("""
<style>
/* ===== SIDEBAR BACKGROUND ===== */
section[data-testid="stSidebar"] {
    background: linear-gradient(
        180deg,
        #2E5F8A 0%,
        #3F7FA5 50%,
        #6EC6C5 100%
    ) !important;
    color: white !important;
}

/* Sidebar headers */
section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 {
    color: white !important;
}

/* Sidebar slicer titles */
section[data-testid="stSidebar"] label {
    color: white !important;
    font-weight: 600;
}

/* Dropdown box */
section[data-testid="stSidebar"] select,
section[data-testid="stSidebar"] input {
    background: white !important;
    color: #6b7280 !important;   /* 👈 GREY text inside box */
    border-radius: 10px !important;
    border: none !important;
    font-size: 16px !important;
}

/* Dropdown options */
section[data-testid="stSidebar"] option {
    color: #1f2937 !important;
    font-size : 4px !important;
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<style>
/* ===== MAIN APP BACKGROUND ===== */
html, body, [data-testid="stAppViewContainer"] {
    background-color: #F7F9FC !important;
}

/* Optional: remove default padding feel */
[data-testid="stVerticalBlock"] {
    padding-top: 0.5rem;
}
</style>
""", unsafe_allow_html=True)


# =========================
# CSS (box around charts/tables)
# =========================
BOX_STYLE = """
<div style="
    background: white;
    padding: 14px 14px 10px 14px;
    border-radius: 14px;
    border: 1px solid rgba(0,0,0,0.10);
    box-shadow: 0 6px 18px rgba(0,0,0,0.05);
">
"""
BOX_END = "</div>"

# =========================
# PATHS
# =========================
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

ME2N_PATH = os.path.join(SCRIPT_DIR, "ME2N.csv")
ME2K_PATH = os.path.join(SCRIPT_DIR, "ME2K.csv")
MANUAL_PATH = os.path.join(SCRIPT_DIR, "Manual_PTJ_template.csv")  # your completed manual file
DIMPTJ_PATH = os.path.join(SCRIPT_DIR, "DimPTJ.csv")


# =========================
# HELPERS
# =========================

from datetime import datetime

def get_last_updated_date(file_paths: list[str]) -> str:
    from datetime import datetime

    latest_ts = 0
    for p in file_paths:
        if os.path.exists(p):
            ts = os.path.getmtime(p)
            if ts > latest_ts:
                latest_ts = ts

    if latest_ts == 0:
        return "N/A"

    dt = datetime.fromtimestamp(latest_ts)
    return dt.strftime("%d/%m/%Y")   # ✅ DATE ONLY


def format_short(num):
    try:
        num = float(num)
    except:
        return ""

    if num >= 1_000_000:
        return f"{num/1_000_000:.1f}m".rstrip("0").rstrip(".")
    elif num >= 1_000:
        return f"{num/1_000:.0f}k"
    else:
        return f"{int(num)}"

def clean_po(s: pd.Series) -> pd.Series:
    return (
        s.astype(str)
         .str.strip()
         .str.replace(r"\.0$", "", regex=True)
    )

def clean_ptj(s: pd.Series) -> pd.Series:
    return (
        s.astype(str)
         .str.strip()
         .str.replace(r"\.0$", "", regex=True)
         .replace({"nan": "", "None": "", "0": ""})
    )

def to_float_safe(s: pd.Series) -> pd.Series:
    # handles "30,960.00", "", NaN
    return pd.to_numeric(
        s.astype(str).str.replace(",", "", regex=False).str.strip(),
        errors="coerce"
    ).fillna(0.0)

@st.cache_data(show_spinner=False)
def load_data():
    # --- Load ME2N (base) ---
    me2n = pd.read_csv(ME2N_PATH, dtype=str, encoding="utf-8-sig")
    me2n.columns = [c.strip() for c in me2n.columns]
    me2n["PO Number"] = clean_po(me2n["PO Number"])

    # --- Load ME2K (PTJ mapping) ---
    me2k = pd.read_csv(ME2K_PATH, dtype=str, encoding="utf-8-sig")
    me2k.columns = [c.strip() for c in me2k.columns]
    me2k["PO Number"] = clean_po(me2k["PO Number"])
    me2k["PTJ Number"] = clean_ptj(me2k["PTJ Number"])

    # --- Load Manual PTJ ---
    manual = pd.read_csv(MANUAL_PATH, dtype=str, encoding="utf-8-sig")
    manual.columns = [c.strip() for c in manual.columns]
    manual["PO Number"] = clean_po(manual["PO Number"])
    manual["PTJ Number"] = clean_ptj(manual["PTJ Number"])

    manual_filled = manual[manual["PTJ Number"].str.strip() != ""]

    ptj_map = pd.concat(
        [
            me2k[["PO Number", "PTJ Number"]].assign(PTJ_Source="ME2K"),
            manual_filled[["PO Number", "PTJ Number"]].assign(PTJ_Source="Manual"),
        ],
        ignore_index=True
    ).sort_values(["PO Number", "PTJ_Source"]) \
     .drop_duplicates("PO Number", keep="last")

    # ✅ STILL INSIDE FUNCTION
    merged = me2n.merge(ptj_map, on="PO Number", how="left")

    # --- Load DimPTJ ---
    dim = pd.read_csv(DIMPTJ_PATH, dtype=str, encoding="utf-8-sig")
    dim.columns = [c.strip() for c in dim.columns]

    if "PTJ NO" not in dim.columns:
        raise ValueError("DimPTJ.csv must contain column: 'PTJ NO'")

    dim = dim.rename(columns={"PTJ NO": "PTJ Number"})
    dim["PTJ Number"] = clean_ptj(dim["PTJ Number"]).astype(str).str.strip()

    merged["PTJ Number"] = clean_ptj(merged["PTJ Number"]).astype(str).str.strip()

    final = merged.merge(dim, on="PTJ Number", how="left")

    # --- Numeric columns ---
    if "PO Balance" in final.columns:
        final["PO Balance_num"] = to_float_safe(final["PO Balance"])
    else:
        final["PO Balance_num"] = 0.0

    if "PO Total Amount" in final.columns:
        final["PO Total Amount_num"] = to_float_safe(final["PO Total Amount"])
    else:
        final["PO Total Amount_num"] = 0.0



    return final



# =========================
# APP
# =========================
st.title("Laporan Tunggakan Pesanan Tempatan")

LOGO_PATH = os.path.join(SCRIPT_DIR, "cidb_logo.png")

st.sidebar.image(LOGO_PATH, width=140)
st.sidebar.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)


missing_files = [p for p in [ME2N_PATH, ME2K_PATH, MANUAL_PATH, DIMPTJ_PATH] if not os.path.exists(p)]
if missing_files:
    st.error("Missing required files in the same folder as this Streamlit app:")
    for p in missing_files:
        st.write("-", p)
    st.stop()

last_updated = get_last_updated_date([ME2N_PATH, ME2K_PATH, MANUAL_PATH, DIMPTJ_PATH])



df = load_data()

# =========================
# BASE FILTER: Outstanding PO only
# =========================
df = df[df["PO Balance_num"] > 0].copy()


# =========================
# SIDEBAR FILTERS (SINGLE SELECT)
# =========================
st.sidebar.header("Tapisan")

SEKTOR_COL = "SEKTOR"
BAHAGIAN_COL = "BAHAGIAN/UNIT"
VENDOR_COL = "Vendor name"

f = df.copy()

# 1) SEKTOR (single select)
sektor_list = sorted(
    [x for x in f[SEKTOR_COL].dropna().astype(str).unique().tolist() if x.strip() != ""]
)
sektor_choice = st.sidebar.selectbox("Sektor", ["All"] + sektor_list, index=0)

if sektor_choice != "All":
    f = f[f[SEKTOR_COL].astype(str) == sektor_choice]

# 2) BAHAGIAN/UNIT/NEG./CAW. (single select, cascades after sektor)
bahagian_list = sorted(
    [x for x in f[BAHAGIAN_COL].dropna().astype(str).unique().tolist() if x.strip() != ""]
)
bahagian_choice = st.sidebar.selectbox("BAHAGIAN/UNIT/NEG./CAW.", ["All"] + bahagian_list, index=0)

if bahagian_choice != "All":
    f = f[f[BAHAGIAN_COL].astype(str) == bahagian_choice]

# 3) Vendor (single select, cascades after bahagian)
vendor_list = sorted(
    [x for x in f[VENDOR_COL].dropna().astype(str).unique().tolist() if x.strip() != ""]
)
vendor_choice = st.sidebar.selectbox("Vendor", ["All"] + vendor_list, index=0)

if vendor_choice != "All":
    f = f[f[VENDOR_COL].astype(str) == vendor_choice]

# =========================
# LAST UPDATED (UNDER SLICER)
# =========================
last_updated = get_last_updated_date([ME2N_PATH, ME2K_PATH, MANUAL_PATH, DIMPTJ_PATH])

st.sidebar.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

st.sidebar.markdown(
    f"""
    <div style="
        font-size: 12px;
        color: rgba(255,255,255,0.85);
        font-weight: 600;
    ">
        Tarikh kemaskini data :
    </div>
    <div style="
        font-size: 13px;
        color: #FFFFFF;
        font-weight: 800;
        letter-spacing: 0.3px;
    ">
        {last_updated}
    </div>
    """,
    unsafe_allow_html=True
)


# =========================
# KPI ROW
# =========================
total_po = f["PO Number"].nunique()
total_balance = f["PO Balance_num"].sum()


c1, c2 = st.columns(2)
with c1:
    st.markdown(BOX_STYLE + f"<div style='font-size:14px;color:#475569;'>Jumlah Pesanan Tempatan</div><div style='font-size:28px;font-weight:800;color:#1F3B57;'>{total_po:,}</div>" + BOX_END, unsafe_allow_html=True)
with c2:
    st.markdown(BOX_STYLE + f"<div style='font-size:14px;color:#475569;'>Baki Pesanan Tempatan (RM)</div><div style='font-size:28px;font-weight:800;color:#1F3B57;'>{total_balance:,.2f}</div>" + BOX_END, unsafe_allow_html=True)


st.write("")

# =========================
# BAR CHART
# =========================
import plotly.graph_objects as go

BAR_COLOR = "#2E5F8A"   # theme blue (matches sidebar top)

if "PTJ" in f.columns:

    chart_df = (
        f.groupby("PTJ", dropna=False)["PO Balance_num"]
         .sum()
         .reset_index()
         .rename(columns={"PO Balance_num": "Total Balance"})
    )

    chart_df["PTJ"] = chart_df["PTJ"].fillna("").astype(str).str.strip()
    chart_df = chart_df[chart_df["PTJ"] != ""]
    chart_df = chart_df.sort_values("Total Balance", ascending=False)

    chart_df["Label"] = chart_df["Total Balance"].apply(format_short)

    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=chart_df["PTJ"],
        y=chart_df["Total Balance"],
        text=chart_df["Label"],
        textposition="outside",
        cliponaxis=False,
        marker=dict(
            color=BAR_COLOR,
            line=dict(width=0),
            cornerradius=8  # rounded bars
        )
    ))

    fig.update_layout(
        title=dict(
            text="Tunggakan Pesanan Tempatan Mengikut PTJ",
            x=0.5,
            xanchor="center",
            font=dict(
                size=16,
                color="#1F2937",
                family="Arial"
            )
        ),
        height=420,
        margin=dict(l=10, r=10, t=40, b=10),
        showlegend=False,
        plot_bgcolor="white",
        paper_bgcolor="white",
        xaxis_title=None,
        yaxis_title=None,
    )

    fig.update_yaxes(
        showticklabels=False,
        showgrid=False,
        zeroline=False
    )

    fig.update_xaxes(showgrid=False)

    st.plotly_chart(fig, use_container_width=True)

else:
    st.info("Column 'PTJ' not found in data (DimPTJ join may be missing).")





# =========================
# PREPARE RAW DATA TABLE (DISPLAY ONLY)
# =========================
display_cols = [
    "PO Number",
    "Vendor name",
    "Posting date",
    "PO Balance",
    "BAHAGIAN/UNIT",
]

table_df = f[display_cols + ["PO Balance_num"]].copy()

# ✅ format same as dashboard
table_df["PO Balance"] = table_df["PO Balance_num"].map(lambda x: f"RM {x:,.2f}")
table_df["Posting date"] = table_df["Posting date"].astype(str)  # optional safety

# ✅ add running number
table_df.insert(0, "No.", range(1, len(table_df) + 1))

# ✅ remove helper col (so download matches table exactly)
table_df.drop(columns=["PO Balance_num"], inplace=True)

# =========================
# PREPARE CSV (MATCH TABLE EXACTLY)
# =========================
csv_bytes = table_df.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")

# =========================
# MAIN TABLE (TITLE + DOWNLOAD BUTTON SAME ROW)
# =========================
left, right = st.columns([7, 2])

with left:
    st.subheader("Butiran Pesanan Tempatan")

with right:
    st.download_button(
        "⬇️ Muat Turun",
        data=csv_bytes,
        file_name="butiran_pesanan_tempatan.csv",
        mime="text/csv",
        use_container_width=True
    )

# =========================
# RENDER TABLE (HTML)
# =========================
table_html = table_df.to_html(index=False, escape=False)

st.markdown(
    f"""
    <div class="table-wrap">
        {table_html}
    </div>
    """,
    unsafe_allow_html=True
)







