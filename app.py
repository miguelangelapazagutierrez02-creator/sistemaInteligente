"""
TuriSafe - Mapeo Inteligente de Zonas de Riesgo para Turistas
Sistema web para la protección del turista en La Paz, Bolivia
Proyecto: Build with AI · GDG La Paz
Base de datos: SQLite
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for, session, make_response
from datetime import datetime
import os, hashlib, sqlite3

app = Flask(__name__)
app.secret_key = "turisafe_emi_2026_lapaz"

DB_FILE = "data/turisafe.db"

# ─── CONEXIÓN ────────────────────────────────────────────────────────────────

def get_db():
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

# ─── INICIALIZAR TABLAS Y DATOS ──────────────────────────────────────────────

def init_db():
    conn = get_db()
    c = conn.cursor()

    c.executescript("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre         TEXT    NOT NULL,
            email          TEXT    NOT NULL UNIQUE,
            password       TEXT    NOT NULL,
            rol            TEXT    NOT NULL DEFAULT 'turista',
            activo         INTEGER NOT NULL DEFAULT 1,
            fecha_registro TEXT    NOT NULL
        );

        CREATE TABLE IF NOT EXISTS casos (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            tipo         TEXT    NOT NULL,
            zona         TEXT    NOT NULL,
            lat          REAL    NOT NULL DEFAULT -16.5,
            lng          REAL    NOT NULL DEFAULT -68.15,
            descripcion  TEXT,
            fecha        TEXT    NOT NULL,
            hora         TEXT,
            nivel_riesgo TEXT    NOT NULL DEFAULT 'medio',
            nacionalidad TEXT,
            estado       TEXT    NOT NULL DEFAULT 'revision',
            reportado_por INTEGER REFERENCES usuarios(id)
        );

        CREATE TABLE IF NOT EXISTS zonas_riesgo (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre    TEXT NOT NULL,
            lat       REAL NOT NULL,
            lng       REAL NOT NULL,
            nivel     TEXT NOT NULL,
            casos_mes INTEGER NOT NULL DEFAULT 0,
            radio     INTEGER NOT NULL DEFAULT 200
        );
    """)

    # Insertar datos solo si las tablas están vacías
    if not c.execute("SELECT 1 FROM usuarios LIMIT 1").fetchone():
        h = lambda p: hashlib.sha256(p.encode()).hexdigest()
        c.executemany(
            "INSERT INTO usuarios (nombre,email,password,rol,activo,fecha_registro) VALUES (?,?,?,?,?,?)",
            [
                ("Administrador TuriSafe", "admin@turisafe.bo",   h("admin123"),   "admin",   1, "2026-01-15"),
                ("Policía Turística La Paz","policia@turisafe.bo", h("policia123"), "policia", 1, "2026-01-20"),
                ("Turista Demo",            "turista@demo.com",    h("turista123"), "turista", 1, "2026-05-01"),
            ]
        )

    if not c.execute("SELECT 1 FROM zonas_riesgo LIMIT 1").fetchone():
        c.executemany(
            "INSERT INTO zonas_riesgo (nombre,lat,lng,nivel,casos_mes,radio) VALUES (?,?,?,?,?,?)",
            [
                ("Mercado Rodríguez", -16.4955, -68.1385, "alto",  47, 300),
                ("Cementerio General",-16.4890, -68.1450, "alto",  31, 250),
                ("Plaza Mayor",       -16.4997, -68.1337, "medio", 18, 200),
                ("Zona Sur",          -16.5150, -68.1300, "medio", 12, 220),
                ("Sopocachi",         -16.5080, -68.1190, "bajo",   5, 280),
                ("Miraflores",        -16.5020, -68.1100, "bajo",   4, 200),
            ]
        )

    if not c.execute("SELECT 1 FROM casos LIMIT 1").fetchone():
        c.executemany(
            "INSERT INTO casos (tipo,zona,lat,lng,descripcion,fecha,hora,nivel_riesgo,nacionalidad,estado,reportado_por) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            [
                ("Robo de celular",  "Mercado Rodríguez",  -16.4955,-68.1385,"Turista argentino reporta robo de celular en la entrada del mercado.", "2026-05-24","14:20","alto", "Argentina",     "validado", 2),
                ("Hurto de cartera", "Plaza Mayor",        -16.4997,-68.1337,"Turista chilena reporta hurto de cartera mientras fotografiaba la catedral.","2026-05-24","11:05","medio","Chile",    "revision", 3),
                ("Asalto",           "Cementerio General", -16.4890,-68.1450,"Turista europeo reporta asalto a mano armada cerca del cementerio.",   "2026-05-23","18:40","alto", "Alemania",      "validado", 2),
                ("Robo de cámara",   "Sopocachi",          -16.5080,-68.1190,"Turista estadounidense reporta robo de cámara fotográfica.",            "2026-05-23","09:15","bajo", "Estados Unidos","revision", 3),
            ]
        )

    conn.commit()
    conn.close()

