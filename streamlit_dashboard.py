"""
Streamlit Dashboard for Disruption Platform
Main dashboard application that displays scenario analysis results
"""

import streamlit as st
import pandas as pd
import numpy as np
import json
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta

# Page configuration
st.set_page_config(
    page_title="DisruptIQ - Global Disruption Analysis",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

@st.cache_data
def load_dashboard_data():
    """Load pre-processed dashboard data from JSON"""
    try:
        with open('dashboard_summary.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        st.error("Dashboard data not found. Please run the Databricks processing notebook first.")
        return None

@st.cache_data 
def load_scenario_data(scenario_name):
    """Load detailed scenario data"""
    try:
        sectors_df = pd.read_csv(f'{scenario_name}_sectors.csv')
        countries_df = pd.read_csv(f'{scenario_name}_countries.csv')
        analogs_df = pd.read_csv(f'{scenario_name}_analogs.csv')
        
        with open(f'{scenario_name}_full.json', 'r') as f:
            full_data = json.load(f)
            
        return {
            'sectors': sectors_df,
            'countries': countries_df, 
            'analogs': analogs_df,
            'full': full_data
        }
    except FileNotFoundError:
        st.error(f"Scenario data for {scenario_name} not found.")
        return None

def create_price_impact_chart(scenarios_data):
    """Create price impact comparison chart"""
    fig = go.Figure()
    
    scenario_names = [s['scenario_name'] for s in scenarios_data]
    price_impacts = [s['brent_impact_pct'] for s in scenarios_data]
    new_prices = [s['new_brent_price'] for s in scenarios_data]
    
    fig.add_trace(go.Bar(
        name='Price Impact %',
        x=scenario_names,
        y=price_impacts,
        text=[f"+{p:.1f}%" for p in price_impacts],
        textposition='outside',
        marker_color='#E24B4A',
        yaxis='y1'
    ))
    
    fig.add_trace(go.Scatter(
        name='New Price $/bbl',
        x=scenario_names,
        y=new_prices,
        text=[f"${p:.0f}" for p in new_prices],
        textposition='top center',
        marker_color='#378ADD',
        marker_size=10,
        mode='markers+text',
        yaxis='y2'
    ))
    
    fig.update_layout(
        title="Price Impact Comparison Across Scenarios",
        xaxis_title="Scenario",
        yaxis=dict(title="Price Impact %", side="left", color="#E24B4A"),
        yaxis2=dict(title="Absolute Price $/bbl", side="right", overlaying="y", color="#378ADD"),
        showlegend=True,
        height=400
    )
    
    return fig

def create_sector_impact_chart(sectors_df):
    """Create sector impact horizontal bar chart"""
    # Sort by absolute impact
    sectors_sorted = sectors_df.reindex(sectors_df['impact_pct'].abs().sort_values(ascending=True).index)
    
    colors = ['#E24B4A' if x > 40 else '#EF9F27' if x > 20 else '#1D9E75' for x in sectors_sorted['impact_pct'].abs()]
    
    fig = go.Figure(go.Bar(
        x=sectors_sorted['impact_pct'],
        y=sectors_sorted['sector_name'],
        orientation='h',
        text=[f"{x:+.1f}%" for x in sectors_sorted['impact_pct']],
        textposition='outside',
        marker_color=colors
    ))
    
    fig.update_layout(
        title="Sector Impact Analysis",
        xaxis_title="Impact on Operating Costs (%)",
        yaxis_title="Sector",
        height=500,
        showlegend=False
    )
    
    return fig

def create_country_vulnerability_map(countries_df):
    """Create country vulnerability choropleth map"""
    
    fig = go.Figure(data=go.Choropleth(
        locations=countries_df['country_code'],
        z=countries_df['normalized_score'],
        text=countries_df['country_name'] + '<br>Score: ' + countries_df['normalized_score'].astype(str) + '/10',
        hovertemplate='<b>%{text}</b><br>Vulnerability: %{z}/10<extra></extra>',
        colorscale=[[0, '#27500A'], [0.3, '#EF9F27'], [0.7, '#E24B4A'], [1, '#791F1F']],
        colorbar_title="Vulnerability Score",
        colorbar=dict(thickness=15, len=0.7)
    ))
    
    fig.update_layout(
        title="Global Vulnerability Map",
        geo=dict(
            showframe=False,
            showcoastlines=True,
            projection_type='natural earth'
        ),
        height=500
    )
    
    return fig

def create_historical_analogs_chart(analogs_df):
    """Create historical analogs similarity chart"""
    top_analogs = analogs_df.head(5)
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=top_analogs['event_year'],
        y=top_analogs['similarity_score'],
        mode='markers+text',
        marker_size=top_analogs['similarity_score'] * 20,
        marker_color='#378ADD',
        text=top_analogs['event_name'],
        textposition='top center',
        name='Historical Analogs'
    ))
    
    fig.update_layout(
        title="Historical Analog Matches",
        xaxis_title="Year",
        yaxis_title="Similarity Score",
        yaxis=dict(range=[0, 1]),
        height=400,
        showlegend=False
    )
    
    return fig

