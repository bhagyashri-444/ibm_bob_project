"""
E-Commerce Sales, Customer & Shipping Analytics Dashboard
=========================================================
Run with:  streamlit run app.py

Flow: load CSV -> clean -> sidebar filters -> calculate (src/analysis.py)
      -> charts (src/visualizations.py) -> pages.
All numbers are calculated from the CSV at run time.
"""
from pathlib import Path

import pandas as pd
import streamlit as st

from src import analysis as an
from src import visualizations as viz
from src.data_cleaning import UNKNOWN, clean_data, data_quality_checks, load_raw, profile_raw

BASE_DIR = Path(__file__).resolve().parent
CSV_NAME = "realistic_e_commerce_sales_data.csv"
CSV_CANDIDATES = [BASE_DIR / "data" / CSV_NAME, BASE_DIR / CSV_NAME]  # data/ first, then project root

st.set_page_config(page_title="E-Commerce Analytics Dashboard", page_icon="📊", layout="wide")

st.markdown("""
<style>
div[data-testid="stMetric"] {background:#f5f8fc; border:1px solid #dbe5f1; border-radius:10px; padding:12px 14px;}
@media (prefers-color-scheme: dark) {div[data-testid="stMetric"] {background:#1c2330; border-color:#2f3b4f;}}
</style>
""", unsafe_allow_html=True)


# ------------------------------------------------------------- data loading
@st.cache_data(show_spinner="Loading and cleaning data...")
def load_and_clean(source):
    """Read the CSV (path or uploaded file), profile it and clean it."""
    raw = load_raw(source)
    clean, log = clean_data(raw)
    return raw, clean, log


def get_data():
    """Locate the CSV automatically; offer an upload box if it cannot be found."""
    path = next((p for p in CSV_CANDIDATES if p.exists()), None)
    if path is not None:
        return load_and_clean(str(path)), str(path.relative_to(BASE_DIR))
    st.warning(f"'{CSV_NAME}' was not found in the project's data/ folder. Upload it below to continue.")
    up = st.file_uploader("Upload the e-commerce CSV file", type="csv")
    if up is None:
        st.stop()
    return load_and_clean(up), up.name


def n(x):
    return f"{x:,.0f}"


# ------------------------------------------------------------------ filters
def sidebar_filters(df: pd.DataFrame) -> pd.DataFrame:
    """Draw the sidebar filters and return the filtered DataFrame."""
    st.sidebar.header("🔎 Filters")
    # Product options depend on the chosen category so filters stay consistent
    regions = st.sidebar.multiselect("Region", sorted(df["region"].unique()), default=sorted(df["region"].unique()))
    genders = st.sidebar.multiselect("Gender", sorted(df["gender"].unique()), default=sorted(df["gender"].unique()))
    cats = st.sidebar.multiselect("Category", sorted(df["category"].unique()), default=sorted(df["category"].unique()))
    prod_opts = sorted(df.loc[df["category"].isin(cats), "product"].unique())
    prods = st.sidebar.multiselect("Product", prod_opts, default=prod_opts)
    statuses = st.sidebar.multiselect("Shipping Status", sorted(df["shipping_status"].unique()),
                                      default=sorted(df["shipping_status"].unique()))
    age_opts = [a for a in df["age_group"].cat.categories if a in set(df["age_group"].astype(str))]
    ages = st.sidebar.multiselect("Age Group", age_opts, default=age_opts)
    dmin, dmax = df["order_date"].min().date(), df["order_date"].max().date()
    dr = st.sidebar.date_input("Order Date Range", value=(dmin, dmax), min_value=dmin, max_value=dmax)
    start, end = (dr[0], dr[1]) if isinstance(dr, (tuple, list)) and len(dr) == 2 else (dmin, dmax)

    mask = (df["region"].isin(regions) & df["gender"].isin(genders) & df["category"].isin(cats)
            & df["product"].isin(prods) & df["shipping_status"].isin(statuses) & df["age_group"].astype(str).isin(ages)
            & (df["order_date"].dt.date >= start) & (df["order_date"].dt.date <= end))
    out = df[mask]
    st.sidebar.success(f"{len(out):,} of {len(df):,} orders selected")
    st.sidebar.download_button("⬇️ Download filtered data (CSV)", out.to_csv(index=False).encode("utf-8"),
                               "filtered_ecommerce_data.csv", "text/csv")
    return out


def kpi_row(items):
    cols = st.columns(len(items))
    for c, (label, value, help_) in zip(cols, items):
        c.metric(label, value, help=help_)


def show(fig):
    st.plotly_chart(fig, use_container_width=True)