# ─── HELPERS ─────────────────────────────────────────────────────────────────

def row_to_dict(row):
    if row is None:
        return None
    return dict(row)

def rows_to_list(rows):
    return [dict(r) for r in rows]

# ─── MÓDULO 1: GESTIÓN DE USUARIOS ──────────────────────────────────────────

VISITANTE = {"id": 0, "nombre": "Visitante", "email": "", "rol": "visitante"}

@app.route("/")
def index():
    return redirect(url_for("mapa"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password_hash = hashlib.sha256(request.form.get("password","").encode()).hexdigest()

        conn = get_db()
        usuario = row_to_dict(conn.execute(
            "SELECT * FROM usuarios WHERE email=? AND password=? AND activo=1",
            (email, password_hash)
        ).fetchone())
        conn.close()

        if usuario:
            session["usuario"] = {
                "id":     usuario["id"],
                "nombre": usuario["nombre"],
                "email":  usuario["email"],
                "rol":    usuario["rol"]
            }
            return redirect(url_for("mapa"))
        return render_template("login.html", error="Credenciales incorrectas.")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/registro", methods=["POST"])
def registro():
    nombre    = request.form.get("nombre","").strip()
    email     = request.form.get("email","").strip().lower()
    password  = request.form.get("password","")
    password2 = request.form.get("password2","")
    rol       = request.form.get("rol","turista")

    if not nombre or not email or not password:
        return render_template("login.html", registro_error="Completa todos los campos.")
    if len(password) < 6:
        return render_template("login.html", registro_error="La contraseña debe tener al menos 6 caracteres.")
    if password != password2:
        return render_template("login.html", registro_error="Las contraseñas no coinciden.")
    if rol not in ("turista","policia"):
        return render_template("login.html", registro_error="Rol no permitido.")

    conn = get_db()
    existe = conn.execute("SELECT 1 FROM usuarios WHERE email=?", (email,)).fetchone()
    if existe:
        conn.close()
        return render_template("login.html", registro_error="Ese correo ya está registrado.")

    conn.execute(
        "INSERT INTO usuarios (nombre,email,password,rol,activo,fecha_registro) VALUES (?,?,?,?,1,?)",
        (nombre, email, hashlib.sha256(password.encode()).hexdigest(), rol, datetime.now().strftime("%Y-%m-%d"))
    )
    conn.commit()
    conn.close()
    return render_template("login.html", registro_ok=True)


@app.route("/usuarios")
def usuarios():
    if "usuario" not in session or session["usuario"]["rol"] != "admin":
        return redirect(url_for("login"))
    conn = get_db()
    lista = rows_to_list(conn.execute("SELECT * FROM usuarios ORDER BY id").fetchall())
    conn.close()
    return render_template("usuarios.html", usuarios=lista, user=session["usuario"])


@app.route("/usuarios/crear", methods=["POST"])
def crear_usuario():
    if "usuario" not in session or session["usuario"]["rol"] != "admin":
        return jsonify({"error": "Sin permisos"}), 403

    nombre   = request.form["nombre"]
    email    = request.form["email"].strip().lower()
    password = hashlib.sha256(request.form["password"].encode()).hexdigest()
    rol      = request.form["rol"]

    conn = get_db()
    if conn.execute("SELECT 1 FROM usuarios WHERE email=?", (email,)).fetchone():
        conn.close()
        return jsonify({"error": "El email ya está registrado"}), 400

    conn.execute(
        "INSERT INTO usuarios (nombre,email,password,rol,activo,fecha_registro) VALUES (?,?,?,?,1,?)",
        (nombre, email, password, rol, datetime.now().strftime("%Y-%m-%d"))
    )
    conn.commit()
    conn.close()
    return redirect(url_for("usuarios"))


@app.route("/usuarios/<int:uid>/toggle", methods=["POST"])
def toggle_usuario(uid):
    if "usuario" not in session or session["usuario"]["rol"] != "admin":
        return jsonify({"error": "Sin permisos"}), 403
    conn = get_db()
    conn.execute("UPDATE usuarios SET activo = 1 - activo WHERE id=?", (uid,))
    conn.commit()
    conn.close()
    return redirect(url_for("usuarios"))


# ─── MÓDULO 2: REGISTRO DE CASOS ────────────────────────────────────────────

@app.route("/casos")
def casos():
    if "usuario" not in session:
        return redirect(url_for("login"))

    conn = get_db()
    if session["usuario"]["rol"] == "turista":
        lista = rows_to_list(conn.execute(
            "SELECT * FROM casos WHERE reportado_por=? ORDER BY id DESC",
            (session["usuario"]["id"],)
        ).fetchall())
    else:
        lista = rows_to_list(conn.execute("SELECT * FROM casos ORDER BY id DESC").fetchall())

    usuarios_map = {r["id"]: r["email"] for r in conn.execute("SELECT id, email FROM usuarios").fetchall()}
    conn.close()
    return render_template("casos.html", casos=lista, user=session["usuario"], usuarios_map=usuarios_map)


@app.route("/casos/nuevo", methods=["GET","POST"])
def nuevo_caso():
    if "usuario" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        tipo  = request.form.get("tipo","")
        zona  = request.form.get("zona","")
        nivel = clasificar_riesgo(tipo, zona)

        conn = get_db()
        conn.execute(
            """INSERT INTO casos
               (tipo,zona,lat,lng,descripcion,fecha,hora,nivel_riesgo,nacionalidad,estado,reportado_por)
               VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
            (
                tipo, zona,
                float(request.form.get("lat", -16.5)),
                float(request.form.get("lng", -68.15)),
                request.form.get("descripcion",""),
                request.form.get("fecha", datetime.now().strftime("%Y-%m-%d")),
                request.form.get("hora",""),
                nivel,
                request.form.get("nacionalidad",""),
                "revision",
                session["usuario"]["id"]
            )
        )
        # Actualizar casos_mes de la zona
        conn.execute(
            "UPDATE zonas_riesgo SET casos_mes = casos_mes + 1 WHERE nombre=?", (zona,)
        )
        conn.commit()
        conn.close()
        return redirect(url_for("casos"))

    return render_template("nuevo_caso.html", user=session["usuario"])


@app.route("/casos/<int:cid>/estado", methods=["POST"])
def cambiar_estado(cid):
    if "usuario" not in session or session["usuario"]["rol"] == "turista":
        return jsonify({"error": "Sin permisos"}), 403
    conn = get_db()
    conn.execute("UPDATE casos SET estado=? WHERE id=?",
                 (request.form.get("estado","revision"), cid))
    conn.commit()
    conn.close()
    return redirect(url_for("casos"))


def clasificar_riesgo(tipo, zona):
    tipos_alto  = ["Asalto","Robo a mano armada","Secuestro exprés"]
    tipos_medio = ["Robo de celular","Robo de cartera","Robo de cámara"]
    zonas_alto  = ["Mercado Rodríguez","Cementerio General","El Alto"]
    if tipo in tipos_alto or zona in zonas_alto:
        return "alto"
    elif tipo in tipos_medio:
        return "medio"
    return "bajo"


# ─── MÓDULO 3: MAPA ─────────────────────────────────────────────────────────

@app.route("/mapa")
def mapa():
    user = session.get("usuario", VISITANTE)
    conn = get_db()
    zonas = rows_to_list(conn.execute("SELECT * FROM zonas_riesgo ORDER BY casos_mes DESC").fetchall())
    conn.close()
    return render_template("mapa.html", zonas=zonas, user=user)


@app.route("/api/zonas")
def api_zonas():
    conn = get_db()
    filtro = request.args.get("nivel")
    if filtro:
        zonas = rows_to_list(conn.execute("SELECT * FROM zonas_riesgo WHERE nivel=?", (filtro,)).fetchall())
    else:
        zonas = rows_to_list(conn.execute("SELECT * FROM zonas_riesgo").fetchall())
    conn.close()
    return jsonify(zonas)

@app.route("/visitante")
def modo_visitante():
    """Permite explorar como visitante sin cuenta."""
    session.pop("usuario", None)
    return redirect(url_for("mapa"))


@app.route("/api/casos")
def api_casos():
    conn = get_db()
    # Solo casos validados para visitantes
    if session.get("usuario", {}).get("rol") in ("admin","policia","turista"):
        lista = rows_to_list(conn.execute("SELECT * FROM casos").fetchall())
    else:
        lista = rows_to_list(conn.execute("SELECT * FROM casos WHERE estado='validado'").fetchall())
    conn.close()
    return jsonify(lista)


# ─── MÓDULO 4: ESTADÍSTICAS ──────────────────────────────────────────────────

def filter_casos_db(conn, filtros):
    query  = "SELECT * FROM casos WHERE 1=1"
    params = []
    if filtros.get("fecha_desde"):
        query += " AND fecha >= ?"; params.append(filtros["fecha_desde"])
    if filtros.get("fecha_hasta"):
        query += " AND fecha <= ?"; params.append(filtros["fecha_hasta"])
    if filtros.get("tipo"):
        query += " AND tipo = ?";   params.append(filtros["tipo"])
    if filtros.get("zona"):
        query += " AND zona LIKE ?"; params.append(f"%{filtros['zona']}%")
    return rows_to_list(conn.execute(query, params).fetchall())


@app.route("/estadisticas", methods=["GET","POST"])
def estadisticas():
    if "usuario" not in session:
        return redirect(url_for("login"))
    if session["usuario"]["rol"] == "turista":
        return redirect(url_for("mapa"))

    filtros = {
        "fecha_desde": request.values.get("fecha_desde","").strip(),
        "fecha_hasta": request.values.get("fecha_hasta","").strip(),
        "tipo":        request.values.get("tipo","").strip(),
        "zona":        request.values.get("zona","").strip(),
    }

    error = None
    no_data_message = None
    conn = get_db()

    try:
        if filtros["fecha_desde"] and filtros["fecha_hasta"] and filtros["fecha_desde"] > filtros["fecha_hasta"]:
            raise ValueError("El rango de fechas es incorrecto.")
        casos = filter_casos_db(conn, filtros)
    except ValueError as e:
        error = str(e)
        casos = rows_to_list(conn.execute("SELECT * FROM casos").fetchall())

    stats = {
        "total":       len(casos),
        "alto":        sum(1 for c in casos if c["nivel_riesgo"] == "alto"),
        "medio":       sum(1 for c in casos if c["nivel_riesgo"] == "medio"),
        "bajo":        sum(1 for c in casos if c["nivel_riesgo"] == "bajo"),
        "validados":   sum(1 for c in casos if c["estado"] == "validado"),
        "en_revision": sum(1 for c in casos if c["estado"] == "revision"),
    }

    por_zona = {}
    for c in casos:
        por_zona[c["zona"]] = por_zona.get(c["zona"], 0) + 1
    por_zona = sorted(por_zona.items(), key=lambda x: x[1], reverse=True)

    por_tipo = {}
    for c in casos:
        por_tipo[c["tipo"]] = por_tipo.get(c["tipo"], 0) + 1
    por_tipo = sorted(por_tipo.items(), key=lambda x: x[1], reverse=True)

    conn.close()

    if not error and len(casos) == 0 and any(filtros.values()):
        no_data_message = "No existen datos para los criterios seleccionados."

    return render_template("estadisticas.html",
        stats=stats, por_zona=por_zona, por_tipo=por_tipo,
        user=session["usuario"], filtros=filtros,
        error=error, no_data_message=no_data_message,
        now=datetime.now().strftime("%Y-%m-%d %H:%M"))


@app.route("/api/exportar/<formato>")
def exportar(formato):
    if "usuario" not in session:
        return jsonify({"error": "No autenticado"}), 401

    filtros = {
        "fecha_desde": request.args.get("fecha_desde","").strip(),
        "fecha_hasta": request.args.get("fecha_hasta","").strip(),
        "tipo":        request.args.get("tipo","").strip(),
        "zona":        request.args.get("zona","").strip(),
    }

    conn = get_db()
    try:
        casos = filter_casos_db(conn, filtros)
    except ValueError as e:
        conn.close()
        return jsonify({"error": str(e)}), 400
    conn.close()

    if formato == "json":
        return jsonify({
            "reporte": "TuriSafe - Reporte de Incidentes",
            "fecha_generacion": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "total_casos": len(casos),
            "casos": casos
        })

    content = (
        f"TuriSafe - Reporte ({formato.upper()})\n"
        f"Generado: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
        f"Total: {len(casos)}\n\n"
        + "\n".join([f"{c['fecha']} - {c['tipo']} - {c['zona']}" for c in casos])
    )
    response = make_response(content)
    response.headers["Content-Type"] = "application/octet-stream"
    response.headers["Content-Disposition"] = f"attachment; filename=turisafe_reporte.txt"
    return response


# ─── PUNTO DE ENTRADA ────────────────────────────────────────────────────────

if __name__ == "__main__":
    init_db()
    print("=" * 55)
    print("  TuriSafe - Mapeo Inteligente de Zonas de Riesgo")
    print("  Build with AI · GDG La Paz · Bolivia")
    print("  Base de datos: SQLite →  data/turisafe.db")
    print("=" * 55)
    print()
    print("  Usuarios de prueba:")
    print("  Admin   → admin@turisafe.bo   / admin123")
    print("  Policía → policia@turisafe.bo / policia123")
    print("  Turista → turista@demo.com    / turista123")
    print()
    print("  Abre tu navegador en: http://localhost:5000")
    print("=" * 55)
    app.run(debug=True, port=5000)
