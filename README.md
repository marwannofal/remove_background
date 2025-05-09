# Background Removal API with FastAPI

A simple FastAPI application that accepts image uploads (JPG, PNG, SVG, etc.), removes their background using [rembg](https://github.com/danielgatis/rembg), and saves the processed images to disk while preserving—or flattening—transparency based on output format.

## Features

* **Supports vector & raster inputs**: Automatically rasterizes SVG at high resolution (300 DPI) or any other common raster formats.
* **Background removal**: Uses U²-Net under the hood via `rembg` for quality subject segmentation.
* **Halo cleanup**: Optional alpha‐thresholding and erosion to eliminate stray “halo” pixels.
* **Preserves extensions**: Outputs in the same format as the input (JPEG, PNG, BMP, TIFF, WEBP), flattening to white for formats that don’t support transparency.
* **Easy integration**: Single `/remove-background/` endpoint with `multipart/form-data` file uploads.

## Prerequisites

* Python 3.8+
* pip

## Installation

1. **Clone the repo**

   ```bash
   git clone https://github.com/marwannofal/remove_background.git
   cd remove_background
   ```

2. **Create and activate a virtual environment**

   ```bash
   python -m venv env
   source env/bin/activate      # Linux/macOS
   env\Scripts\activate       # Windows
   ```

3. **Install dependencies**

   ```bash
   pip install -r req.txt
   ```

   > **requirements.txt** should contain:
   >
   > ```text
   > fastapi
   > uvicorn
   > rembg[cv2]
   > onnxruntime
   > onnxruntime-gpu
   > python-multipart
   > cairosvg
   > pillow
   > ```

## Running the Server

Start the FastAPI server with Uvicorn:

```bash
uvicorn main:app --reload
```

The API will be available at `http://127.0.0.1:8000`.

## API Usage

### Remove Background

* **Endpoint**: `POST /remove-background/`
* **Content-Type**: `multipart/form-data`
* **Form Field**: `file` — the image to process.


#### Response should be like this

```json
{
  "filename": "{uuid}.png",  // or .jpg/.bmp/etc. matching input
  "url": "/processed_images/{uuid}.png"
}
```

* The returned `url` is relative to the server root. You can serve `processed_images/` statically via FastAPI or a reverse proxy (e.g., Nginx).

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

## Acknowledgements

* [FastAPI](https://fastapi.tiangolo.com/)
* [rembg (U²-Net)](https://github.com/danielgatis/rembg)
* [CairoSVG](https://cairosvg.org/)
* [Pillow](https://python-pillow.org/)
