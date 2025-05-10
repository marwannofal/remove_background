import re
import uuid
import os
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import JSONResponse
from PIL import Image, ImageFilter
from rembg import remove
import cairosvg
from io import BytesIO

app = FastAPI()

OUTPUT_DIR = "processed_images"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def readable_filename(original_filename: str, ext: str) -> str:
    # strip extension, lowercase and replace non-alphanum with underscores
    base = os.path.splitext(original_filename)[0]
    safe = re.sub(r"[^a-zA-Z0-9_-]", "_", base).lower()
    # add an 8-char unique suffix to avoid collisions
    suffix = uuid.uuid4().hex[:8]
    return f"{safe}_{suffix}{ext}"

@app.post("/remove-background/")
async def remove_background(file: UploadFile = File(...)):
    data = await file.read()
    original_ext = os.path.splitext(file.filename)[1].lower()

    if original_ext == ".svg":
        try:
            img_bytes = cairosvg.svg2png(bytestring=data, dpi=300)
            target_ext = ".png"
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"SVG rasterization failed: {e}")
    else:
        img_bytes = data
        if original_ext in {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".webp"}:
            target_ext = original_ext
        else:
            target_ext = ".png"

    try:
        result_bytes = remove(img_bytes)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Background removal failed: {e}")

    try:
        img = Image.open(BytesIO(result_bytes))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse model output as image: {e}")

    if img.mode == "RGBA":
        alpha = img.split()[-1]
        threshold = 30
        alpha = alpha.point(lambda p: 255 if p > threshold else 0)
        alpha = alpha.filter(ImageFilter.MinFilter(3))
        img.putalpha(alpha)

    if target_ext in {".jpg", ".jpeg"}:
        canvas = Image.new("RGB", img.size, (255, 255, 255))
        if img.mode in {"RGBA", "LA"}:
            canvas.paste(img, mask=img.split()[-1])
        else:
            canvas.paste(img)
        output_img = canvas
    else:
        output_img = img

    filename = readable_filename(file.filename, target_ext)
    out_path = os.path.join(OUTPUT_DIR, filename)

    try:
        output_img.save(out_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save output image: {e}")

    return JSONResponse({"filename": filename, "url": f"/{OUTPUT_DIR}/{filename}"})
