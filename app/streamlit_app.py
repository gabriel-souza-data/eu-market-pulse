import os
import streamlit as st
import pandas as pd
import plotly.express as px
from dotenv import load_dotenv
from sqlalchemy import create_engine

# ── Page Config ───────────────────────────────────────────────────
st.set_page_config(
    page_title="EU Market Pulse",
    page_icon="🇪🇺",
    layout="wide"
)

# ── Database Connection ──────────────────────────────────────────
load_dotenv()

@st.cache_resource
def get_engine():
    return create_engine(os.getenv('DATABASE_URL'))

@st.cache_data(ttl=3600)
def load_data():
    engine = get_engine()
    kpis = pd.read_sql('SELECT * FROM country_kpis;', engine)
    countries = pd.read_sql('SELECT * FROM countries;', engine)
    return kpis.merge(countries, on='country_code')

@st.cache_data(ttl=3600)
def load_trends():
    engine = get_engine()
    return pd.read_sql('SELECT * FROM market_indicators;', engine)

df = load_data()

# ISO-2 to ISO-3 mapping, required for Plotly's built-in choropleth map
ISO2_TO_ISO3 = {
    'GB': 'GBR', 'CH': 'CHE', 'IE': 'IRL', 'DE': 'DEU', 'FR': 'FRA',
    'NL': 'NLD', 'AT': 'AUT', 'BE': 'BEL', 'PT': 'PRT', 'ES': 'ESP',
    'IT': 'ITA', 'GR': 'GRC', 'PL': 'POL', 'RO': 'ROU', 'HU': 'HUN',
    'CZ': 'CZE', 'SE': 'SWE', 'DK': 'DNK', 'FI': 'FIN'
}
df['country_code_iso3'] = df['country_code'].map(ISO2_TO_ISO3)

# Fixed color palette per country, ensuring consistency across all charts
COUNTRY_COLORS = {
    'United Kingdom': '#1f77b4', 'Switzerland': '#ff7f0e', 'Ireland': '#2ca02c',
    'Germany': '#d62728', 'France': '#9467bd', 'Netherlands': '#8c564b',
    'Austria': '#e377c2', 'Belgium': '#7f7f7f', 'Portugal': '#bcbd22',
    'Spain': '#17becf', 'Italy': '#393b79', 'Greece': '#ad494a',
    'Poland': '#31a354', 'Romania': '#e6550d', 'Hungary': '#756bb1',
    'Czechia': '#636363', 'Sweden': '#a55194', 'Denmark': '#8ca252',
    'Finland': '#3182bd'
}

# ── Header ────────────────────────────────────────────────────────
st.title("🇪🇺 EU Market Pulse")
st.subheader("Where should a remote-first company expand or hire in Europe?")
st.caption("Data source: Eurostat (HICP inflation, price levels, house price index) · 19 countries · 2014–2025")

st.divider()

# ── Region Filter ─────────────────────────────────────────────────
regions = sorted(df['region_group'].unique())
selected_regions = st.multiselect("Filter by region", options=regions, default=regions)

df_filtered = df[df['region_group'].isin(selected_regions)]

if df_filtered.empty:
    st.warning("Select at least one region to see results.")
    st.stop()

st.divider()

# ── Top-Level KPI Cards ──────────────────────────────────────────
best = df_filtered.loc[df_filtered['overall_expansion_score'].idxmax()]
worst = df_filtered.loc[df_filtered['overall_expansion_score'].idxmin()]
avg_score = df_filtered['overall_expansion_score'].mean()

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("🏆 **Best Expansion Candidate**")
    st.markdown(f"## {best['country_name']}")
    st.markdown(f"<span style='color:#2E7D32; font-size:1.1rem; font-weight:600;'>{best['overall_expansion_score']:.1f} score</span>", unsafe_allow_html=True)

with col2:
    st.markdown(f"📊 **Average Score ({len(df_filtered)} countries)**")
    st.markdown(f"## {avg_score:.1f}")

with col3:
    st.markdown("⚠️ **Most Challenging Market**")
    st.markdown(f"## {worst['country_name']}")
    st.markdown(f"<span style='color:#C62828; font-size:1.1rem; font-weight:600;'>{worst['overall_expansion_score']:.1f} score</span>", unsafe_allow_html=True)

st.divider()

# ── Data Table ────────────────────────────────────────────────────
st.subheader("Full Country Data")

df_sorted = df_filtered.sort_values('overall_expansion_score', ascending=False)

st.dataframe(
    df_sorted[['country_name', 'region_group', 'cost_of_living_score', 
               'inflation_stability_score', 'housing_pressure_score', 'overall_expansion_score']],
    use_container_width=True,
    hide_index=True
)

st.divider()

# ── Ranking Chart ─────────────────────────────────────────────────
st.subheader("Overall Expansion Score by Country")

