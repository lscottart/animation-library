"""Start the app on :3020 (dev or prod), run suites against it, then stop it.
APP_ROOT=/path/to/app python suites/run.py dev|prod "harness.py split tuned" "split_react.py" ...
(prod expects `npx next build` to have run.)"""
import os
import signal
import subprocess
import sys
import time
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))  # the suites
APP = os.environ.get("APP_ROOT")  # the Next.js app to serve
if not APP:
    raise SystemExit("set APP_ROOT to the Next.js app with the fixtures in it")
mode, scripts = sys.argv[1], sys.argv[2:]
log = open(os.path.join(HERE, f"server-{mode}.log"), "w")
server = subprocess.Popen(f"npx next {'dev' if mode == 'dev' else 'start'} -p 3020", cwd=APP, shell=True, stdout=log, stderr=log,
                          start_new_session=os.name != "nt")
try:
    t0 = time.time()
    while True:
        try:
            urllib.request.urlopen("http://localhost:3020/", timeout=60)
            break
        except Exception:
            if time.time() - t0 > 180:
                raise SystemExit("server didn't come up")
            time.sleep(1)
    print(f"[{mode} server for {os.path.basename(APP)} up in {time.time() - t0:.0f}s]", flush=True)
    for s in scripts:
        print(f"\n##### {s}  ({mode})", flush=True)
        subprocess.run([sys.executable, os.path.join(HERE, s.split()[0]), *s.split()[1:]], cwd=HERE)
finally:
    # stop the server and its children (npx starts node under a shell)
    if os.name == "nt":
        subprocess.run(["taskkill", "/PID", str(server.pid), "/T", "/F"], capture_output=True)
    else:
        os.killpg(server.pid, signal.SIGTERM)
