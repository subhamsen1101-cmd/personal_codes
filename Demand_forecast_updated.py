# app.py
import streamlit as st
import pandas as pd
import numpy as np
from prophet import Prophet
import plotly.graph_objects as go
from datetime import datetime
import io
import json
import traceback

# Optional GenAI import
try:
    import google.generativeai as genai
    GENAI_MODULE_AVAILABLE = True
except Exception:
    GENAI_MODULE_AVAILABLE = False

# For Excel column letters
from openpyxl.utils import get_column_letter

# -----------------------------
# CONFIG: Hardcoded GenAI key
# -----------------------------
# Replace with your GenAI key (Gemini / Vertex AI). Required for option B behavior.
GENAI_API_KEY = "***********"  # <<-- replace with real key

if GENAI_API_KEY and GENAI_MODULE_AVAILABLE:
    try:
        genai.configure(api_key=GENAI_API_KEY)
    except Exception:
        # keep moving; we'll handle failures later
        pass

# -----------------------------
# PAGE CONFIG
# -----------------------------
st.set_page_config(page_title="Product → Merchant → Forecast (GenAI-driven external factors)", layout="wide")
st.title("📦 Product → Merchant → Demand Forecasting (GenAI external factors)")

# -----------------------------
# Synthetic data generation (multiple merchants per product)
# -----------------------------
@st.cache_data
def generate_synthetic_sales():
    dates = pd.date_range("2024-01-01", "2025-12-31", freq="D")
    products = [
        "Basmati Rice", "Sunflower Oil", "Bread", "Milk",
        "Toothpaste", "Shampoo", "Soap", "Sugar"
    ]

    # One company per product (brand)
    companies = {
        "Basmati Rice": "Tata",
        "Sunflower Oil": "Adani Wilmar",
        "Bread": "Britannia",
        "Milk": "Amul",
        "Toothpaste": "HUL",
        "Shampoo": "HUL",
        "Soap": "ITC",
        "Sugar": "Tata"
    }

    categories = {
        "Basmati Rice": "Grocery",
        "Sunflower Oil": "Grocery",
        "Bread": "Grocery",
        "Milk": "Dairy",
        "Toothpaste": "Personal Care",
        "Shampoo": "Personal Care",
        "Soap": "Personal Care",
        "Sugar": "Grocery"
    }

    merchants_pool = [
        "Spencers - Downtown", "Spencers - Mall", "Spencers - Express",
        "Spencers Online", "Local Kirana A", "Local Kirana B", "Wholesale Partner"
    ]

    rng = np.random.default_rng(123)
    rows = []
    for date in dates:
        for prod in products:
            comp = companies[prod]
            cat = categories[prod]
            sellers = rng.choice(merchants_pool, size=3, replace=False)
            for m in sellers:
                bias_map = {
                    "Spencers - Downtown": 1.0,
                    "Spencers - Mall": 0.9,
                    "Spencers - Express": 0.6,
                    "Spencers Online": 0.7,
                    "Local Kirana A": 0.5,
                    "Local Kirana B": 0.4,
                    "Wholesale Partner": 1.2
                }
                merchant_bias = bias_map.get(m, 0.8)
                base = rng.normal(80, 30) * merchant_bias
                rows.append({
                    "date": date,
                    "product": prod,
                    "company": comp,
                    "merchant": m,
                    "category": cat,
                    "sales": max(1, int(base))
                })

    df = pd.DataFrame(rows)
    df["month"] = df["date"].dt.month
    seasonality = {1:0.9,2:0.92,3:0.95,4:1.0,5:1.05,6:1.10,7:1.15,8:1.20,9:1.10,10:1.05,11:1.20,12:1.30}
    df["sales"] = (df["sales"] * df["month"].map(seasonality)).astype(int)
    df = df.drop(columns=["month"])
    return df

sales_df = generate_synthetic_sales()

# -----------------------------
# Landing page: Product tiles only (no numbers)
# -----------------------------
st.markdown("## Products — click a product to see merchants (no sales shown here)")
product_list = sorted(sales_df["product"].unique())

cols = st.columns(4)
for i, p in enumerate(product_list):
    with cols[i % 4]:
        if st.button(f"📦 {p}", key=f"product_tile_{p}"):
            st.session_state["selected_product"] = p
            # clear merchant selection if any
            if "selected_merchant" in st.session_state:
                st.session_state.pop("selected_merchant")
            st.rerun()

