#!/usr/bin/env bash
#
# Build and install Hub Pessoal:
#   frontend build -> PyInstaller (onedir, windowed) -> AppDir -> AppImage
#   -> ~/.local/share .desktop + icons.
#
# Run from anywhere:  ./release.sh
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PKG="${ROOT}/packaging"
BUILD="${ROOT}/build-release"
APPDIR="${BUILD}/AppDir"
VERSION="$(tr -d '[:space:]' < "${ROOT}/VERSION")"
OUT_DIR="/home/joao/Workspaces_VSCODE/Meus_Projetos/Banco"
OUT="${OUT_DIR}/HubPessoal-x86_64.AppImage"
PY="/home/joao/Workspaces_VSCODE/Meus_Projetos/HubPessoal/backend/.venv/bin/python"
TOOL_SRC="${OUT_DIR}/packaging/appimagetool-x86_64.AppImage"
TOOL="${BUILD}/appimagetool-x86_64.AppImage"
APPS="${HOME}/.local/share/applications"
ICONS="${HOME}/.local/share/icons/hicolor"

echo "==> Hub Pessoal ${VERSION}"

# 1. Frontend ---------------------------------------------------------------
echo "==> Building frontend"
export NVM_DIR="${NVM_DIR:-$HOME/.nvm}"
# shellcheck disable=SC1091
. "${NVM_DIR}/nvm.sh"
(cd "${ROOT}/frontend" && npm run build)

# 2. Icons ------------------------------------------------------------------
echo "==> Generating icons"
QT_QPA_PLATFORM=offscreen "${PY}" "${PKG}/make_icon.py"

# 3. PyInstaller ------------------------------------------------------------
"${PY}" -c "import PyInstaller" 2>/dev/null || "${PY}" -m pip install pyinstaller
echo "==> Running PyInstaller"
mkdir -p "${BUILD}"
rm -rf "${BUILD}/dist" "${BUILD}/work" "${APPDIR}"
"${PY}" -m PyInstaller \
    --name HubPessoal \
    --noconfirm --clean --windowed \
    --distpath "${BUILD}/dist" \
    --workpath "${BUILD}/work" \
    --specpath "${BUILD}" \
    --paths "${ROOT}/backend" \
    --add-data "${ROOT}/frontend/dist:frontend/dist" \
    --add-data "${PKG}/icons:icons" \
    --add-data "${ROOT}/VERSION:." \
    "${ROOT}/backend/hub_desktop.py"

# 4. AppDir -----------------------------------------------------------------
echo "==> Assembling AppDir"
mkdir -p "${APPDIR}/usr/bin" "${APPDIR}/usr/share/icons/hicolor/256x256/apps"
cp -r "${BUILD}/dist/HubPessoal" "${APPDIR}/usr/bin/HubPessoal"
install -m 0755 "${PKG}/AppRun" "${APPDIR}/AppRun"
cp "${PKG}/icons/hubpessoal-256.png" "${APPDIR}/hubpessoal.png"
cp "${PKG}/icons/hubpessoal-256.png" "${APPDIR}/usr/share/icons/hicolor/256x256/apps/hubpessoal.png"
cat > "${APPDIR}/hubpessoal.desktop" <<DESKTOP
[Desktop Entry]
Type=Application
Name=Hub Pessoal
Comment=Finanças e notícias
Exec=HubPessoal
Icon=hubpessoal
Categories=Office;Finance;
Terminal=false
StartupWMClass=Hub Pessoal
X-AppImage-Version=${VERSION}
DESKTOP

# 5. AppImage ---------------------------------------------------------------
if [[ ! -x "${TOOL}" ]]; then
    if [[ -f "${TOOL_SRC}" ]]; then
        cp "${TOOL_SRC}" "${TOOL}"
    else
        curl -L -o "${TOOL}" "https://github.com/AppImage/appimagetool/releases/download/continuous/appimagetool-x86_64.AppImage"
    fi
    chmod +x "${TOOL}"
fi
echo "==> Building AppImage"
mkdir -p "${OUT_DIR}"
rm -f "${OUT}"
ARCH=x86_64 "${TOOL}" --appimage-extract-and-run "${APPDIR}" "${OUT}"
chmod +x "${OUT}"

# 6. Install .desktop + icons -----------------------------------------------
echo "==> Installing .desktop and icons"
for size in 64 128 256 512; do
    mkdir -p "${ICONS}/${size}x${size}/apps"
    cp "${PKG}/icons/hubpessoal-${size}.png" "${ICONS}/${size}x${size}/apps/hubpessoal.png"
done
mkdir -p "${APPS}"
cat > "${APPS}/hubpessoal.desktop" <<DESKTOP
[Desktop Entry]
Type=Application
Name=Hub Pessoal
Comment=Finanças e notícias
Exec=${OUT}
Icon=hubpessoal
Categories=Office;Finance;
Terminal=false
StartupWMClass=Hub Pessoal
DESKTOP
update-desktop-database "${APPS}" 2>/dev/null || true
gtk-update-icon-cache -f -t "${ICONS}" 2>/dev/null || true

echo "==> Done: ${OUT} ($(du -h "${OUT}" | cut -f1))"
