import traceback
try:
    import importlib
    importlib.invalidate_caches()
    import app.core.services as services
    print('Imported app.core.services OK')
    names = [n for n in dir(services) if n in ('suggest_ticket','suggest_priority','summarize_text','draft_response','send_notification')]
    print('Found symbols:', names)
except Exception:
    traceback.print_exc()