# -------------------------------------------------------------------- pages
def page_overview(df):
    st.subheader("Executive Overview")
    k = an.compute_kpis(df)
    kpi_row([("Total Revenue", n(k["Total Revenue"]), "Sum of Total Price (shipping not included)"),
             ("Total Orders", n(k["Total Orders"]), "Each row = one order (no Order ID in data)"),
             ("Quantity Sold", n(k["Total Quantity Sold"]), None),
             ("Avg Order Value", n(k["Average Order Value"]), "Revenue / Orders"),
             ("Avg Unit Price", n(k["Average Unit Price"]), "Mean of Unit Price across orders")])
    kpi_row([("Total Shipping Fees", n(k["Total Shipping Fees"]), None),
             ("Avg Shipping Fee", f"{k['Average Shipping Fee']:.2f}", None),
             ("Return Rate", f"{k['Return Rate %']:.1f}%", "Returned / orders with known status"),
             ("Delivered Rate", f"{k['Delivered Rate %']:.1f}%", "Delivered / orders with known status"),
             ("In Transit Rate", f"{k['In Transit Rate %']:.1f}%", "In Transit / orders with known status")])
    kpi_row([("Net Revenue (excl. returns)", n(k["Net Revenue (excl. returns)"]), "Revenue minus revenue of Returned orders"),
             ("Returned Revenue", n(k["Returned Revenue"]), None),
             ("Unique Customers", n(k["Unique Customers"]), "Distinct Customer IDs"),
             ("Orders / Customer", f"{k['Avg Orders per Customer']:.2f}", None),
             ("Unknown Status", f"{k['Unknown Status %']:.1f}%", "Orders with missing shipping status")])
    st.divider()
    m = an.monthly_summary(df)
    show(viz.monthly_trend(m, "revenue", "Monthly Revenue Trend"))
    if m["partial"].any() if not m.empty else False:
        st.caption("Red hollow marker = month with very few days of data (partial month); do not compare with full months.")
    c1, c2 = st.columns(2)
    with c1:
        show(viz.bar_v(an.group_summary(df, "category"), "category", "revenue", "Revenue by Category", "Revenue"))
    with c2:
        show(viz.bar_v(an.group_summary(df[df["region"] != UNKNOWN], "region"), "region", "revenue",
                       "Revenue by Region (known regions)", "Revenue"))
    st.plotly_chart(viz.donut(df.groupby("shipping_status").size().reset_index(name="orders"), "shipping_status",
                              "orders", "Shipping Status Distribution (all orders)", viz.STATUS_COLORS),
                    use_container_width=True)


def page_sales(df):
    st.subheader("Sales Analysis")
    m = an.monthly_summary(df)
    metric = st.selectbox("Monthly metric", ["revenue", "orders", "quantity", "aov"],
                          format_func=lambda x: {"revenue": "Revenue", "orders": "Orders", "quantity": "Quantity sold",
                                                 "aov": "Average order value"}[x])
    show(viz.monthly_trend(m, metric))
    bw = an.best_worst_month(df)
    if bw:
        c1, c2 = st.columns(2)
        c1.metric("Best complete month", bw["best_month"], f"{n(bw['best_revenue'])} revenue")
        c2.metric("Lowest complete month", bw["worst_month"], f"{n(bw['worst_revenue'])} revenue")
    show(viz.daily_trend(an.daily_summary(df)))
    c1, c2 = st.columns(2)
    prod = an.product_summary(df)
    with c1:
        show(viz.bar_h(prod, "product", "revenue", "Revenue by Product", "Revenue", color="category"))
    with c2:
        show(viz.bar_h(an.group_summary(df, "category"), "category", "quantity", "Quantity Sold by Category", "Units sold"))
    show(viz.histogram(df, "quantity", "Distribution of Order Quantity", "Units per order", nbins=5))
    show(viz.heatmap(an.monthly_pivot(df, "category"), "Monthly Revenue by Category (Heatmap)", "Month", "Category"))


