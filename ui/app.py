import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import streamlit as st
import pandas as pd
import numpy as np
from core.database.models import init_db, SessionLocal, DBPosition, DBLedgerEntry
from core.database.treasury import TreasuryManager
from core.quant.dixon_coles import DixonColesEngine
from core.risk.optimizer import PortfolioRiskOptimizer
from core.scrapers.ingestor import DataIngestor
from core.scrapers.live_scraper import LiveOddsScraper

st.set_page_config(page_title="KAI SYNDICATE - Institutional Terminal", page_icon="🛡️", layout="wide")
init_db()
treasury = TreasuryManager()

st.title("🛡️ KAI SYNDICATE | Institutional Quant Platform")
st.markdown("Plataforma cuantitativa privada de investigación, análisis deportivo y gestión de riesgo. **Jurisdicción:** Colombia.")

st.sidebar.header("📊 Tesorería & Capital")
st.sidebar.metric("Net Worth Total", f"${treasury.net_worth:,.2f} USD")
st.sidebar.metric("Efectivo Disponible", f"${treasury.available_cash:,.2f} USD")
st.sidebar.metric("Exposición Abierta", f"${treasury.open_exposure:,.2f} USD")
st.sidebar.markdown("---")
st.sidebar.info("Modo activo: **PRODUCCIÓN TOTAL 100% REAL**\nZona Horaria: Bogotá (UTC-5)")

t1, t2, t3, t4, t5, t6, t7 = st.tabs([
    "🎯 1. Análisis Multimercado",
    "⚡ 2. Auto-Ingesta & MLE Time-Decay",
    "🌐 3. Live Scraper (Playwright)",
    "📊 4. Kelly Multivariado & Monte Carlo",
    "📈 5. Backtesting & Sharpe",
    "📂 6. Cartera & Auditoría CLV",
    "📒 7. Libro Mayor Contable"
])

with t1:
    st.subheader("1. Motor Cuantitativo Dixon-Coles Bivariado")
    c1, c2 = st.columns(2)
    with c1:
        h_team = st.text_input("Equipo Local", value="Millonarios")
        ah = st.number_input("Alpha Local (Ataque)", -1.0, 2.0, 0.25, 0.05)
        bh = st.number_input("Beta Local (Defensa)", -2.0, 1.0, -0.15, 0.05)
    with c2:
        a_team = st.text_input("Equipo Visitante", value="Atletico Nacional")
        aa = st.number_input("Alpha Visitante (Ataque)", -1.0, 2.0, 0.10, 0.05)
        ba = st.number_input("Beta Visitante (Defensa)", -2.0, 1.0, -0.05, 0.05)

    cm1, cm2, cm3 = st.columns(3)
    with cm1: market = st.selectbox("Mercado", ["1", "X", "2", "Over 2.5", "Under 2.5", "BTTS_Yes", "BTTS_No"])
    with cm2: odds = st.number_input("Cuota Proveedor", 1.01, 20.0, 2.15, 0.05)
    with cm3:
        gamma = st.slider("Ventaja Local (γ)", 0.0, 0.5, 0.20, 0.02)
        rho = st.slider("Dixon-Coles (ρ)", -0.25, 0.0, -0.10, 0.01)

    match_name = f"{h_team} vs {a_team}"
    probs = DixonColesEngine.predict_match(ah, bh, aa, ba, gamma, rho)
    p_model = probs[market]
    fair_odds = 1.0 / p_model if p_model > 0 else 99.0
    ev = (p_model * odds) - 1.0

    st.markdown("---")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Probabilidad Modelo", f"{p_model*100:.2f}%")
    m2.metric("Cuota Justa", f"{fair_odds:.2f}")
    m3.metric("Margen Casa", f"{(1.0/odds - p_model)*100:.2f}%")
    m4.metric("Valor Esperado (EV)", f"{ev*100:+.2f}%")

    if ev < 0.025:
        st.error(f"🛑 **NO_BET** — EV inferior al umbral del 2.5% ({ev*100:+.2f}%).")
    else:
        st.success("✅ **APROBADO (+EV)** — Valor positivo verificado.")
        stake = PortfolioRiskOptimizer.optimize_multivariate_kelly([{'p_model': p_model, 'odds': odds}], treasury.net_worth)[0]
        st.write(f"💼 **Stake Sugerido:** `${stake:,.2f} USD`")
        if st.button("🚀 Registrar Posición en Cartera"):
            session = SessionLocal()
            try:
                treasury.record_transaction("LOCK_STAKE", stake, match_name)
                db_pos = DBPosition(
                    match_name=match_name, league="Liga BetPlay", market=market,
                    odds_placed=odds, odds_fair_model=fair_odds, expected_value_ev=ev,
                    stake_usd=stake, status="PENDING"
                )
                session.add(db_pos)
                session.commit()
                st.success("Posición registrada y capital bloqueado.")
                st.rerun()
            finally: session.close()

with t2:
    st.subheader("2. Calibración MLE con Decaimiento Temporal")
    league = st.selectbox("Liga", list(DataIngestor.LEAGUES.keys()))
    season = st.selectbox("Temporada", ["2324", "2223"])
    xi = st.slider("Decaimiento Temporal (ξ)", 0.0, 0.005, 0.0015, 0.0005)

    if st.button("⚡ Ejecutar Ingesta y Optimización MLE"):
        with st.spinner("Descargando datos y ajustando por Máxima Verosimilitud..."):
            df = DataIngestor.fetch_league(league, season)
            if not df.empty:
                res = DixonColesEngine.fit_mle(df, xi=xi)
                st.success("✅ Modelo MLE calibrado exitosamente.")
                g_val = res['gamma']
                r_val = res['rho']
                st.metric("Gamma (Ventaja Local)", f"{g_val:.4f}")
                st.metric("Rho (Dixon-Coles)", f"{r_val:.4f}")
                alpha_df = pd.DataFrame({
                    'Equipo': list(res['alphas'].keys()),
                    'Alpha': list(res['alphas'].values()),
                    'Beta': list(res['betas'].values())
                })
                st.dataframe(alpha_df, use_container_width=True)
            else: st.error("No se pudieron cargar los datos.")

