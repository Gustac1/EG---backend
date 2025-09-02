from datetime import datetime
def _ts(): return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
def ok(msg):   print(f"✅ {_ts()} | {msg}")
def warn(msg): print(f"⚠️  {_ts()} | {msg}")
def err(msg):  print(f"🚫 {_ts()} | {msg}")
