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
    MainWindow(root)
    root.mainloop()


if __name__ == "__main__":
    main()

