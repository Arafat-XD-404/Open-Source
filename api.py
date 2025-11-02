from flask import Flask, render_template, request, jsonify, send_file
import requests
from io import BytesIO
from zipfile import ZipFile

app = Flask(__name__)

API_KEY = "ymsk_ZOMONKNNqDxpVvhemm4MrukVLUJZZqY4CGIXc1FeItU"
API_URL = "https://yousmind.com/api/image-generator/generate"

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/generate", methods=["POST"])
def generate():
    data = request.form
    prompt = data.get("prompt", "").strip()
    speed = data.get("speed", "fast")
    size = data.get("size", "16")
    n_images = int(data.get("n", 1))

    aspect_map = {"16": "16:9", "1": "1:1", "916": "9:16"}
    aspect_ratio = aspect_map.get(size, "16:9")
    provider = "1.5-Fast" if speed=="fast" else "1.0-Slow"

    # txt ফাইল থেকে prompts
    uploaded_file = request.files.get("file")
    prompts = []
    if uploaded_file:
        content = uploaded_file.read().decode("utf-8").splitlines()
        prompts = [line.strip() for line in content if line.strip()]
    elif prompt:
        prompts = [prompt]
    else:
        return jsonify({"error": "No prompt or file provided"}), 400

    all_image_urls = []
    headers = {"Content-Type": "application/json", "X-API-Key": API_KEY}

    for p in prompts:
        payload = {"prompt": p, "aspect_ratio": aspect_ratio, "provider": provider, "n": n_images}
        try:
            resp = requests.post(API_URL, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
            if "image_urls" in data:
                all_image_urls.extend(data["image_urls"])
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    return jsonify({"image_urls": all_image_urls, "zip_available": True})

@app.route("/download_zip", methods=["GET"])
def download_zip():
    urls = request.args.getlist("url")
    if not urls:
        return "No images to zip", 400

    zip_buffer = BytesIO()
    with ZipFile(zip_buffer, "w") as zipf:
        for idx, img_url in enumerate(urls):
            r = requests.get(img_url)
            r.raise_for_status()
            zipf.writestr(f"image_{idx+1}.png", r.content)
    zip_buffer.seek(0)
    return send_file(zip_buffer, mimetype='application/zip', as_attachment=True, download_name="images.zip")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8019, debug=True)
