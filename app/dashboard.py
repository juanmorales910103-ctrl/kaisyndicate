import streamlit as st
import pandas as pd
from app.database import init_db, SessionLocal, DBPosition, DBLedgerEntry
from app.prediction import PredictionEngine
from app.pricing_risk import TreasuryManager, PricingRiskEngine

st.set_page_config(page_title="KAI SYNDICATE - Institutional Terminal", page_icon="🛡️", layout="wide")
init_db()
treasury = TreasuryManager()

st.title("🛡️ KAI SYNDICATE | Institutional Quant Platform")
st.markdown("Plataforma cuantitativa privada de investigación, análisis deportivo y gestión de riesgo. **Jurisdicción:** Colombia.")

st.sidebar.header("📊 Tesorería & Capital")
st.sidebar.metric("Net Worth Total", f"${treasury.net_worth:,.2f} USD")
st.sidebar.metric("Efectivo Disponible", f"${treasury.cash:,.2f} USD")
st.sidebar.metric("Exposición Abierta", f"${treasury.exposure:,.2f} USD")
st.sidebar.markdown("---")
st.sidebar.info("Modo activo: **ENTRADA DE PARTIDOS REALES**\nZona Horaria: Bogotá (UTC-5)")

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🎯 1. Inicio & Resumen",
    "⚽ 2. Partidos & Oportunidades +EV",
    "📂 3. Cartera & Operaciones",
    "📒 4. Libro Mayor Contable",
    "⚙️ 5. Configuración & Auditoría"
])

with tab1:
    st.subheader("Estado General del Sindicato")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Capital Inicial", "$1,000,000.00 USD")
    c2.metric("Patrimonio Neto Actual", f"${treasury.net_worth:,.2f} USD")
    c3.metric("Rendimiento Acumulado", f"{((treasury.net_worth - 1000000)/1000000)*100:+.2f}%")
    c4.metric("Estado de Riesgo", "Óptimo (Límites Activos)")
    st.markdown("---")
    st.markdown("### Instrucciones:\n1. Ve a la pestaña **Partidos & Oportunidades +EV**.\n2. Escribe los equipos del partido real que quieres analizar.\n3. Ingresa los xG y la cuota de la casa de apuestas.")

with tab2:
    st.subheader("Motor de Análisis de Mercado y Detección de Valor")
    col_t1, col_t2 = st.columns(2)
    with col_t1:
        home_team = st.text_input("Equipo Local", value="Millonarios")
    with col_t2:
        away_team = st.text_input("Equipo Visitante", value="Atletico Nacional")
    match_name = f"{home_team} vs {away_team}"
    
    col1, col2 = st.columns(2)
    with col1:
        xg_home = st.number_input("xG Local", 0.5, 4.0, 1.75, 0.05)
        xg_away = st.number_input("xG Visitante", 0.5, 4.0, 1.15, 0.05)
    with col2:
        market = st.selectbox("Mercado de Apuesta", ["1", "X", "2", "Over 2.5", "Under 2.5"])
        odds_provider = st.number_input("Cuota Ofrecida por Proveedor", 1.01, 20.0, 2.15, 0.05)
        rho = st.slider("Parámetro Dixon-Coles (ρ)", -0.20, 0.0, -0.12, 0.01)

    probs = PredictionEngine.dixon_coles_probabilities(xg_home, xg_away, rho)
    p_model = probs[market]
    fair_odds = PricingRiskEngine.calculate_fair_odds(p_model)
    evaluation = PricingRiskEngine.evaluate_market(p_model, odds_provider)
    stake = PricingRiskEngine.calculate_kelly_stake(treasury.net_worth, p_model, odds_provider)

    st.markdown("---")
    r1, r2, r3, r4 = st.columns(4)
    r1.metric("Probabilidad del Modelo", f"{p_model*100:.2f}%")
    r2.metric("Cuota Justa", f"{fair_odds:.2f}")
    r3.metric("Margen Teórico Proveedor", f"{evaluation['margin']*100:.2f}%")
    r4.metric("Valor Esperado (EV)", f"{evaluation['ev']*100:+.2f}%")

    if evaluation['decision'].startswith("SIN APUESTA"):
        st.error(f"🛑 **ESTADO: SIN APUESTA (NO_BET)** — {evaluation['reason']}")
    else:
        st.success(f"✅ **ESTADO: OPORTUNIDAD APROBADA** — {evaluation['reason']}")
        st.write(f"💼 **Stake Sugerido (Kelly Fraccionado 10%):** ${stake:,.2f} USD")
        if st.button("🚀 Registrar Inversión en Cartera y Bloquear Capital"):
            pos_id = f"POS-{abs(hash(match_name + market)) % 100000}"
            session = SessionLocal()
            try:
                exists = session.query(DBPosition).filter_by(position_id=pos_id).first()
                if exists:
                    st.error("Esta posición ya fue registrada anteriormente.")
                else:
                    treasury.record("LOCK_STAKE", stake, pos_id)
                    db_pos = DBPosition(position_id=pos_id, match_name=match_name, market=market, odds_provider=odds_provider, odds_fair_model=fair_odds, expected_value_ev=evaluation['ev'], stake=stake, status="PENDING")
                    session.add(db_pos)
                    session.commit()
                    st.success(f"Posición {pos_id} almacenada con éxito.")
                    st.rerun()
            finally:
                session.close()

with tab3:
    st.subheader("Gestión de Cartera & Liquidación")
    session = SessionLocal()
    try:
        positions = session.query(DBPosition).all()
        if not positions:
            st.info("No hay posiciones registradas.")
        else:
            data = [{ "ID": p.position_id, "Partido": p.match_name, "Mercado": p.market, "Cuota": p.odds_provider, "EV": f"{p.expected_value_ev*100:+.1f}%", "Stake": f"${p.stake:,.2f}", "Estado": p.status } for p in positions]
            st.dataframe(pd.DataFrame(data), use_container_width=True)
    finally:
        session.close()

with tab4:
    st.subheader("Libro Mayor Contable")
    session = SessionLocal()
    try:
        entries = session.query(DBLedgerEntry).all()
        if not entries:
            st.info("Sin movimientos.")
        else:
            df_e = pd.DataFrame([{ "Fecha": e.timestamp, "Tipo": e.transaction_type, "Monto": f"${e.amount:,.2f}", "Cash": f"${e.available_cash:,.2f}", "Net Worth": f"${e.net_worth:,.2f}" } for e in entries])
            st.dataframe(df_e, use_container_width=True)
    finally:
        session.close()

with tab5:
    st.subheader("Auditoría")
    st.json({"Sistema": "Operativo", "Motor": "Dixon-Coles"})
