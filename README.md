# Lanzador crea y elimina AppImage

Suite gráfica desarrollada en **Python/Tkinter** para crear y eliminar lanzadores `.desktop` de aplicaciones **AppImage** en **Linux Mint**, Ubuntu, Debian y distribuciones compatibles con el estándar XDG.

Este proyecto fue desarrollado por **TECPROG WORLD E.I.R.L.** como una utilidad práctica para integrar aplicaciones portables al menú de Linux y retirarlas de forma segura cuando ya no se requieran.

---

## Descripción general

El proyecto contiene dos herramientas principales:

### 1. AppImage Launcher Creator

Permite crear lanzadores gráficos para aplicaciones distribuidas como archivos `.AppImage`.

Funciones principales:

- Seleccionar un archivo `.AppImage` desde el ordenador.
- Seleccionar una imagen de ícono válida.
- Completar nombre visible, ID interno, comentario, categoría y argumentos de ejecución.
- Copiar el AppImage a una ruta estable dentro del usuario.
- Crear automáticamente un archivo `.desktop`.
- Integrar la aplicación al menú de Linux Mint.
- Probar el lanzador con `gtk-launch`.

### 2. AppImage Launcher Uninstaller

Permite eliminar lanzadores AppImage instalados localmente.

Funciones principales:

- Detectar lanzadores `.desktop` asociados a archivos `.AppImage`.
- Mostrar rutas de ejecutable, ícono y archivo `.desktop`.
- Simular la eliminación antes de borrar archivos.
- Eliminar de forma segura:
  - el lanzador `.desktop`;
  - el AppImage instalado en `~/.local/opt`;
  - el ícono local asociado en `~/.local/share/icons`.
- Evitar el borrado de recursos globales del sistema.

---

## Objetivo

El objetivo del proyecto es facilitar la administración de aplicaciones **AppImage** en Linux sin depender de configuraciones manuales.

Las herramientas permiten mantener una estructura ordenada, reproducible y segura para aplicaciones portables, evitando que los usuarios dependan de la carpeta `Descargas` o de accesos directos creados manualmente.

---

## Estructura sugerida del repositorio

```text
.
├── appimage_launcher_creator.py
├── appimage_launcher_uninstaller.py
├── build_appimage_launcher_creator_deb.sh
├── build_appimage_launcher_uninstaller_deb.sh
├── appimage-launcher-creator.png
├── appimage_launcher_uninstaller.png
├── docs/
│   ├── guia_usuario_appimage_launcher_creator.tex
│   ├── guia_usuario_appimage_launcher_uninstaller.tex
│   └── figuras/
│       ├── appimage_launcher_creator_01.png
│       ├── appimage_launcher_creator_02.png
│       └── appimage_launcher_uninstaller_01.png
├── dist/
│   ├── appimage-launcher-creator_0.1.0_all.deb
│   └── appimage-launcher-uninstaller_0.1.0_all.deb
└── README.md
```

---

## Requisitos

Instalar dependencias básicas:

```bash
sudo apt update
sudo apt install python3 python3-tk dpkg-dev fakeroot desktop-file-utils
```

Dependencias opcionales para mejorar la previsualización de imágenes:

```bash
sudo apt install python3-pil python3-pil.imagetk
```

---

## Ejecución desde código fuente

### AppImage Launcher Creator

```bash
python3 appimage_launcher_creator.py
```

O con permiso de ejecución:

```bash
chmod +x appimage_launcher_creator.py
./appimage_launcher_creator.py
```

### AppImage Launcher Uninstaller

```bash
python3 appimage_launcher_uninstaller.py
```

O con permiso de ejecución:

```bash
chmod +x appimage_launcher_uninstaller.py
./appimage_launcher_uninstaller.py
```

---

## Construcción de paquetes `.deb`

### Crear paquete del creador de lanzadores

```bash
chmod +x build_appimage_launcher_creator_deb.sh
./build_appimage_launcher_creator_deb.sh
```

El paquete se generará en:

```text
dist/appimage-launcher-creator_0.1.0_all.deb
```

Instalación:

```bash
sudo apt install ./dist/appimage-launcher-creator_0.1.0_all.deb
```

Ejecución:

```bash
appimage-launcher-creator
```

También aparecerá en el menú como:

```text
AppImage Launcher Creator
```

---

### Crear paquete del desinstalador

```bash
chmod +x build_appimage_launcher_uninstaller_deb.sh
./build_appimage_launcher_uninstaller_deb.sh
```

El paquete se generará en:

```text
dist/appimage-launcher-uninstaller_0.1.0_all.deb
```

Instalación:

```bash
sudo apt install ./dist/appimage-launcher-uninstaller_0.1.0_all.deb
```

