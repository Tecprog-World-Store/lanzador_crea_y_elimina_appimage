#!/usr/bin/env bash
set -euo pipefail

# ============================================================
# build_appimage_launcher_uninstaller_deb.sh
# Construye un paquete .deb para AppImage Launcher Uninstaller.
#
# Autoría:
#   TECPROG WORLD E.I.R.L.
#   https://tecprog-world-store.github.io/
#
# Requisitos:
#   sudo apt update
#   sudo apt install dpkg-dev fakeroot desktop-file-utils python3 python3-tk
#
# Uso:
#   Colocar este archivo junto a:
#     appimage_launcher_uninstaller.py
#
#   Colocar opcionalmente el icono:
#     appimage_launcher_uninstaller.png
#
#   Ejecutar:
#     chmod +x build_appimage_launcher_uninstaller_deb.sh
#     ./build_appimage_launcher_uninstaller_deb.sh
#
# Salida:
#   ./dist/appimage-launcher-uninstaller_0.1.0_all.deb
# ============================================================

APP_NAME="appimage-launcher-uninstaller"
APP_DISPLAY_NAME="AppImage Launcher Uninstaller"
VERSION="0.1.0"
ARCH="all"
MAINTAINER="TECPROG WORLD E.I.R.L. <contacto@tecprog-world-store.github.io>"
HOMEPAGE="https://tecprog-world-store.github.io/"
DESCRIPTION_SHORT="Desinstalador grafico de lanzadores AppImage"
DESCRIPTION_LONG="Herramienta grafica en Python/Tkinter para detectar y eliminar lanzadores .desktop, iconos y recursos locales asociados a aplicaciones AppImage instaladas en Linux Mint, Ubuntu, Debian y distribuciones compatibles con XDG."

ROOT_DIR="$(pwd)"
SOURCE_PY="${ROOT_DIR}/appimage_launcher_uninstaller.py"
ICON_SOURCE="${ROOT_DIR}/appimage_launcher_uninstaller.png"

BUILD_DIR="${ROOT_DIR}/build/${APP_NAME}_${VERSION}_${ARCH}"
DIST_DIR="${ROOT_DIR}/dist"
DEB_FILE="${DIST_DIR}/${APP_NAME}_${VERSION}_${ARCH}.deb"

echo "============================================================"
echo " Construccion de paquete .deb"
echo "============================================================"
echo "Aplicacion : ${APP_DISPLAY_NAME}"
echo "Version    : ${VERSION}"
echo "Arquitect. : ${ARCH}"
echo "Salida     : ${DEB_FILE}"
echo

# ------------------------------------------------------------
# 1. Validaciones
# ------------------------------------------------------------
if [ ! -f "$SOURCE_PY" ]; then
    echo "ERROR: no se encontro el archivo fuente:"
    echo "  ${SOURCE_PY}"
    echo
    echo "Coloca appimage_launcher_uninstaller.py en la misma carpeta que este script."
    exit 1
fi

if ! command -v dpkg-deb >/dev/null 2>&1; then
    echo "ERROR: dpkg-deb no esta instalado."
    echo "Instala con:"
    echo "  sudo apt update"
    echo "  sudo apt install dpkg-dev"
    exit 1
fi

if ! command -v desktop-file-validate >/dev/null 2>&1; then
    echo "ADVERTENCIA: desktop-file-validate no esta instalado."
    echo "Se recomienda instalarlo con:"
    echo "  sudo apt install desktop-file-utils"
    echo
fi

# ------------------------------------------------------------
# 2. Limpiar y crear estructura Debian
# ------------------------------------------------------------
echo "[1/7] Preparando estructura del paquete..."
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR/DEBIAN"
mkdir -p "$BUILD_DIR/usr/lib/${APP_NAME}"
mkdir -p "$BUILD_DIR/usr/bin"
mkdir -p "$BUILD_DIR/usr/share/applications"
mkdir -p "$BUILD_DIR/usr/share/icons/hicolor/256x256/apps"
mkdir -p "$BUILD_DIR/usr/share/doc/${APP_NAME}"

