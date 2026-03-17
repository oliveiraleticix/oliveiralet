from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st


st.set_page_config(
    page_title="NDF MtM Monthly Variations",
    page_icon=":bar_chart:",
    layout="wide",
)


NUBANK_COLORS = {
    "primary": "#820AD1",
    "secondary": "#9F3CFF",
    "light": "#EDE3FF",
    "dark": "#43006B",
    "text": "#1E1E1E",
}


EXPECTED_COLUMNS = [
    "reference_date",
    "processing_org_full_name",
    "book",
    "product_description",
    "product_currency",
    "position_id",
    "quantity",
    "notional",
    "market_value",
    "npv",
    "accrual_bo",
    "total_accrual",
]


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    renamed = {col: col.strip().lower() for col in df.columns}
    out = df.rename(columns=renamed).copy()
    return out


def load_file(uploaded_file) -> pd.DataFrame:
    name = uploaded_file.name.lower()
    if name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
    elif name.endswith(".parquet"):
        df = pd.read_parquet(uploaded_file)
    else:
        raise ValueError("Unsupported file format. Use CSV or Parquet.")
    return normalize_columns(df)


def prepare_data(df: pd.DataFrame, mtm_column: str) -> pd.DataFrame:
    if "reference_date" not in df.columns:
        raise ValueError("Missing required column: reference_date")

    data = df.copy()
    data["reference_date"] = pd.to_datetime(data["reference_date"]).dt.normalize()

    for col in ("product_type", "product_subtype"):
        if col in data.columns:
            data[col] = data[col].astype(str).str.upper()

    if "product_type" in data.columns or "product_subtype" in data.columns:
        type_ok = data.get("product_type", pd.Series(index=data.index, dtype=str)).eq("FXNDF")
        subtype_ok = data.get("product_subtype", pd.Series(index=data.index, dtype=str)).eq("FXNDF")
        data = data[type_ok | subtype_ok].copy()

    if mtm_column not in data.columns:
        raise ValueError(f"MtM column not found: {mtm_column}")

    data[mtm_column] = pd.to_numeric(data[mtm_column], errors="coerce").fillna(0.0)
    data["book"] = data.get("book", "Unknown").fillna("Unknown")
    data["processing_org_full_name"] = data.get("processing_org_full_name", "Unknown").fillna("Unknown")
    return data


def compute_monthly_delta(
    data: pd.DataFrame, mtm_column: str, breakdown_by_book: bool
) -> tuple[pd.DataFrame, pd.DataFrame]:
    metric = data[["reference_date", "book", mtm_column]].copy()

    if not breakdown_by_book:
        metric["book"] = "TOTAL"

    daily = (
        metric.groupby(["book", "reference_date"], as_index=False)[mtm_column]
        .sum()
        .sort_values(["book", "reference_date"])
    )

    # Reversal logic: daily realized effect is the change vs previous day.
    # First available day assumes previous day MtM = 0.
    daily["daily_delta"] = daily.groupby("book")[mtm_column].diff()
    first_idx = daily.groupby("book").head(1).index
    daily.loc[first_idx, "daily_delta"] = daily.loc[first_idx, mtm_column]
    daily["daily_delta"] = daily["daily_delta"].fillna(0.0)

    daily["month"] = daily["reference_date"].dt.to_period("M").dt.to_timestamp()
    monthly = (
        daily.groupby(["book", "month"], as_index=False)["daily_delta"]
        .sum()
        .rename(columns={"daily_delta": "monthly_delta_effect"})
        .sort_values(["book", "month"])
    )

    monthly["mom_variation"] = monthly.groupby("book")["monthly_delta_effect"].diff()
    prev = monthly.groupby("book")["monthly_delta_effect"].shift(1)
    monthly["mom_variation_pct"] = np.where(
        prev.abs() > 0,
        monthly["mom_variation"] / prev.abs(),
        np.nan,
    )
    return daily, monthly


def format_number(value: float) -> str:
    if pd.isna(value):
        return "-"
    return f"{value:,.2f}"


def render_header() -> None:
    st.markdown(
        f"""
        <style>
        .main-title {{
            font-size: 32px;
            font-weight: 700;
            color: {NUBANK_COLORS["primary"]};
            margin-bottom: 0.25rem;
        }}
        .sub-title {{
            color: {NUBANK_COLORS["dark"]};
            margin-top: 0;
            margin-bottom: 1rem;
        }}
        </style>
        <p class="main-title">NDF MtM - Monthly Variation Dashboard</p>
        <p class="sub-title">Delta monthly effect with daily reversal logic</p>
        """,
        unsafe_allow_html=True,
    )


