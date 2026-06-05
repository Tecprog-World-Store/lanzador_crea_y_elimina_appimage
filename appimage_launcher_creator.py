#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AppImage Launcher Creator
Autoría: TECPROG WORLD E.I.R.L.
Sitio web: https://tecprog-world-store.github.io/

Descripción:
    Software GUI en Tkinter para crear lanzadores .desktop de aplicaciones
    AppImage en Linux Mint, Ubuntu, Debian y variantes con entornos de escritorio
    compatibles con especificaciones XDG.

Uso:
    python3 appimage_launcher_creator.py

Empaquetado futuro:
    - PyInstaller para ejecutable local.
    - Paquete .deb instalando el binario en /usr/bin y el .desktop del software
      en /usr/share/applications.

Dependencias:
    - Python 3
    - Tkinter
    - Pillow opcional para previsualizar JPG/WebP.
"""

import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except Exception:
    PIL_AVAILABLE = False


APP_TITLE = "AppImage Launcher Creator"
AUTHOR = "TECPROG WORLD E.I.R.L."
WEBSITE = "https://tecprog-world-store.github.io/"

VALID_IMAGE_EXTENSIONS = {".png", ".svg", ".xpm", ".jpg", ".jpeg", ".webp"}
VALID_APPIMAGE_EXTENSIONS = {".appimage", ".AppImage"}


def slugify(value: str) -> str:
    """Convierte un nombre de aplicación en un identificador seguro."""
    value = value.strip().lower()
    value = re.sub(r"\s+", "-", value)
    value = re.sub(r"[^a-z0-9._-]", "", value)
    value = value.strip(".-_")
    return value or "appimage-app"


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def is_appimage(path: Path) -> bool:
    return path.is_file() and path.name.lower().endswith(".appimage")


def is_valid_image(path: Path) -> bool:
    return path.is_file() and path.suffix.lower() in VALID_IMAGE_EXTENSIONS


def run_command(command: list[str]) -> tuple[int, str]:
    """Ejecuta un comando y devuelve código + salida acumulada."""
    try:
        proc = subprocess.run(
            command,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )
        return proc.returncode, proc.stdout.strip()
    except Exception as exc:
        return 1, str(exc)


class ScrollableFrame(ttk.Frame):
    """Contenedor con scroll vertical para pantallas pequeñas."""

    def __init__(self, parent):
        super().__init__(parent)
        self.canvas = tk.Canvas(self, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.content = ttk.Frame(self.canvas)

        self.content.bind(
            "<Configure>",
            lambda event: self.canvas.configure(scrollregion=self.canvas.bbox("all")),
        )

        self.window_id = self.canvas.create_window((0, 0), window=self.content, anchor="nw")

        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.scrollbar.grid(row=0, column=1, sticky="ns")

        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

        self.canvas.bind("<Configure>", self._on_canvas_configure)
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind_all("<Button-4>", self._on_linux_scroll_up)
        self.canvas.bind_all("<Button-5>", self._on_linux_scroll_down)

    def _on_canvas_configure(self, event):
        self.canvas.itemconfigure(self.window_id, width=event.width)

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _on_linux_scroll_up(self, event):
        self.canvas.yview_scroll(-3, "units")

    def _on_linux_scroll_down(self, event):
        self.canvas.yview_scroll(3, "units")


class AppImageLauncherCreator(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.minsize(820, 620)

        # Tamaño inicial relativo a la pantalla.
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        width = min(980, max(820, int(screen_w * 0.78)))
        height = min(760, max(620, int(screen_h * 0.82)))
        self.geometry(f"{width}x{height}")

        self.appimage_path = tk.StringVar()
        self.icon_path = tk.StringVar()
        self.app_name = tk.StringVar()
        self.app_comment = tk.StringVar(value="Aplicación AppImage integrada al menú de Linux")
        self.generic_name = tk.StringVar(value="AppImage Application")
        self.categories = tk.StringVar(value="Utility;")
        self.terminal = tk.BooleanVar(value=False)
        self.startup_notify = tk.BooleanVar(value=True)
        self.overwrite = tk.BooleanVar(value=True)
        self.keep_original = tk.BooleanVar(value=True)

        self.install_id = tk.StringVar()
        self.exec_args = tk.StringVar()
        self.status = tk.StringVar(value="Seleccione un archivo .AppImage para empezar.")

        self.icon_preview = None
        self._build_ui()

    def _build_ui(self):
        root = ttk.Frame(self, padding=10)
        root.grid(row=0, column=0, sticky="nsew")
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

        header = ttk.Frame(root)
        header.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        header.columnconfigure(0, weight=1)

        ttk.Label(
            header,
            text=APP_TITLE,
            font=("TkDefaultFont", 18, "bold"),
        ).grid(row=0, column=0, sticky="w")

        ttk.Label(
            header,
            text=f"{AUTHOR}  |  {WEBSITE}",
            foreground="#4b5563",
        ).grid(row=1, column=0, sticky="w", pady=(2, 0))

        scroll = ScrollableFrame(root)
        scroll.grid(row=1, column=0, sticky="nsew")
        root.rowconfigure(1, weight=1)
        root.columnconfigure(0, weight=1)

        form = scroll.content
        for col in range(4):
            form.columnconfigure(col, weight=1 if col in (1, 2) else 0)

        # Sección AppImage
        app_frame = ttk.LabelFrame(form, text="1. Archivo AppImage", padding=10)
        app_frame.grid(row=0, column=0, columnspan=4, sticky="ew", pady=8)
        app_frame.columnconfigure(1, weight=1)

        ttk.Label(app_frame, text="Ruta del AppImage:").grid(row=0, column=0, sticky="w", padx=(0, 8))
        ttk.Entry(app_frame, textvariable=self.appimage_path).grid(row=0, column=1, sticky="ew")
        ttk.Button(app_frame, text="Examinar...", command=self.browse_appimage).grid(row=0, column=2, padx=(8, 0))

        ttk.Label(
            app_frame,
            text="Ejemplo: /home/pc/Descargas/Immersed-x86_64.AppImage",
            foreground="#6b7280",
        ).grid(row=1, column=1, sticky="w", pady=(4, 0))

        # Sección Icono
        icon_frame = ttk.LabelFrame(form, text="2. Ícono de la aplicación", padding=10)
        icon_frame.grid(row=1, column=0, columnspan=4, sticky="ew", pady=8)
        icon_frame.columnconfigure(1, weight=1)

        ttk.Label(icon_frame, text="Ruta del ícono:").grid(row=0, column=0, sticky="w", padx=(0, 8))
        ttk.Entry(icon_frame, textvariable=self.icon_path).grid(row=0, column=1, sticky="ew")
        ttk.Button(icon_frame, text="Examinar...", command=self.browse_icon).grid(row=0, column=2, padx=(8, 0))

        self.preview_label = ttk.Label(icon_frame, text="Sin vista previa", anchor="center")
        self.preview_label.grid(row=1, column=1, sticky="w", pady=(8, 0))

        ttk.Label(
            icon_frame,
            text="Formatos válidos: PNG, SVG, XPM, JPG, JPEG, WEBP. Para JPG/WEBP se recomienda instalar Pillow.",
            foreground="#6b7280",
        ).grid(row=2, column=1, sticky="w", pady=(4, 0))

        # Sección Metadatos
        meta_frame = ttk.LabelFrame(form, text="3. Datos del lanzador", padding=10)
        meta_frame.grid(row=2, column=0, columnspan=4, sticky="ew", pady=8)
        meta_frame.columnconfigure(1, weight=1)
        meta_frame.columnconfigure(3, weight=1)

        ttk.Label(meta_frame, text="Nombre visible:").grid(row=0, column=0, sticky="w", padx=(0, 8), pady=4)
        ttk.Entry(meta_frame, textvariable=self.app_name).grid(row=0, column=1, sticky="ew", pady=4)

        ttk.Label(meta_frame, text="ID interno:").grid(row=0, column=2, sticky="w", padx=(12, 8), pady=4)
        ttk.Entry(meta_frame, textvariable=self.install_id).grid(row=0, column=3, sticky="ew", pady=4)

        ttk.Label(meta_frame, text="Nombre genérico:").grid(row=1, column=0, sticky="w", padx=(0, 8), pady=4)
        ttk.Entry(meta_frame, textvariable=self.generic_name).grid(row=1, column=1, sticky="ew", pady=4)

        ttk.Label(meta_frame, text="Categorías:").grid(row=1, column=2, sticky="w", padx=(12, 8), pady=4)
        ttk.Combobox(
            meta_frame,
            textvariable=self.categories,
            values=[
                "Utility;",
                "Network;RemoteAccess;Utility;",
                "Development;",
                "Graphics;",
                "AudioVideo;",
                "Office;",
                "Education;",
                "Science;Education;",
                "System;",
            ],
        ).grid(row=1, column=3, sticky="ew", pady=4)

        ttk.Label(meta_frame, text="Comentario:").grid(row=2, column=0, sticky="nw", padx=(0, 8), pady=4)
        ttk.Entry(meta_frame, textvariable=self.app_comment).grid(row=2, column=1, columnspan=3, sticky="ew", pady=4)

        ttk.Label(meta_frame, text="Argumentos Exec:").grid(row=3, column=0, sticky="w", padx=(0, 8), pady=4)
        ttk.Entry(meta_frame, textvariable=self.exec_args).grid(row=3, column=1, columnspan=3, sticky="ew", pady=4)

        ttk.Label(
            meta_frame,
            text="Deje los argumentos vacíos, salvo que la AppImage requiera parámetros adicionales.",
            foreground="#6b7280",
        ).grid(row=4, column=1, columnspan=3, sticky="w")

        self.app_name.trace_add("write", self.update_install_id_from_name)

        # Opciones
        options_frame = ttk.LabelFrame(form, text="4. Opciones de instalación", padding=10)
        options_frame.grid(row=3, column=0, columnspan=4, sticky="ew", pady=8)
        options_frame.columnconfigure(0, weight=1)
        options_frame.columnconfigure(1, weight=1)

        ttk.Checkbutton(options_frame, text="Ejecutar en terminal", variable=self.terminal).grid(row=0, column=0, sticky="w", pady=3)
        ttk.Checkbutton(options_frame, text="Activar StartupNotify", variable=self.startup_notify).grid(row=0, column=1, sticky="w", pady=3)
        ttk.Checkbutton(options_frame, text="Sobrescribir lanzador si ya existe", variable=self.overwrite).grid(row=1, column=0, sticky="w", pady=3)
        ttk.Checkbutton(options_frame, text="Copiar AppImage a ~/.local/opt", variable=self.keep_original).grid(row=1, column=1, sticky="w", pady=3)

        # Rutas de salida
        paths_frame = ttk.LabelFrame(form, text="5. Rutas que se crearán", padding=10)
        paths_frame.grid(row=4, column=0, columnspan=4, sticky="ew", pady=8)
        paths_frame.columnconfigure(0, weight=1)

        self.paths_text = tk.Text(paths_frame, height=7, wrap="word")
        self.paths_text.grid(row=0, column=0, sticky="ew")
        self.paths_text.configure(state="disabled")
        self.install_id.trace_add("write", lambda *_: self.update_paths_preview())

        # Botones
        buttons_frame = ttk.Frame(form)
        buttons_frame.grid(row=5, column=0, columnspan=4, sticky="ew", pady=12)
        buttons_frame.columnconfigure(0, weight=1)

        ttk.Button(buttons_frame, text="Validar datos", command=self.validate_form).grid(row=0, column=1, padx=4)
        ttk.Button(buttons_frame, text="Crear lanzador", command=self.create_launcher).grid(row=0, column=2, padx=4)
        ttk.Button(buttons_frame, text="Probar lanzador", command=self.test_launcher).grid(row=0, column=3, padx=4)
        ttk.Button(buttons_frame, text="Salir", command=self.destroy).grid(row=0, column=4, padx=4)

        # Estado
        status_frame = ttk.Frame(root)
        status_frame.grid(row=2, column=0, sticky="ew", pady=(8, 0))
        status_frame.columnconfigure(0, weight=1)

        ttk.Label(status_frame, textvariable=self.status, foreground="#065f46").grid(row=0, column=0, sticky="w")

        self.update_paths_preview()

    def update_install_id_from_name(self, *_):
        current = self.install_id.get().strip()
        # Solo autocompletar si está vacío o coincide con una versión anterior generada.
        if not current or current == slugify(current):
            self.install_id.set(slugify(self.app_name.get()))

    def update_paths_preview(self):
        app_id = slugify(self.install_id.get() or self.app_name.get() or "mi-aplicacion")
        home = Path.home()
        install_dir = home / ".local" / "opt" / app_id
        app_dest = install_dir / f"{app_id}.AppImage"
        icon_dest = home / ".local" / "share" / "icons" / f"{app_id}{self._normalized_icon_suffix()}"
        desktop_file = home / ".local" / "share" / "applications" / f"{app_id}.desktop"

        text = (
            f"Directorio de instalación:\n  {install_dir}\n\n"
            f"AppImage instalado:\n  {app_dest}\n\n"
            f"Ícono instalado:\n  {icon_dest}\n\n"
            f"Lanzador .desktop:\n  {desktop_file}\n"
        )

        self.paths_text.configure(state="normal")
        self.paths_text.delete("1.0", "end")
        self.paths_text.insert("1.0", text)
        self.paths_text.configure(state="disabled")

    def _normalized_icon_suffix(self) -> str:
        p = Path(self.icon_path.get().strip())
        if p.suffix.lower() in VALID_IMAGE_EXTENSIONS:
            return p.suffix.lower()
        return ".png"

    def browse_appimage(self):
        path = filedialog.askopenfilename(
            title="Seleccionar archivo AppImage",
            filetypes=[
                ("AppImage", "*.AppImage *.appimage"),
                ("Todos los archivos", "*.*"),
            ],
        )
        if path:
            self.appimage_path.set(path)
            p = Path(path)
            if not self.app_name.get().strip():
                name = p.name
                name = re.sub(r"\.appimage$", "", name, flags=re.IGNORECASE)
                name = name.replace("_", " ").replace("-", " ")
                self.app_name.set(name.strip().title())
            self.status.set("AppImage seleccionado.")
            self.update_paths_preview()

    def browse_icon(self):
        path = filedialog.askopenfilename(
            title="Seleccionar ícono",
            filetypes=[
                ("Imágenes válidas", "*.png *.svg *.xpm *.jpg *.jpeg *.webp"),
                ("PNG", "*.png"),
                ("SVG", "*.svg"),
                ("Todos los archivos", "*.*"),
            ],
        )
        if path:
            self.icon_path.set(path)
            self.load_icon_preview(Path(path))
            self.status.set("Ícono seleccionado.")
            self.update_paths_preview()

    def load_icon_preview(self, path: Path):
        if not is_valid_image(path):
            self.preview_label.configure(text="Ícono inválido", image="")
            return

        if path.suffix.lower() == ".png":
            try:
                img = tk.PhotoImage(file=str(path))
                # Reducir si es muy grande.
                max_side = max(img.width(), img.height())
                if max_side > 96:
                    factor = max(1, int(max_side / 96))
                    img = img.subsample(factor, factor)
                self.icon_preview = img
                self.preview_label.configure(image=self.icon_preview, text="")
                return
            except Exception:
                pass

        if PIL_AVAILABLE and path.suffix.lower() in {".jpg", ".jpeg", ".webp", ".png"}:
            try:
                image = Image.open(path)
                image.thumbnail((96, 96))
                self.icon_preview = ImageTk.PhotoImage(image)
                self.preview_label.configure(image=self.icon_preview, text="")
                return
            except Exception:
                pass

        if path.suffix.lower() == ".svg":
            self.preview_label.configure(text="SVG seleccionado: vista previa no disponible en Tkinter básico.", image="")
        else:
            self.preview_label.configure(text="Imagen seleccionada. Para previsualizar JPG/WEBP instale Pillow.", image="")

    def validate_form(self) -> bool:
        appimage = Path(self.appimage_path.get().strip())
        icon = Path(self.icon_path.get().strip()) if self.icon_path.get().strip() else None
        name = self.app_name.get().strip()
        app_id = slugify(self.install_id.get().strip() or name)

        if not is_appimage(appimage):
            messagebox.showerror("Validación", "Seleccione un archivo .AppImage válido.")
            return False

        if not name:
            messagebox.showerror("Validación", "Ingrese el nombre visible de la aplicación.")
            return False

        if not app_id:
            messagebox.showerror("Validación", "El ID interno no es válido.")
            return False

        if icon and not is_valid_image(icon):
            messagebox.showerror("Validación", "Seleccione una imagen válida para el ícono.")
            return False

        self.install_id.set(app_id)
        self.status.set("Validación correcta.")
        messagebox.showinfo("Validación", "Los datos son correctos.")
        return True

    def create_launcher(self):
        if not self.validate_form():
            return

        appimage_src = Path(self.appimage_path.get().strip())
        icon_src = Path(self.icon_path.get().strip()) if self.icon_path.get().strip() else None
        app_name = self.app_name.get().strip()
        app_id = slugify(self.install_id.get().strip() or app_name)
        comment = self.app_comment.get().strip()
        generic_name = self.generic_name.get().strip()
        categories = self.categories.get().strip()
        exec_args = self.exec_args.get().strip()

        home = Path.home()
        install_dir = home / ".local" / "opt" / app_id
        desktop_dir = home / ".local" / "share" / "applications"
        icon_dir = home / ".local" / "share" / "icons"

        ensure_dir(install_dir)
        ensure_dir(desktop_dir)
        ensure_dir(icon_dir)

        appimage_dest = install_dir / f"{app_id}.AppImage"
        desktop_file = desktop_dir / f"{app_id}.desktop"

        if desktop_file.exists() and not self.overwrite.get():
            messagebox.showerror("Lanzador existente", f"Ya existe:\n{desktop_file}")
            return

        if self.keep_original.get():
            shutil.copy2(appimage_src, appimage_dest)
        else:
            shutil.move(str(appimage_src), str(appimage_dest))
        appimage_dest.chmod(0o755)

        if icon_src and icon_src.exists():
            icon_dest = icon_dir / f"{app_id}{icon_src.suffix.lower()}"
            shutil.copy2(icon_src, icon_dest)
            icon_dest.chmod(0o644)
            icon_line = f"Icon={icon_dest}"
        else:
            icon_line = "Icon=application-x-executable"

        exec_command = f'"{appimage_dest}"'
        if exec_args:
            exec_command += f" {exec_args}"

        terminal_value = "true" if self.terminal.get() else "false"
        startup_value = "true" if self.startup_notify.get() else "false"

        desktop_content = f"""[Desktop Entry]