# ------------------------------------------------------------
# 3. Instalar archivo Python principal
# ------------------------------------------------------------
echo "[2/7] Copiando aplicacion Python..."
cp "$SOURCE_PY" "$BUILD_DIR/usr/lib/${APP_NAME}/appimage_launcher_uninstaller.py"
chmod 755 "$BUILD_DIR/usr/lib/${APP_NAME}/appimage_launcher_uninstaller.py"

# ------------------------------------------------------------
# 4. Crear wrapper ejecutable en /usr/bin
# ------------------------------------------------------------
echo "[3/7] Creando ejecutable wrapper..."
cat > "$BUILD_DIR/usr/bin/${APP_NAME}" <<EOF
#!/usr/bin/env bash
exec python3 /usr/lib/${APP_NAME}/appimage_launcher_uninstaller.py "\$@"
EOF
chmod 755 "$BUILD_DIR/usr/bin/${APP_NAME}"

# ------------------------------------------------------------
# 5. Instalar icono
# ------------------------------------------------------------
echo "[4/7] Preparando icono..."
if [ -f "$ICON_SOURCE" ]; then
    cp "$ICON_SOURCE" "$BUILD_DIR/usr/share/icons/hicolor/256x256/apps/${APP_NAME}.png"
else
    echo "No se encontro ${ICON_SOURCE}."
    echo "Se generara un icono PNG simple temporal."
    python3 - <<'PY'
from pathlib import Path
import struct
import zlib

w, h = 256, 256
bg = (17, 24, 39, 255)
green = (127, 178, 57, 255)
red = (220, 38, 38, 255)
white = (245, 245, 245, 255)
gray = (75, 85, 99, 255)

rows = []
for y in range(h):
    row = bytearray([0])
    for x in range(w):
        px = bg
        # marco
        if x < 10 or x >= w-10 or y < 10 or y >= h-10:
            px = gray
        # documento verde
        if 54 <= x <= 164 and 54 <= y <= 190:
            px = green
        # engranaje simple blanco
        if 88 <= x <= 132 and 106 <= y <= 150:
            px = white
        if 98 <= x <= 122 and 116 <= y <= 140:
            px = green
        # tacho
        if 158 <= x <= 218 and 144 <= y <= 218:
            px = white
        if 150 <= x <= 226 and 132 <= y <= 152:
            px = gray
        if 170 <= x <= 178 and 162 <= y <= 204:
            px = gray
        if 192 <= x <= 200 and 162 <= y <= 204:
            px = gray
        # circulo rojo con menos
        cx, cy, r = 190, 72, 42
        if (x-cx)**2 + (y-cy)**2 <= r*r:
            px = red
        if 162 <= x <= 218 and 66 <= y <= 78:
            px = white
        row.extend(px)
    rows.append(bytes(row))

raw = b''.join(rows)

def chunk(tag, data):
    return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xffffffff)

png = b"\x89PNG\r\n\x1a\n"
png += chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0))
png += chunk(b"IDAT", zlib.compress(raw, 9))
png += chunk(b"IEND", b"")

out = Path("build/appimage-launcher-uninstaller_0.1.0_all/usr/share/icons/hicolor/256x256/apps/appimage-launcher-uninstaller.png")
out.write_bytes(png)
PY
fi
chmod 644 "$BUILD_DIR/usr/share/icons/hicolor/256x256/apps/${APP_NAME}.png"

# ------------------------------------------------------------
# 6. Crear archivo .desktop del software
# ------------------------------------------------------------
echo "[5/7] Creando lanzador .desktop del software..."
cat > "$BUILD_DIR/usr/share/applications/${APP_NAME}.desktop" <<EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=${APP_DISPLAY_NAME}
GenericName=AppImage Launcher Uninstaller
Comment=Desinstala lanzadores AppImage locales y elimina sus recursos asociados
Exec=${APP_NAME}
Icon=${APP_NAME}
Terminal=false
StartupNotify=true
Categories=Utility;
Keywords=AppImage;Uninstaller;Launcher;Linux Mint;Desktop;XDG;Remove;
EOF

