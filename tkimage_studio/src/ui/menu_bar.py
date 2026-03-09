from __future__ import annotations

import tkinter as tk
from tkinter import messagebox


class MenuBar:
    """
    Application menu bar for TkImage Studio.

    For now, all actions are wired to placeholder callbacks that either
    call a provided function from `callbacks` (when available) or show
    a simple message box / print to the console.
    """

    def __init__(self, root: tk.Tk, callbacks: dict[str, callable] | None = None) -> None:
        self.root = root
        self.callbacks = callbacks or {}

        self.menubar = tk.Menu(self.root)
        self._build_menus()

        # Attach the menu bar to the root window.
        self.root.config(menu=self.menubar)

    # ------------------------------------------------------------------ #
    # Menu construction helpers
    # ------------------------------------------------------------------ #
    def _build_menus(self) -> None:
        """Build all top-level menus."""
        self._build_file_menu()
        self._build_edit_menu()
        self._build_filters_menu()
        self._build_segmentation_menu()
        self._build_visualisation_menu()
        self._build_models_menu()
        self._build_about_menu()

    def _add_command(
        self,
        menu: tk.Menu,
        label: str,
        command_key: str,
        accelerator: str | None = None,
    ) -> None:
        """
        Add a command to a menu, resolving the actual callback from
        the callbacks mapping, or falling back to a generic placeholder.
        """
        callback = self.callbacks.get(
            command_key,
            lambda key=command_key: self._not_implemented(label, key),
        )
        menu.add_command(label=label, command=callback, accelerator=accelerator or "")

    # ------------------------------------------------------------------ #
    # Individual menus
    # ------------------------------------------------------------------ #
    def _build_file_menu(self) -> None:
        fichier_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="Fichier", menu=fichier_menu)

        self._add_command(fichier_menu, "Ouvrir image", "file_open_image", "Ctrl+O")
        self._add_command(fichier_menu, "Ouvrir dossier", "file_open_folder", "Ctrl+Shift+O")
        fichier_menu.add_separator()
        self._add_command(fichier_menu, "Enregistrer", "file_save", "Ctrl+S")
        self._add_command(fichier_menu, "Enregistrer sous", "file_save_as", "Ctrl+Shift+S")
        fichier_menu.add_separator()
        self._add_command(
            fichier_menu,
            "Importer annotations",
            "file_import_annotations",
        )
        self._add_command(
            fichier_menu,
            "Importer annotations",
            "file_import_annotations",
        )
        self._add_command(
            fichier_menu,
            "Exporter annotations",
            "file_export_annotations",
        )
        fichier_menu.add_separator()
        self._add_command(fichier_menu, "Quitter", "file_quit", "Ctrl+Q")

    def _build_edit_menu(self) -> None:
        edit_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="Édition", menu=edit_menu)

        self._add_command(edit_menu, "Annuler", "edit_undo", "Ctrl+Z")
        self._add_command(edit_menu, "Rétablir", "edit_redo", "Ctrl+Y")
        edit_menu.add_separator()
        self._add_command(
            edit_menu,
            "Supprimer de la session",
            "edit_remove_from_session",
        )
        self._add_command(
            edit_menu,
            "Réinitialiser l'image",
            "edit_reset_image",
        )

    def _build_filters_menu(self) -> None:
        filters_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="Filtres", menu=filters_menu)

        self._add_command(filters_menu, "Niveaux de gris", "filter_grayscale")
        self._add_command(filters_menu, "Flou", "filter_blur")
        self._add_command(filters_menu, "Netteté", "filter_sharpness")
        self._add_command(filters_menu, "Contraste", "filter_contrast")
        self._add_command(filters_menu, "Luminosité", "filter_brightness")
        self._add_command(filters_menu, "Inversion", "filter_invert")
        self._add_command(filters_menu, "Autocontraste", "filter_autocontrast")

    def _build_segmentation_menu(self) -> None:
        seg_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="Segmentation", menu=seg_menu)

        self._add_command(seg_menu, "Seuillage simple", "seg_threshold")
        self._add_command(seg_menu, "Masque binaire", "seg_binary_mask")
        self._add_command(seg_menu, "Extraction ROI", "seg_extract_roi")

    def _build_visualisation_menu(self) -> None:
        vis_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="Visualisation 3D", menu=vis_menu)

        self._add_command(vis_menu, "Carte simulée", "vis_heatmap")
        self._add_command(vis_menu, "Surface d'intensité", "vis_surface")
        self._add_command(vis_menu, "Empilement de couches", "vis_stack_channels")

    def _build_models_menu(self) -> None:
        models_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="Modèles", menu=models_menu)

        self._add_command(
            models_menu,
            "Entraîner un modèle de classification…",
            "model_open_training_window",
        )

    def _build_about_menu(self) -> None:
        about_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="À propos", menu=about_menu)

        self._add_command(about_menu, "Version", "about_version")
        self._add_command(about_menu, "Auteur", "about_author")
        self._add_command(about_menu, "Aide", "about_help")

    # ------------------------------------------------------------------ #
    # Fallback handler
    # ------------------------------------------------------------------ #
    def _not_implemented(self, label: str, key: str) -> None:
        """
        Generic handler used when no concrete callback is supplied
        for a given menu item.
        """
        message = f"Action « {label} » ({key}) non implémentée pour le moment."
        print(message)
        try:
            messagebox.showinfo("TkImage Studio", message)
        except tk.TclError:
            # If the messagebox cannot be displayed (e.g. during tests),
            # we silently ignore the GUI error.
            pass

