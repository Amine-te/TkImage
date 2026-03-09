import tkinter as tk

try:
    # When running as a module: `python -m tkimage_studio.main`
    from .src.ui.main_window import MainWindow  # type: ignore[import]
except ImportError:
    # Fallback for running as a script: `python tkimage_studio/main.py`
    from src.ui.main_window import MainWindow  # type: ignore[import]


def main() -> None:
    """
    Entry point for the TkImage Studio application.

    Creates the main Tkinter root window, instantiates the MainWindow
    layout class, and starts the Tkinter event loop.
    """
    root = tk.Tk()
    try:
        from pathlib import Path
        icon_path = Path(__file__).parent / "static" / "image.png"
        icon = tk.PhotoImage(file=str(icon_path))
        root.iconphoto(False, icon)
    except Exception as e:
        print(f"Could not load application icon: {e}")
    MainWindow(root)
    root.mainloop()


if __name__ == "__main__":
    main()

