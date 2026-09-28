import io, contextlib, sqlite3
from harness import traductor, PROJ
import sys
print("## SQL: nombres de tabla maliciosos en un esquema en memoria")
c = sqlite3.connect(":memory:")
for nombre in ['nivel1_ok', 'nivel1_x"; DROP TABLE nivel1_ok; --', 'nivel1_A', 'otra_tabla']:
    c.execute(f'CREATE TABLE {traductor._identificador_sql(nombre)} (id INTEGER, palabra_frase TEXT, traduccion TEXT, pronunciacion TEXT, significado TEXT)')
    c.execute(f'INSERT INTO {traductor._identificador_sql(nombre)} VALUES (1, "q", "e", "", "")')
print("tablas aceptadas por _tablas_de_vocabulario:", [t[0] for t in traductor._tablas_de_vocabulario(c)])
print("búsqueda con texto malicioso:", traductor.buscar_vocabulario("x'; DROP TABLE nivel1_ok;--", "espanol", c)["encontrado"],
      "| tabla sigue existiendo:", bool(c.execute("select count(*) from nivel1_ok").fetchone()))
print("_identificador_sql('a\"b') =", traductor._identificador_sql('a"b'))

print("\n## Flask: rutas, métodos, cabeceras")
sys.path.insert(0, PROJ)
with contextlib.redirect_stdout(io.StringIO()):
    import web.app as w
for r in w.app.url_map.iter_rules():
    print(" ", r.rule, sorted(r.methods - {"HEAD", "OPTIONS"}))
cl = w.app.test_client()
r = cl.get("/api/status")
print("GET /api/status sin credenciales:", r.status_code, "| cabeceras de seguridad:",
      {h: r.headers.get(h) for h in ("X-Frame-Options", "Content-Security-Policy", "X-Content-Type-Options", "Access-Control-Allow-Origin")})
print("POST /api/status:", cl.post("/api/status").status_code, "| GET /no-existe:", cl.get("/no-existe").status_code)
print("app.debug =", w.app.debug, "| SECRET_KEY configurada:", bool(w.app.config.get("SECRET_KEY")))
