from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware

from .config_store import init_db, get_config, save_config
from .booking import run_booking, test_booking


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inicializa la base de datos al arrancar
init_db()


@app.get("/", response_class=HTMLResponse)
async def home():
    config = get_config()
    hora = config["hora_clase"]
    tipo = config["tipo_clase"]
    sede = config["sede"]
    dias_offset = config["dias_offset"]

    tipos_entrenamiento = ["JAB", "SAVAGE", "TONIC", "GIRO", "SOLIDO"]

    sedes = [
        "Alto de Palmas",
        "City Plaza",
        "Intermedia",
        "Viva Envigado",
        "Viva Palmas",
    ]

    # Opciones de días (offset en días desde hoy)
    dias_opciones = [
        (0, "Hoy"),
        (1, "Mañana"),
        (2, "En 2 días"),
        (3, "En 3 días"),
    ]

    def options_html(opciones, valor_actual):
        html = ""
        for op in opciones:
            if isinstance(op, tuple):
                value, label = op
            else:
                value, label = op, op
            sel = "selected" if str(value) == str(valor_actual) else ""
            html += f'<option value="{value}" {sel}>{label}</option>'
        return html

    tipos_html = options_html(tipos_entrenamiento, tipo)
    sedes_html = options_html(sedes, sede)
    dias_html = options_html(dias_opciones, dias_offset)

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>ActionBlack Reservas</title>
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{
                font-family: -apple-system, BlinkMacSystemFont, system-ui, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                padding: 20px;
                display: flex;
                justify-content: center;
                align-items: center;
            }}
            .card {{
                width: 100%;
                max-width: 420px;
                background: #fff;
                border-radius: 24px;
                padding: 28px 24px 32px;
                box-shadow: 0 18px 45px rgba(0,0,0,0.35);
            }}
            .title {{
                display: flex;
                align-items: center;
                gap: 8px;
                margin-bottom: 24px;
                justify-content: center;
                text-align: center;
            }}
            .logo {{
                width: 32px;
                height: 32px;
                border-radius: 50%;
                background: #f97373;
                display: flex;
                align-items: center;
                justify-content: center;
                color: #fff;
                font-weight: 900;
                font-size: 18px;
            }}
            h1 {{
                font-size: 26px;
                line-height: 1.1;
                color: #1f2933;
                font-family: system-ui, -apple-system, BlinkMacSystemFont;
            }}
            .config-actual {{
                margin-bottom: 18px;
                font-size: 14px;
                color: #111827;
            }}
            .config-actual span {{
                font-weight: 600;
            }}
            .field {{
                margin-bottom: 16px;
            }}
            label {{
                display: block;
                font-size: 13px;
                font-weight: 600;
                color: #4b5563;
                margin-bottom: 6px;
            }}
            input[type="time"], select {{
                width: 100%;
                padding: 11px 12px;
                border-radius: 12px;
                border: 2px solid #e5e7eb;
                font-size: 15px;
                outline: none;
                transition: border-color 0.15s ease, box-shadow 0.15s ease;
            }}
            input[type="time"]:focus, select:focus {{
                border-color: #6366f1;
                box-shadow: 0 0 0 1px rgba(99,102,241,0.35);
            }}
            button {{
                width: 100%;
                margin-top: 12px;
                padding: 13px 0;
                border-radius: 14px;
                border: none;
                cursor: pointer;
                font-size: 16px;
                font-weight: 600;
                background: linear-gradient(135deg, #6366f1, #4f46e5);
                color: #fff;
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 8px;
                box-shadow: 0 12px 25px rgba(79,70,229,0.45);
            }}
            button:hover {{
                filter: brightness(1.03);
            }}
            button span.icon {{
                font-size: 18px;
            }}
            #status {{
                margin-top: 14px;
                padding: 10px 12px;
                border-radius: 10px;
                font-size: 13px;
                display: none;
                text-align: center;
                font-weight: 500;
            }}
            #status.ok {{
                background: #dcfce7;
                color: #166534;
            }}
            #status.err {{
                background: #fee2e2;
                color: #991b1b;
            }}
        </style>
    </head>
    <body>
        <div class="card">
            <div class="title">
                <div class="logo">🏋</div>
                <h1>ActionBlack<br>Reservas</h1>
            </div>

            <div class="config-actual">
                <p><strong>Config actual:</strong></p>
                <p>Hora: <span>{hora}</span></p>
                <p>Tipo: <span>{tipo}</span></p>
                <p>Sede: <span>{sede}</span></p>
                <p>Día: <span>{"Hoy" if dias_offset == 0 else ("Mañana" if dias_offset == 1 else f"En {dias_offset} días")}</span></p>
            </div>

            <form id="form">
                <div class="field">
                    <label>Hora de la clase</label>
                    <input type="time" id="hora" value="{hora}">
                </div>

                <div class="field">
                    <label>Tipo de entrenamiento</label>
                    <select id="tipo">
                        {tipos_html}
                    </select>
                </div>

                <div class="field">
                    <label>Sede</label>
                    <select id="sede">
                        {sedes_html}
                    </select>
                </div>

                <div class="field">
                    <label>Día a reservar</label>
                    <select id="dias_offset">
                        {dias_html}
                    </select>
                </div>

                <button type="submit">
                    <span class="icon">💾</span>
                    Guardar configuración y reservar
                </button>
            </form>

            <div id="status"></div>
        </div>

        <script>
        const form = document.getElementById('form');
        const statusBox = document.getElementById('status');

        form.addEventListener('submit', async (e) => {{
            e.preventDefault();
            const hora = document.getElementById('hora').value;
            const tipo = document.getElementById('tipo').value;
            const sede = document.getElementById('sede').value;
            const dias_offset = document.getElementById('dias_offset').value;

            statusBox.style.display = 'block';
            statusBox.className = '';
            statusBox.innerText = 'Guardando configuración...';

            const formData = new FormData();
            formData.append('hora_clase', hora);
            formData.append('tipo_clase', tipo);
            formData.append('sede', sede);
            formData.append('dias_offset', dias_offset);

            try {{
                // 1) Guardar configuración
                const res = await fetch('/api/config', {{
                    method: 'POST',
                    body: formData
                }});
                const data = await res.json();
                if (data.status === 'ok') {{
                    statusBox.className = 'ok';
                    statusBox.innerText = 'Configuración guardada. Ejecutando reserva...';

                    // 2) Ejecutar reserva
                    try {{
                        const resBook = await fetch('/api/booking/test', {{
                            method: 'POST'
                        }});
                        const dataBook = await resBook.json();
                        if (dataBook.status === 'success') {{
                            statusBox.className = 'ok';
                            statusBox.innerText = dataBook.message || 'Reserva realizada correctamente.';
                        }} else {{
                            statusBox.className = 'err';
                            statusBox.innerText = dataBook.message || 'Error al ejecutar la reserva.';
                        }}
                    }} catch (err2) {{
                        console.error(err2);
                        statusBox.className = 'err';
                        statusBox.innerText = 'Error de red al ejecutar la reserva.';
                    }}

                    // Recargar para reflejar la nueva config después de un momento
                    setTimeout(() => window.location.reload(), 1500);
                }} else {{
                    statusBox.className = 'err';
                    statusBox.innerText = 'Error al guardar configuración';
                }}
            }} catch (err) {{
                console.error(err);
                statusBox.className = 'err';
                statusBox.innerText = 'Error de red al guardar configuración';
            }}
        }});
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html)


@app.get("/api/config")
async def api_get_config():
    return get_config()


@app.post("/api/config")
async def api_save_config(
    hora_clase: str = Form(...),
    tipo_clase: str = Form(...),
    sede: str = Form(...),
    dias_offset: int = Form(...),
):
    save_config(hora_clase, tipo_clase, sede, dias_offset)
    return {"status": "ok"}


@app.post("/api/booking/test")
async def api_booking_test():
    """
    Ejecuta run_booking usando la configuración guardada
    y devuelve el dict que retorna booking.run_booking().
    """
    result = run_booking()
    print("RESULTADO BOOKING:", result)  # <- línea nueva para ver el dict en logs

    return result
