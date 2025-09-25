from flask import Flask, render_template, request, send_file
import os
import tempfile
import shutil
import subprocess
from werkzeug.utils import secure_filename
import zipfile

app = Flask(__name__)

JAR_FILE = os.path.join("libs", "lib_dat.jar")

def run_processing(input_pdf_path, output_folder):
    os.makedirs(output_folder, exist_ok=True)
    
    # Call the Java extractor
    try:
        subprocess.check_call([
            "java", "-Xms512m", "-jar", JAR_FILE, input_pdf_path, output_folder
        ])
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Java processing failed: {e}")

@app.route("/", methods=["GET", "POST"])
def index():
    message = None
    if request.method == "POST":
        if "pdf_file" not in request.files:
            message = "No file uploaded."
            return render_template("index.html", message=message)

        file = request.files["pdf_file"]
        if file.filename == "":
            message = "No file selected."
            return render_template("index.html", message=message)

        temp_dir = tempfile.mkdtemp()
        try:
            pdf_filename = secure_filename(file.filename)
            input_pdf_path = os.path.join(temp_dir, pdf_filename)
            file.save(input_pdf_path)

            output_folder = os.path.join(temp_dir, "output")
            run_processing(input_pdf_path, output_folder)

            zip_path = os.path.join(temp_dir, "output.zip")
            shutil.make_archive(zip_path.replace(".zip",""), 'zip', output_folder)

            return send_file(zip_path, as_attachment=True, download_name="output.zip")

        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    return render_template("index.html", message=message)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