st.markdown("---")
st.write("Tip: Select a product, then choose a merchant to view company, forecast, inventory suggestions, and GenAI-driven external factor impacts.")

# If no product selected, stop here
if "selected_product" not in st.session_state:
    st.stop()

# -----------------------------
# Product page: show merchants for that product
# -----------------------------
selected_product = st.session_state["selected_product"]
st.header(f"Product: {selected_product}")
st.write("Merchants selling this product:")

merchants_for_product = sorted(sales_df[sales_df["product"]==selected_product]["merchant"].unique().tolist())
cols = st.columns(2)
for i, m in enumerate(merchants_for_product):
    with cols[i % 2]:
        if st.button(m, key=f"merchant_btn_{m}"):
            st.session_state["selected_merchant"] = m
            st.rerun()

st.markdown("---")
st.write("Select a merchant to view forecasts and actions.")

# If no merchant selected yet, stop
if "selected_merchant" not in st.session_state:
    st.stop()

# -----------------------------
# Merchant detail page
# -----------------------------
selected_merchant = st.session_state["selected_merchant"]
company = sales_df[(sales_df["product"]==selected_product) & (sales_df["merchant"]==selected_merchant)]["company"].iloc[0]
category = sales_df[(sales_df["product"]==selected_product) & (sales_df["merchant"]==selected_merchant)]["category"].iloc[0]

st.header(f"{selected_product}  — Merchant: {selected_merchant}")
st.subheader(f"Company: {company}   |   Category: {category}")

# show small recent sample (no big table)
st.markdown("Recent sales (sample)")
sample_recent = sales_df[(sales_df["product"]==selected_product) & (sales_df["merchant"]==selected_merchant)].sort_values("date").tail(10)
st.dataframe(sample_recent[["date","sales"]].rename(columns={"date":"Date","sales":"Sales"}), use_container_width=True)

# -----------------------------
# Sidebar controls
# -----------------------------
st.sidebar.header("Controls")
view = st.sidebar.selectbox("Aggregation", ["Daily","Weekly","Monthly"], index=0)
if view == "Daily":
    horizon = st.sidebar.number_input("Forecast horizon (days)", min_value=7, max_value=365, value=90, step=7)
elif view == "Weekly":
    horizon = st.sidebar.number_input("Forecast horizon (weeks)", min_value=1, max_value=52, value=13, step=1)
else:
    horizon = st.sidebar.number_input("Forecast horizon (months)", min_value=1, max_value=24, value=6, step=1)

use_genai = st.sidebar.checkbox("Enable GenAI features (external-factor generation & insights)", value=bool(GENAI_API_KEY and GENAI_MODULE_AVAILABLE))

# -----------------------------
# GenAI-powered automatic external-factor generation
# -----------------------------
def genai_generate_events(product_name, merchant_name, company_name, category_name):
    """
    Ask GenAI to propose 3-5 recent events that can affect demand,
    each as: {"title":..., "scope": product|merchant|company|category|all, "impact": float, "notes":...}
    Returns list of events or None on failure.
    """
    if not (use_genai and GENAI_MODULE_AVAILABLE and GENAI_API_KEY):
        return None
    try:
        prompt = f"""
You are a retail events generator for demand forecasting. For the product '{product_name}' (merchant '{merchant_name}', company '{company_name}', category '{category_name}'),
generate 3 to 5 plausible recent events/news items that would affect demand in the next 1-8 weeks.
For each event return a JSON object with fields:
- title: short one-line event description
- scope: one of ["product","merchant","company","category","all"] indicating which entities are affected
- impact: a decimal between -0.5 and +0.5 representing relative demand change (e.g. -0.20 => -20% drop)
- notes: one-line explanation

Return a JSON array of these event objects, and nothing else.
"""
        model = genai.GenerativeModel("gemini-2.0-flash")
        resp = model.generate_content(prompt, temperature=0.2, max_output_tokens=500)
        text = resp.text.strip()
        # try to parse JSON
        events = json.loads(text)
        # validate & clamp impact
        clean_events = []
        for e in events:
            imp = float(e.get("impact",0.0))
            if imp < -0.5: imp = -0.5
            if imp > 0.5: imp = 0.5
            e["impact"] = imp
            if e.get("scope") not in ["product","merchant","company","category","all"]:
                e["scope"] = "merchant"
            clean_events.append(e)
        return clean_events
    except Exception:
        # On any failure, return None so fallback runs
        return None

