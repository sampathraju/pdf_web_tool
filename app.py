from flask import Flask, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
import os
import threading
import time
import traceback
import uuid
import shutil
import zipfile

app = Flask(__name__)

# Folder paths
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'output'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# In-memory job tracker
jobs = {}

# Dummy processing function (replace with your real JAR call)
def run_processing(input_pdf_path, output_folder_path):
    time.sleep(5)  # simulate delay
    os.makedirs(output_folder_path, exist_ok=True)
    with open(os.path.join(output_folder_path, "result.txt"), "w") as f:
        f.write("Processing complete.")

# Background worker
def background_task(job_id, input_pdf_path, output_folder_path, zip_output_path):
    try:
        print(f"[{job_id}] Processing started...")
        jobs[job_id]["status"] = "processing"

        run_processing(input_pdf_path, output_folder_path)

        # Create zip of results
        with zipfile.ZipFile(zip_output_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            for root, _, files in os.walk(output_folder_path):
                for f in files:
                    file_path = os.path.join(root, f)
                    arcname = os.path.relpath(file_path, output_folder_path)
                    zipf.write(file_path, arcname)

        jobs[job_id]["status"] = "completed"
        jobs[job_id]["result"] = f"/output/{os.path.basename(zip_output_path)}"
        print(f"[{job_id}] Completed ✅")
    except Exception as e:
        jobs[job_id]["status"] = "error"
        jobs[job_id]["error"] = str(e)
        print(f"[{job_id}] Error ❌ {e}")
        traceback.print_exc()

# Upload route
@app.route("/upload", methods=["POST"])
def upload_file():
    if "pdf_file" not in request.files:
        return jsonify(success=False, message="No file part"), 400

    file = request.files["pdf_file"]
    if file.filename == "":
        return jsonify(success=False, message="No selected file"), 400

    if not file.filename.lower().endswith(".pdf"):
        return jsonify(success=False, message="File is not a PDF"), 400

    try:
        job_id = str(uuid.uuid4())
        original_filename = secure_filename(file.filename)
        unique_filename = f"{job_id}_{original_filename}"

        input_pdf_path = os.path.join(UPLOAD_FOLDER, unique_filename)
        output_folder_path = os.path.join(OUTPUT_FOLDER, job_id)
        zip_output_path = os.path.join(OUTPUT_FOLDER, f"{job_id}.zip")

        file.save(input_pdf_path)

        # Register job
        jobs[job_id] = {"status": "queued"}

        # Start background thread
        thread = threading.Thread(
            target=background_task,
            args=(job_id, input_pdf_path, output_folder_path, zip_output_path)
        )
        thread.start()

        return jsonify(success=True, job_id=job_id)

    except Exception as e:
        traceback.print_exc()
        return jsonify(success=False, message=f"Upload failed: {str(e)}"), 500

# Job status route
@app.route("/status/<job_id>", methods=["GET"])
def check_status(job_id):
    job = jobs.get(job_id)
    if not job:
        return jsonify({"status": "not_found"}), 404
    return jsonify(job)

# Serve completed zip
@app.route("/output/<path:filename>", methods=["GET"])
def serve_output(filename):
    return send_from_directory(OUTPUT_FOLDER, filename, as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True, port=5000)
