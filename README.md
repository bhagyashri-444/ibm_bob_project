# E-Commerce Sales, Customer & Shipping Analytics Dashboard

## Project Overview
A beginner-friendly, end-to-end **Data Analyst project in Python**. It loads an e-commerce transaction file, cleans it, performs exploratory and statistical analysis, and presents the results in an interactive **Streamlit** dashboard (6 pages, sidebar filters, Plotly charts, automatic business insights). A full Word report is included in `report/`.

## Problem Statement
An e-commerce business has accumulated sales and order data but lacks a centralized analytical system to understand sales performance, customer behavior, product/category performance, regional trends, and shipping outcomes. The objective of this project is to develop a Python-based interactive analytics application that processes historical e-commerce transaction data, performs exploratory and statistical analysis, identifies important business trends and underperforming areas, and presents actionable insights through an interactive frontend dashboard. The system should help business users monitor revenue, order quantity, product performance, customer demographics, regional sales, and shipping status to support data-driven business decisions.

## Objectives
- Load, profile and clean the data, documenting every cleaning decision
- Calculate sales, customer and shipping KPIs without double counting
- Analyse product, category, region, customer (age/gender) and time-based performance
- Analyse shipping status and return rates with confidence intervals and statistical tests
- Build an interactive dashboard with filters and automatically generated insights
- Give evidence-based recommendations and state limitations honestly

## Dataset
Dataset: `realistic_e_commerce_sales_data.csv` (provided with this project; stored in `data/`, with a copy in the project root). No public source URL is available, so none is cited.

1,000 rows x 12 columns, orders from 01 Jan 2023 to 03 Jan 2024.

## Dataset Description
| Column | Meaning |
|---|---|
| Customer ID | Customer identifier (repeats across orders) |
| Gender | Male / Female |
| Region | East, North, South, West (50 missing) |
| Age | Age in years (100 missing) |
| Product Name | 7 products (Laptop, Smartphone, Monitor, Smartwatch, Headphones, Keyboard, Mouse) |
| Category | Accessories, Electronics, Wearables |
| Unit Price | Price per unit |
| Quantity | Units ordered (1-5) |
| Total Price | Order value (Unit Price x Quantity), used as **revenue** |
| Shipping Fee | Shipping charge (kept separate from revenue) |
| Shipping Status | Delivered / In Transit / Returned (50 missing) |
| Order Date | dd-mm-yyyy text, converted to date |

There is no Order ID (each row = one order) and no currency is stated.

## Technologies Used
Python, pandas, NumPy, SciPy, Plotly, Streamlit. (The report scripts additionally use Matplotlib and python-docx.)

## Project Structure
```
ecommerce-sales-analytics/
├── app.py                         # Streamlit dashboard
├── requirements.txt               # dependencies of the app
├── README.md
├── realistic_e_commerce_sales_data.csv
├── data/realistic_e_commerce_sales_data.csv
├── src/
│   ├── data_cleaning.py           # load, profile, clean, data-quality checks
│   ├── analysis.py                # KPIs, summaries, customers, statistics, insights
│   └── visualizations.py          # Plotly charts
├── report/
│   ├── E_Commerce_Sales_Analytics_Report.docx
│   ├── make_figures.py            # creates report figures from the data
│   ├── build_report.py            # builds the .docx from the data
│   ├── requirements-report.txt
│   └── figures/
└── screenshots/                   # add your dashboard screenshots here
```

## Data Cleaning
| Issue | Decision |
|---|---|
| Region missing (50) and Shipping Status missing (50) | Labelled `Unknown` (rows kept so sales stay complete); excluded from rate denominators |
| Age missing (100) | Filled from the same Customer ID's known age (93 rows), else the median age (7 rows); `age_imputed` flag kept |
| Unit Price x Quantity != Total Price (20 rows) | Total Price trusted; Unit Price recomputed = Total Price / Quantity; `unit_price_corrected` flag kept |
| Order Date as text | Converted with format `%d-%m-%Y` |
| Duplicates | None found (check is automatic) |
| Text consistency | Whitespace trimmed, consistent casing |

The dashboard shows the full cleaning log (Business Insights page).

## Data Analysis
- **KPIs:** revenue, net revenue, orders, units, AOV, unit price, shipping fees, return/delivered/in-transit rates, customers
- **Product / category / region** summaries with revenue share and return rate
- **Customers:** repeat vs one-time, frequency, Pareto concentration, age group, gender, frequency x value segments
- **Shipping:** status mix, return rate with 95% Wilson confidence intervals by region/category/product
- **Time series:** daily (7-day average) and monthly trends; partial months are flagged
- **Statistics:** descriptive stats, correlation, chi-square, Kruskal-Wallis, Mann-Whitney, Spearman

Definitions: *Revenue* = sum of Total Price (shipping excluded, so nothing is double counted). *Return rate* = returned orders / orders with known status.

## Key KPIs
| KPI | Value |
|---|---|
| Total revenue | 1,346,600 |
| Net revenue (excl. returned orders) | 930,960 |
| Orders / units sold | 1,000 / 3,008 |
| Average order value | 1,346.60 |
| Average unit price (after correction) | 446.63 |
| Total / average shipping fee | 12,416.39 / 12.42 |
| Return / delivered / in-transit rate | 32.4% / 32.9% / 34.6% |
| Unique customer IDs | 292 |