def synthetic_events_fallback(product_name, merchant_name, company_name, category_name):
    """
    Generate a few synthetic events based on simple heuristics:
    - festival spikes, season, random social trend, disease/outbreak randomly
    """
    rng = np.random.default_rng(abs(hash(product_name + merchant_name)) % (2**32))
    events = []
    # festival tendency based on month (we will not attach month now, just generic)
    festival_imp = 0.12 if category_name in ["Grocery","Dairy"] else 0.06
    events.append({
        "title": "Upcoming festival season — higher grocery demand",
        "scope": "category",
        "impact": festival_imp,
        "notes": "Seasonal shopping increases for groceries / gifts."
    })
    # random social media event (positive/negative)
    sm = rng.choice(["positive campaign", "negative viral video", "noisy mention"])
    if sm == "positive campaign":
        events.append({"title":"Positive social campaign", "scope":"merchant", "impact":0.08, "notes":"Local campaign increases store footfall."})
    elif sm == "negative viral video":
        events.append({"title":"Negative social media mention", "scope":"merchant", "impact":-0.15, "notes":"Negative PR for specific merchant."})
    else:
        events.append({"title":"Minor online chatter", "scope":"product", "impact":0.02, "notes":"Small attention, limited effect."})
    # disease/outbreak effect occasionally
    if rng.random() < 0.25:
        # bias impact by category
        if category_name.lower() in ["dairy","grocery"]:
            imp = 0.12
        else:
            imp = -0.06
        events.append({"title":"Regional disease/outbreak signal", "scope":"category", "impact":imp, "notes":"Health event affecting category demand."})
    # economic price shock possible for some categories
    if rng.random() < 0.2:
        events.append({"title":"Price pressure on raw materials", "scope":"product", "impact":-0.08, "notes":"Price increase reducing demand slightly."})
    return events

# Generate events (GenAI preferred)
events = genai_generate_events(selected_product, selected_merchant, company, category) if use_genai else None
if events is None:
    events = synthetic_events_fallback(selected_product, selected_merchant, company, category)

# Show events to user
st.subheader("Auto-detected external events (GenAI-simulated)")
for e in events:
    st.markdown(f"- **{e['title']}** — scope: *{e['scope']}*, impact: **{e['impact']:+.2f}** — {e.get('notes','')}")

# -----------------------------
# Aggregate impacts into a single net impact for this merchant page
# Scope handling: for simplicity we convert all events into merchant-level effect if their scope affects this merchant.
# Rules:
# - If event.scope == 'all' -> apply to all merchants (so applies here)
# - if 'merchant' and target unspecified -> assume affects selected merchant
# - if 'company' -> affects this merchant if company matches (it does on this page)
# - if 'category' -> affects merchant if category matches (it does)
# - if 'product' -> affects this product (applies here)
# We'll compute a weighted sum (simple average) of impacts that apply.
# -----------------------------
def compute_net_impact(events, product_name, merchant_name, company_name, category_name):
    impacts = []
    for e in events:
        scope = e.get("scope","merchant")
        imp = float(e.get("impact",0.0))
        applies = False
        if scope == "all":
            applies = True
        elif scope == "merchant":
            applies = True  # assume merchant-targeted events affect the merchant page
        elif scope == "company" and company_name:
            applies = True  # company matches
        elif scope == "category" and category_name:
            applies = True
        elif scope == "product" and product_name:
            applies = True
        if applies:
            impacts.append(imp)
    if not impacts:
        return 0.0
    # We average impacts (simple approach) but reduce effect if many conflicting events
    net = float(np.mean(impacts))
    # limit to [-0.5, 0.5]
    net = max(-0.5, min(0.5, net))
    return net

net_impact = compute_net_impact(events, selected_product, selected_merchant, company, category)
st.metric("Aggregated external impact applied to this merchant", f"{net_impact:+.2f}")

