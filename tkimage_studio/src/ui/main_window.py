from __future__ import annotations

import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk
from pathlib import Path
from typing import Optional, List, Callable

from PIL import Image, ImageTk

from .menu_bar import MenuBar
from .left_toolbar import LeftToolbar
from .image_viewer import ImageViewer
from .status_panel import StatusPanel
from .right_panel import RightPanel
from .training_window import TrainingWindow
from ..core.image_loader import load_image
from ..core.file_manager import open_folder, save_image, OUTPUT_IMAGES_DIR
from ..core import image_processor
from ..core import annotation_manager
from ..core import stats_manager


class MainWindow:
    """
    Main application window for TkImage Studio.

    This class is responsible for building the high-level 4-zone layout:
      - Top:    menu bar placeholder
      - Left:   vertical toolbar panel
      - Center: main image viewer area
      - Right:  optional side panel
      - Bottom: status / info bar
    """

    MIN_WIDTH = 900
    MIN_HEIGHT = 600
    LEFT_PANEL_WIDTH = 52
    RIGHT_PANEL_WIDTH = 260
    BOTTOM_PANEL_HEIGHT = 80

    def __init__(self, root: tk.Tk) -> None:
        self.root = root

        # Simple application state for image classification workflow.
        self.current_image: Optional[Image.Image] = None
        self.original_image: Optional[Image.Image] = None
        self.current_image_path: Optional[Path] = None
        self.saved_image_path: Optional[Path] = None
        self.image_folder_files: List[Path] = []
        self.current_index: int = -1

        # History for undo (up to 10 previous images).
        self.history: List[Image.Image] = []

        # Thumbnails for dataset navigation.
        self.thumbnail_images: List[ImageTk.PhotoImage] = []

        # Mouse-ROI mode flag
        self._roi_mode_enabled: bool = False

        # UI panels that will be created in _build_layout.
        self.status_panel: Optional[StatusPanel] = None
        self.right_panel: Optional[RightPanel] = None

        self._configure_root()
        self._build_layout()

    def _configure_root(self) -> None:
        """Configure root window properties such as title and minimum size."""
        self.root.title("TkImage Studio")
        self.root.minsize(self.MIN_WIDTH, self.MIN_HEIGHT)

        # Light theme with colored accents (purple / blue / yellow / red).
        # Inspired by modern ML tooling dashboards.
        self.root.configure(bg="#f5f5f7")
        style = ttk.Style(self.root)
        try:
            style.theme_use("clam")
        except tk.TclError:
            # Fallback silently if the theme isn't available.
            pass
        base_bg = "#f5f5f7"
        card_bg = "#ffffff"
        text_main = "#1f2933"
        accent_purple = "#7c3aed"  # primary actions
        accent_blue = "#2563eb"    # informational
        accent_yellow = "#f59e0b"  # warnings
        accent_red = "#dc2626"     # destructive

        # Base widgets
        style.configure("TFrame", background=base_bg)
        style.configure("Card.TFrame", background=card_bg, relief="flat")
        style.configure("TLabel", background=base_bg, foreground=text_main)
        style.configure("Muted.TLabel", background=base_bg, foreground="#6b7280")

        # Generic buttons
        style.configure(
            "TButton",
            padding=4,
            background=card_bg,
            foreground=text_main,
            borderwidth=1,
            focusthickness=1,
        )
        style.map(
            "TButton",
            background=[("active", "#e5e7eb")],
        )

        # Primary navigation buttons
        style.configure(
            "Primary.TButton",
            background=accent_purple,
            foreground="#ffffff",
        )
        style.map(
            "Primary.TButton",
            background=[("active", "#6d28d9")],
        )

        # Toolbar buttons (subtle)
        style.configure(
            "Tool.TButton",
            background=card_bg,
            foreground=text_main,
        )

        # Use grid to organize the main zones: top, center, bottom.
        self.root.rowconfigure(0, weight=0)  # Top menu area (fixed height)
        self.root.rowconfigure(1, weight=1)  # Central working area (expands)
        self.root.rowconfigure(2, weight=0)  # Bottom status bar (fixed height)
        self.root.columnconfigure(0, weight=1)

    def _build_layout(self) -> None:
        """Create and place the main layout frames."""
        self._create_top_area_with_menu()
        self._create_central_panes()
        self._create_bottom_status_bar()

    def _create_top_area_with_menu(self) -> None:
        """
        Create the top area and attach the application menu bar.

        The actual menu bar is managed by the `MenuBar` class which
        attaches a native menubar to the root window. We keep a thin
        top frame as a project header / placeholder strip.
        """
        # Shared callbacks between menu bar and toolbar.
        callbacks = {
            # File related
            "file_open_image": self.open_image_dialog,
            "file_open_folder": self.open_folder_dialog,
            "file_save": self.save_image_action,
            "file_save_as": self.save_image_as_action,
            "file_export_annotations": self.export_annotations_dialog,
            "file_import_annotations": self.import_annotations_dialog,
            "file_quit": self.root.quit,
            # Edit
            "edit_undo": self.undo,
            "edit_redo": self.not_implemented,
            "edit_remove_from_session": self.not_implemented,
            "edit_reset_image": self.reset_image,
            # Filters
            "filter_grayscale": self.apply_filter_grayscale,
            "filter_blur": self.apply_filter_blur,
            "filter_sharpness": self.apply_filter_sharpness,
            "filter_contrast": self.apply_filter_contrast,
            "filter_brightness": self.apply_filter_brightness,
            "filter_invert": self.apply_filter_invert,
            "filter_autocontrast": self.apply_filter_autocontrast,
            # Segmentation
            "seg_threshold": self.not_implemented,
            "seg_binary_mask": self.not_implemented,
            "seg_extract_roi": self.not_implemented,
            # Visualisation
            "vis_heatmap": self.not_implemented,
            "vis_surface": self.not_implemented,
            "vis_stack_channels": self.not_implemented,
            # About
            "about_version": self.show_about_version,
            "about_author": self.show_about_author,
            "about_help": self.show_about_help,
            # Models
            "model_open_training_window": self.open_training_window,
            # Toolbar specific tools
            "tool_resize": self.resize_image_dialog,
            "tool_compress": self.compress_image_dialog,
            "tool_crop_dialog": self.crop_image_dialog,
            "tool_rotate": self.rotate_image_dialog,
            "tool_mouse_crop": self.start_mouse_roi_crop,
            "tool_pointer": self.not_implemented,
            "tool_stats": self.show_stats_popup,
            "view_zoom_in": self.zoom_in,
            "view_zoom_out": self.zoom_out,
            "view_fit_window": self.fit_to_window,
        }

        # Instantiate the menu bar with functional callbacks.
        MenuBar(self.root, callbacks=callbacks)

        top_frame = ttk.Frame(self.root)
        top_frame.grid(row=0, column=0, sticky="ew")

        # Give the top row a minimal fixed height hint.
        self.root.grid_rowconfigure(0, minsize=30)

        title_label = ttk.Label(
            top_frame,
            text="TkImage Studio — Projet de classification (menu prêt)",
            anchor="w",
        )
        title_label.pack(fill="x", padx=8, pady=4)

    def _create_central_panes(self) -> None:
        """
        Create the central working area with left toolbar, center viewer,
        and right side panel using a grid-based layout.
        """
        central_frame = ttk.Frame(self.root)
        central_frame.grid(row=1, column=0, sticky="nsew")

        # Let the central area expand with the window.
        central_frame.rowconfigure(0, weight=1)

        # Central layout:
        #   - Column 0: slim vertical toolbar
        #   - Column 1: main viewer + thumbnails + nav
        #   - Column 2: right info panel
        central_frame.columnconfigure(0, weight=0, minsize=self.LEFT_PANEL_WIDTH)
        central_frame.columnconfigure(1, weight=1)
        central_frame.columnconfigure(2, weight=0, minsize=self.RIGHT_PANEL_WIDTH)
        central_frame.rowconfigure(0, weight=1)

        # Left toolbar
        self.left_toolbar = LeftToolbar(
            central_frame,
            callbacks=self._callbacks_for_toolbar_and_menu,
        )
        self.left_toolbar.grid(row=0, column=0, sticky="ns")

        # Center stack: image viewer (dominant), nav buttons, thumbnails
        center_container = ttk.Frame(central_frame, style="Card.TFrame")
        center_container.grid(row=0, column=1, sticky="nsew", padx=(4, 4), pady=(0, 4))
        center_container.rowconfigure(0, weight=1)
        center_container.rowconfigure(1, weight=0)
        center_container.rowconfigure(2, weight=0)
        center_container.columnconfigure(0, weight=1)

        self.image_viewer = ImageViewer(center_container)
        self.image_viewer.grid(row=0, column=0, sticky="nsew")

        nav_frame = ttk.Frame(center_container)
        nav_frame.grid(row=1, column=0, sticky="ew", pady=(4, 0))
        nav_frame.columnconfigure(0, weight=1)
        nav_frame.columnconfigure(1, weight=1)

        prev_btn = ttk.Button(
            nav_frame,
            text="◀ Précédent",
            command=self.go_previous_image,
            style="Primary.TButton",
        )
        next_btn = ttk.Button(
            nav_frame,
            text="Suivant ▶",
            command=self.go_next_image,
            style="Primary.TButton",
        )
        prev_btn.grid(row=0, column=0, sticky="ew", padx=(0, 2))
        next_btn.grid(row=0, column=1, sticky="ew", padx=(2, 0))

        # Thumbnails strip directly under nav
        thumb_container = ttk.Frame(center_container)
        thumb_container.grid(row=2, column=0, sticky="ew", pady=(4, 0))
        thumb_canvas = tk.Canvas(
            thumb_container,
            height=72,
            bg="#e5e7eb",
            highlightthickness=0,
        )
        h_scroll = ttk.Scrollbar(
            thumb_container,
            orient="horizontal",
            command=thumb_canvas.xview,
        )
        self.thumbnail_inner = ttk.Frame(thumb_canvas)
        self.thumbnail_inner.bind(
            "<Configure>",
            lambda e: thumb_canvas.configure(scrollregion=thumb_canvas.bbox("all")),
        )
        thumb_canvas.create_window((0, 0), window=self.thumbnail_inner, anchor="nw")
        thumb_canvas.configure(xscrollcommand=h_scroll.set)

        thumb_canvas.pack(fill="x", side="top", expand=False)
        h_scroll.pack(fill="x", side="bottom")

        self.thumb_canvas = thumb_canvas

        # Right side annotation & stats panel
        self.right_panel = RightPanel(central_frame)
        self.right_panel.grid(row=0, column=2, sticky="nsew", pady=(0, 4))

    def _create_bottom_status_bar(self) -> None:
        """Create a simple status/info bar at the bottom of the window."""
        status_frame = ttk.Frame(self.root, relief="groove", borderwidth=1)
        status_frame.grid(row=2, column=0, sticky="ew")

        # Give the bottom row a fixed height hint.
        self.root.grid_rowconfigure(2, minsize=self.BOTTOM_PANEL_HEIGHT)

        self.status_panel = StatusPanel(status_frame)
        self.status_panel.pack(fill="x", expand=True)

        # Global key bindings for quick dataset navigation.
        self.root.bind("<Left>", lambda _e: self.go_previous_image())
        self.root.bind("<Right>", lambda _e: self.go_next_image())
        self.root.bind("<Control-z>", lambda _e: self.undo())

    # ------------------------------------------------------------------ #
    # Callbacks mapping
    # ------------------------------------------------------------------ #
    @property
    def _callbacks_for_toolbar_and_menu(self) -> dict[str, callable]:
        """
        Expose the same callbacks dict used by the MenuBar for the toolbar,
        ensuring both control surfaces stay in sync.
        """
        # Recreate the same mapping used in _create_top_area_with_menu.
        # This avoids circular initialization order; in a larger refactor
        # this could be stored centrally.
        return {
            "file_open_image": self.open_image_dialog,
            "file_open_folder": self.open_folder_dialog,
            "file_save": self.save_image_action,
            "file_save_as": self.save_image_as_action,
            "file_export_annotations": self.export_annotations_dialog,
            "file_import_annotations": self.import_annotations_dialog,
            "file_quit": self.root.quit,
            "edit_undo": self.undo,
            "edit_redo": self.not_implemented,
            "edit_remove_from_session": self.not_implemented,
            "edit_reset_image": self.reset_image,
            "filter_grayscale": self.apply_filter_grayscale,
            "filter_blur": self.apply_filter_blur,
            "filter_sharpness": self.apply_filter_sharpness,
            "filter_contrast": self.apply_filter_contrast,
            "filter_brightness": self.apply_filter_brightness,
            "filter_invert": self.apply_filter_invert,
            "filter_autocontrast": self.apply_filter_autocontrast,
            "seg_threshold": self.not_implemented,
            "seg_binary_mask": self.not_implemented,
            "seg_extract_roi": self.not_implemented,
            "vis_heatmap": self.not_implemented,
            "vis_surface": self.not_implemented,
            "vis_stack_channels": self.not_implemented,
            "about_version": self.show_about_version,
            "about_author": self.show_about_author,
            "about_help": self.show_about_help,
            "tool_resize": self.resize_image_dialog,
            "tool_compress": self.compress_image_dialog,
            "tool_crop_dialog": self.crop_image_dialog,
            "tool_rotate": self.rotate_image_dialog,
            "tool_mouse_crop": self.start_mouse_roi_crop,
            "tool_pointer": self.not_implemented,
            "tool_stats": self.show_stats_popup,
            "view_zoom_in": self.zoom_in,
            "view_zoom_out": self.zoom_out,
            "view_fit_window": self.fit_to_window,
        }

    # ------------------------------------------------------------------ #
    # Image loading and navigation
    # ------------------------------------------------------------------ #
    def open_image_dialog(self) -> None:
        """Open a file dialog to select a single image and display it."""
        filetypes = [
            ("Images", "*.png *.jpg *.jpeg *.bmp *.tiff *.tif"),
            ("Tous les fichiers", "*.*"),
        ]
        path_str = filedialog.askopenfilename(
            title="Ouvrir une image",
            filetypes=filetypes,
        )
        if not path_str:
            return

        img = load_image(path_str)
        if img is None:
            messagebox.showerror(
                "Erreur de chargement",
                "Impossible de charger l'image sélectionnée.",
            )
            return

        self.current_image = img
        self.original_image = img.copy()
        self.current_image_path = Path(path_str)
        self.saved_image_path = None
        self.image_folder_files = []
        self.current_index = -1

        self.image_viewer.set_image(img)
        self._load_annotation_for_current_image()
        self._update_status_with_current_image()

    def open_folder_dialog(self) -> None:
        """Open a folder and prepare an image dataset for navigation."""
        folder = filedialog.askdirectory(title="Ouvrir un dossier d'images")
        if not folder:
            return

        files = open_folder(folder)
        if not files:
            messagebox.showinfo(
                "Aucune image",
                "Aucune image compatible trouvée dans ce dossier.",
            )
            return

        # Save any annotation on the currently opened image before changing folder.
        self._save_current_annotation_if_possible()

        # Save annotation for the current image before switching dataset.
        self._save_current_annotation_if_possible()

        self.image_folder_files = files
        self.current_index = 0
        self._load_image_at_index(self.current_index)
        self._build_thumbnails()

    def _load_image_at_index(self, index: int) -> None:
        if not (0 <= index < len(self.image_folder_files)):
            return

        path = self.image_folder_files[index]
        img = load_image(path)
        if img is None:
            messagebox.showerror(
                "Erreur de chargement",
                f"Impossible de charger l'image : {path.name}",
            )
            return

        # Save annotation of the current image before moving index.
        self._save_current_annotation_if_possible()

        self.current_image = img
        self.original_image = img.copy()
        self.current_image_path = path
        self.saved_image_path = None
        self.current_index = index
        self.image_viewer.set_image(img)
        self._load_annotation_for_current_image()
        self._update_status_with_current_image()

        # Clear history when moving to another file.
        self.history.clear()

    def _build_thumbnails(self) -> None:
        """Build a horizontal strip of clickable thumbnails for the dataset."""
        # Clear previous thumbnails.
        for child in self.thumbnail_inner.winfo_children():
            child.destroy()
        self.thumbnail_images.clear()

        thumb_size = 72

        for idx, path in enumerate(self.image_folder_files):
            try:
                img = load_image(path)
                if img is None:
                    continue
                thumb = img.copy()
                thumb.thumbnail((thumb_size, thumb_size), Image.LANCZOS)
                tk_img = ImageTk.PhotoImage(thumb)
            except Exception:
                continue

            self.thumbnail_images.append(tk_img)
            frame = ttk.Frame(self.thumbnail_inner, padding=2)
            frame.grid(row=0, column=idx, padx=2, pady=2)

            btn = ttk.Button(
                frame,
                image=tk_img,
                command=lambda i=idx: self._load_image_at_index(i),
            )
            btn.pack()

            label = ttk.Label(frame, text=path.name[:12], anchor="center")
            label.pack()

    def _update_status_with_current_image(self) -> None:
        """Update the bottom status bar with basic info on the current image."""
        if self.status_panel is None:
            return
        if self.current_image is None or self.current_image_path is None:
            self.status_panel.update_metadata(
                index=0,
                total=0,
                filename="",
                width=0,
                height=0,
                mode="",
                file_size_kb=0.0,
            )
            return

        w, h = self.current_image.size
        mode = getattr(self.current_image, "mode", "")
        try:
            file_size_kb = self.current_image_path.stat().st_size / 1024.0
        except OSError:
            file_size_kb = 0.0

        index = self.current_index + 1 if self.current_index >= 0 else 0
        total = len(self.image_folder_files)

        self.status_panel.update_metadata(
            index=index,
            total=total,
            filename=self.current_image_path.name,
            width=w,
            height=h,
            mode=mode,
            file_size_kb=file_size_kb,
        )

    # ------------------------------------------------------------------ #
    # Annotation persistence helpers
    # ------------------------------------------------------------------ #
    def _save_current_annotation_if_possible(self) -> None:
        """Persist annotation for the current image, if any info is available."""
        if self.current_image is None or self.current_image_path is None:
            return
        if self.status_panel is None:
            return

        description, note, classe, tags = self.status_panel.get_annotation()
        # If all fields are empty and note is 0, skip writing a file.
        if not any([description, note, classe, tags]):
            return

        w, h = self.current_image.size
        mode = getattr(self.current_image, "mode", "")
        try:
            file_size_kb = self.current_image_path.stat().st_size / 1024.0
        except OSError:
            file_size_kb = 0.0

        annotation_manager.save_annotation(
            image_path=self.current_image_path,
            description=description,
            note=note,
            classe=classe,
            tags=tags,
            width=w,
            height=h,
            mode=mode,
            file_size_kb=file_size_kb,
        )

    def _load_annotation_for_current_image(self) -> None:
        """Load existing annotation (if any) for the current image into the UI."""
        if self.current_image_path is None or self.status_panel is None:
            return

        ann = annotation_manager.load_annotation(self.current_image_path)
        if ann is None:
            # Reset fields.
            self.status_panel.set_annotation("", 0, "", "")
            if self.right_panel is not None:
                self.right_panel.set_annotation("", 0, "", "")
            return

        self.status_panel.set_annotation(
            description=ann.description,
            note=ann.note,
            classe=ann.classe,
            tags=ann.tags,
        )
        if self.right_panel is not None:
            self.right_panel.set_annotation(
                description=ann.description,
                note=ann.note,
                classe=ann.classe,
                tags=ann.tags,
            )

    # ------------------------------------------------------------------ #
    # Annotations export / import
    # ------------------------------------------------------------------ #
    def export_annotations_dialog(self) -> None:
        """
        Export all stored annotations to JSON or CSV.

        If the user cancels the dialog, falls back to default paths
        `data/annotations/export.json` or `export.csv`.
        """
        # Ensure current annotation is persisted before exporting.
        self._save_current_annotation_if_possible()

        filetypes = [
            ("Fichier JSON", "*.json"),
            ("Fichier CSV", "*.csv"),
            ("Tous les fichiers", "*.*"),
        ]
        path_str = filedialog.asksaveasfilename(
            title="Exporter les annotations",
            defaultextension=".json",
            filetypes=filetypes,
        )
        # Determine target path and format.
        if not path_str:
            # No path chosen → use defaults.
            json_path = annotation_manager.ANNOTATIONS_DIR / "export.json"
            csv_path = annotation_manager.ANNOTATIONS_DIR / "export.csv"
            annotation_manager.export_annotations_json(json_path)
            annotation_manager.export_annotations_csv(csv_path)
            messagebox.showinfo(
                "Export terminé",
                f"Annotations exportées vers :\n- {json_path}\n- {csv_path}",
            )
            return

        path = Path(path_str)
        ext = path.suffix.lower()
        try:
            if ext == ".csv":
                out = annotation_manager.export_annotations_csv(path)
            else:
                out = annotation_manager.export_annotations_json(path)
            messagebox.showinfo(
                "Export terminé",
                f"Annotations exportées vers :\n{out}",
            )
        except Exception as exc:
            messagebox.showerror("Erreur export", str(exc))

    def import_annotations_dialog(self) -> None:
        """
        Import annotations from a JSON export file.

        This recreates per-image JSON descriptors in `data/annotations`.
        """
        filetypes = [
            ("Fichier JSON", "*.json"),
            ("Tous les fichiers", "*.*"),
        ]
        path_str = filedialog.askopenfilename(
            title="Importer des annotations",
            filetypes=filetypes,
        )
        if not path_str:
            return

        path = Path(path_str)
        try:
            count = annotation_manager.import_annotations_json(path)
        except Exception as exc:
            messagebox.showerror("Erreur import", str(exc))
            return

        messagebox.showinfo(
            "Import terminé",
            f"{count} annotations importées depuis {path.name}.",
        )

    # ------------------------------------------------------------------ #
    # Stats popup
    # ------------------------------------------------------------------ #
    def show_stats_popup(self) -> None:
        """Open a popup window showing statistics for the current image/dataset."""
        if self.current_image is None:
            messagebox.showinfo("Statistiques", "Aucune image chargée.")
            return

        try:
            stats = stats_manager.compute_stats(
                image=self.current_image,
                image_path=self.current_image_path,
                folder_images=self.image_folder_files,
            )
        except Exception as exc:
            messagebox.showerror("Erreur statistiques", str(exc))
            return

        win = tk.Toplevel(self.root)
        win.title("Statistiques de l'image / dataset")
        win.transient(self.root)
        win.grab_set()

        frame = ttk.Frame(win, padding=12)
        frame.grid(row=0, column=0, sticky="nsew")
        win.columnconfigure(0, weight=1)
        win.rowconfigure(0, weight=1)

        # Image-level stats
        ttk.Label(frame, text="Image courante", anchor="w").grid(
            row=0, column=0, columnspan=2, sticky="ew"
        )
        ttk.Label(frame, text="Dimensions:", style="Muted.TLabel").grid(
            row=1, column=0, sticky="w"
        )
        ttk.Label(
            frame,
            text=f"{stats['width']} x {stats['height']}",
        ).grid(row=1, column=1, sticky="w")

        ttk.Label(frame, text="Mode:", style="Muted.TLabel").grid(
            row=2, column=0, sticky="w"
        )
        ttk.Label(frame, text=str(stats["mode"])).grid(row=2, column=1, sticky="w")

        ttk.Label(frame, text="Taille fichier:", style="Muted.TLabel").grid(
            row=3, column=0, sticky="w"
        )
        ttk.Label(
            frame,
            text=f"{stats['file_size_kb']:.1f} Ko",
        ).grid(row=3, column=1, sticky="w")

        # Channel stats
        ttk.Label(frame, text="Canaux (moy / min / max):", anchor="w").grid(
            row=4, column=0, columnspan=2, sticky="ew", pady=(8, 0)
        )
        row = 5
        for ch, ch_stats in stats["channels"].items():
            ttk.Label(frame, text=f"{ch}:", style="Muted.TLabel").grid(
                row=row, column=0, sticky="w"
            )
            ttk.Label(
                frame,
                text=f"{ch_stats['mean']:.1f}  (min {ch_stats['min']:.0f}, max {ch_stats['max']:.0f})",
            ).grid(row=row, column=1, sticky="w")
            row += 1

        # Dataset stats
        ttk.Label(frame, text="Dataset", anchor="w").grid(
            row=row, column=0, columnspan=2, sticky="ew", pady=(8, 0)
        )
        row += 1

        ttk.Label(frame, text="Nombre d'images:", style="Muted.TLabel").grid(
            row=row, column=0, sticky="w"
        )
        ttk.Label(frame, text=str(stats["dataset_size"])).grid(
            row=row, column=1, sticky="w"
        )
        row += 1

        ttk.Label(frame, text="Note moyenne:", style="Muted.TLabel").grid(
            row=row, column=0, sticky="w"
        )
        ttk.Label(
            frame,
            text=f"{stats['average_note']:.2f}" if stats["average_note"] else "-",
        ).grid(row=row, column=1, sticky="w")
        row += 1

        ttk.Label(frame, text="Images par classe:", style="Muted.TLabel").grid(
            row=row, column=0, sticky="nw", pady=(4, 0)
        )
        classes_text = ", ".join(
            f"{cls or '(sans classe)'}: {count}"
            for cls, count in stats["images_per_class"].items()
        ) or "-"
        ttk.Label(frame, text=classes_text, wraplength=320, justify="left").grid(
            row=row, column=1, sticky="w", pady=(4, 0)
        )

        ttk.Button(frame, text="Fermer", command=win.destroy).grid(
            row=row + 1, column=0, columnspan=2, pady=(12, 0)
        )

    # ------------------------------------------------------------------ #
    # Save / Save As / Reset
    # ------------------------------------------------------------------ #
    def save_image_action(self) -> None:
        """
        Save the processed image to disk.

        By default, images are written to `data/output_images/` to avoid
        overwriting raw data. Subsequent saves reuse the last chosen path.
        """
        if self.current_image is None:
            messagebox.showinfo("Enregistrer", "Aucune image à enregistrer.")
            return

        # Determine target path.
        if self.saved_image_path is not None:
            target = self.saved_image_path
        elif self.current_image_path is not None:
            target = OUTPUT_IMAGES_DIR / self.current_image_path.name
        else:
            target = OUTPUT_IMAGES_DIR / "image.png"

        try:
            out = save_image(self.current_image, target)
            self.saved_image_path = out
            messagebox.showinfo(
                "Enregistrer",
                f"Image enregistrée dans :\n{out}",
            )
        except Exception as exc:
            messagebox.showerror("Erreur d'enregistrement", str(exc))

    def save_image_as_action(self) -> None:
        """
        Save the processed image with a user-chosen path and format.
        """
        if self.current_image is None:
            messagebox.showinfo("Enregistrer sous", "Aucune image à enregistrer.")
            return

        initial_dir = OUTPUT_IMAGES_DIR
        initial_file = (
            self.current_image_path.name if self.current_image_path is not None else "image.png"
        )

        filetypes = [
            ("PNG", "*.png"),
            ("JPEG", "*.jpg;*.jpeg"),
            ("BMP", "*.bmp"),
            ("Tous les fichiers", "*.*"),
        ]
        path_str = filedialog.asksaveasfilename(
            title="Enregistrer l'image sous",
            defaultextension=".png",
            initialdir=str(initial_dir),
            initialfile=initial_file,
            filetypes=filetypes,
        )
        if not path_str:
            return

        target = Path(path_str)
        try:
            out = save_image(self.current_image, target)
            self.saved_image_path = out
            messagebox.showinfo(
                "Enregistrer sous",
                f"Image enregistrée dans :\n{out}",
            )
        except Exception as exc:
            messagebox.showerror("Erreur d'enregistrement", str(exc))

    def reset_image(self) -> None:
        """
        Reset the current image to its originally loaded pixels.
        """
        if self.original_image is None:
            return
        self.current_image = self.original_image.copy()
        self.history.clear()
        self.image_viewer.set_image(self.current_image)
        self._update_status_with_current_image()

    # ------------------------------------------------------------------ #
    # Simple generic placeholders / about dialogs
    # ------------------------------------------------------------------ #
    def not_implemented(self) -> None:
        messagebox.showinfo(
            "TkImage Studio",
            "Cette fonctionnalité sera disponible plus tard dans TkImage Studio.",
        )

    # Dataset navigation helpers
    def go_previous_image(self) -> None:
        """Navigate to the previous image in the current folder, if any."""
        if not self.image_folder_files:
            return
        new_index = self.current_index - 1
        if new_index < 0:
            return
        self._load_image_at_index(new_index)

    def go_next_image(self) -> None:
        """Navigate to the next image in the current folder, if any."""
        if not self.image_folder_files:
            return
        new_index = self.current_index + 1
        if new_index >= len(self.image_folder_files):
            return
        self._load_image_at_index(new_index)

    # ------------------------------------------------------------------ #
    # Image transformations & undo
    # ------------------------------------------------------------------ #
    def _push_history(self) -> None:
        """Store the current image in history for undo."""
        if self.current_image is None:
            return
        # Keep a copy so later mutations don't affect history.
        self.history.append(self.current_image.copy())
        # Limit history size.
        if len(self.history) > 10:
            self.history.pop(0)

    def undo(self) -> None:
        """Revert to the previous image state if available."""
        if not self.history:
            return
        prev = self.history.pop()
        self.current_image = prev
        if self.current_image is not None:
            self.image_viewer.set_image(self.current_image)
            self._update_status_with_current_image()

    def _apply_transformation(self, func: Callable[..., Image.Image], *args, **kwargs) -> None:
        """
        Apply a transformation function to the current image and update
        the viewer, while pushing the previous state onto the undo stack.
        """
        if self.current_image is None:
            return

        self._push_history()
        try:
            new_img = func(self.current_image, *args, **kwargs)
        except Exception as exc:  # pragma: no cover - defensive
            messagebox.showerror("Erreur traitement", str(exc))
            # Roll back history push on failure.
            if self.history:
                self.history.pop()
            return

        self.current_image = new_img
        self.image_viewer.set_image(new_img)
        self._update_status_with_current_image()

    # Concrete filter handlers wired to the menu.
    def apply_filter_grayscale(self) -> None:
        if self.current_image is None:
            return
        self._apply_transformation(image_processor.apply_grayscale)

    def apply_filter_blur(self) -> None:
        if self.current_image is None:
            return
        self._apply_transformation(image_processor.apply_blur)

    def apply_filter_sharpness(self) -> None:
        if self.current_image is None:
            return
        self._apply_transformation(image_processor.apply_sharpness, 1.8)

    def apply_filter_contrast(self) -> None:
        if self.current_image is None:
            return
        factor = simpledialog.askfloat(
            "Contraste",
            "Facteur de contraste (0.0-3.0, 1.0 = normal) :",
            parent=self.root,
            minvalue=0.0,
            maxvalue=3.0,
            initialvalue=1.2,
        )
        if factor is None:
            return
        self._apply_transformation(image_processor.apply_contrast, factor)

    def apply_filter_brightness(self) -> None:
        if self.current_image is None:
            return
        factor = simpledialog.askfloat(
            "Luminosité",
            "Facteur de luminosité (0.0-3.0, 1.0 = normal) :",
            parent=self.root,
            minvalue=0.0,
            maxvalue=3.0,
            initialvalue=1.1,
        )
        if factor is None:
            return
        self._apply_transformation(image_processor.apply_brightness, factor)

    def apply_filter_invert(self) -> None:
        if self.current_image is None:
            return
        self._apply_transformation(image_processor.apply_inversion)

    def apply_filter_autocontrast(self) -> None:
        if self.current_image is None:
            return
        self._apply_transformation(image_processor.apply_autocontrast)

    # Basic geometric tools (toolbar + future menu wiring)
    def resize_image_dialog(self) -> None:
        """Ask for new dimensions and resize the current image."""
        if self.current_image is None:
            return

        w, h = self.current_image.size
        new_w = simpledialog.askinteger(
            "Redimensionner",
            f"Nouvelle largeur (px) — actuelle {w} :",
            parent=self.root,
            minvalue=1,
            maxvalue=8192,
            initialvalue=w,
        )
        if new_w is None:
            return
        new_h = simpledialog.askinteger(
            "Redimensionner",
            f"Nouvelle hauteur (px) — actuelle {h} :",
            parent=self.root,
            minvalue=1,
            maxvalue=8192,
            initialvalue=h,
        )
        if new_h is None:
            return

        self._apply_transformation(image_processor.resize_image, new_w, new_h)

    def rotate_image_dialog(self) -> None:
        """Rotate the current image by a chosen angle."""
        if self.current_image is None:
            return

        angle = simpledialog.askinteger(
            "Pivoter",
            "Angle de rotation (90, 180, 270) :",
            parent=self.root,
            minvalue=0,
            maxvalue=360,
            initialvalue=90,
        )
        if angle is None:
            return

        self._apply_transformation(image_processor.rotate_image, angle)

    def compress_image_dialog(self) -> None:
        """
        Simple "compression" helper that rescales the image by a percentage.

        This is useful to quickly downscale high-resolution images for
        faster annotation and preview, even if we are not writing files yet.
        """
        if self.current_image is None:
            return

        percent = simpledialog.askinteger(
            "Compresser",
            "Échelle en pourcentage (par ex. 50 pour réduire à moitié) :",
            parent=self.root,
            minvalue=1,
            maxvalue=400,
            initialvalue=50,
        )
        if percent is None:
            return

        scale = percent / 100.0
        w, h = self.current_image.size
        new_w = max(1, int(w * scale))
        new_h = max(1, int(h * scale))
        self._apply_transformation(image_processor.resize_image, new_w, new_h)

    def crop_image_dialog(self) -> None:
        """
        Crop using numeric coordinates as a quick utility.

        Mouse-based ROI cropping will come in the dedicated step; here we
        provide a simple bounding box input.
        """
        if self.current_image is None:
            return

        w, h = self.current_image.size
        left = simpledialog.askinteger(
            "Rogner",
            f"Coordonnée gauche (0-{w-1}) :",
            parent=self.root,
            minvalue=0,
            maxvalue=max(0, w - 1),
            initialvalue=0,
        )
        if left is None:
            return
        top = simpledialog.askinteger(
            "Rogner",
            f"Coordonnée haute (0-{h-1}) :",
            parent=self.root,
            minvalue=0,
            maxvalue=max(0, h - 1),
            initialvalue=0,
        )
        if top is None:
            return
        right = simpledialog.askinteger(
            "Rogner",
            f"Coordonnée droite ({left+1}-{w}) :",
            parent=self.root,
            minvalue=min(w, left + 1),
            maxvalue=w,
            initialvalue=w,
        )
        if right is None:
            return
        bottom = simpledialog.askinteger(
            "Rogner",
            f"Coordonnée basse ({top+1}-{h}) :",
            parent=self.root,
            minvalue=min(h, top + 1),
            maxvalue=h,
            initialvalue=h,
        )
        if bottom is None:
            return

        box = (left, top, right, bottom)
        self._apply_transformation(image_processor.crop_image, box)

    def start_mouse_roi_crop(self) -> None:
        """
        Activate mouse-based ROI selection on the viewer.

        The user can drag a rectangle over the image; when released,
        the selected region is used to crop the image.
        """
        if self.current_image is None:
            return

        self._roi_mode_enabled = True
        self.status_label.config(
            text="Mode ROI souris — cliquez et faites glisser pour sélectionner une région.",
        )

        def on_box_selected(box: tuple[int, int, int, int]) -> None:
            # Apply crop with undo support.
            self._apply_transformation(image_processor.crop_image, box)
            self._roi_mode_enabled = False
            self._update_status_with_current_image()

        self.image_viewer.enable_roi_mode(on_box_selected)

    # Zoom controls (toolbar + menu)
    def zoom_in(self) -> None:
        if self.current_image is None:
            return
        self.image_viewer.zoom_in()

    def zoom_out(self) -> None:
        if self.current_image is None:
            return
        self.image_viewer.zoom_out()

    def fit_to_window(self) -> None:
        if self.current_image is None:
            return
        self.image_viewer.fit_to_window()

    # ------------------------------------------------------------------ #
    # Model training window
    # ------------------------------------------------------------------ #
    def open_training_window(self) -> None:
        """Open a dedicated window for CNN model training/testing."""
        image_paths: List[Path] = []
        if self.image_folder_files:
            image_paths = self.image_folder_files
        elif self.current_image_path is not None:
            image_paths = [self.current_image_path]

        TrainingWindow(self.root, image_paths=image_paths)

    # Dataset navigation helpers
    def go_previous_image(self) -> None:
        """Navigate to the previous image in the current folder, if any."""
        if not self.image_folder_files:
            return
        new_index = self.current_index - 1
        if new_index < 0:
            return
        self._load_image_at_index(new_index)

    def go_next_image(self) -> None:
        """Navigate to the next image in the current folder, if any."""
        if not self.image_folder_files:
            return
        new_index = self.current_index + 1
        if new_index >= len(self.image_folder_files):
            return
        self._load_image_at_index(new_index)

    def show_about_version(self) -> None:
        messagebox.showinfo("Version", "TkImage Studio — version 0.1 (pré-alpha)")

    def show_about_author(self) -> None:
        messagebox.showinfo("Auteur", "Conçu pour des workflows de classification inspirés de Roboflow.")

    def show_about_help(self) -> None:
        messagebox.showinfo(
            "Aide",
            "1. Fichier → Ouvrir image ou dossier\n"
            "2. Parcourez et préparez vos images pour la classification.",
        )


