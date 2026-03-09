## TkImage Studio

TkImage Studio is a desktop tool for **image dataset exploration, preprocessing, annotation, and lightweight classification model training**, built with **Tkinter**, **Pillow**, and optional **PyTorch**/**torchvision**.

It is inspired by tools like Roboflow: load a folder of images, browse and preprocess them, annotate for classification, export annotations, and (optionally) train a small CNN classifier — all from a clean, single-window interface plus a dedicated training window.

---

### Features

- **Dataset navigation**
  - Open a single image or an entire folder.
  - Thumbnail strip and Prev/Next navigation.
  - Keyboard support: **← / →** to move between images.

- **Image viewing & interaction**
  - Centered canvas with **fit-to-window scaling**.
  - **Zoom** via mouse wheel or toolbar (Zoom + / Zoom - / Adapter).
  - **Pan** when zoomed in (middle mouse drag).
  - **Mouse-based ROI cropping** (Souris ROI) with precise mapping back to image coordinates.

- **Preprocessing (Pillow-based)**
  - Geometry: resize, compress (scale by percentage), numeric crop, rotate.
  - Filters: grayscale, blur, sharpness, contrast, brightness, inversion, autocontrast.
  - Undo stack (up to 10 steps) with **Édition → Annuler** or **Ctrl+Z**.

- **Annotations for classification**
  - Per-image JSON annotation files stored in `tkimage_studio/data/annotations/`.
  - Fields: description, note (1–5), classe (label), tags (comma-separated).
  - Auto-save when switching images or dataset; auto-load when revisiting images.
  - Bottom status bar for quick edits, right panel for a more spacious view.
  - Export/import all annotations to/from **JSON** and **CSV**.

- **Statistics**
  - Per-image stats: width, height, color mode, file size, per-channel mean/min/max.
  - Dataset stats: number of images, average note, images per class.
  - Stats popup accessible from the left toolbar (**Stats** button).

- **Classification model training (optional)**
  - Uses the **current dataset and annotations** from the main UI.
  - Simple CNN backed by PyTorch/torchvision.
  - Training window with configurable epochs, batch size, and learning rate.
  - Training logs and final loss/accuracy.
  - Single-image prediction with top-k class probabilities.

---

### Installation

From the project root (`TkImage_v1`):

```bash
pip install -r requirements.txt
```

Requirements:

- **Required**
  - Python 3.9+
  - `Pillow` (image I/O and processing)
- **Optional (for model training / inference)**
  - `torch`
  - `torchvision`

Tkinter is part of the standard Python distribution on Windows, so no extra dependency is needed.

---

### Running the Application

From the project root:

```bash
cd TkImage_v1
py -m tkimage_studio.main
```

This launches the main TkImage Studio window.

---

### Quick Start Workflow

#### 1. Load a dataset

- Use **Fichier → Ouvrir dossier** to select a folder of images.
- Use the **thumbnail strip** and **Prev/Next** buttons (or **← / →** keys) to navigate between images.

#### 2. Explore and preprocess

- Use the **left toolbar**:
  - `Redimensionner`, `Compresser`, `Rogner`, `Pivoter` for geometric changes.
  - `Souris ROI` to crop an area by drawing a rectangle with the mouse.
  - `Zoom +`, `Zoom -`, `Adapter` to inspect details or reset view.
- Alternatively, use the **Filtres** menu to apply grayscale, blur, contrast, etc.
- Use **Édition → Annuler** or **Ctrl+Z** to revert up to 10 operations.

#### 3. Annotate for classification

- In the **bottom bar**, fill in:
  - **Description**: free text.
  - **Note (1–5)**: quality/importance/confidence score.
  - **Classe**: class/label for classification.
  - **Tags**: comma-separated keywords (e.g. `blurry, night, occluded`).
- The **right panel** mirrors these fields with a larger editable area.
- When you change images or folders, annotations are automatically saved to `tkimage_studio/data/annotations/{image_name}.json` and reloaded when you come back.

#### 4. Export / import annotations

- **Export**:
  - Use **Fichier → Exporter annotations**.
  - Choose a JSON or CSV file path, or cancel to write to defaults:
    - `tkimage_studio/data/annotations/export.json`
    - `tkimage_studio/data/annotations/export.csv`
- **Import**:
  - Use **Fichier → Importer annotations**.
  - Select a JSON export file; per-image JSON files in `tkimage_studio/data/annotations/` will be recreated/updated accordingly.

#### 5. View stats

- Click **Stats** in the left toolbar.
- The popup shows:
  - Image stats: dimensions, mode, file size, per-channel mean/min/max.
  - Dataset stats: number of images in the current dataset, average note, image counts per class.

#### 6. Train a simple classification model (optional)

- Ensure your images are annotated with **Classe** values.
- With a folder open, go to **Modèles → Entraîner un modèle de classification…**.
- In the training window:
  - Confirm the dataset summary (number of images from the main UI).
  - Set model to `simple_cnn` (default) and adjust epochs, batch size, learning rate if desired.
  - Click **Lancer l'entraînement**:
    - Training runs in the background; logs appear in the text area.
  - When training completes, click **Tester sur une image…** to evaluate an arbitrary image:
    - A popup shows predicted class and top-k probabilities.

---

### Keyboard and Mouse Shortcuts

- **Navigation**
  - `←` / `→`: Previous / next image (if a folder is loaded).

- **Undo**
  - `Ctrl+Z`: Undo last image operation.

- **Zoom & Pan**
  - Mouse wheel over image: zoom in/out.
  - Middle mouse button drag: pan when zoomed.

- **ROI Crop**
  - Click **Souris ROI**, then left-click and drag on the image to select a region. Release to crop.

---

### Project Structure (Overview)

- `tkimage_studio/main.py`: Application entry point. Creates the Tk root and `MainWindow`.
- `tkimage_studio/src/ui/`:
  - `main_window.py`: Overall layout, state management, glue between UI and core logic.
  - `menu_bar.py`: All menus and items, mapped by callback keys.
  - `left_toolbar.py`: Slim vertical toolbar for image utilities and stats.
  - `image_viewer.py`: Canvas-based viewer with zoom, pan, and ROI selection.
  - `status_panel.py`: Bottom status + quick annotation controls.
  - `right_panel.py`: Right-side annotation panel (larger text area).
  - `training_window.py`: Separate model training/testing window for CNNs.
- `tkimage_studio/src/core/`:
  - `file_manager.py`: Image open/save operations and dataset folder listing.
  - `image_loader.py`: Safe image loading wrapper around `Pillow`.
  - `image_processor.py`: Pure image transformations (resize, crop, rotate, filters).
  - `annotation_manager.py`: Per-image annotation JSON storage, export/import utilities.
  - `stats_manager.py`: Per-image and dataset statistics computation.
  - `classification_manager.py`: Optional PyTorch-based dataset adapter, training loop, and inference helpers.
- `tkimage_studio/data/`:
  - `input_images/`: Suggested location for raw inputs.
  - `output_images/`: Saved outputs from “Enregistrer” / “Enregistrer sous”.
  - `annotations/`: Per-image annotation JSON files and exported datasets (`export.json`, `export.csv`).

For a deeper architectural explanation and design rationale, see `tkimage_studio/TECHNICAL_REPORT.md`.

## TkImage Studio (Work-in-Progress)

TkImage Studio is a desktop application built with **Tkinter** and **Pillow** for managing, preprocessing, and annotating image datasets for **machine learning (classification)** projects.  
The layout and workflow are inspired by tools like Roboflow: load a project (folder of images), browse, preprocess, and (later) assign classes and metadata.

This README documents the current implementation state so future developers can continue building on top of it.

---

### Current Features (Status by Step)

- **Step 1 – Main Window Layout**
  - Resizable main window (`900x600` minimum) with a 4-zone layout:
    - Top: header + menu bar.
    - Left: slim vertical toolbar for image utilities.
    - Center: main image viewer with navigation and thumbnail strip.
    - Right: placeholder panel for future class/tags/statistics.
  - Uses Tkinter `grid` for a responsive layout.

- **Step 2 – Menu Bar**
  - `MenuBar` class with the following menus and stubbed actions:
    - **Fichier**: Ouvrir image, Ouvrir dossier, Enregistrer, Enregistrer sous, Exporter annotations, Quitter.
    - **Édition**: Annuler, Rétablir, Supprimer de la session, Réinitialiser l'image.
    - **Filtres**: Niveaux de gris, Flou, Netteté, Contraste, Luminosité, Inversion, Autocontraste.
    - **Segmentation**, **Visualisation 3D**, **À propos** (callbacks ready; many still to implement).
  - Menu items are wired through a callbacks dictionary in `MainWindow`.

- **Step 3 – Left Toolbar**
  - `LeftToolbar` with compact buttons for **image utilities** only:
    - Redimensionner, Compresser, Rogner, Pivoter.
    - Souris ROI (mouse-based crop), Repère (reserved for future tools).
    - Zoom +, Zoom -, Adapter (now fully wired to zoom/pan).
  - Toolbar uses callback keys so behavior lives in `MainWindow`.

- **Step 4 – Image Viewer (Open & Display Single Image)**
  - `ImageViewer` (central canvas) can display a **single PIL image**, scaled to fit and centered while preserving aspect ratio.
  - `Fichier → Ouvrir image`:
    - Uses `filedialog.askopenfilename`.
    - Loads images via `src/core/image_loader.load_image`.
    - Displays the image in the viewer and shows filename + dimensions in the status bar.

- **Step 5 – Folder Navigation**
  - `Fichier → Ouvrir dossier`:
    - Finds images using `src/core/file_manager.open_folder`.
    - Maintains `image_folder_files` and `current_index` in `MainWindow`.
  - Navigation:
    - **Prev/Next** buttons under the viewer.
    - Left/Right **arrow keys** for keyboard navigation.
    - Horizontal **thumbnail strip** (clickable) for quick image jumps.
  - Status bar shows `[index/total] filename — WxH`.

- **Step 6 – Image Transformations (Core + UI Integration)**
  - `src/core/image_processor.py` implements:
    - Geometric: `resize_image`, `crop_image`, `rotate_image`.
    - Intensity: `apply_grayscale`, `apply_blur`, `apply_contrast`, `apply_brightness`, `apply_sharpness`, `apply_inversion`, `apply_autocontrast`.
  - `MainWindow` exposes these via:
    - **Filtres** menu:
      - Niveaux de gris, Flou, Netteté, Contraste (with factor dialog), Luminosité (with factor dialog), Inversion, Autocontraste.
    - **Toolbar**:
      - Redimensionner: prompts for new width/height and resizes the image.
      - Compresser: prompts for a percentage scale and resizes accordingly.
      - Rogner: prompts for a numeric bounding box (fallback crop tool).
      - Pivoter: prompts for a rotation angle.
  - **Undo support**:
    - `MainWindow.history` stores up to 10 previous image states.
    - `Édition → Annuler` and `Ctrl+Z` revert one step at a time.

- **Step 7 – Mouse Crop / ROI Selection**
  - `ImageViewer` supports **mouse-based ROI selection**:
    - Tracks scaling and offsets to map canvas coordinates back to image coordinates.
    - Draws a purple dashed rectangle while dragging.
  - Left toolbar **“Souris ROI”**:
    - Activates ROI mode; user drags a rectangle over the image.
    - On mouse release, the selection is converted to an image-space bounding box.
    - `MainWindow` crops the image using `image_processor.crop_image`, with undo support.
  - Numeric `Rogner` remains available for precise coordinate-based cropping.

- **Step 8 – Zoom and Pan**
  - `ImageViewer` now supports interactive zoom and pan:
    - **Zoom**:
      - Mouse wheel over the image zooms in/out (bounded between ~25% and 600%).
      - Toolbar buttons **Zoom +**, **Zoom -**, and **Adapter** call `zoom_in`, `zoom_out`, and `fit_to_window` respectively.
      - Implementation detail: a base scale is computed to fit the image to the canvas, then multiplied by an internal zoom factor (`_zoom`); the effective display scale is stored in `_display_scale`.
    - **Pan**:
      - Middle mouse button drag (button 2) adjusts the display offsets so the image can be moved inside the canvas when zoomed.
      - Implementation detail: pan works by updating `_display_offset_x/_display_offset_y` from the mouse delta and re-rendering while temporarily preserving offsets via `_keep_offsets`.

- **Step 9 – Annotation Panel (Bottom + Right)**
  - `src/core/annotation_manager.py`:
    - Defines an `Annotation` dataclass and per-image JSON storage under `data/annotations/{image_stem}.json`.
    - Provides `save_annotation(image_path, description, note, classe, tags, width, height, mode, file_size_kb)` and `load_annotation(image_path)`.
  - Bottom **Status / Annotation bar** (`StatusPanel`):
    - Shows file metadata: filename, size (WxH), mode, file size in KB, and a summary line like `[i/n] filename — WxH MODE, XX.X Ko`.
    - Provides compact annotation fields:
      - `Description` (single-line).
      - `Note` (1–5; rating/quality/confidence score).
      - `Classe` (classification label).
      - `Tags` (comma-separated keywords for conditions/context).
  - Right **Annotation panel** (`RightPanel`):
    - Mirrors the same fields in a more spacious layout:
      - Multi-line description, note, class, and tags.
    - Synced from `MainWindow` when loading annotations so both panels represent the same data.
  - `MainWindow` behavior (technical):
    - On navigation (new folder or new index), `_save_current_annotation_if_possible()` flushes bottom-panel fields to disk via `annotation_manager.save_annotation`.
    - After loading an image, `_load_annotation_for_current_image()` populates both panels if a JSON exists; otherwise clears fields.
    - Status metadata is computed directly from the `PIL.Image` (`size`, `mode`) and filesystem (`Path.stat().st_size`), and passed to `StatusPanel.update_metadata`.

- **Step 10 – Export / Import Annotations**
  - Extended `annotation_manager.py`:
    - `load_all_annotations()` returns all stored `Annotation` objects from `data/annotations/`.
    - `export_annotations_json(output_path=None)`:
      - Exports all annotations as a JSON **list** to the given path, or to `data/annotations/export.json` by default.
    - `export_annotations_csv(output_path=None)`:
      - Exports as CSV with columns `filename, description, note, classe, tags, width, height, mode, file_size_kb` to the given path, or `data/annotations/export.csv` by default.
    - `import_annotations_json(input_path)`:
      - Reads a JSON export (list of dicts), recreates per-image JSON files, and returns the number of imported annotations.
  - `MainWindow` wiring:
    - `Fichier → Exporter annotations` opens a save dialog:
      - If a path is chosen: writes JSON if `.json`, CSV if `.csv`.
      - If cancelled: falls back to writing both `export.json` and `export.csv` under `data/annotations/`.
      - Always calls `_save_current_annotation_if_possible()` first to avoid losing the active image’s edits.
    - `Fichier → Importer annotations`:
      - Opens a file dialog for an exported JSON file.
      - Invokes `import_annotations_json` and reports how many rows were imported.

> **Not yet implemented (planned)**
> - Segmentation tools, 3D visualizations.
> - Persistent saving of processed pixels to disk (Enregistrer / Enregistrer sous) and reset-to-original behavior.

- **Model Training – Simple CNN Classifier**
  - `src/core/classification_manager.py`:
    - Integrates **PyTorch** / **torchvision** (optional dependency) to train small CNNs on top of the existing annotated dataset.
    - `TrainingConfig` holds hyperparameters and the list of image paths to use (taken directly from the main UI's current dataset).
    - `AnnotationDataset`:
      - Uses `annotation_manager.load_all_annotations()` and filters annotations to the current image filenames from the main UI.
      - Builds `class_to_idx` and `idx_to_class` based on the `classe` field in annotations.
      - Loads images from the exact paths currently used by the main interface and applies `Resize(image_size, image_size) + ToTensor()`.
    - `train_model(config, log_fn)`:
      - Trains a small `simple_cnn` model using a standard loop (Adam + CrossEntropy).
      - Logs per-epoch loss and accuracy via the callback provided by the training window.
      - Returns `(model, metrics)` where `metrics` includes `train_loss` and `train_accuracy`.
      - Attaches `class_to_idx`, `idx_to_class`, and `image_size` to the model for later inference.
    - `predict_single(model, image_path)`:
      - Runs softmax inference on a single image and returns:
        - The predicted class label.
        - A list of top-k `(class, probability)` tuples.
  - `src/ui/training_window.py` (`TrainingWindow`):
    - Opened via **Modèles → Entraîner un modèle de classification…**.
    - Automatically uses the **current dataset** from the main UI:
      - If a folder is open: all image paths from `image_folder_files`.
      - Otherwise, falls back to the current single image (if any).
    - UI elements:
      - Displays a read-only summary: “Dataset courant : N image(s) chargée(s) dans l'interface principale.”
      - Lets the user choose:
        - Model (`simple_cnn`).
        - Number of epochs, batch size, learning rate.
      - Provides:
        - `Lancer l'entraînement`: starts training in a background thread, streaming log lines into a text area and showing a summary message when done.
        - `Tester sur une image…`: runs `predict_single` on a user-chosen image, displaying predicted class and probability breakdown.
    - Design:
      - Fully separated window so model training/testing is modular and does not clutter the main annotation UI.

---

### Project Structure (Relevant So Far)

- `main.py` – Application entry point, creates the Tk root and `MainWindow`.
- `src/`
  - `ui/`
    - `main_window.py` – Overall layout, menu/toolbar wiring, image state, navigation, transformations, undo.
    - `menu_bar.py` – Menu definitions and callback binding.
    - `left_toolbar.py` – Vertical image utilities toolbar.
    - `image_viewer.py` – Canvas-based viewer and ROI selection logic.
  - `core/`
    - `file_manager.py` – Open image file/folder, list image paths.
    - `image_loader.py` – Safe `PIL.Image` loading wrapper.
    - `image_processor.py` – Pure functions for image operations (resize, crop, rotate, filters).

Other folders (`assets/`, `data/`, `models/`, `utils/`) are scaffolded for future features (icons, themes, annotations, caching, etc.).

---

### Running the Application

From the parent folder (`TkImage_v1`):

```bash
cd TkImage_v1
py -m tkimage_studio.main
```

Requirements (see `requirements.txt`):
- Python 3.9+
- `Pillow`
- `torch` and `torchvision` (only required for model training / inference)

Install dependencies and run:

```bash
pip install -r requirements.txt
py -m tkimage_studio.main
```

---

### Notes for Future Developers

- **State location**:
  - All runtime image state lives in `MainWindow` (no globals): current image, current path, folder list, index, history.
  - UI widgets (`MenuBar`, `LeftToolbar`, `ImageViewer`) are mostly “dumb” and communicate via callbacks.
- **Extensibility points**:
  - Add new image operations in `image_processor.py` and wire them through `_apply_transformation` in `MainWindow`.
  - Extend the right-hand panel to display statistics and classification metadata.
  - Implement zoom/pan in `ImageViewer` (there are already zoom-related toolbar keys reserved).
- **Error handling**:
  - File operations are wrapped with `try/except` and use `messagebox.showerror` / `showinfo` for user feedback.
  - Pure core functions are kept UI-free for testability.

This README should be updated as new steps (segmentation, annotation export, stats, 3D views, etc.) are implemented.