with t3:
    st.subheader("3. Extraer Cuotas Vivas en Tiempo Real (Playwright)")
    target_url = st.text_input("URL de Cuotas", value="https://www.oddsportal.com/soccer/colombia/liga-betplay/")
    if st.button("🕷️ Ejecutar Playwright Scraper en Vivo"):
        with st.spinner("Lanzando Chromium invisible y capturando cuotas del mercado..."):
            scraped_data = LiveOddsScraper.get_live_odds_sync(target_url)
            if scraped_data:
                st.success(f"🔥 Se capturaron {len(scraped_data)} registros en vivo!")
                st.dataframe(pd.DataFrame(scraped_data), use_container_width=True)
            else:
                st.info("Barrido completado.")

with t4:
    st.subheader("4. Portafolio Kelly Multivariado & Monte Carlo VaR")
    uploaded = st.file_uploader("Cargar jornada (.csv)", type=["csv"])
    if uploaded:
        df_j = pd.read_csv(uploaded)
        st.write(df_j.head())
        if st.button("🧮 Simular Riesgo Monte Carlo"):
            opps = [{'p_model': float(r.get('Prob_Modelo', 0.5)), 'odds': float(r.get('Cuota', 2.0))} for _, r in df_j.iterrows()]
            mc = PortfolioRiskOptimizer.run_monte_carlo(treasury.net_worth, opps)
            v95 = mc['var_95_pct']
            v99 = mc['var_99_pct']
            mdd = mc['max_drawdown_pct']
            c1, c2, c3 = st.columns(3)
            c1.metric("VaR 95%", f"{v95:.2f}%")
            c2.metric("VaR 99%", f"{v99:.2f}%")
            c3.metric("Max Drawdown", f"{mdd:.2f}%")

with t5:
    st.subheader("5. Backtesting & Sharpe Ratio")
    ns = st.slider("Partidos simulados", 100, 2000, 500, 100)
    if st.button("📊 Ejecutar Backtesting"):
        np.random.seed(42)
        bank, hist, rets, wins, bets = 1000000.0, [1000000.0], [], 0, 0
        for _ in range(ns):
            p = np.random.uniform(0.42, 0.58)
            odds = (1.0 / p) * 1.05
            if (p * odds - 1.0) > 0.025:
                bets += 1
                stk = bank * 0.01
                if np.random.rand() < p:
                    prof = stk * (odds - 1.0)
                    bank += prof
                    wins += 1
                    rets.append(prof / bank)
                else:
                    bank -= stk
                    rets.append(-stk / bank)
            hist.append(bank)
        sharpe = (np.mean(rets) / np.std(rets)) * np.sqrt(50) if len(rets) > 1 else 0.0
        st.success("Backtesting finalizado.")
        st.metric("Ratio Sharpe", f"{sharpe:.2f}")
        st.line_chart(hist)

with t6:
    st.subheader("6. Cartera y Liquidación con Auditoría CLV")
    session = SessionLocal()
    try:
        positions = session.query(DBPosition).all()
        if positions:
            pos_data = [{
                'ID': p.position_id, 'Partido': p.match_name, 'Mercado': p.market, 
                'Cuota': p.odds_placed, 'CLV': p.odds_closing or 'Pendiente', 
                'EV': f"{p.expected_value_ev*100:+.2f}%", 'Stake': f"${p.stake_usd:,.2f}", 'Estado': p.status 
            } for p in positions]
            st.dataframe(pd.DataFrame(pos_data), use_container_width=True)
            
            pending = [p for p in positions if p.status == "PENDING"]
            if pending:
                sel = st.selectbox("Seleccionar ID", [p.position_id for p in pending])
                clv = st.number_input("Cuota de Cierre (CLV)", 1.01, 20.0, 2.0, 0.05)
                c_w, c_l = st.columns(2)
                with c_w:
                    if st.button("🟢 Liquidar GANADA"):
                        pos = session.query(DBPosition).filter_by(position_id=sel).first()
                        prof = pos.stake_usd * (pos.odds_placed - 1.0)
                        treasury.record_transaction("SETTLE_WIN", pos.stake_usd + prof, sel, net_worth_delta=prof)
                        pos.status, pos.odds_closing = "WON", clv
                        session.commit()
                        st.rerun()
                with c_l:
                    if st.button("🔴 Liquidar PERDIDA"):
                        pos = session.query(DBPosition).filter_by(position_id=sel).first()
                        treasury.record_transaction("SETTLE_LOSS", pos.stake_usd, sel)
                        pos.status, pos.odds_closing = "LOST", clv
                        session.commit()
                        st.rerun()
        else: st.info("Sin posiciones registradas.")
    finally: session.close()

with t7:
    st.subheader("7. Libro Mayor Contable (Inmutable)")
    session = SessionLocal()
    try:
        entries = session.query(DBLedgerEntry).order_by(DBLedgerEntry.timestamp.desc()).all()
        if entries:
            ledger_data = [{
                'Fecha': e.timestamp, 'Tipo': e.transaction_type, 'Monto': f"${e.amount:,.2f}", 
                'Efectivo': f"${e.available_cash:,.2f}", 'Net Worth': f"${e.net_worth:,.2f}", 'Ref': e.reference_id 
            } for e in entries]
            st.dataframe(pd.DataFrame(ledger_data), use_container_width=True)
    finally: session.close()
