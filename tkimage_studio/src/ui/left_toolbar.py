from __future__ import annotations

import tkinter as tk
from tkinter import ttk


class LeftToolbar(ttk.Frame):
    """
    Vertical toolbar docked on the left side of the main window.

    Buttons are wired to callback keys so that the main window can
    provide concrete behavior (open, save, zoom, transforms, etc.).
    """

    def __init__(self, master: tk.Widget, callbacks: dict[str, callable] | None = None) -> None:
        super().__init__(master, padding=2)
        self.callbacks = callbacks or {}
        self._build_ui()

    # ------------------------------------------------------------------ #
    # UI construction
    # ------------------------------------------------------------------ #
    def _build_ui(self) -> None:
        """
        Build a very compact vertical strip of tool buttons.

        We avoid scrollbars for now to keep the toolbar visually slim
        and unobtrusive; the current number of tools fits comfortably
        on typical screens.
        """
        inner = ttk.Frame(self)
        inner.pack(fill="y", expand=False, padx=4, pady=4)

        # Helper to create a button bound to a callback key.
        def add_btn(text: str, key: str) -> None:
            btn = ttk.Button(
                inner,
                text=text,
                command=lambda k=key: self._invoke(k),
                width=12,
                style="Tool.TButton",
            )
            btn.pack(fill="x", pady=2)

        # Geometric transforms and utilities focused on image operations.
        add_btn("Redimensionner", "tool_resize")
        add_btn("Compresser", "tool_compress")
        add_btn("Rogner", "tool_crop_dialog")
        add_btn("Pivoter", "tool_rotate")

        ttk.Separator(inner, orient="horizontal").pack(fill="x", pady=4)

        # Mouse tools
        add_btn("Souris ROI", "tool_mouse_crop")
        add_btn("Repère", "tool_pointer")

        ttk.Separator(inner, orient="horizontal").pack(fill="x", pady=4)

        # Zoom controls
        add_btn("Zoom +", "view_zoom_in")
        add_btn("Zoom -", "view_zoom_out")
        add_btn("Adapter", "view_fit_window")

        ttk.Separator(inner, orient="horizontal").pack(fill="x", pady=4)

        # Dataset tools
        add_btn("Stats", "tool_stats")

    # ------------------------------------------------------------------ #
    # Callbacks
    # ------------------------------------------------------------------ #
    def _invoke(self, key: str) -> None:
        """Invoke a callback if available."""
        cb = self.callbacks.get(key)
        if cb is not None:
            cb()

