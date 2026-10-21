import streamlit as st
import pandas as pd
import plotly.express as px
from core.database.models import SessionLocal, DBPosition

st.set_page_config(
    page_title="KAI SYNDICATE | Institutional Quant Dashboard",
    page_icon="⚡",
    layout="wide"
)

st.title("⚡ KAI SYNDICATE — Dashboard Cuantitativo Institucional")
st.markdown("---")

session = SessionLocal()
positions = session.query(DBPosition).all()
session.close()

net_worth = 1000000.0
locked_cash = sum([getattr(p, 'stake_usd', 0) for p in positions if getattr(p, 'status', '') == "PENDING"])
available_cash = max(0.0, net_worth - locked_cash)

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Net Worth (COP)", f"${net_worth:,.0f}")
with col2:
    st.metric("Efectivo Disponible", f"${available_cash:,.0f}")
with col3:
    st.metric("Capital Bloqueado (Risk)", f"${locked_cash:,.0f}")
with col4:
    st.metric("Drawdown Actual", "0.0% (Seguro)")

st.markdown("---")

if positions:
    data = []
    for idx, p in enumerate(positions):
        data.append({
            "ID": getattr(p, 'id', idx + 1),
            "Partido": getattr(p, 'match_name', 'N/A'),
            "Liga": getattr(p, 'league', 'N/A'),
            "Mercado": getattr(p, 'market', 'N/A'),
            "Cuota": getattr(p, 'odds_placed', 0.0),
            "EV": getattr(p, 'expected_value_ev', 0.0),
            "Stake": getattr(p, 'stake_usd', 0.0),
            "Estado": getattr(p, 'status', 'PENDING'),
            "Fecha": getattr(p, 'created_at', 'N/A')
        })
    df = pd.DataFrame(data)
    
    settled = df[df["Estado"].isin(["WON", "LOST"])]
    total_bets = len(settled)
    won_bets = len(settled[settled["Estado"] == "WON"])
    win_rate = (won_bets / total_bets * 100) if total_bets > 0 else 0.0
    
    total_staked = settled["Stake"].sum() if not settled.empty else 0.0
    total_returned = settled[settled["Estado"] == "WON"].apply(lambda x: x["Stake"] * x["Cuota"], axis=1).sum() if not settled.empty else 0.0
    net_profit = total_returned - total_staked
    roi = (net_profit / total_staked * 100) if total_staked > 0 else 0.0
    profit_factor = (total_returned / total_staked) if total_staked > 0 else 1.0

    st.subheader("📊 Analítica Avanzada de Rendimiento y ROI")
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    with kpi1:
        st.metric("Win Rate", f"{win_rate:.1f}%")
    with kpi2:
        st.metric("ROI Histórico", f"{roi:+.2f}%")
    with kpi3:
        st.metric("Profit Factor", f"{profit_factor:.2f}")
    with kpi4:
        st.metric("Beneficio Neto", f"${net_profit:,.0f} COP")

    st.markdown("---")

    c_left, c_right = st.columns(2)
    with c_left:
        st.markdown("### 📈 Curva de Crecimiento del Bankroll")
        if not settled.empty:
            settled["Cumulative_Profit"] = settled.apply(
                lambda x: (x["Stake"] * x["Cuota"] - x["Stake"]) if x["Estado"] == "WON" else -x["Stake"], axis=1
            ).cumsum()
            
            fig_bankroll = px.line(
                settled, x="Fecha", y="Cumulative_Profit",
                markers=True, title="Evolución del Beneficio Acumulado",
                labels={"Cumulative_Profit": "Beneficio (COP)", "Fecha": "Tiempo"}
            )
            fig_bankroll.update_layout(template="plotly_dark")
            st.plotly_chart(fig_bankroll, use_container_width=True)
        else:
            st.info("Esperando liquidación de primeras apuestas para trazar curva.")

    with c_right:
        st.markdown("### 🎯 Desglose por Tipo de Mercado")
        if not settled.empty:
            market_group = settled.groupby("Mercado").size().reset_index(name="Count")
            fig_market = px.pie(
                market_group, names="Mercado", values="Count",
                title="Distribución de Apuestas por Mercado", hole=0.4
            )
            fig_market.update_layout(template="plotly_dark")
            st.plotly_chart(fig_market, use_container_width=True)
        else:
            st.info("Sin datos de mercado suficientes.")

    st.markdown("---")
    st.subheader("📋 Registro Detallado de Posiciones")
    st.dataframe(df, use_container_width=True)

else:
    st.info("📭 No hay posiciones registradas todavía en la base de datos del fondo.")

if st.button("🔄 Actualizar Datos"):
    st.rerun()
