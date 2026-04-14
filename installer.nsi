; ════════════════════════════════════════════════════════════════
;  Moon Predictions — Installeur NSIS Windows
;  Package le dossier build/main.dist en un installeur .exe classique
; ════════════════════════════════════════════════════════════════
;
;  Prérequis : NSIS installé (https://nsis.sourceforge.io/)
;  Usage     : makensis installer.nsi
;  Sortie    : MoonPredictions-Setup-1.0.0.exe
; ════════════════════════════════════════════════════════════════

!define PRODUCT_NAME        "Moon Predictions"
!ifndef PRODUCT_VERSION
  !define PRODUCT_VERSION   "1.0.0"
!endif
!define PRODUCT_PUBLISHER   "ON7KGK"
!define PRODUCT_WEB_SITE    "https://github.com/ON7KGK"
!define PRODUCT_EXE         "MoonPredictions.exe"
!define PRODUCT_REG_KEY     "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}"

; ── Compression maximale ──
SetCompressor /SOLID lzma

; ── Modern UI ──
!include "MUI2.nsh"

; ── Métadonnées installeur ──
Name "${PRODUCT_NAME} ${PRODUCT_VERSION}"
OutFile "MoonPredictions-Setup-${PRODUCT_VERSION}.exe"
InstallDir "$PROGRAMFILES64\${PRODUCT_NAME}"
InstallDirRegKey HKLM "${PRODUCT_REG_KEY}" "InstallLocation"
RequestExecutionLevel admin
ShowInstDetails show
ShowUnInstDetails show

; ── Interface utilisateur ──
!define MUI_ABORTWARNING
!define MUI_ICON "${NSISDIR}\Contrib\Graphics\Icons\modern-install.ico"
!define MUI_UNICON "${NSISDIR}\Contrib\Graphics\Icons\modern-uninstall.ico"

; Pages installation
; Titre page Welcome sans la version (sinon 1.4.1 est tronqué)
!define MUI_WELCOMEPAGE_TITLE "Bienvenue dans le programme d'installation de ${PRODUCT_NAME}"
!define MUI_WELCOMEPAGE_TEXT "Vous êtes sur le point d'installer ${PRODUCT_NAME} ${PRODUCT_VERSION} sur votre ordinateur.$\r$\n$\r$\nAvant de démarrer l'installation, il est recommandé de fermer toutes les autres applications. Cela permettra la mise à jour de certains fichiers système sans redémarrer votre ordinateur.$\r$\n$\r$\nCliquez sur Suivant pour continuer."
!insertmacro MUI_PAGE_WELCOME
; !insertmacro MUI_PAGE_LICENSE "LICENSE.txt"  ; Décommenter si LICENSE fourni
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!define MUI_FINISHPAGE_RUN "$INSTDIR\${PRODUCT_EXE}"
!define MUI_FINISHPAGE_RUN_TEXT "Lancer ${PRODUCT_NAME}"
!insertmacro MUI_PAGE_FINISH

; Pages désinstallation
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

; Langues
!insertmacro MUI_LANGUAGE "French"
!insertmacro MUI_LANGUAGE "English"

; ════════════════════════════════════════════════════════════════
; Section principale
; ════════════════════════════════════════════════════════════════

Section "Moon Predictions (requis)" SecMain
  SectionIn RO   ; Section obligatoire

  SetOutPath "$INSTDIR"
  SetOverwrite ifnewer

  ; Copier tout le contenu du dossier Nuitka standalone
  File /r "build\main.dist\*.*"

  ; Icône (pour la barre des tâches et la fenêtre)
  File "moon.ico"

  ; Créer le désinstalleur
  WriteUninstaller "$INSTDIR\uninstall.exe"

  ; Enregistrement dans la base de registre (panneau de configuration)
  WriteRegStr HKLM "${PRODUCT_REG_KEY}" "DisplayName"     "${PRODUCT_NAME}"
  WriteRegStr HKLM "${PRODUCT_REG_KEY}" "DisplayVersion"  "${PRODUCT_VERSION}"
  WriteRegStr HKLM "${PRODUCT_REG_KEY}" "Publisher"       "${PRODUCT_PUBLISHER}"
  WriteRegStr HKLM "${PRODUCT_REG_KEY}" "URLInfoAbout"    "${PRODUCT_WEB_SITE}"
  WriteRegStr HKLM "${PRODUCT_REG_KEY}" "InstallLocation" "$INSTDIR"
  WriteRegStr HKLM "${PRODUCT_REG_KEY}" "DisplayIcon"     "$INSTDIR\${PRODUCT_EXE}"
  WriteRegStr HKLM "${PRODUCT_REG_KEY}" "UninstallString" "$INSTDIR\uninstall.exe"
  WriteRegDWORD HKLM "${PRODUCT_REG_KEY}" "NoModify" 1
  WriteRegDWORD HKLM "${PRODUCT_REG_KEY}" "NoRepair" 1
SectionEnd

Section "Raccourci Menu Démarrer" SecStartMenu
  CreateDirectory "$SMPROGRAMS\${PRODUCT_NAME}"
  ; Forcer l'icône moon.ico sur les raccourcis (évite l'icône générique
  ; Windows au premier lancement avant que le cache shell soit rafraîchi)
  CreateShortcut "$SMPROGRAMS\${PRODUCT_NAME}\${PRODUCT_NAME}.lnk" "$INSTDIR\${PRODUCT_EXE}" "" "$INSTDIR\moon.ico" 0
  CreateShortcut "$SMPROGRAMS\${PRODUCT_NAME}\Désinstaller.lnk" "$INSTDIR\uninstall.exe"
