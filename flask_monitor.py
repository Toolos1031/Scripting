from flask import Flask, Response, render_template_string
import time
import os

LOG_FILE = r"G:\_Przetwarzanie\processing_log.log"  # Path to your existing log file

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>LAS Processing Monitor</title>
    <meta charset="utf-8" />
    <style>
        body { font-family: monospace; background: #111; color: #0f0; padding: 1em; }
        pre { white-space: pre-wrap; }
    </style>
</head>
<body>
    <h2>LAS Processing Log</h2>
    <pre id="log"></pre>
    <script>
        const log = document.getElementById("log");
        const es = new EventSource("/stream");
        es.onmessage = (event) => {
            log.textContent += event.data + "\\n";
            window.scrollTo(0, document.body.scrollHeight);
        };
    </script>
</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route("/stream")
def stream():
    def generate():
        with open(LOG_FILE, "r") as f:
            f.seek(0, os.SEEK_END)  # Move to end of file
            while True:
                line = f.readline()
                if not line:
                    time.sleep(0.5)
                    continue
                yield f"data: {line.strip()}\n\n"
    return Response(generate(), mimetype="text/event-stream")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, threaded=True)