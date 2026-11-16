import pandas as pd
import plotly.express as px
import streamlit as st

import data

st.set_page_config(page_title="Sales Dashboard", page_icon="📊", layout="wide")

PALETTE = ["#4F46E5", "#06B6D4", "#F59E0B", "#10B981", "#EF4444", "#8B5CF6"]

# ---------- Custom styling ----------
st.markdown(
    """
    <style>
    .block-container {padding-top: 2rem; padding-bottom: 2rem;}
    .hero {
        background: linear-gradient(135deg, #4F46E5 0%, #06B6D4 100%);
        padding: 28px 32px; border-radius: 18px; color: white; margin-bottom: 24px;
    }
    .hero h1 {color: white; margin: 0; font-size: 2.2rem;}
    .hero p {margin: 6px 0 0 0; opacity: 0.9; font-size: 1.05rem;}
    div[data-testid="stMetric"] {
        background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 16px;
        padding: 18px 22px; box-shadow: 0 2px 8px rgba(15, 23, 42, 0.06);
    }
    div[data-testid="stMetricLabel"] {color: #64748B; font-weight: 600;}
    div[data-testid="stMetricValue"] {color: #0F172A;}
    .insight {
        background: #EEF2FF; border-left: 6px solid #4F46E5; border-radius: 10px;
        padding: 16px 20px; margin: 20px 0; font-size: 1.05rem; color: #1E1B4B;
    }
    .stTabs [data-baseweb="tab"] {font-weight: 600; font-size: 1rem;}
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data
def get_data():
    return data.load_data()


def style(fig, height=380):
    fig.update_layout(
        template="plotly_white",
        height=height,
        margin=dict(l=10, r=10, t=50, b=10),
        title_font=dict(size=18),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        legend=dict(orientation="h", yanchor="bottom", y=-0.25, xanchor="center", x=0.5),
    )
    return fig


df = get_data()

# ---------- Header ----------
st.markdown(
    """
    <div class="hero">
        <h1>📊 Superstore Sales Dashboard</h1>
        <p>Which categories, regions and months drive sales, and is the business growing?</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------- Sidebar filters ----------
st.sidebar.header("🔎 Filters")

min_d, max_d = df["Order Date"].min().date(), df["Order Date"].max().date()
date_range = st.sidebar.date_input("Date range", (min_d, max_d), min_d, max_d)

regions = sorted(df["Region"].unique())
categories = sorted(df["Category"].unique())
segments = sorted(df["Segment"].unique())

region = st.sidebar.multiselect("Region", regions, regions)
category = st.sidebar.multiselect("Category", categories, categories)
segment = st.sidebar.multiselect("Segment", segments, segments)

if len(date_range) != 2:
    st.info("Please select both a start date and an end date.")
    st.stop()

f = data.filter_data(df, region, category, segment, date_range[0], date_range[1])

if f.empty:
    st.warning("No data available for the selected filters.")
    st.stop()

# ---------- KPIs ----------
k = data.kpis(f)
c1, c2, c3, c4 = st.columns(4)
c1.metric("💰 Total Sales", f"${k['total_sales']:,.0f}")
c2.metric("🧾 Orders", f"{k['orders']:,}")
c3.metric("👥 Customers", f"{k['customers']:,}")
c4.metric("🛒 Avg Order Value", f"${k['avg_order']:,.0f}")

# ---------- Key message ----------
cat_sales = f.groupby("Category")["Sales"].sum().reset_index()
reg_sales = f.groupby("Region")["Sales"].sum().reset_index()
top_cat = cat_sales.loc[cat_sales["Sales"].idxmax()]
top_reg = reg_sales.loc[reg_sales["Sales"].idxmax()]
top_cat_share = top_cat["Sales"] / k["total_sales"] * 100

message = (
    f"<b>{top_cat['Category']}</b> accounts for {top_cat_share:.0f}% of sales, "
    f"<b>{top_reg['Region']}</b> is the top region, and sales peak in "
    f"<b>{data.peak_month(f)}</b>."
)
growth = data.growth_vs_previous_year(f)
if growth:
    year, pct = growth
    message += f" Sales in {year} are {pct:+.0f}% compared with the year before."

st.markdown(f'<div class="insight">💡 <b>Key insight:</b> {message}</div>', unsafe_allow_html=True)
st.caption("Note: the dataset has Sales only (no profit, quantity or discount), so this shows revenue, not profitability.")

# ---------- Tabs ----------
tab1, tab2, tab3, tab4 = st.tabs(["📈 Overview", "📅 Trends", "🏷️ Products", "📄 Data"])

with tab1:
    left, right = st.columns([3, 2])

    monthly = f.groupby(f["Order Date"].dt.to_period("M"))["Sales"].sum().reset_index()
    monthly["Order Date"] = monthly["Order Date"].dt.to_timestamp()
    fig = px.area(monthly, x="Order Date", y="Sales", title="Monthly Sales Trend",
                  color_discrete_sequence=[PALETTE[0]])
    fig.update_traces(line=dict(width=3))
    left.plotly_chart(style(fig), width="stretch")

    fig = px.pie(reg_sales, names="Region", values="Sales", hole=0.55,
                 title="Sales by Region", color_discrete_sequence=PALETTE)
    fig.update_traces(textinfo="percent+label")
    right.plotly_chart(style(fig), width="stretch")

    left, right = st.columns(2)

    fig = px.bar(cat_sales, x="Category", y="Sales", color="Category",
                 title="Sales by Category", color_discrete_sequence=PALETTE)
    fig.update_layout(showlegend=False)
    left.plotly_chart(style(fig), width="stretch")

    seg_sales = f.groupby("Segment")["Sales"].sum().reset_index()
    fig = px.bar(seg_sales, x="Segment", y="Sales", color="Segment",
                 title="Sales by Segment", color_discrete_sequence=PALETTE[1:])
    fig.update_layout(showlegend=False)
    right.plotly_chart(style(fig), width="stretch")

with tab2:
    left, right = st.columns([3, 2])

    seasonal = (
        f.assign(Year=f["Order Date"].dt.year.astype(str), Month=f["Order Date"].dt.month)
        .groupby(["Year", "Month"])["Sales"].sum().reset_index()
    )
    fig = px.line(seasonal, x="Month", y="Sales", color="Year", markers=True,
                  title="Sales by Month, Year over Year", color_discrete_sequence=PALETTE)
    fig.update_xaxes(tickmode="linear", dtick=1)
    left.plotly_chart(style(fig, 420), width="stretch")

    yearly = data.yearly_sales(f)
    yearly["Year"] = yearly["Year"].astype(str)
    fig = px.bar(yearly, x="Year", y="Sales", text_auto=".3s", title="Total Sales per Year",
                 color_discrete_sequence=[PALETTE[1]])
    right.plotly_chart(style(fig, 420), width="stretch")

    top_states = f.groupby("State")["Sales"].sum().nlargest(10).reset_index()
    fig = px.bar(top_states.sort_values("Sales"), x="Sales", y="State", orientation="h",
                 title="Top 10 States", color_discrete_sequence=[PALETTE[3]])
    st.plotly_chart(style(fig, 420), width="stretch")

with tab3:
    left, right = st.columns(2)

    top_sub = f.groupby("Sub-Category")["Sales"].sum().nlargest(10).reset_index()
    fig = px.bar(top_sub.sort_values("Sales"), x="Sales", y="Sub-Category",
                 orientation="h", title="Top 10 Sub-Categories",
                 color="Sales", color_continuous_scale="Blues")
    fig.update_layout(coloraxis_showscale=False)
    left.plotly_chart(style(fig, 460), width="stretch")

    top_prod = f.groupby("Product Name")["Sales"].sum().nlargest(10).reset_index()
    top_prod["Product Name"] = top_prod["Product Name"].str.slice(0, 35)
    fig = px.bar(top_prod.sort_values("Sales"), x="Sales", y="Product Name",
                 orientation="h", title="Top 10 Products",
                 color="Sales", color_continuous_scale="Teal")
    fig.update_layout(coloraxis_showscale=False)
    right.plotly_chart(style(fig, 460), width="stretch")

with tab4:
    st.dataframe(f, width="stretch", height=450)
    st.download_button(
        "⬇️ Download filtered data (CSV)",
        f.to_csv(index=False).encode("utf-8"),
        file_name="filtered_sales.csv",
        mime="text/csv",
    )