def page_customers(df):
    st.subheader("Customer Analysis")
    st.info("Customer IDs in this file are not fully consistent (the same ID can appear with different genders/regions), "
            "so customer-level results are **indicative**. See Business Insights page for the data-quality check.")
    cust = an.customer_segments(an.customer_table(df))
    if cust.empty:
        st.warning("No data for the selected filters.")
        return
    rep = (cust["customer_type"] == "Repeat").mean() * 100
    kpi_row([("Customers (IDs)", n(len(cust)), None), ("Repeat customers", f"{rep:.1f}%", "Customer IDs with more than 1 order"),
             ("Avg orders / customer", f"{cust['orders'].mean():.2f}", None),
             ("Avg revenue / customer", n(cust["revenue"].mean()), None),
             ("Top 20% customers' share", f"{an.pareto_share(cust):.1f}%", "Share of revenue from the top 20% of customers")])
    c1, c2 = st.columns(2)
    with c1:
        show(viz.histogram(df, "age", "Age Distribution of Orders", "Age (years)", nbins=26))
    with c2:
        show(viz.bar_v(an.group_summary(df, "age_group"), "age_group", "revenue", "Revenue by Age Group", "Revenue"))
    c1, c2 = st.columns(2)
    gs = an.group_summary(df, "gender")
    with c1:
        show(viz.bar_v(gs, "gender", "revenue", "Revenue by Gender", "Revenue"))
    with c2:
        show(viz.bar_v(gs, "gender", "orders", "Orders by Gender", "Orders"))
    c1, c2 = st.columns(2)
    with c1:
        freq = cust["orders"].value_counts().sort_index().reset_index()
        freq.columns = ["orders_per_customer", "customers"]
        show(viz.bar_v(freq, "orders_per_customer", "customers", "Purchase Frequency (orders per customer)", "Customers"))
    with c2:
        show(viz.pareto_curve(cust))
    seg = cust.groupby(["frequency_band", "value_tier"], observed=True).agg(customers=("customer_id", "size"),
                                                                           revenue=("revenue", "sum")).reset_index()
    show(viz.grouped_bar(seg, "frequency_band", "customers", "value_tier", "Customer Segments: Purchase Frequency x Value Tier", "Customers"))
    show(viz.scatter(cust, "orders", "revenue", "Customer Orders vs Revenue", "Orders per customer", "Revenue per customer",
                     color="customer_type", hover=["customer_id"]))
    st.markdown("**Top 10 customers by revenue**")
    top = cust.head(10).copy()
    top["revenue_share_%"] = (top["revenue"] / cust["revenue"].sum() * 100).round(2)
    st.dataframe(top[["customer_id", "orders", "quantity", "revenue", "revenue_share_%", "frequency_band", "value_tier"]],
                 use_container_width=True, hide_index=True)


def page_products(df):
    st.subheader("Product & Category Analysis")
    prod, cat = an.product_summary(df), an.group_summary(df, "category")
    c1, c2 = st.columns(2)
    with c1:
        show(viz.bar_h(prod, "product", "revenue", "Top Products by Revenue", "Revenue", color="category"))
    with c2:
        show(viz.bar_h(prod, "product", "quantity", "Top Products by Quantity Sold", "Units sold", color="category"))
    c1, c2 = st.columns(2)
    with c1:
        show(viz.donut(cat, "category", "revenue", "Category Contribution to Revenue"))
    with c2:
        show(viz.donut(cat, "category", "orders", "Category Share of Orders"))
    show(viz.bar_v(cat, "category", "aov", "Average Order Value by Category", "Average order value"))
    show(viz.box(df, "product", "total_price", "Order Value Distribution by Product", "Order value (Total Price)"))
    if not prod.empty:
        show(viz.scatter(prod, "avg_unit_price", "quantity", "Unit Price vs Units Sold by Product", "Average unit price",
                         "Units sold", color="product", size="revenue"))
    show(viz.heatmap(df.pivot_table(index="product", columns="region", values="total_price", aggfunc="sum", fill_value=0),
                     "Revenue: Product x Region", "Region", "Product"))
    st.markdown("**Product performance table**")
    if not prod.empty:
        t = prod[["product", "category", "orders", "quantity", "revenue", "revenue_share_pct", "avg_unit_price", "aov", "return_rate_pct"]]
        st.dataframe(t.round(2), use_container_width=True, hide_index=True)