fig = px.bar(
    df_sorted,
    x='overall_expansion_score',
    y='country_name',
    orientation='h',
    labels={'overall_expansion_score': 'Expansion Score (0-100, higher = more favorable)', 'country_name': ''},
    height=600,
    color_discrete_sequence=['#4C72B0']
)
fig.update_layout(yaxis={'categoryorder': 'total ascending'}, showlegend=False)

st.plotly_chart(fig, use_container_width=True)

st.divider()

# ── Map ───────────────────────────────────────────────────────────
st.subheader("Expansion Score Map")

fig_map = px.choropleth(
    df_filtered,
    locations='country_code_iso3',
    color='overall_expansion_score',
    hover_name='country_name',
    color_continuous_scale='Blues',
    range_color=(0, 100),
    scope='europe',
    labels={'overall_expansion_score': 'Expansion Score'}
)
fig_map.update_layout(height=600, margin={"r":0,"t":0,"l":0,"b":0})

st.plotly_chart(fig_map, use_container_width=True)

st.divider()

# ── Country Comparison ────────────────────────────────────────────
st.subheader("Compare Countries")

compare_countries = st.multiselect(
    "Select 2-4 countries to compare",
    options=sorted(df['country_name'].unique()),
    default=[best['country_name'], worst['country_name']],
    max_selections=4
)

if len(compare_countries) < 2:
    st.info("Select at least 2 countries to compare.")
else:
    df_compare = df[df['country_name'].isin(compare_countries)]

    df_melted = df_compare.melt(
        id_vars='country_name',
        value_vars=['cost_of_living_score', 'inflation_stability_score', 'housing_pressure_score'],
        var_name='dimension',
        value_name='score'
    )
    # Visual-only floor so zero-value bars remain visible; the label still shows the true score
    df_melted['bar_height'] = df_melted['score'].apply(lambda x: max(x, 3))

    fig_compare = px.bar(
        df_melted,
        x='dimension',
        y='bar_height',
        color='country_name',
        color_discrete_map=COUNTRY_COLORS,
        barmode='group',
        text=df_melted['score'].round(1),
        labels={'dimension': '', 'bar_height': 'Score (0-100, higher = more favorable)', 'country_name': 'Country'},
        height=450
    )
    fig_compare.update_traces(textposition='outside')
    fig_compare.update_xaxes(ticktext=['Cost of Living', 'Inflation Stability', 'Housing Pressure'], 
                              tickvals=['cost_of_living_score', 'inflation_stability_score', 'housing_pressure_score'])
    fig_compare.update_layout(yaxis_range=[0, 110])

    st.plotly_chart(fig_compare, use_container_width=True)

    trends = load_trends()
    trends_compare = trends.merge(df_compare[['country_code', 'country_name']], on='country_code')

    fig_trend = px.line(
        trends_compare,
        x='year',
        y='inflation_rate',
        color='country_name',
        color_discrete_map=COUNTRY_COLORS,
        labels={'year': '', 'inflation_rate': 'Inflation Rate (%)', 'country_name': 'Country'},
        height=400
    )
    st.plotly_chart(fig_trend, use_container_width=True)

st.divider()

# ── Methodology ───────────────────────────────────────────────────
with st.expander("📋 Methodology & Data Limitations"):
    st.markdown("""
    **Data Sources (Eurostat, public API):**
    - `tec00118` — HICP Inflation Rate (annual average rate of change)
    - `tec00120` — Price Level Indices (household consumption, EU-27 average = 100)
    - `tipsho10` — House Price Index (deflated, 2015 = 100)

    **Scoring Methodology:**
    Each of the three dimensions (cost of living, inflation stability, housing pressure) 
    is normalized to a 0–100 scale, where 100 always represents the most favorable 
    outcome for business expansion — regardless of the original metric's direction. 
    The Overall Expansion Score is a simple average of the three, giving equal weight 
    to each dimension.

    **Known Limitations:**
    - **United Kingdom**: excluded from the Cost of Living score and Overall Expansion 
      Score, as Eurostat's price level data for the UK stops in 2019 (pre-pandemic), 
      making it non-comparable with 2025 figures for other countries. UK remains 
      included in Inflation Stability and Housing Pressure, where data is complete.
    - **Switzerland & United Kingdom**: excluded from the House Price Index, as this 
      Eurostat series does not cover these two countries.
    - **Forecasting**: a linear trend forecast for future inflation was explored but 
      excluded from this analysis after testing showed the short post-2022 recovery 
      period does not provide a statistically reliable signal. See the project's 
      GitHub repository (notebook 05) for the full analysis.

    **Automation:** Data is refreshed weekly via an automated pipeline (GitHub Actions) 
    that fetches the latest values directly from the Eurostat API.
    """)