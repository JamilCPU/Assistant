# Plan 07 — img2img and Inpainting

## Problem
The current image generation UI only supports `txt2img`. Automatic1111 also exposes `img2img` (generate based on an input image) and `inpainting` (selectively regenerate masked areas). These are heavily used workflows that the current frontend has no support for.

---

## Auto1111 API Endpoints to Use

```
POST /sdapi/v1/img2img     — img2img and inpainting
POST /sdapi/v1/extra-single-image  — upscale/post-process a single image
```

The `img2img` endpoint accepts all the same parameters as `txt2img` plus:
- `init_images`: list of base64-encoded input images
- `denoising_strength`: how much to deviate from the input (0.0–1.0)
- `mask`: base64-encoded mask image (white = regenerate, black = keep) for inpainting
- `mask_blur`: blur radius for mask edges
- `inpainting_fill`: fill mode (0=fill, 1=original, 2=latent noise, 3=latent nothing)
- `inpaint_full_res`: use full resolution for inpainting
- `inpaint_full_res_padding`: padding in pixels

---

## Backend

### New endpoint
```
POST /api/image/img2img
```

New Pydantic model `Img2ImgRequest` extending `ImageGenerateRequest` with:
```python
class Img2ImgRequest(ImageGenerateRequest):
    init_image: str           # base64-encoded or URL to existing image
    denoising_strength: float = 0.75
    mask: Optional[str] = None           # base64 mask for inpainting
    mask_blur: int = 4
    inpainting_fill: int = 1             # 0=fill, 1=original, 2=latent noise
    inpaint_full_res: bool = True
    inpaint_full_res_padding: int = 32
    resize_mode: int = 0                 # 0=just resize, 1=crop and resize, 2=resize and fill
```

### `Auto1111Adapter`
Add `img2img()` method:
- If `init_image` is a local `/images/` URL: read from disk, base64-encode
- If `init_image` is a base64 string: use directly
- Call `POST /sdapi/v1/img2img` with the body
- Save and return images the same way as `txt2img`

---

## Frontend

### Mode tabs inside `ImageView`
Add a tab bar at the top of the controls panel:
- **txt2img** (current default)
- **img2img**
- **Inpainting**

### img2img tab
All existing controls, plus:
- **Input image** section (above prompt): drag-and-drop image zone or "Browse" button
  - Accepts image file from disk
  - Accepts URL to a previously generated image (with "Use generated image" picker)
  - Shows thumbnail preview with remove button
- **Denoising strength** slider: 0.0–1.0 (how much to change from source)
- **Resize mode** dropdown: Just resize / Crop and resize / Resize and fill

### Inpainting tab
- Same as img2img but adds a **mask editor**:
  - Shows the uploaded image with a brush tool overlay
  - User paints white over areas to regenerate
  - Uses HTML Canvas for the mask editor
  - "Clear mask" and "Invert mask" buttons
- Mask is serialized to base64 PNG and sent as `mask` parameter
- **Mask blur** slider
- **Inpainting fill** dropdown: Fill / Original / Latent noise / Latent nothing
- **Full resolution inpainting** toggle

### "Send to img2img" button
In the image gallery output panel, each generated image gets a **"Send to img2img"** button in its hover overlay. Clicking it:
1. Sets the img2img input image to this generated image
2. Switches to the img2img tab

---

## Files to touch
- `backend/models/image.py` — add `Img2ImgRequest`
- `backend/services/image_service/adapters/auto1111_adapter.py` — add `img2img()` method
- `backend/services/image_service/image_service.py` — add `img2img()` delegation
- `backend/gateway/router.py` — add `POST /api/image/img2img`
- `frontend-web/src/api/client.ts` — add `img2img()` function and types
- `frontend-web/src/components/ImageView.tsx` — add tab bar, img2img controls, inpainting mask editor

---

## Acceptance criteria
- [ ] img2img tab visible in ImageView
- [ ] User can upload an image or pick a previously generated one
- [ ] Denoising strength slider controls deviation from source
- [ ] img2img generates successfully via Auto1111
- [ ] Inpainting tab shows canvas-based mask editor
- [ ] Brush tool draws mask on the image
- [ ] Inpainting generates only the masked region
- [ ] "Send to img2img" button works from the gallery