Ejecución:

```bash
appimage-launcher-uninstaller
```

También aparecerá en el menú como:

```text
AppImage Launcher Uninstaller
```

---

## Rutas gestionadas por las herramientas

Las herramientas trabajan principalmente dentro del espacio local del usuario:

```text
~/.local/opt/
~/.local/share/applications/
~/.local/share/icons/
```

El creador instala los recursos de una aplicación AppImage en rutas locales del usuario.

El desinstalador elimina únicamente recursos seguros dentro de estas rutas, evitando borrar archivos globales del sistema como `/usr/share/applications`, `/usr/share/icons` o paquetes instalados con `apt`.

---

## Ejemplo de uso: Immersed

Para crear un lanzador de Immersed:

```text
AppImage:
/home/pc/Descargas/Immersed-x86_64.AppImage

Ícono:
/home/pc/Descargas/immersed.png

Nombre visible:
Immersed

ID interno:
immersed

Categorías:
Network;RemoteAccess;Utility;
```

Después de crear el lanzador, la estructura local esperada será:

```text
/home/pc/.local/opt/immersed/immersed.AppImage
/home/pc/.local/share/icons/immersed.png
/home/pc/.local/share/applications/immersed.desktop
```

Para probarlo:

```bash
gtk-launch immersed
```

Para desinstalarlo, abrir:

```bash
appimage-launcher-uninstaller
```

Luego seleccionar **Immersed**, simular la eliminación y confirmar la desinstalación.

---

## Documentación en LaTeX

El proyecto incluye guías de usuario en formato `.tex`, listas para compilar con `pdflatex`.

Compilar guía del creador:

```bash
cd docs
pdflatex guia_usuario_appimage_launcher_creator.tex
pdflatex guia_usuario_appimage_launcher_creator.tex
```

Compilar guía del desinstalador:

```bash
cd docs
pdflatex guia_usuario_appimage_launcher_uninstaller.tex
pdflatex guia_usuario_appimage_launcher_uninstaller.tex
```

Si se requiere soporte completo de LaTeX:

```bash
sudo apt update
sudo apt install texlive-full
```

O una instalación más ligera:

```bash
sudo apt install texlive-latex-base texlive-latex-recommended texlive-latex-extra texlive-lang-spanish texlive-fonts-recommended latexmk
```

---

## Instalación recomendada del proyecto desde GitHub

Clonar el repositorio:

```bash
cd /home/pc/Escritorio
git clone https://github.com/Tecprog-World-Store/lanzador_crea_y_elimina_appimage.git
cd lanzador_crea_y_elimina_appimage
```

Construir los paquetes:

```bash
chmod +x build_appimage_launcher_creator_deb.sh
chmod +x build_appimage_launcher_uninstaller_deb.sh

./build_appimage_launcher_creator_deb.sh
./build_appimage_launcher_uninstaller_deb.sh
```

Instalar:

```bash
sudo apt install ./dist/appimage-launcher-creator_0.1.0_all.deb
sudo apt install ./dist/appimage-launcher-uninstaller_0.1.0_all.deb
```

---

## Desinstalación de las herramientas

Para retirar el creador:

```bash
sudo apt remove appimage-launcher-creator
```

Para retirar el desinstalador:

```bash
sudo apt remove appimage-launcher-uninstaller
```

---

## Estado del proyecto

Versión inicial:

```text
0.1.0
```

Componentes implementados:

- GUI del creador de lanzadores AppImage.
- GUI del desinstalador de lanzadores AppImage.
- Generación de paquetes `.deb`.
- Íconos de aplicación.
- Guías técnicas en LaTeX.
- Flujo compatible con Linux Mint XFCE.

---

## Futuras mejoras

Posibles líneas de desarrollo:

- Integrar creador y desinstalador en una sola suite.
- Añadir base de datos local de aplicaciones gestionadas.
- Agregar vista previa avanzada de íconos SVG.
- Implementar modo oscuro propio.
- Crear instalador `.deb` unificado.
- Incorporar soporte para traducciones.
- Agregar detección de configuraciones residuales en `~/.config`, con confirmación avanzada.
- Crear documentación HTML para publicación en GitHub Pages.

---

## Autoría

**TECPROG WORLD E.I.R.L.**

RUC: `20608743252`

Actividad principal:  
Actividades de arquitectura e ingeniería y actividades conexas de consultoría técnica.

Sitio web:  
https://tecprog-world-store.github.io/

---

## Licencia

Este proyecto se publica inicialmente bajo licencia **MIT**.

Se recomienda revisar y adaptar el archivo `LICENSE` según la política institucional de TECPROG WORLD E.I.R.L.
