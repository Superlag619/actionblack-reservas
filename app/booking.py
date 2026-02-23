# app/booking.py
import os
import time

from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from .config_store import get_config

load_dotenv()

# Mapea sede -> ciudad para el popup "Selecciona una ciudad"
SEDE_CIUDAD = {
    "Alto de Palmas": "ENVIGADO",
    "City Plaza": "ENVIGADO",
    "Intermedia": "ENVIGADO",
    "Viva Envigado": "ENVIGADO",
    "Viva Palmas": "ENVIGADO",
}


def _build_time_label(hh_mm: str) -> str:
    """
    Convierte '05:20' -> '5:20 AM', '19:30' -> '7:30 PM'. [file:83]
    """
    h, m = hh_mm.split(":")
    h = int(h)
    m = int(m)
    am_pm = "AM" if h < 12 else "PM"
    h12 = h if 1 <= h <= 12 else (h - 12 if h > 12 else 12)
    return f"{h12}:{m:02d} {am_pm}"


def _compact_time_key(hh_mm: str) -> str:
    """
    Convierte '05:20' -> '520AM', '19:30' -> '730PM'. [file:83]
    """
    h, m = hh_mm.split(":")
    h = int(h)
    m = int(m)
    am_pm = "AM" if h < 12 else "PM"
    h12 = h if 1 <= h <= 12 else (h - 12 if h > 12 else 12)
    return f"{h12}{m:02d}{am_pm}"


def _row_compact_time_text(text: str) -> str:
    """
    De todo el texto de la fila, deja solo dígitos y las letras A/P/M
    y las pega juntas. [file:83]
    """
    t = text.upper()
    return "".join(ch for ch in t if ch.isdigit() or ch in "APM")


def test_booking():
    config = get_config()
    return {"status": "ok", "config": config}


