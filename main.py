from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import JSONResponse
import os
import uuid
from PIL import Image, ImageFilter
from rembg import remove
import cairosvg
from io import BytesIO

app = FastAPI()

# Directory to save the processed images
OUTPUT_DIR = "processed_images"
os.makedirs(OUTPUT_DIR, exist_ok=True)

@app.post("/remove-background/")
async def remove_background(file: UploadFile = File(...)):
    """
    Accept an uploaded image (any extension), remove its background,
    perform a quick alpha‐cleanup to drop halos, and save using
    the same extension in OUTPUT_DIR.
    """
    # 1) Read upload bytes
    data = await file.read()
    original_ext = os.path.splitext(file.filename)[1].lower()

    # 2) Rasterize SVG at higher resolution, or pass through other formats
    if original_ext == ".svg":
        try:
            img_bytes = cairosvg.svg2png(
                bytestring=data,
                dpi=300,            # ↑ higher resolution (default is 96)
            )
            target_ext = ".png"
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"SVG rasterization failed: {e}")
    else:
        img_bytes = data
        if original_ext in {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".webp"}:
            target_ext = original_ext
        else:
            target_ext = ".png"

    # 3) Run background removal
    try:
        result_bytes = remove(img_bytes)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Background removal failed: {e}")

    # 4) Load into PIL (always a PNG with alpha)
    try:
        img = Image.open(BytesIO(result_bytes))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse model output as image: {e}")

    # 4.5) Clean up any residual “halo” by thresholding + eroding the alpha channel
    if img.mode == "RGBA":
        alpha = img.split()[-1]
        # Binarize: make pixels with alpha ≤ threshold fully transparent
        threshold = 30
        alpha = alpha.point(lambda p: 255 if p > threshold else 0)
        # Erode to knock off tiny matte fringes
        alpha = alpha.filter(ImageFilter.MinFilter(3))
        img.putalpha(alpha)

    # 5) Composite white background if saving as JPEG
    if target_ext in {".jpg", ".jpeg"}:
        canvas = Image.new("RGB", img.size, (255, 255, 255))
        if img.mode in {"RGBA", "LA"}:
            canvas.paste(img, mask=img.split()[-1])
        else:
            canvas.paste(img)
        output_img = canvas
    else:
        output_img = img

    # 6) Save out
    filename = f"{uuid.uuid4().hex}{target_ext}"
    out_path = os.path.join(OUTPUT_DIR, filename)
    try:
        output_img.save(out_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save output image: {e}")

    # 7) Return the file info
    return JSONResponse({
        "filename": filename,
        "url": f"/{OUTPUT_DIR}/{filename}"
    })

