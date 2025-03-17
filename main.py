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


BG_COLOR = os.environ.get("BG_COLOR", "white")

app = Flask(__name__)
storage_client = storage.Client()


os.makedirs("files", exist_ok=True)


def generate_title_and_description(local_image_path):
    """
    Sends the local image to the Gemini model with a prompt to return:
      {
        "title":"Short Title",
        "description":"A short 1-2 sentence description."
      }
    If the returned text is not valid JSON, we gracefully degrade.
    """
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
                        "text": """Please generate a short title and also a 1-2 sentence
description of the above image. Return them in valid JSON with
keys "title" and "description" only. Example:
{"title":"Sunset Beach","description":"A beach at sunset..."}"""
                    }
                ]
            }
        ]
    }

    headers = {"Content-Type": "application/json"}
    resp = requests.post(API_URL, headers=headers, json=payload, timeout=60)
    if resp.status_code != 200:
        return {"title": "Unknown Title", "description": f"ERROR: {resp.text}"}

    data = resp.json()
    candidates = data.get("candidates", [])
    if not candidates:
        return {"title": "Unknown Title", "description": "No output from model."}

    first_candidate = candidates[0]
    content = first_candidate.get("content", {})
    parts = content.get("parts", [])
    if not parts:
        return {"title": "Unknown Title", "description": "No text returned by model."}

 
    model_text = parts[0].get("text", "{}").strip()


    try:
        parsed = json.loads(model_text)
        return {
            "title": parsed.get("title", "Untitled"),
            "description": parsed.get("description", "No description provided.")
        }
    except:

        return {
            "title": "Untitled",
            "description": model_text
        }


def list_files():
    """
    Lists all files (under 'files/') in the GCS bucket, returning their names
    without the 'files/' prefix.
    """
    bucket = storage_client.bucket(BUCKET_NAME)
    blobs = bucket.list_blobs(prefix="files/")
    names = []
    for b in blobs:
        if not b.name.endswith("/"):
            names.append(b.name.replace("files/", ""))
    return names

def upload_to_bucket(local_path, blob_name):
    """Upload a local file to 'files/<blob_name>' in the GCS bucket."""
    bucket = storage_client.bucket(BUCKET_NAME)
    blob = bucket.blob(f"files/{blob_name}")
    blob.upload_from_filename(local_path)

def download_from_bucket(blob_name, local_path):
    """Download a file from 'files/<blob_name>' in the GCS bucket to local_path."""
    bucket = storage_client.bucket(BUCKET_NAME)
    blob = bucket.blob(f"files/{blob_name}")
    blob.download_to_filename(local_path)


@app.route("/")
def index():
    """
    Main page: shows the upload form, lists images from the bucket,
    and shows local images. The background color is set by BG_COLOR.
    """
    html = f"""
    <html>
      <body style="background-color:{BG_COLOR};">
        <h2>Upload a JPEG</h2>
        <form method="POST" action="/upload" enctype="multipart/form-data">
          <input type="file" name="form_file" accept="image/jpeg" />
          <button>Upload</button>
        </form>
        <hr>
        <h3>Files in GCS:</h3>
        <ul>
    """


    for fname in list_files():
        if fname.lower().endswith((".jpg", ".jpeg")):
            html += f'<li><a href="/view/{fname}">{fname}</a></li>'
    html += "</ul>"


    html += "<hr><h3>Local Images:</h3><ul>"
    local_dir = "files"
    if os.path.exists(local_dir):
        for fname in os.listdir(local_dir):
            if fname.lower().endswith((".jpg", ".jpeg")):
                html += f'<li><a href="/view_local/{fname}">{fname}</a></li>'
    html += "</ul>"

    html += "</body></html>"
    return html

@app.route("/upload", methods=["POST"])
def upload():
    """
    Receives an uploaded JPEG, saves locally, calls AI to generate title+description,
    then saves that JSON and uploads both the image + JSON to GCS.
    """
    uploaded_file = request.files.get("form_file")
    if not uploaded_file:
        return "No file submitted", 400

    local_path = os.path.join("files", uploaded_file.filename)
    uploaded_file.save(local_path)


    ai_data = generate_title_and_description(local_path)
    ai_title = ai_data.get("title", "Untitled")
    ai_description = ai_data.get("description", "No description.")


    base_name, _ = os.path.splitext(uploaded_file.filename)
    json_name = base_name + ".json"
    json_path = os.path.join("files", json_name)

    with open(json_path, "w") as f:
        json.dump({"title": ai_title, "description": ai_description}, f)


    upload_to_bucket(local_path, uploaded_file.filename)
    upload_to_bucket(json_path, json_name)

    return redirect("/")

@app.route("/view/<filename>")
def view_file(filename):
    """
    Displays an image from GCS (download locally if needed) plus any associated JSON.
    """
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
      <body style="background-color:{BG_COLOR};">
        <h1>{title}</h1>
        <img src="/files/{filename}" style="max-width:400px;"/>
        <p>{description}</p>
        <a href="/">Back</a>
      </body>
    </html>
    """
    return html

@app.route("/view_local/<filename>")
def view_local_file(filename):
    """
    Displays a locally stored image plus any associated JSON metadata.
    """
    local_path = os.path.join("files", filename)
    if not os.path.exists(local_path):
        return "Local file not found.", 404

    base_name, _ = os.path.splitext(filename)
    local_json = os.path.join("files", base_name + ".json")

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
      <body style="background-color:{BG_COLOR};">
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
    """
    Serves a file from the local 'files/' directory. If it doesn't exist,
    attempts to download from GCS.
    """
    local_path = os.path.join("files", filename)
    if not os.path.exists(local_path):
        download_from_bucket(filename, local_path)
    if not os.path.exists(local_path):
        return "File not found", 404
    return send_file(local_path)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
