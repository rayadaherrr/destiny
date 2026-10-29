"""
Environment diagnostic.

Run with:  uv run python check_setup.py

Each FAIL line tells you what is missing and what to do. Work through them
in order.
"""
import sys
import pathlib

ok = True


def check(label, passed, detail=""):
    global ok
    mark = "OK  " if passed else "FAIL"
    print(f"[{mark}] {label}" + (f"  ->  {detail}" if detail else ""))
    if not passed:
        ok = False
    return passed


print("=" * 60)
print("ENVIRONMENT DIAGNOSTIC - Capstone Project")
print("=" * 60)

v = sys.version_info
if not check("Python 3.12 or newer", v >= (3, 12), f"you have {v.major}.{v.minor}.{v.micro}"):
    print("       run: uv python install 3.12 && uv sync")

for mod, name in [("google.genai", "google-genai"), ("dotenv", "python-dotenv"), ("streamlit", "streamlit")]:
    try:
        m = __import__(mod, fromlist=["__version__"])
        check(f"package {name}", True, getattr(m, "__version__", "installed"))
    except ImportError:
        check(f"package {name}", False, "run 'uv sync'")

env = pathlib.Path(__file__).parent / ".env"
check(".env file exists", env.exists(), "copy it from .env.example" if not env.exists() else "")

try:
    import config
except Exception as e:
    check("config.py loads", False, str(e))
    sys.exit(1)

key = config.API_KEY
if not key:
    print("       create a key at aistudio.google.com/apikey and paste it")
    print("       into the GOOGLE_API_KEY line of your .env")
if check("key read from .env", bool(key), "GOOGLE_API_KEY line is empty" if not key else ""):
    if key.startswith("AQ."):
        print("       key type: auth key (the correct one)")
    else:
        print("       key type: standard - standard keys are being retired.")
        print("       Create a new one at aistudio.google.com/apikey")

if key:
    try:
        from google import genai
        client = genai.Client(api_key=key)
        r = client.models.generate_content(model=config.MODEL, contents="Reply with just: ready")
        check("API call", True, f"model {r.model_version}")
        print(f"       response: {r.text.strip()[:60]}")
    except Exception as e:
        check("API call", False, type(e).__name__ + ": " + str(e)[:120])

print("=" * 60)
print("ALL GOOD" if ok else "SOMETHING IS MISSING - see the FAIL lines above")
print("=" * 60)