# -----------------------------
# Prepare time series aggregated according to view for this merchant-product
# -----------------------------
def prepare_series(df, product_name, merchant_name, view_mode):
    tmp = df[(df["product"]==product_name) & (df["merchant"]==merchant_name)].copy()
    tmp["date"] = pd.to_datetime(tmp["date"])
    if view_mode == "Daily":
        agg = tmp.groupby("date", as_index=False)["sales"].sum().rename(columns={"date":"ds","sales":"y"})
    elif view_mode == "Weekly":
        tmp["week_start"] = tmp["date"].dt.to_period("W").apply(lambda r: r.start_time)
        agg = tmp.groupby("week_start", as_index=False)["sales"].sum().rename(columns={"week_start":"ds","sales":"y"})
    else:
        tmp["month_start"] = tmp["date"].dt.to_period("M").apply(lambda r: r.start_time)
        agg = tmp.groupby("month_start", as_index=False)["sales"].sum().rename(columns={"month_start":"ds","sales":"y"})
    return agg

series = prepare_series(sales_df, selected_product, selected_merchant, view)
st.subheader("Observed series (sample)")
st.dataframe(series.tail(8).rename(columns={"ds":"Date","y":"Observed_Sales"}), use_container_width=True)

# -----------------------------
# Prophet forecasting
# -----------------------------
st.subheader("Forecast")
m = Prophet(yearly_seasonality=True, weekly_seasonality=(view=="Daily"))
with st.spinner("Training Prophet..."):
    m.fit(series.rename(columns={"ds":"ds","y":"y"}))

# construct future
freq = 'D' if view=="Daily" else ('W' if view=="Weekly" else 'M')
future = m.make_future_dataframe(periods=int(horizon), freq=freq)
forecast = m.predict(future)

# Apply net_impact multiplicatively to forecast and bounds
if net_impact != 0.0:
    forecast["yhat"] = forecast["yhat"] * (1 + net_impact)
    forecast["yhat_lower"] = forecast["yhat_lower"] * (1 + net_impact)
    forecast["yhat_upper"] = forecast["yhat_upper"] * (1 + net_impact)

# Friendly columns
friendly = forecast.rename(columns={
    "ds":"Date",
    "yhat":"Expected_Demand",
    "yhat_lower":"Minimum_Expected_Demand",
    "yhat_upper":"Maximum_Expected_Demand"
})[["Date","Expected_Demand","Minimum_Expected_Demand","Maximum_Expected_Demand"]].copy()
friendly[["Expected_Demand","Minimum_Expected_Demand","Maximum_Expected_Demand"]] = friendly[["Expected_Demand","Minimum_Expected_Demand","Maximum_Expected_Demand"]].round(2)

# Show tail of forecast
st.dataframe(friendly.tail(min(max(10,int(horizon)), len(friendly))).reset_index(drop=True), use_container_width=True)

# -----------------------------
# Quick alert (color-coded)
# -----------------------------
st.subheader("Quick alert")
recent_median = series.tail(30)["y"].median() if len(series)>0 else 0
last_obs = series["ds"].max()
next_rows = friendly[friendly["Date"] > last_obs]
if len(next_rows) > 0:
    next_expected = next_rows.iloc[0]["Expected_Demand"]
else:
    next_expected = friendly.iloc[-1]["Expected_Demand"]

if recent_median <= 0:
    alert = ("🟢","Stable")
else:
    if next_expected >= recent_median * 1.2:
        alert = ("🔴","High Surge Expected")
    elif next_expected <= recent_median * 0.8:
        alert = ("🔴","Significant Drop Expected")
    elif next_expected >= recent_median * 1.05:
        alert = ("🟡","Moderate Increase")
    else:
        alert = ("🟢","Stable / Low Change")

st.markdown(f"**{alert[0]} {alert[1]}** — Next expected: **{next_expected:.1f}** (recent median: {recent_median:.1f})")

# -----------------------------
# Inventory optimization suggestions
# -----------------------------
st.subheader("Inventory optimization (next window)")
if view=="Daily":
    window_len = min(30,int(horizon))
elif view=="Weekly":
    window_len = min(13,int(horizon))
else:
    window_len = min(6,int(horizon))
window = friendly.tail(window_len)
avg_demand = float(window["Expected_Demand"].mean())
peak_demand = float(window["Maximum_Expected_Demand"].max())
safety_stock = int(round(peak_demand * 1.3))
if view=="Daily":
    reorder_point = int(round(avg_demand * 7))
elif view=="Weekly":
    reorder_point = int(round(avg_demand * 1))
else:
    reorder_point = int(round(avg_demand * 1))

c1,c2,c3,c4 = st.columns(4)
c1.metric("Avg Expected Demand", f"{avg_demand:.1f}")
c2.metric("Peak Expected Demand", f"{peak_demand:.1f}")
c3.metric("Recommended Safety Stock", f"{safety_stock:,}")
c4.metric("Reorder Point (lead time)", f"{reorder_point:,}")

