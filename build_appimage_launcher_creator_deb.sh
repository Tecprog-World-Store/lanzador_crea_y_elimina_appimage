#!/usr/bin/env bash
set -euo pipefail

# ============================================================
# build_appimage_launcher_creator_deb.sh
# Construye un paquete .deb para AppImage Launcher Creator.
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
#     appimage_launcher_creator.py
#
#   Opcionalmente colocar también:
#     appimage-launcher-creator.png
#
#   Ejecutar:
#     chmod +x build_appimage_launcher_creator_deb.sh
#     ./build_appimage_launcher_creator_deb.sh
#
# Salida:
#   ./dist/appimage-launcher-creator_0.1.0_all.deb
# ============================================================

APP_NAME="appimage-launcher-creator"
APP_DISPLAY_NAME="AppImage Launcher Creator"
VERSION="0.1.0"
ARCH="all"
MAINTAINER="TECPROG WORLD E.I.R.L. <contacto@tecprog-world-store.github.io>"
HOMEPAGE="https://tecprog-world-store.github.io/"
DESCRIPTION_SHORT="Creador grafico de lanzadores para AppImage"
DESCRIPTION_LONG="Herramienta grafica en Python/Tkinter para crear lanzadores .desktop de aplicaciones AppImage en Linux Mint, Ubuntu, Debian y distribuciones compatibles con XDG."

ROOT_DIR="$(pwd)"
SOURCE_PY="${ROOT_DIR}/appimage_launcher_creator.py"
ICON_SOURCE="${ROOT_DIR}/appimage-launcher-creator.png"

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
    echo "Coloca appimage_launcher_creator.py en la misma carpeta que este script."
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
cp "$SOURCE_PY" "$BUILD_DIR/usr/lib/${APP_NAME}/appimage_launcher_creator.py"
chmod 755 "$BUILD_DIR/usr/lib/${APP_NAME}/appimage_launcher_creator.py"

# ------------------------------------------------------------
# 4. Crear wrapper ejecutable en /usr/bin
# ------------------------------------------------------------
echo "[3/7] Creando ejecutable wrapper..."
cat > "$BUILD_DIR/usr/bin/${APP_NAME}" <<EOF
#!/usr/bin/env bash
exec python3 /usr/lib/${APP_NAME}/appimage_launcher_creator.py "\$@"
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

# Genera un PNG 256x256 simple verde oscuro con bloque central.
# No usa dependencias externas.
w, h = 256, 256
bg = (17, 24, 39, 255)
green = (127, 178, 57, 255)
white = (245, 245, 245, 255)

rows = []
for y in range(h):
    row = bytearray()
    row.append(0)  # filter type
    for x in range(w):
        # Marco verde y bloque tipo "A"
        if x < 12 or x >= w-12 or y < 12 or y >= h-12:
            px = green
        elif 68 < x < 188 and 66 < y < 190:
            if (78 < x < 100 and 96 < y < 176) or (156 < x < 178 and 96 < y < 176) or (100 < x < 156 and 66 < y < 92) or (102 < x < 154 and 124 < y < 146):
                px = white
            else:
                px = green
        else:
            px = bg
        row.extend(px)
    rows.append(bytes(row))

raw = b''.join(rows)

def chunk(tag, data):
    return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xffffffff)

png = b"\x89PNG\r\n\x1a\n"
png += chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0))
png += chunk(b"IDAT", zlib.compress(raw, 9))
png += chunk(b"IEND", b"")

out = Path("build/appimage-launcher-creator_0.1.0_all/usr/share/icons/hicolor/256x256/apps/appimage-launcher-creator.png")
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
GenericName=AppImage Launcher Creator
Comment=Crea lanzadores de aplicaciones AppImage para el menu de Linux
Exec=${APP_NAME}
Icon=${APP_NAME}
Terminal=false
StartupNotify=true
Categories=Utility;System;
Keywords=AppImage;Launcher;Linux Mint;Desktop;XDG;
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

Herramienta grafica para crear lanzadores .desktop de aplicaciones AppImage.

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
Recommends: python3-pil, python3-pil.imagetk, desktop-file-utils
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
