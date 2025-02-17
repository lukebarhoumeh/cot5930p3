import os
import json
import base64
import requests

from flask import Flask, request, redirect, send_file
from google.cloud import storage


API_KEY = os.environ.get("GENAI_API_KEY") 
MODEL_ID = "gemini-1.5-pro-002"
BUCKET_NAME = "cot5930-image-p1"

API_URL = f"https://generativelanguage.googleapis.com/v1/models/{MODEL_ID}:generateContent?key={API_KEY}"

app = Flask(__name__)
storage_client = storage.Client()
os.makedirs("files", exist_ok=True)

def generate_image_description(local_image_path):
    with open(local_image_path, "rb") as f:
        raw = f.read()
    b64_str = base64.b64encode(raw).decode("utf-8")

    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "inline_data": {
                            "mime_type": "image/jpeg",
                            "data": b64_str
                        }
                    },
                    {
                        "text": "Please provide a short 1-2 sentence description of the above image."
                    }
                ]
            }
        ]
    }

    headers = {"Content-Type": "application/json"}
    resp = requests.post(API_URL, headers=headers, json=payload, timeout=60)
    if resp.status_code != 200:
        return f"ERROR calling Gemini: {resp.text}"

    data = resp.json()
    candidates = data.get("candidates", [])
    if not candidates:
        return "No candidates returned."

    first_candidate = candidates[0]
    content = first_candidate.get("content", {})
    parts = content.get("parts", [])
    if not parts:
        return "No text in the candidate output."

    description = ""
    for p in parts:
        description += p.get("text", "")

    return description.strip()

def list_files():
    bucket = storage_client.bucket(BUCKET_NAME)
    blobs = bucket.list_blobs(prefix="files/")
    names = []
    for b in blobs:
        if not b.name.endswith("/"):
            names.append(b.name.replace("files/", ""))
    return names

def upload_to_bucket(local_path, blob_name):
    bucket = storage_client.bucket(BUCKET_NAME)
    blob = bucket.blob(f"files/{blob_name}")
    blob.upload_from_filename(local_path)

def download_from_bucket(blob_name, local_path):
    bucket = storage_client.bucket(BUCKET_NAME)
    blob = bucket.blob(f"files/{blob_name}")
    blob.download_to_filename(local_path)

@app.route("/")
def index():
    html = """
    <html><body>
    <h2>Upload a JPEG</h2>
    <form method="POST" action="/upload" enctype="multipart/form-data">
      <input type="file" name="form_file" accept="image/jpeg"/>
      <button>Upload</button>
    </form>
    <hr>
    <h3>Files in GCS:</h3>
    <ul>
    """
    for fname in list_files():
        if fname.lower().endswith((".jpg", ".jpeg")):
            html += f'<li><a href="/view/{fname}">{fname}</a></li>'
    html += "</ul></body></html>"
    return html

@app.route("/upload", methods=["POST"])
def upload():
    uploaded_file = request.files.get("form_file")
    if not uploaded_file:
        return "No file submitted", 400

    local_path = os.path.join("files", uploaded_file.filename)
    uploaded_file.save(local_path)

    description = generate_image_description(local_path)

    base_name, _ = os.path.splitext(uploaded_file.filename)
    json_name = base_name + ".json"
    json_path = os.path.join("files", json_name)
    with open(json_path, "w") as f:
        json.dump({"title": uploaded_file.filename, "description": description}, f)

    upload_to_bucket(local_path, uploaded_file.filename)
    upload_to_bucket(json_path, json_name)

    return redirect("/")

@app.route("/view/<filename>")
def view_file(filename):
    local_img = os.path.join("files", filename)
    if not os.path.exists(local_img):
        download_from_bucket(filename, local_img)

    base_name, _ = os.path.splitext(filename)
    local_json = os.path.join("files", base_name + ".json")
    if not os.path.exists(local_json):
        download_from_bucket(base_name + ".json", local_json)

    title = filename
    description = "No description found."
    if os.path.exists(local_json):
        with open(local_json, "r") as f:
            data = json.load(f)
            title = data.get("title", title)
            description = data.get("description", description)

    html = f"""
    <html>
    <head><title>{title}</title></head>
    <body>
      <h1>{title}</h1>
      <img src="/files/{filename}" style="max-width:400px;"/>
      <p>{description}</p>
      <a href="/">Back</a>
    </body>
    </html>
    """
    return html

@app.route("/files/<filename>")
def serve_file(filename):
    local_path = os.path.join("files", filename)
    if not os.path.exists(local_path):
        download_from_bucket(filename, local_path)
    if not os.path.exists(local_path):
        return "File not found", 404
    return send_file(local_path)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=True)