# -----------------------------
# Clean forecast chart
# -----------------------------
st.subheader("Forecast chart (observed + expected + bounds)")
obs_plot = series.rename(columns={"ds":"Date","y":"Observed_Sales"})
fig = go.Figure()
fig.add_trace(go.Scatter(x=obs_plot["Date"], y=obs_plot["Observed_Sales"], mode="lines", name="Observed"))
fig.add_trace(go.Scatter(x=friendly["Date"], y=friendly["Expected_Demand"], mode="lines", name="Expected"))
fig.add_trace(go.Scatter(x=friendly["Date"], y=friendly["Maximum_Expected_Demand"], mode="lines", name="Max (upper)", line=dict(dash="dash"), opacity=0.6))
fig.add_trace(go.Scatter(x=friendly["Date"], y=friendly["Minimum_Expected_Demand"], mode="lines", name="Min (lower)", line=dict(dash="dash"), opacity=0.6))
fig.update_layout(height=520, xaxis_title="Date", yaxis_title="Units")
st.plotly_chart(fig, use_container_width=True)

# -----------------------------
# GenAI Insights (3 bullets + 3 actions) with fallback
# -----------------------------
st.subheader("AI Insights (3 short bullets & 3 short actions)")

def genai_insights_or_fallback(avg_d, peak, safety, reorder, product_name, merchant_name, company_name, use_genai_flag):
    if use_genai_flag and GENAI_MODULE_AVAILABLE and GENAI_API_KEY:
        try:
            prompt = f"""
You are a concise retail analyst. For product '{product_name}' sold by merchant '{merchant_name}' (company: {company_name}), given:
avg={avg_d:.1f}, peak={peak:.1f}, safety={safety}, reorder={reorder}
Return:
- Three one-line insights (numbered 1.,2.,3.)
- Three one-line actions (A.,B.,C.)

Keep everything short and for a store manager. Return plain text.
"""
            model = genai.GenerativeModel("gemini-pro")
            resp = model.generate_content(prompt, temperature=0.2, max_output_tokens=250)
            return resp.text
        except Exception:
            # fall through to fallback
            traceback.print_exc()
    # fallback
    insights = [
        f"1. Expected average demand ~ {avg_d:.1f} units in the next window.",
        f"2. Peak demand could reach {peak:.1f} units — prepare stock buffers.",
        f"3. Net external impact applied: {net_impact:+.2f} (from recent events)."
    ]
    actions = [
        "A. Increase safety stock to cover peaks and avoid stockouts.",
        "B. Review supplier lead times and pre-order if lead times >1 week.",
        "C. Run targeted promos on slow days; prioritize fast-moving SKUs."
    ]
    return "\n".join(insights + [""] + actions)

if st.button("Generate short AI insights"):
    insights_text = genai_insights_or_fallback(avg_demand, peak_demand, safety_stock, reorder_point, selected_product, selected_merchant, company, use_genai)
    st.text(insights_text)

# -----------------------------
# Downloads: CSV & Excel (friendly headers)
# -----------------------------
st.subheader("Download forecast")

csv_bytes = friendly.to_csv(index=False).encode("utf-8")
st.download_button("⬇ Download CSV", data=csv_bytes, file_name=f"{selected_product}_{selected_merchant}_forecast.csv", mime="text/csv")

def to_excel_bytes(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Forecast")
        ws = writer.sheets["Forecast"]
        for i, col in enumerate(df.columns, 1):
            max_len = max(df[col].astype(str).map(len).max(), len(col)) + 2
            col_letter = get_column_letter(i)
            ws.column_dimensions[col_letter].width = max_len
    return output.getvalue()

excel_data = to_excel_bytes(friendly)
st.download_button("⬇ Download Excel (.xlsx)", data=excel_data, file_name=f"{selected_product}_{selected_merchant}_forecast.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# -----------------------------
# Navigation back buttons
# -----------------------------
nav_cols = st.columns(3)
if nav_cols[0].button("⬅ Back to merchants"):
    st.session_state.pop("selected_merchant", None)
    st.rerun()
if nav_cols[1].button("⬅ Back to products"):
    st.session_state.pop("selected_product", None)
    # clear merchant if present
    if "selected_merchant" in st.session_state:
        st.session_state.pop("selected_merchant")
    st.rerun()