def page_shipping(df):
    st.subheader("Shipping Analysis")
    k = an.compute_kpis(df)
    kpi_row([("Return Rate", f"{k['Return Rate %']:.1f}%", None), ("Delivered", f"{k['Delivered Rate %']:.1f}%", None),
             ("In Transit", f"{k['In Transit Rate %']:.1f}%", None), ("Returned Revenue", n(k["Returned Revenue"]), None),
             ("Avg Shipping Fee", f"{k['Average Shipping Fee']:.2f}", None)])
    st.caption("Rates use orders with a known status; orders with missing status are shown as 'Unknown' in counts.")
    c1, c2 = st.columns(2)
    with c1:
        show(viz.donut(df.groupby("shipping_status").size().reset_index(name="orders"), "shipping_status", "orders",
                       "Shipping Status Distribution", viz.STATUS_COLORS))
    with c2:
        show(viz.histogram(df, "shipping_fee", "Shipping Fee Distribution", "Shipping fee", nbins=20))
    show(viz.stacked_pct(an.status_crosstab(df[df["region"] != UNKNOWN], "region"), "Shipping Status by Region", "Region"))
    c1, c2 = st.columns(2)
    with c1:
        show(viz.stacked_pct(an.status_crosstab(df, "category"), "Shipping Status by Category", "Category"))
    with c2:
        show(viz.stacked_pct(an.status_crosstab(df, "product"), "Shipping Status by Product", "Product"))
    st.markdown("#### Return rate with 95% confidence intervals")
    st.caption("Overlapping error bars mean the difference between groups may just be random variation.")
    c1, c2, c3 = st.columns(3)
    with c1:
        show(viz.return_rate_chart(an.return_rate_table(df[df["region"] != UNKNOWN], "region"), "region", "Return Rate by Region"))
    with c2:
        show(viz.return_rate_chart(an.return_rate_table(df, "category"), "category", "Return Rate by Category"))
    with c3:
        show(viz.return_rate_chart(an.return_rate_table(df, "product"), "product", "Return Rate by Product"))
    c1, c2 = st.columns(2)
    with c1:
        show(viz.box(df, "shipping_status", "shipping_fee", "Shipping Fee by Shipping Status", "Shipping fee"))
    with c2:
        show(viz.scatter(df, "total_price", "shipping_fee", "Shipping Fee vs Order Value", "Order value (Total Price)",
                         "Shipping fee", color="shipping_status"))
    st.markdown("**Shipping performance by region**")
    reg = an.group_summary(df[df["region"] != UNKNOWN], "region")
    if not reg.empty:
        st.dataframe(reg[["region", "orders", "revenue", "avg_shipping_fee", "known_orders", "returned", "return_rate_pct",
                          "ci_low", "ci_high"]].round(2), use_container_width=True, hide_index=True)


def page_insights(df, raw, log, full_df):
    st.subheader("Business Insights (generated automatically from the filtered data)")
    for item in an.generate_insights(df):
        st.markdown(f"**{item['topic']}** — {item['text']}")
    st.divider()
    st.markdown("#### Regional performance")
    reg = an.group_summary(df, "region")
    if not reg.empty:
        st.dataframe(reg[["region", "orders", "quantity", "revenue", "aov", "revenue_share_pct", "return_rate_pct"]].round(2),
                     use_container_width=True, hide_index=True)
    st.markdown("#### Statistical tests (5% significance level)")
    tests = an.run_statistical_tests(df)
    if tests.empty:
        st.write("Not enough data for statistical tests.")
    else:
        st.dataframe(tests, use_container_width=True, hide_index=True)
        st.caption("p-value < 0.05 suggests the pattern is unlikely to be pure chance. A statistically significant result can "
                   "still be a very small effect (check the statistic/correlation size).")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Descriptive statistics**")
        if not df.empty:
            st.dataframe(an.descriptive_stats(df), use_container_width=True)
    with c2:
        if not df.empty:
            show(viz.correlation_heatmap(an.correlation_matrix(df)))
    with st.expander("Data cleaning log (what was done and why)"):
        st.dataframe(pd.DataFrame(log), use_container_width=True, hide_index=True)
    with st.expander("Data quality observations & limitations"):
        st.dataframe(data_quality_checks(full_df), use_container_width=True, hide_index=True)
    with st.expander("Raw data profile (before cleaning)"):
        prof = profile_raw(raw)
        st.write(f"{prof['rows']:,} rows x {prof['columns']} columns; duplicate rows: {prof['duplicates']}")
        st.dataframe(prof["table"], use_container_width=True, hide_index=True)


# --------------------------------------------------------------------- main
def main():
    st.title("📊 E-Commerce Sales, Customer & Shipping Analytics Dashboard")
    st.caption("An interactive Python analytics application that turns historical e-commerce transactions into insights on "
               "revenue, products, customers, regions and shipping outcomes. Use the sidebar filters to explore.")
    try:
        (raw, df, log), source = get_data()
    except Exception as exc:  # show a friendly message instead of a traceback
        st.error(f"Could not load or clean the data: {exc}")
        st.stop()

    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Go to", ["1. Executive Overview", "2. Sales Analysis", "3. Customer Analysis",
                                      "4. Product & Category", "5. Shipping Analysis", "6. Business Insights"])
    st.sidebar.caption(f"Data source: {source}")
    fdf = sidebar_filters(df)
    if fdf.empty:
        st.warning("No orders match the current filters. Please widen your selection in the sidebar.")
        st.stop()
    try:
        if page.startswith("1"):
            page_overview(fdf)
        elif page.startswith("2"):
            page_sales(fdf)
        elif page.startswith("3"):
            page_customers(fdf)
        elif page.startswith("4"):
            page_products(fdf)
        elif page.startswith("5"):
            page_shipping(fdf)
        else:
            page_insights(fdf, raw, log, df)
    except Exception as exc:
        st.error(f"Something went wrong while building this page: {exc}")
        st.exception(exc)


if __name__ == "__main__":
    main()
