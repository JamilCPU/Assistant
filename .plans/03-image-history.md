# Plan 03 — Image History & Gallery

## Problem
Every generated image is saved to disk and metadata is stored in the `generated_images` SQLite table, but there is no way to view past generations in the app. The `GET /api/images` endpoint already exists and returns the full list — it just has no frontend.

---

## Backend

### Existing (no changes needed)
- `GET /api/images` — returns all images with metadata (already implemented)
- Static file serving at `/images/{filename}` (already implemented)

### New endpoints

```
GET  /api/images?page=1&per_page=20&model=&prompt=
```
Add pagination and filtering to the existing endpoint:
- `page` / `per_page` for pagination (default: page=1, per_page=24)
- `model` filter (optional, partial match)
- `prompt` filter (optional, substring search on prompt text)
- Response adds `total` and `page` fields

```
DELETE /api/images/{image_id}
```
- Deletes the database row and the image file from disk

```
GET /api/images/{image_id}
```
- Returns single image detail (already partially available via the list)

---

## Frontend

### New mode: `'gallery'` in `AppMode`

Add a **Gallery** mode to `ChatContext` and the sidebar alongside Chat / Image Generation / Models.

### New component: `GalleryView.tsx`

#### Layout
- Masonry or uniform grid of past images (3–4 columns)
- Each card shows: thumbnail, prompt snippet (truncated), model name, date
- Hover overlay: full prompt, "Use as template" button, delete button

#### Controls (top bar)
- Search input: filters by prompt text
- Model filter dropdown: filter by checkpoint name
- Sort: newest first / oldest first

#### Pagination
- "Load more" button or infinite scroll
- Shows total count ("Showing 24 of 137 images")

#### Image detail modal
When clicking a card:
- Full-size image display
- Complete metadata: prompt, negative prompt, model, sampler, steps, CFG, seed, size, LoRAs, date
- **"Use as template"** button: pre-fills all `ImageView` parameters with this image's settings and switches to Image Generation mode
- Download button
- Delete button (with confirmation)

#### "Use as template" flow
In `ChatContext` or a shared state atom, store a `imageTemplate` value. When `GalleryView` sets it, the app switches to `mode: 'image'` and `ImageView` reads the template on mount to pre-fill all form fields.

---

## Files to touch
- `backend/gateway/router.py` — update `GET /api/images` with pagination/filtering, add `DELETE /api/images/{id}`, add `GET /api/images/{id}`
- `backend/storage/database.py` — add `get_images_paginated()`, `delete_image()` methods
- `frontend-web/src/api/client.ts` — add `listImagesPaginated()`, `deleteImage()`, `getImage()` functions
- `frontend-web/src/components/GalleryView.tsx` — new file
- `frontend-web/src/components/Sidebar.tsx` — add Gallery mode button
- `frontend-web/src/components/ImageView.tsx` — read and apply template on mount
- `frontend-web/src/context/ChatContext.tsx` — add `'gallery'` to `AppMode`, add `imageTemplate` state + `SET_IMAGE_TEMPLATE` action
- `frontend-web/src/App.tsx` — render `GalleryView` for `mode === 'gallery'`

---

## Acceptance criteria
- [ ] Gallery mode appears in sidebar
- [ ] All past generated images display as a grid with metadata
- [ ] Search filters results by prompt text
- [ ] Model filter works
- [ ] Pagination works (load more or pages)
- [ ] Clicking an image shows full detail modal with all generation parameters
- [ ] "Use as template" populates ImageView with all previous settings
- [ ] Delete removes image from disk and database
- [ ] Gallery handles empty state gracefully
