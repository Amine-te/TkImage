from __future__ import annotations

import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pathlib import Path
from typing import List, Optional

from ..core import classification_manager


class TrainingWindow(tk.Toplevel):
    """
    Separate window to configure and launch a simple CNN training run
    based on existing annotations.
    """

    def __init__(self, master: tk.Tk, image_paths: List[Path]) -> None:
        super().__init__(master)
        self.title("Entraînement de modèle de classification")
        self.transient(master)

        self.model: Optional[object] = None
        self._training_thread: Optional[threading.Thread] = None
        self.image_paths: List[Path] = image_paths

        self._build_ui()

    def _build_ui(self) -> None:
        main = ttk.Frame(self, padding=12)
        main.grid(row=0, column=0, sticky="nsew")
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

        # Dataset info (uses current images from main UI)
        count = len(self.image_paths)
        ttk.Label(
            main,
            text=f"Dataset courant : {count} image(s) chargée(s) dans l'interface principale.",
            anchor="w",
        ).grid(row=0, column=0, columnspan=3, sticky="w")

        # Model selection
        ttk.Label(main, text="Modèle :", anchor="w").grid(row=1, column=0, sticky="w", pady=(8, 0))
        self.model_combo = ttk.Combobox(
            main,
            values=classification_manager.available_models(),
            state="readonly",
            width=20,
        )
        self.model_combo.set("simple_cnn")
        self.model_combo.grid(row=1, column=1, sticky="w", pady=(8, 0))

        # Hyperparameters
        ttk.Label(main, text="Époques :", anchor="w").grid(row=2, column=0, sticky="w", pady=(4, 0))
        self.epochs_entry = ttk.Entry(main, width=6)
        self.epochs_entry.insert(0, "5")
        self.epochs_entry.grid(row=2, column=1, sticky="w", pady=(4, 0))

        ttk.Label(main, text="Taille de lot :", anchor="w").grid(
            row=3, column=0, sticky="w", pady=(4, 0)
        )
        self.batch_entry = ttk.Entry(main, width=6)
        self.batch_entry.insert(0, "8")
        self.batch_entry.grid(row=3, column=1, sticky="w", pady=(4, 0))

        ttk.Label(main, text="Taux d'apprentissage :", anchor="w").grid(
            row=4, column=0, sticky="w", pady=(4, 0)
        )
        self.lr_entry = ttk.Entry(main, width=8)
        self.lr_entry.insert(0, "0.001")
        self.lr_entry.grid(row=4, column=1, sticky="w", pady=(4, 0))

        # Controls
        train_btn = ttk.Button(main, text="Lancer l'entraînement", command=self._on_train_clicked)
        train_btn.grid(row=5, column=0, columnspan=3, sticky="ew", pady=(8, 4))

        test_btn = ttk.Button(main, text="Tester sur une image…", command=self._on_test_clicked)
        test_btn.grid(row=6, column=0, columnspan=3, sticky="ew", pady=(0, 8))

        # Log area
        ttk.Label(main, text="Journal d'entraînement :", anchor="w").grid(
            row=7, column=0, columnspan=3, sticky="w"
        )
        self.log_text = tk.Text(main, height=12, width=60, state="disabled")
        self.log_text.grid(row=8, column=0, columnspan=3, sticky="nsew", pady=(2, 0))

        main.rowconfigure(8, weight=1)
        main.columnconfigure(1, weight=1)

    # ------------------------------------------------------------------ #
    # Helper methods
    # ------------------------------------------------------------------ #
    def _append_log(self, text: str) -> None:
        self.log_text.configure(state="normal")
        self.log_text.insert(tk.END, text + "\n")
        self.log_text.see(tk.END)
        self.log_text.configure(state="disabled")
        self.update_idletasks()

    def _on_train_clicked(self) -> None:
        if self._training_thread is not None and self._training_thread.is_alive():
            messagebox.showinfo("Entraînement", "Un entraînement est déjà en cours.")
            return

        if not self.image_paths:
            messagebox.showinfo(
                "Entraînement",
                "Aucun dataset n'est chargé dans l'interface principale.\n"
                "Ouvrez un dossier d'images puis relancez cette fenêtre.",
            )
            return

        try:
            epochs = int(self.epochs_entry.get())
            batch_size = int(self.batch_entry.get())
            lr = float(self.lr_entry.get())
        except ValueError:
            messagebox.showerror(
                "Paramètres incorrects",
                "Époques, taille de lot et taux d'apprentissage doivent être numériques.",
            )
            return

        model_name = self.model_combo.get()

        config = classification_manager.TrainingConfig(
            image_paths=self.image_paths,
            model_name=model_name,
            num_epochs=epochs,
            batch_size=batch_size,
            learning_rate=lr,
            image_size=128,
            device="cpu",
        )

        def run_training() -> None:
            try:
                self._append_log("Démarrage de l'entraînement…")
                model, metrics = classification_manager.train_model(
                    config,
                    log_fn=self._append_log,
                )
                self.model = model
                self._append_log(
                    f"Terminé. Perte finale: {metrics['train_loss']:.4f}, "
                    f"Précision: {metrics['train_accuracy']:.3f}",
                )
                messagebox.showinfo(
                    "Entraînement terminé",
                    "Le modèle a été entraîné. Utilisez 'Tester sur une image…' pour évaluer.",
                )
            except Exception as exc:
                self._append_log(f"Erreur: {exc}")
                messagebox.showerror("Erreur d'entraînement", str(exc))

        self._training_thread = threading.Thread(target=run_training, daemon=True)
        self._training_thread.start()

    def _on_test_clicked(self) -> None:
        if self.model is None:
            messagebox.showinfo(
                "Tester un modèle",
                "Aucun modèle n'a encore été entraîné dans cette session.",
            )
            return

        path_str = filedialog.askopenfilename(
            title="Choisir une image de test",
            filetypes=[("Images", "*.png *.jpg *.jpeg *.bmp *.tiff *.tif"), ("Tous les fichiers", "*.*")],
        )
        if not path_str:
            return

        path = Path(path_str)
        try:
            predicted, scores = classification_manager.predict_single(self.model, path)
        except Exception as exc:
            messagebox.showerror("Erreur de prédiction", str(exc))
            return

        details = "\n".join(f"{cls}: {p:.2%}" for cls, p in scores)
        messagebox.showinfo(
            "Résultat de la prédiction",
            f"Classe prédite: {predicted}\n\nScores:\n{details}",
        )
        self._append_log(f"Test sur {path.name} → {predicted}")