Version=1.0
Type=Application
Name={app_name}
GenericName={generic_name}
Comment={comment}
Exec={exec_command}
{icon_line}
Terminal={terminal_value}
StartupNotify={startup_value}
Categories={categories}
MimeType=
"""

        desktop_file.write_text(desktop_content, encoding="utf-8")
        desktop_file.chmod(0o755)

        if shutil.which("update-desktop-database"):
            run_command(["update-desktop-database", str(desktop_dir)])

        # No reiniciamos automáticamente el panel para evitar incomodar al usuario.
        self.status.set(f"Lanzador creado: {desktop_file}")

        messagebox.showinfo(
            "Instalación finalizada",
            "El lanzador fue creado correctamente.\n\n"
            f"Aplicación: {app_name}\n"
            f"Lanzador: {desktop_file}\n\n"
            "Busque la aplicación en el menú de Linux Mint.\n"
            "Si no aparece, cierre sesión o reinicie el panel XFCE.",
        )

    def test_launcher(self):
        app_id = slugify(self.install_id.get().strip() or self.app_name.get().strip())
        if not app_id:
            messagebox.showerror("Probar lanzador", "Primero indique el nombre o ID interno.")
            return

        if not shutil.which("gtk-launch"):
            messagebox.showwarning(
                "gtk-launch no encontrado",
                "No se encontró gtk-launch. Puede probar la aplicación desde el menú.",
            )
            return

        code, output = run_command(["gtk-launch", app_id])
        if code == 0:
            self.status.set("Lanzador ejecutado con gtk-launch.")
        else:
            messagebox.showerror(
                "Error al probar lanzador",
                f"No se pudo ejecutar gtk-launch {app_id}\n\n{output}",
            )


def main():
    app = AppImageLauncherCreator()
    app.mainloop()


if __name__ == "__main__":
    main()
