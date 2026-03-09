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