def run_booking():
    """
    Bot principal:
    - Lee config (hora_clase, tipo_clase, sede, dias_offset)
    - Login en ActionBlack
    - Selecciona ciudad + sede
    - Actualiza calendario
    - (Opcional) selecciona día objetivo (offset desde el día activo)
    - Recorre todos los botones 'Reservar', sube varios niveles de padres
      hasta un div que tenga texto con 'AM' o 'PM', y allí busca la hora
      compacta (ej. '520AM').
    - Clic en ese botón y (si aplica) 'Confirmar'
    """
    config = get_config()
    hora_objetivo = config["hora_clase"]       # p.ej. '05:20'
    tipo_objetivo = config["tipo_clase"]       # p.ej. 'TONIC'
    sede_objetivo = config["sede"]             # p.ej. 'Viva Envigado'
    dias_offset = int(config.get("dias_offset", 1))  # 0=hoy,1=mañana,...

    if dias_offset < 0:
        dias_offset = 0
    if dias_offset > 6:
        dias_offset = 6

    hora_label = _build_time_label(hora_objetivo)
    hora_compact = _compact_time_key(hora_objetivo)  # '520AM'

    print(
        f"🔧 Config: {hora_objetivo} ({hora_label}) - {tipo_objetivo} "
        f"- {sede_objetivo} - offset {dias_offset} día(s)"
    )

    email = os.getenv("ACTIONBLACK_EMAIL")
    password = os.getenv("ACTIONBLACK_PASSWORD")
    if not email or not password:
        return {
            "status": "error",
            "message": "Faltan ACTIONBLACK_EMAIL o ACTIONBLACK_PASSWORD en .env",
        }

    ciudad = SEDE_CIUDAD.get(sede_objetivo, "ENVIGADO")

       # ChromeOptions: headless solo en Render
    options = webdriver.ChromeOptions()

    # Si estamos en Render, forzar headless
    if os.getenv("RENDER") == "true":
        options.add_argument("--headless=new")

    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1280,800")


    driver = webdriver.Chrome(options=options)
    wait = WebDriverWait(driver, 25)

    step = "inicio"
    try:
        step = "abrir /reservas"
        driver.get("https://www.actionblack.co/reservas")
        print(f"[{step}]")
        time.sleep(3)

        step = "clic boton Inicia sesión"
        login_btn = wait.until(
            EC.element_to_be_clickable(
                (By.XPATH, "//p[contains(.,'Inicia sesión')]/ancestor::button")
            )
        )
        driver.execute_script("arguments[0].click();", login_btn)
        print(f"[{step}] OK")
        time.sleep(1.5)

        step = "ingresar credenciales"
        email_input = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='email']"))
        )
        pass_input = driver.find_element(By.CSS_SELECTOR, "input[type='password']")
        email_input.clear()
        email_input.send_keys(email)
        pass_input.clear()
        pass_input.send_keys(password)
        print(f"[{step}] OK")

        step = "enviar login"
        submit_btn = wait.until(
            EC.element_to_be_clickable(
                (By.XPATH, "//button[contains(.,'Iniciar Sesión')]")
            )
        )
        driver.execute_script("arguments[0].click();", submit_btn)
        print(f"[{step}] OK")
        time.sleep(5)

        step = "abrir cambiar de sede"
        cambiar_sede_btn = wait.until(
            EC.element_to_be_clickable(
                (By.XPATH, "//button[contains(.,'Cambiar de sede')]")
            )
        )
        driver.execute_script("arguments[0].click();", cambiar_sede_btn)
        print(f"[{step}] OK")
        time.sleep(2)

        step = "seleccionar ciudad"
        ciudad_combo = wait.until(
            EC.element_to_be_clickable(
                (By.XPATH, "//div[@role='combobox' and @aria-labelledby='city-select-label']")
            )
        )
        driver.execute_script("arguments[0].click();", ciudad_combo)
        time.sleep(1)

        ciudad_option = wait.until(
            EC.presence_of_element_located(
                (By.XPATH, f"//span[contains(.,'{ciudad}')]")
            )
        )
        driver.execute_script("arguments[0].click();", ciudad_option)
        print(f"[{step}] OK -> {ciudad}")
        time.sleep(1.5)

        step = "seleccionar sede"
        sede_btn = wait.until(
            EC.presence_of_element_located(
                (By.XPATH, f"//button[.//span[contains(.,'{sede_objetivo}')]]")
            )
        )
        driver.execute_script("arguments[0].click();", sede_btn)
        print(f"[{step}] OK -> {sede_objetivo}")
        time.sleep(3)

        step = "actualizar calendario"
        actualizar_btn = wait.until(
            EC.element_to_be_clickable(
                (By.XPATH, "//button[contains(.,'Actualizar calendario')]")
            )
        )
        driver.execute_script("arguments[0].click();", actualizar_btn)
        print(f"[{step}] OK")
        time.sleep(5)

        # Seleccionar día objetivo SOLO si offset > 0
        step = "seleccionar dia objetivo"
        if dias_offset == 0:
            print(f"[{step}] offset 0 -> uso día ya activo, no hago clic")
        else:
            dia_div = None
            for _ in range(25):
                dia_div = driver.execute_script(
                    "return document.querySelector('div[class*=\"agendaactive\"]');"
                )
                if dia_div:
                    break
                time.sleep(1)
            if not dia_div:
                driver.quit()
                return {
                    "status": "error",
                    "message": f"[{step}] No encontré el día activo en el calendario.",
                }

            for i in range(dias_offset):
                dia_div = driver.execute_script(
                    "return arguments[0].nextElementSibling;", dia_div
                )
                if dia_div is None:
                    driver.quit()
                    return {
                        "status": "error",
                        "message": f"[{step}] No hay suficientes días hacia adelante para offset {dias_offset}.",
                    }

            driver.execute_script("arguments[0].click();", dia_div)
            print(f"[{step}] OK -> offset {dias_offset}")
            time.sleep(4)

        # ==========================
        # Buscar la fila correcta usando los botones "Reservar"
        # ==========================
        step = "buscar tarjeta hora"
        print(f"[{step}] Recorriendo botones para encontrar hora '{hora_label}' (clave '{hora_compact}')")

        # 1) Tomar todos los botones y filtrar los que digan RESERVAR
        all_buttons = driver.find_elements(By.TAG_NAME, "button")
        botones_reservar = []
        for b in all_buttons:
            try:
                txt = b.text.strip().upper()
                if "RESERVAR" in txt:
                    botones_reservar.append(b)
            except Exception:
                continue

        print(f"[{step}] Encontré {len(botones_reservar)} botones con texto RESERVAR")

        if not botones_reservar:
            driver.quit()
            return {
                "status": "error",
                "message": f"[{step}] No encontré ningún botón 'Reservar' en la agenda.",
            }

        target_row = None
        target_button = None

        for idx, b in enumerate(botones_reservar, start=1):
            try:
                # Subir padres hasta encontrar un div cuyo texto contenga 'AM' o 'PM'
                row = b
                for _ in range(8):  # hasta 8 niveles por seguridad
                    parent = row.find_element(By.XPATH, "./..")
                    row = parent
                    if "AM" in row.text or "PM" in row.text:
                        break

                full_text = row.text
                compact = _row_compact_time_text(full_text)

                print(f"[debug fila {idx}] raw: {full_text.replace(chr(10), ' | ')}")
                print(f"[debug fila {idx}] compact: {compact}")

                if hora_compact in compact:
                    print(f"[debug] MATCH en fila {idx} (contiene '{hora_compact}')")
                    target_row = row
                    target_button = b
                    break
            except Exception as e:
                print(f"[debug fila {idx}] error al procesar fila: {type(e).__name__} -> {e}")
                continue

        if target_row is None or target_button is None:
            driver.quit()
            return {
                "status": "error",
                "message": (
                    f"[{step}] No encontré ninguna fila con hora '{hora_label}' "
                    f"(clave '{hora_compact}') que además tenga botón 'Reservar'."
                ),
            }

        step = "clic reservar"
        print(f"[{step}] Encontrado botón RESERVAR en la fila de {hora_label}, haciendo clic…")
        driver.execute_script("arguments[0].click();", target_button)
        time.sleep(3)

        step = "confirmar (si aparece)"
        try:
            confirmar_btn = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//button[contains(.,'Confirmar')]")
                )
            )
            driver.execute_script("arguments[0].click();", confirmar_btn)
            print(f"[{step}] OK")
            time.sleep(2)
        except Exception:
            print(f"[{step}] No apareció botón Confirmar (posible reserva directa)")

        driver.quit()
        return {
            "status": "success",
            "message": (
                f"Reserva hecha: {hora_objetivo} ({hora_label}) - {tipo_objetivo} - "
                f"{sede_objetivo} (offset {dias_offset})"
            ),
        }

    except Exception as e:
        try:
            driver.quit()
        except Exception:
            pass
        return {
            "status": "error",
            "message": f"Fallo en paso '{step}': {type(e).__name__} -> {str(e)}",
        }