render_header()

with st.expander("Required columns / SQL reference", expanded=False):
    st.write(
        "Upload CSV or Parquet with at least: "
        "`reference_date`, `book`, `market_value` or `npv`, "
        "and optionally `product_type`/`product_subtype`."
    )
    st.code(
        """SELECT
  to_date(file_datetime) AS reference_date,
  processing_org_full_name,
  book,
  product_description,
  product_currency,
  position_id,
  quantity,
  notional,
  market_value,
  npv,
  accrual_bo,
  total_accrual,
  product_type,
  product_subtype
FROM br__dataset.calypso_positions_report_bonds_latest
WHERE (product_type = 'FXNDF' OR product_subtype = 'FXNDF')
  AND to_date(file_datetime) BETWEEN DATE '2025-01-01' AND DATE '2025-12-31'"""
    )

uploaded = st.file_uploader("Upload positions file (CSV or Parquet)", type=["csv", "parquet"])

if not uploaded:
    st.info("Upload a file to start the analysis.")
    st.stop()

raw = load_file(uploaded)
available_metric_columns = [c for c in ["market_value", "npv"] if c in raw.columns]
if not available_metric_columns:
    st.error("Input file must include either `market_value` or `npv`.")
    st.stop()

left, right = st.columns([1, 1])
with left:
    mtm_column = st.selectbox("MtM base column", options=available_metric_columns, index=0)
with right:
    breakdown_by_book = st.toggle("Breakdown by book", value=True)

data = prepare_data(raw, mtm_column=mtm_column)

org_options = sorted(data["processing_org_full_name"].dropna().unique().tolist())
if org_options:
    selected_orgs = st.multiselect(
        "Processing org filter",
        options=org_options,
        default=org_options,
    )
    if selected_orgs:
        data = data[data["processing_org_full_name"].isin(selected_orgs)]

book_options = sorted(data["book"].dropna().unique().tolist())
if breakdown_by_book and book_options:
    selected_books = st.multiselect("Book filter", options=book_options, default=book_options)
    if selected_books:
        data = data[data["book"].isin(selected_books)]

if data.empty:
    st.warning("No data after filters.")
    st.stop()

daily, monthly = compute_monthly_delta(data, mtm_column=mtm_column, breakdown_by_book=breakdown_by_book)

if monthly.empty:
    st.warning("No monthly variation available for the selected data.")
    st.stop()

latest_month = monthly["month"].max()
latest_rows = monthly[monthly["month"] == latest_month]
latest_total = latest_rows["monthly_delta_effect"].sum()
latest_mom = latest_rows["mom_variation"].sum(skipna=True)
latest_prev_total = latest_total - latest_mom
latest_mom_pct = (latest_mom / abs(latest_prev_total)) if latest_prev_total != 0 else np.nan

k1, k2, k3 = st.columns(3)
k1.metric("Latest month delta effect", format_number(latest_total))
k2.metric("MoM variation (abs)", format_number(latest_mom))
k3.metric("MoM variation (%)", "-" if pd.isna(latest_mom_pct) else f"{latest_mom_pct:.2%}")

line_fig = px.line(
    monthly,
    x="month",
    y="monthly_delta_effect",
    color="book",
    markers=True,
    title="Monthly delta effect (sum of daily MtM deltas)",
    color_discrete_sequence=[NUBANK_COLORS["primary"], NUBANK_COLORS["secondary"], "#C58CFF", "#5A189A"],
)
line_fig.update_layout(
    xaxis_title="Month",
    yaxis_title="Delta effect",
    plot_bgcolor="white",
    paper_bgcolor="white",
)
st.plotly_chart(line_fig, use_container_width=True)

bar_fig = px.bar(
    monthly,
    x="month",
    y="mom_variation",
    color="book",
    barmode="group",
    title="Month-over-month variation of the monthly delta effect",
    color_discrete_sequence=[NUBANK_COLORS["primary"], NUBANK_COLORS["secondary"], "#C58CFF", "#5A189A"],
)
bar_fig.update_layout(
    xaxis_title="Month",
    yaxis_title="MoM variation",
    plot_bgcolor="white",
    paper_bgcolor="white",
)
st.plotly_chart(bar_fig, use_container_width=True)

with st.expander("Detailed tables", expanded=False):
    st.subheader("Monthly")
    st.dataframe(monthly, use_container_width=True)
    st.subheader("Daily deltas")
    st.dataframe(daily, use_container_width=True)
