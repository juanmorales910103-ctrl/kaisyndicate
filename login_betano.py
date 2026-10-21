from playwright.sync_api import sync_playwright
import os

user_dir = os.path.abspath("./user_session")
os.makedirs(user_dir, exist_ok=True)
print("🔑 Abriendo navegador para guardar sesión de Betano...")

with sync_playwright() as p:
    context = p.chromium.launch_persistent_context(
        user_dir,
        headless=False,
        args=["--disable-blink-features=AutomationControlled", "--no-sandbox", "--start-maximized"],
        viewport=None
    )
    page = context.pages[0] if context.pages else context.new_page()
    page.goto("https://www.betano.co", timeout=60000, wait_until="domcontentloaded")
    
    print("\n" + "="*60)
    print("👉 1. VE A LA VENTANA DE BETANO QUE SE ACABA DE ABRIR.")
    print("👉 2. INICIA SESIÓN CON TU USUARIO Y CONTRASEÑA.")
    print("👉 3. CUANDO VEAS TU SALDO EN PANTALLA, VUELVE AQUÍ Y PRESIONA ENTER.")
    print("="*60 + "\n")
    
    input("⏸️  Presiona la tecla ENTER aquí cuando hayas iniciado sesión en Betano... ")
    context.close()

print("\n✅ ¡Listo! Sesión de Betano guardada exitosamente en ./user_session")
