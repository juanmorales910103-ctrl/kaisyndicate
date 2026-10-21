from playwright.sync_api import sync_playwright
import time
import logging
import os
import glob
import re

class RealBookmakerBroker:
    def __init__(self, user_data_dir="./user_session"):
        self.user_data_dir = os.path.abspath(user_data_dir)
        os.makedirs("logs/screenshots", exist_ok=True)

    def _unlock_profile(self):
        for lock_file in glob.glob(os.path.join(self.user_data_dir, "Singleton*")):
            try:
                os.remove(lock_file)
            except:
                pass

    def execute_live_order(self, bookmaker_url="https://www.betano.co", match_name="", market_type="1", stake_amount=2000, auto_confirm=True):
        logging.info(f"⚡ [BETANO 100% BLINDADO] Orden: {match_name} | Stake: ${stake_amount:,.0f}")
        self._unlock_profile()
        success = False
        attempts = 3

        for attempt in range(attempts):
            try:
                with sync_playwright() as p:
                    context = p.chromium.launch_persistent_context(
                        self.user_data_dir,
                        headless=False,
                        args=[
                            "--disable-blink-features=AutomationControlled",
                            "--no-sandbox",
                            "--disable-infobars",
                            "--start-maximized",
                            "--disable-dev-shm-usage"
                        ],
                        viewport=None
                    )
                    
                    page = context.pages[0] if context.pages else context.new_page()
                    page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
                    
                    page.goto(bookmaker_url, timeout=60000, wait_until="domcontentloaded")
                    time.sleep(5)

                    # Detección de Cloudflare o bloqueo de seguridad
                    if "Cloudflare" in page.title() or "Access Denied" in page.content():
                        logging.warning(f"⚠️ [CLOUDFLARE] Bloqueo detectado en intento {attempt+1}. Reintentando con nueva sesión...")
                        context.close()
                        time.sleep(5)
                        continue

                    # Búsqueda y ejecución normal
                    home_team = match_name.split(" vs ")[0].strip() if " vs " in match_name else match_name
                    search_term = home_team.split()[0] if len(home_team.split()) > 1 else home_team

                    for trig in ["[data-qa='header-search-button']", "button[aria-label*='Buscar']"]:
                        try:
                            if page.locator(trig).first.is_visible(timeout=2000):
                                page.locator(trig).first.click()
                                time.sleep(1)
                                break
                        except:
                            continue

                    for inp in ["input[data-qa*='search']", "input[placeholder*='Buscar']"]:
                        try:
                            box = page.locator(inp).first
                            if box.is_visible(timeout=2500):
                                box.click()
                                box.fill(search_term)
                                time.sleep(2)
                                box.press("Enter")
                                time.sleep(3)
                                break
                        except:
                            continue

                    clicked_odd = False
                    for o_sel in ["button.selections__selection", "button[data-qa*='selection']", "[data-qa*='outcome']"]:
                        try:
                            odd_btn = page.locator(o_sel).first
                            if odd_btn.is_visible(timeout=4000):
                                odd_btn.click()
                                clicked_odd = True
                                time.sleep(2)
                                break
                        except:
                            continue

                    clean_stake = str(max(1000, int(round(stake_amount))))
                    stake_typed = False
                    for s_sel in ["input[data-qa*='stake']", "input[class*='betslip']"]:
                        try:
                            s_inp = page.locator(s_sel).first
                            if s_inp.is_visible(timeout=3000):
                                s_inp.click()
                                s_inp.fill("")
                                s_inp.type(clean_stake, delay=50)
                                stake_typed = True
                                time.sleep(2)
                                break
                        except:
                            continue

                    if auto_confirm and clicked_odd and stake_typed:
                        for c_sel in ["button[data-qa='place-bet-button']", "button:has-text('Apuesta ya')"]:
                            try:
                                c_btn = page.locator(c_sel).first
                                if c_btn.is_visible(timeout=3000) and c_btn.is_enabled():
                                    c_btn.click()
                                    logging.info("🚀 [BETANO] ¡Apuesta confirmada exitosamente bajo protocolo institucional!")
                                    success = True
                                    break
                            except:
                                continue

                    context.close()
                    if success:
                        break

            except Exception as e:
                logging.error(f"❌ [INTENTO {attempt+1} FALLIDO] {e}")
                time.sleep(5)

        return success
