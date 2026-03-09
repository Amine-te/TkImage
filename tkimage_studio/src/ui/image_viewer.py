from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Optional, Tuple, Callable

from PIL import Image, ImageTk


class ImageViewer(ttk.Frame):
    """
    Central image viewing area using a Tkinter Canvas.

    Handles displaying a single PIL Image, scaled to fit while
    preserving aspect ratio. Further interaction (zoom, ROI, etc.)
    will be built on top of this widget.
    """

    def __init__(self, master: tk.Widget) -> None:
        super().__init__(master)
        self.canvas = tk.Canvas(self, bg="#f3f4f6", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        self._pil_image: Optional[Image.Image] = None
        self._tk_image: Optional[ImageTk.PhotoImage] = None
        self._image_id: Optional[int] = None

        # Parameters describing how the current image is displayed.
        self._display_scale: float = 1.0
        self._display_offset_x: int = 0  # top-left of displayed image in canvas coords
        self._display_offset_y: int = 0

        # Zoom / pan state
        self._zoom: float = 1.0
        self._min_zoom: float = 0.25
        self._max_zoom: float = 6.0
        self._keep_offsets: bool = False
        self._pan_active: bool = False
        self._pan_start_canvas: Optional[Tuple[int, int]] = None
        self._pan_start_offset: Optional[Tuple[int, int]] = None

        # ROI selection state
        self._roi_active: bool = False
        self._roi_start: Optional[Tuple[int, int]] = None
        self._roi_rect_id: Optional[int] = None
        self._roi_callback: Optional[Callable[[Tuple[int, int, int, int]], None]] = None

        # Redraw image when the viewer is resized.
        self.canvas.bind("<Configure>", self._on_resize)

        # Mouse wheel zoom and middle-button pan.
        self.canvas.bind("<MouseWheel>", self._on_mouse_wheel)
        self.canvas.bind("<Button-2>", self._on_pan_start)
        self.canvas.bind("<B2-Motion>", self._on_pan_move)
        self.canvas.bind("<ButtonRelease-2>", self._on_pan_end)

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #
    def set_image(self, image: Image.Image) -> None:
        """
        Set the image to display.

        The image is stored and then rendered to fit the available canvas
        area while preserving aspect ratio.
        """
        self._pil_image = image
        # Reset zoom and centering when a new image is set.
        self._zoom = 1.0
        self._display_offset_x = 0
        self._display_offset_y = 0
        self._render_image()

    def enable_roi_mode(self, callback: Callable[[Tuple[int, int, int, int]], None]) -> None:
        """
        Enable mouse-based ROI selection.

        When the user drags with the left button and releases it, the
        callback is invoked with a bounding box in image coordinates.
        """
        self._roi_active = True
        self._roi_callback = callback
        self._roi_start = None
        if self._roi_rect_id is not None:
            self.canvas.delete(self._roi_rect_id)
            self._roi_rect_id = None

        self.canvas.bind("<Button-1>", self._on_mouse_down)
        self.canvas.bind("<B1-Motion>", self._on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_mouse_up)

    def disable_roi_mode(self) -> None:
        """Disable ROI selection and remove any temporary rectangle."""
        self._roi_active = False
        self._roi_callback = None
        self._roi_start = None

        if self._roi_rect_id is not None:
            self.canvas.delete(self._roi_rect_id)
            self._roi_rect_id = None

        # Unbind ROI-specific handlers but keep resize handler.
        self.canvas.unbind("<Button-1>")
        self.canvas.unbind("<B1-Motion>")
        self.canvas.unbind("<ButtonRelease-1>")

    def get_image_size(self) -> Optional[Tuple[int, int]]:
        """Return the underlying image size in pixels if present."""
        if self._pil_image is None:
            return None
        return self._pil_image.size

    def zoom_in(self) -> None:
        """Increase zoom level and redraw."""
        self._set_zoom(self._zoom * 1.25)

    def zoom_out(self) -> None:
        """Decrease zoom level and redraw."""
        self._set_zoom(self._zoom / 1.25)

    def fit_to_window(self) -> None:
        """Reset zoom and center the image within the canvas."""
        self._zoom = 1.0
        self._display_offset_x = 0
        self._display_offset_y = 0
        self._render_image()

    # ------------------------------------------------------------------ #
    # Internal helpers
    # ------------------------------------------------------------------ #
    def _on_resize(self, event: tk.Event) -> None:  # type: ignore[type-arg]
        if self._pil_image is not None:
            self._render_image()

    def _render_image(self) -> None:
        """Render the current PIL image into the canvas, scaled to fit."""
        if self._pil_image is None:
            return

        canvas_width = max(self.canvas.winfo_width(), 1)
        canvas_height = max(self.canvas.winfo_height(), 1)

        # Compute base scale to fit, then apply zoom factor.
        img_w, img_h = self._pil_image.size
        base_scale = min(canvas_width / img_w, canvas_height / img_h)
        scale = base_scale * self._zoom
        new_w = max(int(img_w * scale), 1)
        new_h = max(int(img_h * scale), 1)
        self._display_scale = scale

        resized = self._pil_image.resize((new_w, new_h), Image.LANCZOS)
        self._tk_image = ImageTk.PhotoImage(resized)

        # Center the image unless we intentionally keep offsets (during pan).
        if not self._keep_offsets or self._image_id is None:
            self._display_offset_x = (canvas_width - new_w) // 2
            self._display_offset_y = (canvas_height - new_h) // 2

        # Clear previous content and draw at current offsets.
        self.canvas.delete("all")
        center_x = self._display_offset_x + new_w // 2
        center_y = self._display_offset_y + new_h // 2
        self._image_id = self.canvas.create_image(
            center_x,
            center_y,
            image=self._tk_image,
            anchor="center",
        )

    # ------------------------------------------------------------------
    # ROI mouse handlers
    # ------------------------------------------------------------------
    def _on_mouse_down(self, event: tk.Event) -> None:  # type: ignore[type-arg]
        if not self._roi_active:
            return
        self._roi_start = (event.x, event.y)
        if self._roi_rect_id is not None:
            self.canvas.delete(self._roi_rect_id)
            self._roi_rect_id = None

    def _on_mouse_drag(self, event: tk.Event) -> None:  # type: ignore[type-arg]
        if not self._roi_active or self._roi_start is None:
            return
        x0, y0 = self._roi_start
        x1, y1 = event.x, event.y

        if self._roi_rect_id is None:
            self._roi_rect_id = self.canvas.create_rectangle(
                x0,
                y0,
                x1,
                y1,
                outline="#7c3aed",
                width=2,
                dash=(4, 2),
            )
        else:
            self.canvas.coords(self._roi_rect_id, x0, y0, x1, y1)

    def _on_mouse_up(self, event: tk.Event) -> None:  # type: ignore[type-arg]
        if not self._roi_active or self._roi_start is None or self._roi_callback is None:
            return

        x0, y0 = self._roi_start
        x1, y1 = event.x, event.y

        # Normalize coordinates.
        left_c = min(x0, x1)
        right_c = max(x0, x1)
        top_c = min(y0, y1)
        bottom_c = max(y0, y1)

        # Map canvas coordinates back to image coordinates.
        if self._display_scale <= 0 or self._pil_image is None:
            return

        img_w, img_h = self._pil_image.size

        def to_img_x(cx: int) -> int:
            return int((cx - self._display_offset_x) / self._display_scale)

        def to_img_y(cy: int) -> int:
            return int((cy - self._display_offset_y) / self._display_scale)

        left = max(0, min(img_w, to_img_x(left_c)))
        right = max(0, min(img_w, to_img_x(right_c)))
        top = max(0, min(img_h, to_img_y(top_c)))
        bottom = max(0, min(img_h, to_img_y(bottom_c)))

        if right - left <= 1 or bottom - top <= 1:
            # Too small; ignore selection.
            self.disable_roi_mode()
            return

        box = (left, top, right, bottom)
        # Call the callback in image coordinates.
        self._roi_callback(box)
        # Disable ROI mode after one selection.
        self.disable_roi_mode()

    # ------------------------------------------------------------------
    # Zoom & pan helpers
    # ------------------------------------------------------------------
    def _set_zoom(self, zoom: float) -> None:
        """Clamp and apply a new zoom value."""
        zoom = max(self._min_zoom, min(self._max_zoom, zoom))
        if abs(zoom - self._zoom) < 1e-3:
            return
        self._zoom = zoom
        self._display_offset_x = 0
        self._display_offset_y = 0
        self._render_image()

    def _on_mouse_wheel(self, event: tk.Event) -> str:  # type: ignore[type-arg]
        """
        Zoom in/out with the mouse wheel.

        Positive delta → zoom in, negative delta → zoom out.
        """
        if event.delta > 0:
            self.zoom_in()
        elif event.delta < 0:
            self.zoom_out()
        return "break"

    def _on_pan_start(self, event: tk.Event) -> None:  # type: ignore[type-arg]
        if self._pil_image is None:
            return
        self._pan_active = True
        self._pan_start_canvas = (event.x, event.y)
        self._pan_start_offset = (self._display_offset_x, self._display_offset_y)

    def _on_pan_move(self, event: tk.Event) -> None:  # type: ignore[type-arg]
        if not self._pan_active or self._pan_start_canvas is None or self._pan_start_offset is None:
            return
        dx = event.x - self._pan_start_canvas[0]
        dy = event.y - self._pan_start_canvas[1]
        self._display_offset_x = self._pan_start_offset[0] + dx
        self._display_offset_y = self._pan_start_offset[1] + dy

        # Re-render while preserving offsets.
        self._keep_offsets = True
        self._render_image()
        self._keep_offsets = False

    def _on_pan_end(self, _event: tk.Event) -> None:  # type: ignore[type-arg]
        self._pan_active = False
        self._pan_start_canvas = None
        self._pan_start_offset = None

