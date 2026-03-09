from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Tuple


class StatusPanel(ttk.Frame):
    """
    Bottom annotation and metadata bar.

    Shows basic file information and allows entering simple
    classification-related metadata for the current image.
    """

    def __init__(self, master: tk.Widget) -> None:
        super().__init__(master, padding=(16, 8))

        # Metadata summary line
        self._summary_label = ttk.Label(
            self,
            text="Prêt — aucune image chargée",
            anchor="w",
            style="Muted.TLabel",
        )
        self._summary_label.grid(row=0, column=0, columnspan=6, sticky="ew", pady=(0, 4))

        # Detailed metadata
        ttk.Label(self, text="Fichier:", style="Muted.TLabel").grid(
            row=1, column=0, sticky="w"
        )
        self._filename_value = ttk.Label(self, text="-")
        self._filename_value.grid(row=1, column=1, sticky="w")

        ttk.Label(self, text="Taille:", style="Muted.TLabel").grid(
            row=1, column=2, sticky="w", padx=(8, 0)
        )
        self._size_value = ttk.Label(self, text="-")
        self._size_value.grid(row=1, column=3, sticky="w")

        ttk.Label(self, text="Mode:", style="Muted.TLabel").grid(
            row=1, column=4, sticky="w", padx=(8, 0)
        )
        self._mode_value = ttk.Label(self, text="-")
        self._mode_value.grid(row=1, column=5, sticky="w")

        ttk.Label(self, text="Poids:", style="Muted.TLabel").grid(
            row=1, column=6, sticky="w", padx=(8, 0)
        )
        self._filesize_value = ttk.Label(self, text="-")
        self._filesize_value.grid(row=1, column=7, sticky="w")

        # Annotation fields (compact)
        ttk.Label(self, text="Description:", style="Muted.TLabel").grid(
            row=2, column=0, sticky="w", pady=(4, 0)
        )
        self.description_entry = ttk.Entry(self, width=40)
        self.description_entry.grid(row=2, column=1, columnspan=3, sticky="ew", pady=(4, 0))

        ttk.Label(self, text="Note (1–5):", style="Muted.TLabel").grid(
            row=2, column=4, sticky="w", padx=(8, 0), pady=(4, 0)
        )
        self.note_spin = ttk.Spinbox(self, from_=1, to=5, width=4)
        self.note_spin.set("3")
        self.note_spin.grid(row=2, column=5, sticky="w", pady=(4, 0))

        ttk.Label(self, text="Classe:", style="Muted.TLabel").grid(
            row=3, column=0, sticky="w", pady=(4, 0)
        )
        self.class_entry = ttk.Entry(self, width=20)
        self.class_entry.grid(row=3, column=1, sticky="w", pady=(4, 0))

        ttk.Label(self, text="Tags:", style="Muted.TLabel").grid(
            row=3, column=2, sticky="w", padx=(8, 0), pady=(4, 0)
        )
        self.tags_entry = ttk.Entry(self, width=30)
        self.tags_entry.grid(row=3, column=3, columnspan=3, sticky="ew", pady=(4, 0))

        # Grid behavior
        for col in range(0, 8):
            weight = 1 if col in (1, 3) else 0
            self.columnconfigure(col, weight=weight)

    # ------------------------------------------------------------------ #
    # Metadata handling
    # ------------------------------------------------------------------ #
    def update_metadata(
        self,
        index: int,
        total: int,
        filename: str,
        width: int,
        height: int,
        mode: str,
        file_size_kb: float,
    ) -> None:
        """Update file-related information in the panel."""
        if filename:
            prefix = f"[{index}/{total}] " if total > 0 and index > 0 else ""
            summary = f"{prefix}{filename} — {width}x{height} {mode}, {file_size_kb:.1f} Ko"
        else:
            summary = "Prêt — aucune image chargée"

        self._summary_label.config(text=summary)
        self._filename_value.config(text=filename or "-")
        self._size_value.config(text=f"{width}x{height}" if width and height else "-")
        self._mode_value.config(text=mode or "-")
        self._filesize_value.config(text=f"{file_size_kb:.1f} Ko" if file_size_kb else "-")

    def set_message(self, text: str) -> None:
        """
        Update only the summary message line.

        Used for transient statuses such as ROI mode hints without
        touching the detailed metadata fields.
        """
        self._summary_label.config(text=text)

    # ------------------------------------------------------------------ #
    # Annotation handling
    # ------------------------------------------------------------------ #
    def set_annotation(
        self,
        description: str,
        note: int,
        classe: str,
        tags: str,
    ) -> None:
        self.description_entry.delete(0, tk.END)
        self.description_entry.insert(0, description or "")
        self.note_spin.delete(0, tk.END)
        self.note_spin.insert(0, str(note or 0))
        self.class_entry.delete(0, tk.END)
        self.class_entry.insert(0, classe or "")
        self.tags_entry.delete(0, tk.END)
        self.tags_entry.insert(0, tags or "")

    def get_annotation(self) -> Tuple[str, int, str, str]:
        description = self.description_entry.get().strip()
        try:
            note = int(self.note_spin.get())
        except ValueError:
            note = 0
        classe = self.class_entry.get().strip()
        tags = self.tags_entry.get().strip()
        return description, note, classe, tags