SectionEnd

Section "Raccourci Bureau" SecDesktop
  CreateShortcut "$DESKTOP\${PRODUCT_NAME}.lnk" "$INSTDIR\${PRODUCT_EXE}" "" "$INSTDIR\moon.ico" 0
SectionEnd

; ────────────────────────────────────────────────────────────────
; Descriptions des sections (info-bulles)
; ────────────────────────────────────────────────────────────────

LangString DESC_SecMain      ${LANG_FRENCH} "Fichiers principaux de l'application (obligatoire)."
LangString DESC_SecStartMenu ${LANG_FRENCH} "Créer les raccourcis dans le menu Démarrer."
LangString DESC_SecDesktop   ${LANG_FRENCH} "Créer un raccourci sur le Bureau."

LangString DESC_SecMain      ${LANG_ENGLISH} "Main application files (required)."
LangString DESC_SecStartMenu ${LANG_ENGLISH} "Create Start Menu shortcuts."
LangString DESC_SecDesktop   ${LANG_ENGLISH} "Create Desktop shortcut."

!insertmacro MUI_FUNCTION_DESCRIPTION_BEGIN
  !insertmacro MUI_DESCRIPTION_TEXT ${SecMain}      $(DESC_SecMain)
  !insertmacro MUI_DESCRIPTION_TEXT ${SecStartMenu} $(DESC_SecStartMenu)
  !insertmacro MUI_DESCRIPTION_TEXT ${SecDesktop}   $(DESC_SecDesktop)
!insertmacro MUI_FUNCTION_DESCRIPTION_END

; ════════════════════════════════════════════════════════════════
; Section désinstallation
; ════════════════════════════════════════════════════════════════

Section "Uninstall"
  ; Supprimer les raccourcis
  Delete "$SMPROGRAMS\${PRODUCT_NAME}\${PRODUCT_NAME}.lnk"
  Delete "$SMPROGRAMS\${PRODUCT_NAME}\Désinstaller.lnk"
  RMDir  "$SMPROGRAMS\${PRODUCT_NAME}"
  Delete "$DESKTOP\${PRODUCT_NAME}.lnk"

  ; Supprimer les fichiers installés
  RMDir /r "$INSTDIR"

  ; Supprimer la clé de registre
  DeleteRegKey HKLM "${PRODUCT_REG_KEY}"
SectionEnd