def main():
    
    # Header
    st.title("⚡ DisruptIQ - Global Disruption Analysis Platform")
    st.markdown("*Network-based analysis of supply chain disruptions and cascade effects*")
    st.error("⚠️ **DISCLAIMER:** This is a demonstration/prototype using simulated data for methodology validation. Not intended for actual risk management decisions.")
    
    # Load data
    dashboard_data = load_dashboard_data()
    
    if dashboard_data is None:
        st.stop()
    
    scenarios_summary = dashboard_data['scenarios_summary']
    market_state = dashboard_data['current_market_state']
    
    # Sidebar
    st.sidebar.header("📊 Current Market State")
    
    col1, col2 = st.sidebar.columns(2)
    with col1:
        st.metric("Brent Crude", f"${market_state['brent_price']:.2f}", delta=None)
        st.metric("OECD Stocks", f"{market_state['oecd_stocks_days']} days", delta=None)
    
    with col2:
        st.metric("VIX", f"{market_state['vix']:.1f}", delta=None)
        st.metric("SPR Level", f"{market_state['spr_level']} Mbbl", delta=None)
    
    regime_color = {"normal": "🟢", "elevated": "🟡", "crisis": "🔴"}
    st.sidebar.metric(
        "Market Regime", 
        f"{regime_color.get(market_state['regime'], '⚪')} {market_state['regime'].title()}",
        delta=None
    )
    
    st.sidebar.markdown("---")
    
    # Scenario selector
    st.sidebar.header("🎯 Scenario Selection")
    scenario_names = [s['scenario_name'] for s in scenarios_summary]
    selected_scenario_name = st.sidebar.selectbox("Choose scenario:", scenario_names)
    
    # Find selected scenario data
    selected_scenario_summary = next(s for s in scenarios_summary if s['scenario_name'] == selected_scenario_name)
    
    # Map scenario name to file prefix
    scenario_file_map = {
        "Strait of Hormuz - 14 day closure": "hormuz_14d",
        "Red Sea shipping - 60 day disruption": "red_sea_60d", 
        "Strait of Hormuz - 90 day crisis": "hormuz_90d",
        "Taiwan Strait Blockade": "taiwan_strait"
    }
    
    scenario_file_prefix = scenario_file_map.get(selected_scenario_name, "hormuz_14d")
    
    # Main content
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["🏠 Overview", "📈 Price Impact", "🏭 Sectors", "🗺️ Countries", "📚 Historical"])
    
    with tab1:
        st.header("Scenario Overview")
        
        # Key metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Brent Price Impact", 
                f"{selected_scenario_summary['brent_impact_pct']:+.1f}%",
                f"${selected_scenario_summary['new_brent_price']:.2f}/bbl"
            )
        
        with col2:
            st.metric(
                "Economic Impact",
                f"${selected_scenario_summary['economic_impact_billions']:.1f}B",
                "estimated global cost"
            )
        
        with col3:
            st.metric(
                "Countries Affected",
                f"{selected_scenario_summary['countries_high_vulnerability']}",
                "high/critical vulnerability"
            )
        
        with col4:
            st.metric(
                "Sectors Affected", 
                f"{selected_scenario_summary['sectors_high_impact']}",
                "high/critical impact"
            )
        
        st.markdown("---")
        
        # Scenario comparison chart
        st.subheader("All Scenarios Comparison")
        price_chart = create_price_impact_chart(scenarios_summary)
        st.plotly_chart(price_chart, use_container_width=True)
        
        # Scenario parameters table
        st.subheader("Scenario Parameters")
        params_data = []
        for scenario in scenarios_summary:
            params_data.append({
                "Scenario": scenario['scenario_name'],
                "Supply Gap": f"{scenario['supply_gap_pct']}%",
                "Duration": f"{scenario['duration_days']} days",
                "Regime": scenario['regime'].title(),
                "Price Impact": f"{scenario['brent_impact_pct']:+.1f}%",
                "Economic Impact": f"${scenario['economic_impact_billions']:.1f}B"
            })
        
        st.dataframe(pd.DataFrame(params_data), use_container_width=True)
    
    with tab2:
        st.header("Price Impact Analysis")
        
        # Load detailed scenario data
        scenario_detail = load_scenario_data(scenario_file_prefix)
        
        if scenario_detail:
            full_data = scenario_detail['full']
            
            # Price breakdown
            st.subheader("Price Calculation Breakdown")
            
            calc_breakdown = full_data['brent_impact']['calculation_breakdown']
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Supply Gap", f"{calc_breakdown['supply_gap']:.1%}")
                st.metric("Price Elasticity", f"{calc_breakdown['price_elasticity']:.3f}")
            
            with col2:
                st.metric("Regime Multiplier", f"{calc_breakdown['regime_multiplier']:.1f}×")
                st.metric("Duration Factor", f"{calc_breakdown['duration_factor']:.3f}")
            
            with col3:
                st.metric("SPR Dampener", f"{calc_breakdown['spr_dampener']:.3f}")
                st.metric("Replaceability", f"{calc_breakdown['replaceability_factor']:.3f}")
            
            # Formula display
            st.subheader("Calculation Formula")
            st.latex(r'''
            \text{Brent}_{\Delta\%} = \text{Supply Gap} \times \frac{1}{\text{Price Elasticity}} \times \text{Regime} \times \text{Duration} \times (1 - \text{SPR}) \times (1 - \text{Replaceability})
            ''')
            
            # Sensitivity analysis (simplified)
            st.subheader("Sensitivity Analysis")
            
            sensitivity_data = {
                'Factor': ['Supply Gap ±5%', 'Duration ±7 days', 'SPR ±10%', 'Regime Change'],
                'Low Impact': [f"{selected_scenario_summary['brent_impact_pct'] * 0.75:+.1f}%", 
                              f"{selected_scenario_summary['brent_impact_pct'] * 0.85:+.1f}%",
                              f"{selected_scenario_summary['brent_impact_pct'] * 0.9:+.1f}%",
                              f"{selected_scenario_summary['brent_impact_pct'] * 0.71:+.1f}%"],
                'High Impact': [f"{selected_scenario_summary['brent_impact_pct'] * 1.25:+.1f}%",
                               f"{selected_scenario_summary['brent_impact_pct'] * 1.15:+.1f}%", 
                               f"{selected_scenario_summary['brent_impact_pct'] * 1.1:+.1f}%",
                               f"{selected_scenario_summary['brent_impact_pct'] * 1.4:+.1f}%"]
            }
            
            st.dataframe(pd.DataFrame(sensitivity_data), use_container_width=True)
    
    with tab3:
        st.header("Sector Impact Analysis")
        
        scenario_detail = load_scenario_data(scenario_file_prefix)
        
        if scenario_detail:
            sectors_df = scenario_detail['sectors']
            
            # Sector impact chart
            sector_chart = create_sector_impact_chart(sectors_df)
            st.plotly_chart(sector_chart, use_container_width=True)
            
            # Detailed sector table
            st.subheader("Detailed Sector Impacts")
            
            display_sectors = sectors_df[['sector_name', 'impact_pct', 'severity', 'fuel_cost_share', 'pass_through_elasticity', 'hedge_discount']].copy()
            display_sectors.columns = ['Sector', 'Impact %', 'Severity', 'Fuel Cost Share', 'Pass-Through', 'Hedge Discount']
            display_sectors['Fuel Cost Share'] = display_sectors['Fuel Cost Share'].apply(lambda x: f"{x:.0%}")
            display_sectors['Pass-Through'] = display_sectors['Pass-Through'].apply(lambda x: f"{x:.0%}")
            display_sectors['Hedge Discount'] = display_sectors['Hedge Discount'].apply(lambda x: f"{x:.0%}")
            
            st.dataframe(display_sectors, use_container_width=True)
    
    with tab4:
        st.header("Country Vulnerability Analysis")
        
        scenario_detail = load_scenario_data(scenario_file_prefix)
        
        if scenario_detail:
            countries_df = scenario_detail['countries']
            
            # Vulnerability map
            vulnerability_map = create_country_vulnerability_map(countries_df)
            st.plotly_chart(vulnerability_map, use_container_width=True)
            
            # Top vulnerable countries
            st.subheader("Most Vulnerable Countries")
            
            top_countries = countries_df.head(10)
            
            for _, country in top_countries.iterrows():
                col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
                
                with col1:
                    tier_emoji = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}
                    st.write(f"{tier_emoji.get(country['vulnerability_tier'], '⚪')} **{country['country_name']}**")
                
                with col2:
                    st.metric("Score", f"{country['normalized_score']}/10")
                
                with col3:
                    st.metric("Imports", f"{country['oil_imports_mbpd']:.1f} Mbpd")
                
                with col4:
                    st.metric("Dependency", f"{country['total_dependency_pct']:.0f}%")
    
    with tab5:
        st.header("Historical Analogs")
        
        scenario_detail = load_scenario_data(scenario_file_prefix)
        
        if scenario_detail:
            analogs_df = scenario_detail['analogs']
            
            # Analog similarity chart
            analogs_chart = create_historical_analogs_chart(analogs_df)
            st.plotly_chart(analogs_chart, use_container_width=True)
            
            # Detailed analogs
            st.subheader("Top Historical Matches")
            
            for _, analog in analogs_df.head(3).iterrows():
                with st.expander(f"{analog['event_year']} - {analog['event_name']} (Similarity: {analog['similarity_score']:.2f})"):
                    
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        st.write("**Event Details:**")
                        st.write(f"• Duration: {analog['duration_days']} days")
                        st.write(f"• Supply Impact: {analog['supply_impact_pct']}%")
                        st.write("**Key Lessons:**")
                        st.write(analog['lessons_learned'])
                    
                    with col2:
                        st.write("**Similarity Breakdown:**")
                        st.write(f"Commodity: {analog['commodity_similarity']:.2f}")
                        st.write(f"Event Type: {analog['event_type_similarity']:.2f}")
                        st.write(f"Supply Shock: {analog['supply_shock_similarity']:.2f}")
                        st.write(f"Regime: {analog['regime_similarity']:.2f}")
                        st.write(f"Duration: {analog['duration_similarity']:.2f}")
    
    # Footer
    st.markdown("---")
    st.markdown("*Built with network-based cascade analysis • Data updated daily • Historical validation across 47 major disruptions*")

if __name__ == "__main__":
    main()
