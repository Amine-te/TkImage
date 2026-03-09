from __future__ import annotations

import tkinter as tk
from tkinter import ttk


class RightPanel(ttk.Frame):
    """
    Right-side annotation panel.

    Mirrors the annotation fields from the bottom status bar and can be
    used as a more spacious view for classification metadata.
    """

    def __init__(self, master: tk.Widget) -> None:
        super().__init__(master, style="Card.TFrame", padding=16)

        ttk.Label(self, text="Annotations", anchor="w").grid(
            row=0, column=0, columnspan=2, sticky="ew", pady=(0, 4)
        )

        ttk.Label(self, text="Description:", style="Muted.TLabel").grid(
            row=1, column=0, sticky="nw", pady=(4, 0)
        )
        self.description_text = tk.Text(self, height=4, width=24, wrap="word")
        self.description_text.grid(row=1, column=1, sticky="nsew", pady=(4, 0))

        ttk.Label(self, text="Note (1–5):", style="Muted.TLabel").grid(
            row=2, column=0, sticky="w", pady=(4, 0)
        )
        self.note_spin = ttk.Spinbox(self, from_=1, to=5, width=4)
        self.note_spin.set("3")
        self.note_spin.grid(row=2, column=1, sticky="w", pady=(4, 0))

        ttk.Label(self, text="Classe / catégorie:", style="Muted.TLabel").grid(
            row=3, column=0, sticky="w", pady=(4, 0)
        )
        self.class_entry = ttk.Entry(self, width=20)
        self.class_entry.grid(row=3, column=1, sticky="ew", pady=(4, 0))

        ttk.Label(self, text="Tags (séparés par des virgules):", style="Muted.TLabel").grid(
            row=4, column=0, sticky="w", pady=(4, 0)
        )
        self.tags_entry = ttk.Entry(self, width=24)
        self.tags_entry.grid(row=4, column=1, sticky="ew", pady=(4, 0))

        # Layout behavior
        self.columnconfigure(0, weight=0)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(1, weight=1)

    # ------------------------------------------------------------------ #
    # Public API for synchronization with StatusPanel
    # ------------------------------------------------------------------ #
    def set_annotation(
        self,
        description: str,
        note: int,
        classe: str,
        tags: str,
    ) -> None:
        self.description_text.delete("1.0", tk.END)
        self.description_text.insert("1.0", description or "")

        self.note_spin.delete(0, tk.END)
        self.note_spin.insert(0, str(note or 0))

        self.class_entry.delete(0, tk.END)
        self.class_entry.insert(0, classe or "")

        self.tags_entry.delete(0, tk.END)
        self.tags_entry.insert(0, tags or "")

