from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from datetime import datetime
from functools import wraps

app = Flask(__name__)
app.secret_key = "dev-secret-change-this"  # ganti di produksi

# Simulasi database (in-memory). Produksi: pakai SQLite/Postgres.
# Tiap item: {room, sender, ciphertext, iv, ts}
MESSAGES = []

def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "username" not in session or "room" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return wrapper

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        room = request.form.get("room", "").strip()
        # passphrase TIDAK disimpan di server (biar E2EE)
        if not username or not room:
            return render_template("login.html", error="Isi username & room.")
        session["username"] = username
        session["room"] = room
        return redirect(url_for("chat"))
    return render_template("login.html")

@app.route("/chat")
@login_required
def chat():
    return render_template("chat.html", username=session["username"], room=session["room"])

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/server")
def server_view():
    # Halaman admin melihat semua ciphertext
    return render_template("server.html", messages=MESSAGES)

# ---------- API ----------

@app.route("/api/messages", methods=["GET"])
@login_required
def api_messages():
    room = session["room"]
    msgs = [m for m in MESSAGES if m["room"] == room]
    return jsonify({"ok": True, "messages": msgs})

@app.route("/api/send", methods=["POST"])
@login_required
def api_send():
    data = request.get_json(force=True)
    ciphertext = data.get("ciphertext")
    iv = data.get("iv")
    if not ciphertext or not iv:
        return jsonify({"ok": False, "error": "missing ciphertext/iv"}), 400
    MESSAGES.append({
        "room": session["room"],
        "sender": session["username"],
        "ciphertext": ciphertext,
        "iv": iv,
        "ts": datetime.utcnow().isoformat() + "Z"
    })
    return jsonify({"ok": True})

if __name__ == "__main__":
    app.run(debug=True)