(These are the values for the full dataset; the dashboard recalculates them for any filter selection.)

## Dashboard Features
1. **Executive Overview** - 15 KPI cards, revenue trend, revenue by category/region, status donut
2. **Sales Analysis** - monthly metric selector, best/lowest month, daily trend, product/category/quantity charts, heatmap
3. **Customer Analysis** - demographics, frequency, Pareto curve, segments, top-10 customers
4. **Product & Category** - rankings, shares, AOV, box plot, scatter, product x region heatmap
5. **Shipping Analysis** - status mix, return rates with confidence intervals, fee analysis
6. **Business Insights** - automatic insights, statistical tests, cleaning log, data-quality notes

Sidebar: Region, Gender, Category, Product, Shipping Status, Age Group, Date Range, plus a CSV download of the filtered data.

## Installation
Python 3.9+ is recommended.

```bash
python -m venv venv
```
Windows:
```bash
venv\Scripts\activate
```
macOS / Linux:
```bash
source venv/bin/activate
```
Then:
```bash
pip install -r requirements.txt
```
Run:
```bash
streamlit run app.py
```
The app opens at http://localhost:8501.

## Usage Instructions
1. Use the sidebar to choose a page and set filters; all numbers and charts update.
2. Hover over charts for tooltips; use the chart toolbar to zoom or save an image.
3. Open *Business Insights* for automatically generated findings, tests and the cleaning log.
4. Click *Download filtered data* to export the current selection.
5. (Optional) Rebuild the report: `pip install -r report/requirements-report.txt`, then `python report/make_figures.py` and `python report/build_report.py`. Edit the name/college placeholders at the top of `report/build_report.py` first.

## Key Insights
(Generated by the code from the full dataset.)

- **Overview:** The selection contains 1,000 orders from 292 customer IDs, generating revenue of 1,346,600 (average order value 1,347).
- **Products:** Laptop generates the highest revenue (696,000, 51.7% of sales). Monitor sells the most units (503). Mouse is the lowest revenue product (0.9% of sales).
- **Categories:** Electronics is the top category with 89.2% of revenue from 47.7% of orders; the lowest is Accessories (5.3% of revenue).
- **Regions:** East leads on revenue (329,950, 25.8%); South is lowest (301,040). The best region is 9.6% above the lowest one.
- **Trend:** Best complete month by revenue: 2023-11 (147,150); lowest: 2023-03 (67,660). Partial month(s) 2024-01 were excluded from this comparison.
- **Shipping:** Return rate is 32.4% (delivered 32.9%, in transit 34.6%) among orders with known status. Returned orders account for 415,640 of revenue (30.9%).
- **Returns:** Highest return rate by region: West (39.9%, 95% CI 33.9-46.3%); lowest: South (27.5%).
- **Returns:** Highest return rate by category: Accessories (33.1%, 95% CI 28.6-37.9%); lowest: Electronics (31.8%).
- **Returns:** Highest return rate by product: Headphones (34.5%, 95% CI 26.5-43.5%); lowest: Monitor (30.2%).
- **Statistics:** Significant at the 5% level: Is shipping status related to Region?; Is customer age related to order value? (correlation 0.07: statistically detectable but very weak, so of little practical importance).
- **Customers:** 86.0% of customer IDs purchased more than once. The top 20% of customers generate 48.7% of revenue. (Customer IDs show inconsistent gender/region, so treat customer-level results as indicative.)
- **Demographics:** The age group with the highest revenue is 46-55 (23.0%). By gender, Male customers contribute 53.1% of revenue.
- **Attention areas:** 32.4% of orders with a known status were returned, which removes 415,640 from revenue (net revenue 930,960). 5.0% of orders have no shipping status recorded, a data-capture gap.

## Business Recommendations
- Investigate returns in the **West** region first (39.9% vs 27.5% in South; chi-square p = 0.0004).
- Treat the overall return rate (32.4%) as a company-wide issue and start capturing return reasons.
- Protect the Electronics line (especially Laptop), which provides 89.2% of revenue; test bundles to lift Accessories/Wearables order value.
- Review the weakest months (2023-03) after confirming with a second year of data.
- Improve data capture: mandatory Region/Shipping Status, an Order ID, consistent Customer IDs, and a Unit Price x Quantity = Total Price validation.

## Limitations
- No Order ID: each row is treated as one order
- Customer IDs are inconsistent (same ID with different gender/region), so customer results are indicative
- Missing Region/Status/Age (Unknown labels and imputed ages reduce precision)
- About one year of data (the last month is a single day), so seasonality cannot be confirmed
- No cost, profit or return-reason data; currency not stated
- The dashboard was written and its logic tested against the data, but visual appearance depends on your Streamlit/Plotly versions; screenshots were not generated

## Future Improvements
Forecasting, RFM segmentation with reliable IDs, return-risk prediction, database connection, cloud deployment, profit and basket analysis.

## Author
[Your Name] - [Course / College] - [Email / GitHub / LinkedIn]
