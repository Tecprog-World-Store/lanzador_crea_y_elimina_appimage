#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AppImage Launcher Uninstaller
Autoría: TECPROG WORLD E.I.R.L.
Sitio web: https://tecprog-world-store.github.io/

Descripción:
    Software GUI en Tkinter para desinstalar lanzadores .desktop creados para
    aplicaciones AppImage dentro del espacio local del usuario.

Alcance seguro:
    - Analiza ~/.local/share/applications/*.desktop
    - Detecta lanzadores cuyo Exec apunte a ~/.local/opt/... o a un .AppImage
    - Permite eliminar:
        * archivo .desktop
        * archivo AppImage o carpeta local en ~/.local/opt/<id>
        * icono local en ~/.local/share/icons
    - No elimina archivos fuera del HOME del usuario salvo que el usuario seleccione
      manualmente un modo inseguro; esta versión evita borrados globales.

Uso:
    python3 appimage_launcher_uninstaller.py

Dependencias:
    - Python 3
    - Tkinter
"""

import configparser
import os
import re
import shlex
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox


APP_TITLE = "AppImage Launcher Uninstaller"
AUTHOR = "TECPROG WORLD E.I.R.L."
WEBSITE = "https://tecprog-world-store.github.io/"


def run_command(command: list[str]) -> tuple[int, str]:
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


def safe_read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return ""


def normalize_exec_path(exec_value: str) -> Path | None:
    """Extrae la ruta principal desde la línea Exec de un .desktop."""
    if not exec_value.strip():
        return None

    try:
        parts = shlex.split(exec_value)
    except Exception:
        parts = exec_value.split()

    if not parts:
        return None

    first = parts[0]

    # Si Exec usa env, tomar el siguiente argumento con apariencia de ruta.
    if first.endswith("/env") or first == "env":
        for item in parts[1:]:
            if item.startswith("/") or item.startswith("~"):
                first = item
                break

    first = first.replace("%U", "").replace("%u", "").replace("%F", "").replace("%f", "").strip()
    if not first:
        return None

    p = Path(os.path.expanduser(first))
    return p


def slug_from_desktop(desktop_file: Path) -> str:
    return desktop_file.stem.strip()


def is_inside(path: Path, parent: Path) -> bool:
    try:
        path.resolve().relative_to(parent.resolve())
        return True
    except Exception:
        return False


@dataclass
class LauncherEntry:
    name: str
    desktop_file: Path
    exec_line: str
    exec_path: Path | None
    icon_line: str
    icon_path: Path | None
    comment: str
    categories: str
    app_id: str
    install_dir: Path | None
    detected_type: str


class AppImageLauncherUninstaller(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.minsize(900, 620)

        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        width = min(1100, max(900, int(screen_w * 0.82)))
        height = min(780, max(620, int(screen_h * 0.82)))
        self.geometry(f"{width}x{height}")

        self.home = Path.home()
        self.desktop_dir = self.home / ".local" / "share" / "applications"
        self.icons_dir = self.home / ".local" / "share" / "icons"
        self.opt_dir = self.home / ".local" / "opt"

        self.entries: list[LauncherEntry] = []
        self.selected_entry: LauncherEntry | None = None

        self.delete_desktop = tk.BooleanVar(value=True)
        self.delete_appimage_or_dir = tk.BooleanVar(value=True)
        self.delete_icon = tk.BooleanVar(value=True)
        self.only_created_style = tk.BooleanVar(value=True)
        self.status = tk.StringVar(value="Listo. Presione 'Buscar lanzadores' para iniciar.")

        self._build_ui()
        self.scan_launchers()

    def _build_ui(self):
        root = ttk.Frame(self, padding=10)
        root.grid(row=0, column=0, sticky="nsew")
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

        header = ttk.Frame(root)
        header.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        header.columnconfigure(0, weight=1)

        ttk.Label(header, text=APP_TITLE, font=("TkDefaultFont", 18, "bold")).grid(row=0, column=0, sticky="w")
        ttk.Label(header, text=f"{AUTHOR}  |  {WEBSITE}", foreground="#4b5563").grid(row=1, column=0, sticky="w")

        main = ttk.PanedWindow(root, orient="horizontal")
        main.grid(row=1, column=0, sticky="nsew")
        root.rowconfigure(1, weight=1)

        left = ttk.Frame(main, padding=(0, 0, 8, 0))
        right = ttk.Frame(main, padding=(8, 0, 0, 0))
        main.add(left, weight=2)
        main.add(right, weight=3)

        # Panel izquierdo: listado
        list_frame = ttk.LabelFrame(left, text="Lanzadores AppImage detectados", padding=8)
        list_frame.grid(row=0, column=0, sticky="nsew")
        left.rowconfigure(0, weight=1)
        left.columnconfigure(0, weight=1)

        columns = ("name", "type", "app_id")
        self.tree = ttk.Treeview(list_frame, columns=columns, show="headings", selectmode="browse")
        self.tree.heading("name", text="Nombre")
        self.tree.heading("type", text="Tipo")
        self.tree.heading("app_id", text="ID")
        self.tree.column("name", width=260, anchor="w")
        self.tree.column("type", width=130, anchor="w")
        self.tree.column("app_id", width=140, anchor="w")

        yscroll = ttk.Scrollbar(list_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=yscroll.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        yscroll.grid(row=0, column=1, sticky="ns")
        list_frame.rowconfigure(0, weight=1)
        list_frame.columnconfigure(0, weight=1)

        self.tree.bind("<<TreeviewSelect>>", self.on_select_entry)

        list_buttons = ttk.Frame(left)
        list_buttons.grid(row=1, column=0, sticky="ew", pady=(8, 0))
        list_buttons.columnconfigure(0, weight=1)

        ttk.Button(list_buttons, text="Buscar lanzadores", command=self.scan_launchers).grid(row=0, column=0, padx=3, sticky="ew")
        ttk.Button(list_buttons, text="Abrir carpeta .desktop", command=self.open_desktop_folder).grid(row=0, column=1, padx=3)

        # Panel derecho: detalles
        detail_frame = ttk.LabelFrame(right, text="Detalles del lanzador seleccionado", padding=8)
        detail_frame.grid(row=0, column=0, sticky="nsew")
        right.rowconfigure(0, weight=1)
        right.columnconfigure(0, weight=1)

        self.detail_text = tk.Text(detail_frame, height=18, wrap="word")
        self.detail_text.grid(row=0, column=0, sticky="nsew")
        detail_scroll = ttk.Scrollbar(detail_frame, orient="vertical", command=self.detail_text.yview)
        self.detail_text.configure(yscrollcommand=detail_scroll.set)
        detail_scroll.grid(row=0, column=1, sticky="ns")
        detail_frame.rowconfigure(0, weight=1)
        detail_frame.columnconfigure(0, weight=1)
        self.detail_text.configure(state="disabled")

        options = ttk.LabelFrame(right, text="Opciones de desinstalación", padding=8)
        options.grid(row=1, column=0, sticky="ew", pady=(8, 0))
        options.columnconfigure(0, weight=1)
        options.columnconfigure(1, weight=1)

        ttk.Checkbutton(options, text="Eliminar lanzador .desktop", variable=self.delete_desktop, command=self.update_details).grid(row=0, column=0, sticky="w", pady=3)
        ttk.Checkbutton(options, text="Eliminar AppImage / carpeta en ~/.local/opt", variable=self.delete_appimage_or_dir, command=self.update_details).grid(row=0, column=1, sticky="w", pady=3)
        ttk.Checkbutton(options, text="Eliminar ícono local asociado", variable=self.delete_icon, command=self.update_details).grid(row=1, column=0, sticky="w", pady=3)
        ttk.Checkbutton(options, text="Mostrar solo lanzadores tipo AppImage local", variable=self.only_created_style, command=self.scan_launchers).grid(row=1, column=1, sticky="w", pady=3)

        actions = ttk.Frame(right)
        actions.grid(row=2, column=0, sticky="ew", pady=(10, 0))
        actions.columnconfigure(0, weight=1)

        ttk.Button(actions, text="Simular eliminación", command=self.preview_uninstall).grid(row=0, column=1, padx=4)
        ttk.Button(actions, text="Desinstalar seleccionado", command=self.uninstall_selected).grid(row=0, column=2, padx=4)
        ttk.Button(actions, text="Salir", command=self.destroy).grid(row=0, column=3, padx=4)

        status = ttk.Frame(root)
        status.grid(row=2, column=0, sticky="ew", pady=(8, 0))
        status.columnconfigure(0, weight=1)
        ttk.Label(status, textvariable=self.status, foreground="#065f46").grid(row=0, column=0, sticky="w")

    def scan_launchers(self):
        self.entries.clear()
        self.tree.delete(*self.tree.get_children())

        if not self.desktop_dir.exists():
            self.status.set(f"No existe: {self.desktop_dir}")
            self.update_details()
            return

        for desktop_file in sorted(self.desktop_dir.glob("*.desktop")):
            entry = self.parse_desktop_file(desktop_file)
            if entry is None:
                continue

            if self.only_created_style.get():
                if entry.detected_type not in ("AppImage local", "AppImage externo"):
                    continue

            self.entries.append(entry)

        for idx, entry in enumerate(self.entries):
            self.tree.insert("", "end", iid=str(idx), values=(entry.name, entry.detected_type, entry.app_id))

        self.status.set(f"Lanzadores detectados: {len(self.entries)}")
        self.selected_entry = None
        self.update_details()

    def parse_desktop_file(self, desktop_file: Path) -> LauncherEntry | None:
        text = safe_read_text(desktop_file)
        if "[Desktop Entry]" not in text:
            return None

        parser = configparser.ConfigParser(interpolation=None, strict=False)
        try:
            parser.read_string(text)
        except Exception:
            return None

        if "Desktop Entry" not in parser:
            return None

        section = parser["Desktop Entry"]
        if section.get("Type", "Application") != "Application":
            return None

        name = section.get("Name", desktop_file.stem)
        exec_line = section.get("Exec", "")
        icon_line = section.get("Icon", "")
        comment = section.get("Comment", "")
        categories = section.get("Categories", "")
        app_id = slug_from_desktop(desktop_file)

        exec_path = normalize_exec_path(exec_line)
        icon_path = None

        if icon_line:
            possible = Path(os.path.expanduser(icon_line))
            if possible.is_absolute():
                icon_path = possible
            else:
                # Si el Icon no es ruta absoluta, intentar resolverlo en iconos locales.
                for ext in (".png", ".svg", ".xpm", ".jpg", ".jpeg", ".webp"):
                    candidate = self.icons_dir / f"{icon_line}{ext}"
                    if candidate.exists():
                        icon_path = candidate
                        break

        install_dir = None
        detected_type = "Otro"

        if exec_path:
            if exec_path.suffix.lower() == ".appimage":
                detected_type = "AppImage externo"
                if is_inside(exec_path, self.opt_dir):
                    detected_type = "AppImage local"
                    # Si está en ~/.local/opt/<id>/archivo.AppImage, se eliminará esa carpeta.
                    try:
                        rel = exec_path.resolve().relative_to(self.opt_dir.resolve())
                        if len(rel.parts) >= 2:
                            install_dir = self.opt_dir / rel.parts[0]
                        else:
                            install_dir = exec_path.parent
                    except Exception:
                        install_dir = exec_path.parent

        return LauncherEntry(
            name=name,
            desktop_file=desktop_file,
            exec_line=exec_line,
            exec_path=exec_path,
            icon_line=icon_line,
            icon_path=icon_path,
            comment=comment,
            categories=categories,
            app_id=app_id,
            install_dir=install_dir,
            detected_type=detected_type,
        )

    def on_select_entry(self, event=None):
        selection = self.tree.selection()
        if not selection:
            self.selected_entry = None
        else:
            idx = int(selection[0])
            self.selected_entry = self.entries[idx]
        self.update_details()

    def build_delete_plan(self, entry: LauncherEntry) -> list[Path]:
        plan: list[Path] = []

        if self.delete_desktop.get():
            plan.append(entry.desktop_file)

        if self.delete_appimage_or_dir.get():
            if entry.install_dir and entry.install_dir.exists() and is_inside(entry.install_dir, self.opt_dir):
                plan.append(entry.install_dir)
            elif entry.exec_path and entry.exec_path.exists() and is_inside(entry.exec_path, self.opt_dir):
                plan.append(entry.exec_path)

        if self.delete_icon.get() and entry.icon_path and entry.icon_path.exists():
            # Seguridad: solo borrar iconos en ~/.local/share/icons
            if is_inside(entry.icon_path, self.icons_dir):
                plan.append(entry.icon_path)

        # Remover duplicados conservando orden.
        unique = []
        seen = set()
        for p in plan:
            key = str(p.resolve()) if p.exists() else str(p)
            if key not in seen:
                unique.append(p)
                seen.add(key)
        return unique

    def update_details(self):
        self.detail_text.configure(state="normal")
        self.detail_text.delete("1.0", "end")

        if not self.selected_entry:
            self.detail_text.insert("1.0", "Seleccione un lanzador para ver sus detalles.\n")
            self.detail_text.configure(state="disabled")
            return

        e = self.selected_entry
        plan = self.build_delete_plan(e)

        lines = []
        lines.append(f"Nombre:\n  {e.name}\n")
        lines.append(f"ID:\n  {e.app_id}\n")
        lines.append(f"Tipo detectado:\n  {e.detected_type}\n")
        lines.append(f"Archivo .desktop:\n  {e.desktop_file}\n")
        lines.append(f"Exec:\n  {e.exec_line}\n")
        lines.append(f"Ruta ejecutable detectada:\n  {e.exec_path if e.exec_path else 'No detectada'}\n")
        lines.append(f"Directorio de instalación:\n  {e.install_dir if e.install_dir else 'No aplica / no detectado'}\n")
        lines.append(f"Icon:\n  {e.icon_line if e.icon_line else 'No definido'}\n")
        lines.append(f"Ruta de ícono detectada:\n  {e.icon_path if e.icon_path else 'No detectada'}\n")
        lines.append(f"Comentario:\n  {e.comment}\n")
        lines.append(f"Categorías:\n  {e.categories}\n")
        lines.append("\nPlan de eliminación según opciones activas:\n")

        if plan:
            for p in plan:
                marker = "[DIR]" if p.is_dir() else "[FILE]"
                lines.append(f"  {marker} {p}\n")
        else:
            lines.append("  No hay archivos seguros para eliminar con las opciones actuales.\n")

        lines.append("\nNota de seguridad:\n")
        lines.append("  Esta herramienta elimina recursos locales dentro de ~/.local/share/applications,\n")
        lines.append("  ~/.local/share/icons y ~/.local/opt. No elimina recursos globales del sistema.\n")

        self.detail_text.insert("1.0", "".join(lines))
        self.detail_text.configure(state="disabled")

    def preview_uninstall(self):
        if not self.selected_entry:
            messagebox.showwarning("Simulación", "Seleccione un lanzador.")
            return
        plan = self.build_delete_plan(self.selected_entry)
        if not plan:
            messagebox.showinfo("Simulación", "No hay archivos para eliminar con las opciones actuales.")
            return

        msg = "Se eliminarían los siguientes recursos:\n\n"
        msg += "\n".join(str(p) for p in plan)
        messagebox.showinfo("Simulación de eliminación", msg)

    def uninstall_selected(self):
        if not self.selected_entry:
            messagebox.showwarning("Desinstalar", "Seleccione un lanzador.")
            return

        entry = self.selected_entry
        plan = self.build_delete_plan(entry)

        if not plan:
            messagebox.showinfo("Desinstalar", "No hay archivos seguros para eliminar con las opciones actuales.")
            return

        msg = (
            f"Se desinstalará el lanzador:\n\n"
            f"{entry.name}\n\n"
            f"Recursos que se eliminarán:\n\n"
            + "\n".join(str(p) for p in plan)
            + "\n\nEsta acción no se puede deshacer.\n¿Desea continuar?"
        )

        if not messagebox.askyesno("Confirmar desinstalación", msg):
            return

        errors = []
        deleted = []

        for path in plan:
            try:
                if path.is_dir():
                    # Seguridad adicional: solo borrar carpetas dentro de ~/.local/opt
                    if not is_inside(path, self.opt_dir):
                        errors.append(f"No permitido fuera de ~/.local/opt: {path}")
                        continue
                    shutil.rmtree(path)
                    deleted.append(path)
                elif path.exists():
                    # Seguridad adicional para archivos.
                    allowed = (
                        is_inside(path, self.desktop_dir)
                        or is_inside(path, self.icons_dir)
                        or is_inside(path, self.opt_dir)
                    )
                    if not allowed:
                        errors.append(f"No permitido fuera de rutas locales: {path}")
                        continue
                    path.unlink()
                    deleted.append(path)
            except Exception as exc:
                errors.append(f"{path}: {exc}")

        if shutil.which("update-desktop-database"):
            run_command(["update-desktop-database", str(self.desktop_dir)])

        if shutil.which("gtk-update-icon-cache"):
            # Puede fallar en iconos locales; no es crítico.
            run_command(["gtk-update-icon-cache", "-q", str(self.home / ".local" / "share" / "icons")])

        self.scan_launchers()

        if errors:
            messagebox.showwarning(
                "Desinstalación parcial",
                "Algunos recursos no pudieron eliminarse:\n\n" + "\n".join(errors),
            )
        else:
            messagebox.showinfo(
                "Desinstalación finalizada",
                "Recursos eliminados correctamente:\n\n" + "\n".join(str(p) for p in deleted),
            )

    def open_desktop_folder(self):
        if self.desktop_dir.exists():
            code, output = run_command(["xdg-open", str(self.desktop_dir)])
            if code != 0:
                messagebox.showerror("Abrir carpeta", output)
        else:
            messagebox.showinfo("Abrir carpeta", f"No existe:\n{self.desktop_dir}")


def main():
    app = AppImageLauncherUninstaller()
    app.mainloop()


if __name__ == "__main__":
    main()
