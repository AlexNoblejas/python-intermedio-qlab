"""
Chequeo previo — Tarea 1. Corre esto ANTES que los notebooks:
    python 00_verificar_entorno.py

En 30 segundos te dice si falta algo, en vez de que te enteres a los 20 minutos
de scraping o a mitad del entrenamiento.
"""
import importlib, json, socket, sys, urllib.request

OK, AVISO, MAL = "[ OK ]", "[AVISO]", "[ MAL ]"
problemas, avisos = [], []

def head(t):
    print(f"\n{'-' * 62}\n{t}\n{'-' * 62}")

# ---------------------------------------------------------------- Python
head("1. Python")
v = sys.version_info
print(f"  Version   : {sys.version.split()[0]}")
print(f"  Ejecutable: {sys.executable}")
if v < (3, 9):
    problemas.append("Python 3.9+ requerido")
    print(f"  {MAL} demasiado antiguo")
elif v >= (3, 13):
    avisos.append("Python 3.13+ puede no tener ruedas de torch todavia")
    print(f"  {AVISO} muy nuevo para torch; 3.10-3.12 es lo seguro")
else:
    print(f"  {OK}")

# ---------------------------------------------------------------- paquetes
head("2. Paquetes")
REQUERIDOS = {
    "requests": "requests", "bs4": "beautifulsoup4", "lxml": "lxml",
    "pandas": "pandas", "numpy": "numpy", "plotly": "plotly",
    "matplotlib": "matplotlib", "seaborn": "seaborn",
    "sklearn": "scikit-learn", "torch": "torch",
    "transformers": "transformers", "datasets": "datasets",
    "accelerate": "accelerate", "streamlit": "streamlit",
}
faltan = []
for modulo, paquete in REQUERIDOS.items():
    try:
        m = importlib.import_module(modulo)
        print(f"  {OK} {paquete:18s} {getattr(m, '__version__', '?')}")
    except ImportError:
        print(f"  {MAL} {paquete:18s} NO INSTALADO")
        faltan.append(paquete)
if faltan:
    problemas.append("pip install " + " ".join(faltan))

# ---------------------------------------------------------------- GPU
head("3. Aceleracion por hardware")
try:
    import torch
    if torch.cuda.is_available():
        p = torch.cuda.get_device_properties(0)
        print(f"  {OK} CUDA — {p.name} ({p.total_memory/1e9:.1f} GB VRAM)")
        print(f"       torch {torch.__version__} / CUDA {torch.version.cuda}")
        if p.total_memory / 1e9 < 4:
            avisos.append("Menos de 4 GB de VRAM: baja el batch de 16 a 8 si da OutOfMemory")
    elif getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
        print(f"  {OK} MPS (Apple Silicon)")
    else:
        print(f"  {AVISO} sin GPU: el entrenamiento correra en CPU (20-40 min)")
        if "+cpu" in torch.__version__:
            print(f"       torch esta instalado en version SOLO CPU ({torch.__version__}).")
            print(f"       Si tienes NVIDIA, reinstalalo con:")
            print(f"         pip uninstall -y torch")
            print(f"         pip install torch --index-url https://download.pytorch.org/whl/cu124")
            avisos.append("torch instalado sin soporte CUDA pese a tener GPU NVIDIA")
except ImportError:
    print(f"  {MAL} torch no instalado, no se puede comprobar")

# ---------------------------------------------------------------- Ollama
head("4. Ollama (etiquetado con LLM)")
try:
    with urllib.request.urlopen("http://localhost:11434/api/tags", timeout=8) as r:
        modelos = [m["name"] for m in json.load(r).get("models", [])]
    if modelos:
        print(f"  {OK} respondiendo. Modelos: {', '.join(modelos)}")
        utiles = [m for m in modelos
                  if any(m.startswith(p) for p in ("qwen", "llama", "gemma", "mistral", "phi"))]
        if not utiles:
            avisos.append("Ninguno de tus modelos de Ollama es de texto general: ollama pull qwen2.5:7b")
            print(f"  {AVISO} ninguno sirve para clasificar texto")
    else:
        print(f"  {AVISO} corriendo pero sin modelos: ollama pull qwen2.5:7b")
        problemas.append("ollama pull qwen2.5:7b")
except Exception as e:
    print(f"  {MAL} no responde en localhost:11434 ({type(e).__name__})")
    print(f"       Abre otra terminal y deja corriendo:  ollama serve")
    problemas.append("Levantar Ollama (ollama serve) y descargar qwen2.5:7b")

# ---------------------------------------------------------------- red
head("5. Red")
for nombre, url in [
    ("La Republica (RSS)", "https://larepublica.pe/rss/politica.xml"),
    ("El Comercio (RSS)",  "https://elcomercio.pe/arc/outboundfeeds/google-news-feed/category/politica/?outputType=xml"),
    ("Hugging Face",       "https://huggingface.co"),
]:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "TareaAcademica/1.0"})
        with urllib.request.urlopen(req, timeout=20) as r:
            print(f"  {OK} {nombre:22s} HTTP {r.status}")
    except Exception as e:
        print(f"  {MAL} {nombre:22s} {type(e).__name__}: {e}")
        problemas.append(f"Sin acceso a {nombre}")

# ---------------------------------------------------------------- veredicto
head("VEREDICTO")
if problemas:
    print("  Resuelve esto antes de empezar:")
    for p in problemas:
        print(f"    - {p}")
else:
    print("  Todo listo. Puedes abrir 01_recoleccion.ipynb.")
if avisos:
    print("\n  Avisos (no bloquean, pero tenlos presentes):")
    for a in avisos:
        print(f"    - {a}")
print()
sys.exit(1 if problemas else 0)