chmod 644 "$BUILD_DIR/usr/share/applications/${APP_NAME}.desktop"

if command -v desktop-file-validate >/dev/null 2>&1; then
    desktop-file-validate "$BUILD_DIR/usr/share/applications/${APP_NAME}.desktop"
fi

# ------------------------------------------------------------
# 7. Documentacion minima
# ------------------------------------------------------------
echo "[6/7] Agregando documentacion..."
cat > "$BUILD_DIR/usr/share/doc/${APP_NAME}/README" <<EOF
${APP_DISPLAY_NAME}

Herramienta grafica para desinstalar lanzadores .desktop de aplicaciones AppImage
instaladas en el espacio local del usuario.

Autoría:
  TECPROG WORLD E.I.R.L.
  ${HOMEPAGE}

Ejecución:
  ${APP_NAME}

Dependencias principales:
  python3, python3-tk
EOF

cat > "$BUILD_DIR/usr/share/doc/${APP_NAME}/copyright" <<EOF
Format: https://www.debian.org/doc/packaging-manuals/copyright-format/1.0/
Upstream-Name: ${APP_NAME}
Source: ${HOMEPAGE}

Files: *
Copyright: 2026 TECPROG WORLD E.I.R.L.
License: Proprietary
 Documento técnico y software generado para uso institucional y educativo.
EOF

chmod 644 "$BUILD_DIR/usr/share/doc/${APP_NAME}/README"
chmod 644 "$BUILD_DIR/usr/share/doc/${APP_NAME}/copyright"

# ------------------------------------------------------------
# 8. Control Debian
# ------------------------------------------------------------
cat > "$BUILD_DIR/DEBIAN/control" <<EOF
Package: ${APP_NAME}
Version: ${VERSION}
Section: utils
Priority: optional
Architecture: ${ARCH}
Maintainer: ${MAINTAINER}
Depends: python3, python3-tk
Recommends: desktop-file-utils
Homepage: ${HOMEPAGE}
Description: ${DESCRIPTION_SHORT}
 ${DESCRIPTION_LONG}
EOF

cat > "$BUILD_DIR/DEBIAN/postinst" <<'EOF'
#!/usr/bin/env bash
set -e

if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database /usr/share/applications || true
fi

if command -v gtk-update-icon-cache >/dev/null 2>&1; then
    gtk-update-icon-cache -q /usr/share/icons/hicolor || true
fi

exit 0
EOF

cat > "$BUILD_DIR/DEBIAN/postrm" <<'EOF'
#!/usr/bin/env bash
set -e

if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database /usr/share/applications || true
fi

if command -v gtk-update-icon-cache >/dev/null 2>&1; then
    gtk-update-icon-cache -q /usr/share/icons/hicolor || true
fi

exit 0
EOF

chmod 755 "$BUILD_DIR/DEBIAN/postinst"
chmod 755 "$BUILD_DIR/DEBIAN/postrm"

# ------------------------------------------------------------
# 9. Construir paquete .deb
# ------------------------------------------------------------
echo "[7/7] Construyendo paquete .deb..."
mkdir -p "$DIST_DIR"
dpkg-deb --build "$BUILD_DIR" "$DEB_FILE"

echo
echo "============================================================"
echo " Paquete construido correctamente"
echo "============================================================"
echo "Archivo:"
echo "  ${DEB_FILE}"
echo
echo "Instalar con:"
echo "  sudo apt install ./dist/${APP_NAME}_${VERSION}_${ARCH}.deb"
echo
echo "Ejecutar con:"
echo "  ${APP_NAME}"
echo
echo "O buscar en el menu:"
echo "  ${APP_DISPLAY_NAME}"
