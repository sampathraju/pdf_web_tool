import subprocess
import zipfile
import os
import shutil
import re
from bs4 import BeautifulSoup, Comment

# Constants
JAR_FILE_NAME = "lib_dat.jar"
EXTRACT_DIR = "jar_temp"
ZIP_FILE = "libs.zip"


def run_processing(input_pdf_path, output_folder_path):
    """
    Main pipeline: run Java jar, clean HTML, convert to XHTML.
    """
    
os.makedirs(output_folder_path, exist_ok=True)
    # Step 1: Extract JAR if not already extracted
    os.makedirs(EXTRACT_DIR, exist_ok=True)
    jar_path = os.path.join(EXTRACT_DIR, JAR_FILE_NAME)
    if not os.path.exists(jar_path):
        if not os.path.exists(ZIP_FILE):
            raise FileNotFoundError(f"{ZIP_FILE} not found. Place it beside app.py")
        with zipfile.ZipFile(ZIP_FILE, 'r') as zip_ref:
            zip_ref.extractall(EXTRACT_DIR)

    # Step 2: Run Java tool
    proc = subprocess.run(
        ["java", "-Xms512m", "-jar", jar_path, input_pdf_path, output_folder_path],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    if proc.returncode != 0:
        raise RuntimeError(f"Java failed: {proc.stderr}")

    # Step 3: Organize and clean HTML
    clean_and_organize_output(output_folder_path)

    # Step 4: Convert cleaned HTML to XHTML
    convert_html_to_xhtml_all(output_folder_path)

    # Optional cleanup of jar_temp
    shutil.rmtree(EXTRACT_DIR, ignore_errors=True)


def clean_and_organize_output(output_folder):
    """
    Cleans up extracted HTML files.
    """
    for filename in os.listdir(output_folder):
        if filename.endswith(".html"):
            file_path = os.path.join(output_folder, filename)
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Remove comments
            soup = BeautifulSoup(content, "html.parser")
            for element in soup(text=lambda text: isinstance(text, Comment)):
                element.extract()

            # Remove unwanted tags (example: <script>, <style>)
            for tag in soup(["script", "style"]):
                tag.decompose()

            # Remove empty tags
            for tag in soup.find_all():
                if not tag.text.strip() and not tag.find_all():
                    tag.decompose()

            with open(file_path, "w", encoding="utf-8") as f:
                f.write(str(soup))


def convert_html_to_xhtml_all(output_folder):
    """
    Converts HTML files to XHTML (adds closing tags, fixes nesting).
    """
    for filename in os.listdir(output_folder):
        if filename.endswith(".html"):
            file_path = os.path.join(output_folder, filename)
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Basic XHTML cleanup
            content = re.sub(r"<br>", "<br/>", content)
            content = re.sub(r"<hr>", "<hr/>", content)

            # Parse with lxml for stricter XHTML compliance
            soup = BeautifulSoup(content, "lxml-xml")

            xhtml_path = file_path.replace(".html", ".xhtml")
            with open(xhtml_path, "w", encoding="utf-8") as f:
                f.write(str(soup))
