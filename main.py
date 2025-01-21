"""
############################
# 1st phase - all in 1 app #
############################
1. flask hello world

2. add other flask endpoints

3. hard code responses

4. look up how to accept only POST (GET is default)

5. return html for GET /
<form method="post" enctype="multipart/form-data" action="/upload" method="post">
  <div>
    <label for="file">Choose file to upload</label>
    <input type="file" id="file" name="form_file" accept="image/jpeg"/>
  </div>
  <div>
    <button>Submit</button>
  </div>
</form>

6. in GET /files return a hardcoded list for initial testing
files = ['file1.jpeg', 'file2.jpeg', 'file3.jpeg']

7. in GET / call the function for GET /files and loop through the list to add to the HTML
GET /
    ...
    for file in list_files():
        index_html += "<li><a href=\"/files/" + file + "\">" + file + "</a></li>"

    return index_html

8. in POST /upload - lookup how to extract uploaded file and save locally to ./files
def upload():
    file = request.files['form_file']  # item name must match name in HTML form
    file.save(os.path.join("./files", file.filename))

    return redirect("/")
#https://flask.palletsprojects.com/en/2.2.x/patterns/fileuploads/

9. in GET /files - look up how to list files in a directory

    files = os.listdir("./files")
    #TODO: filter jpeg only
    return files

10. filter only .jpeg
@app.route('/files')
def list_files():
    files = os.listdir("./files")
    for file in files:
        if not file.endswith(".jpeg"):
            files.remove(file)
    return files
"""
import os
from flask import Flask, redirect, request, send_file
from google.cloud import storage
os.makedirs('files', exist_ok = True)

app = Flask(__name__)
BUCKET_NAME = "cot5930-image-p1"


@app.route('/')
def index():
    index_html="""
<form method="post" enctype="multipart/form-data" action="/upload" method="post">
  <div>
    <label for="file">Choose file to upload</label>
    <input type="file" id="file" name="form_file" accept="image/jpeg"/>
  </div>
  <div>
    <button>Submit</button>
  </div>
</form>"""    

    for file in list_files():
        index_html += "<li><a href=\"/files/" + file + "\">" + file + "</a></li>"

    return index_html

@app.route('/upload', methods=["POST"])
def upload():
    file = request.files['form_file']  # item name must match name in HTML form
    file_path = os.path.join("./files", file.filename)  # Define the file path
    file.save(file_path)  # Save the file locally

    from storage import upload_file
    upload_file(BUCKET_NAME, file_path)  # Upload to the cloud bucket

    return redirect("/")


@app.route('/files')
def list_files():
    from storage import get_list_of_files
    files = get_list_of_files(BUCKET_NAME)
    return files

@app.route('/files/<filename>')
def get_file(filename):
    from storage import download_file
    local_path = os.path.join("./files", filename)
    
    # Check if file exists locally
    if not os.path.exists(local_path):
        # If not, download it from Google Cloud Storage
        download_file(BUCKET_NAME, filename)

    # Serve the file
    if os.path.exists(local_path):
        return send_file(local_path)
    else:
        return "File not found", 404


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)