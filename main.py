#!/usr/bin/env python3
"""
Moon Predictions — Application standalone de prévision des passages lunaires.

Calcule les passages de la Lune au-dessus de l'horizon pour une station
définie par son locator Maidenhead. Affiche elevation max, durée, distance,
path loss EME, score qualité.

Indépendant du EME Rotator Controller — peut tourner sans aucun matériel.
Utilise Skyfield + ephemerides JPL DE440s (précision sub-km).

Auteur : ON7KGK + Claude
Licence : MIT
"""

import math
import sys
import os
from datetime import datetime, timezone, timedelta

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QSpinBox, QPushButton, QTableWidget,
    QTableWidgetItem, QHeaderView, QSlider, QCheckBox, QComboBox,
    QFileDialog, QMessageBox, QGroupBox, QScrollArea, QDialog,
    QRadioButton, QButtonGroup,
)
from PyQt6.QtCore import Qt, QSettings, QTimer
from PyQt6.QtGui import QColor, QFont, QIcon, QTextDocument, QPageLayout
from PyQt6.QtPrintSupport import QPrinter
from PyQt6.QtWidgets import QToolTip

from moon_calc import (
    locator_to_latlon, get_moon_passes, enrich_moon_pass, compute_moon,
    sample_pass_timeline, compute_hour_angles, days_since_perigee,
    compute_degradation, compute_libration, compute_sun, ts as _ts,
)
from i18n import tr, set_language, get_language

APP_VERSION = "1.8.1"
APP_DATE = "2026-04-16"


# ════════════════════════════════════════════
# Constantes EME
# ════════════════════════════════════════════
_C_LIGHT = 299_792_458.0
_D_PERIGEE = 356_500e3
_A_MOON = 1_737.4e3
_RHO_MOON = 0.065

_EME_FREQS = [
    ("50 MHz",   50e6),
    ("144 MHz",  144e6),
    ("432 MHz",  432e6),
    ("1.2 GHz",  1296e6),
    ("2.3 GHz",  2304e6),
    ("5.7 GHz",  5760e6),
    ("10 GHz",   10368e6),
    ("24 GHz",   24048e6),
]

_DIST_GREEN = 370000
_DIST_ORANGE = 390000
_EL_GREEN = 20.0
_EL_ORANGE = 10.0
_DUR_GREEN = 300
_DUR_ORANGE = 120
_PL_GREEN = 1.0
_PL_ORANGE = 2.0


# ════════════════════════════════════════════
# Thèmes clair / sombre
# ════════════════════════════════════════════

_THEMES = {
    "dark": {
        # Fond principal et groupes
        "bg_main": "#19232D", "bg_group": "#1e2a36", "bg_input": "#2a3742",
        "fg_text": "#cccccc", "fg_input": "#ffffff", "fg_dim": "#888888",
        # Boutons
        "btn_bg": "#2E3D47", "btn_hover": "#3A4D59", "btn_checked": "#4a6080",
        "btn_border": "#555", "btn_discrete_fg": "#888", "btn_discrete_border": "#444",
        "btn_discrete_hover_fg": "#ccc", "btn_discrete_hover_border": "#666",
        "compute_bg": "#2a5a3a", "compute_hover": "#3a7a4a",
        # Table
        "bg_table": "#19232D", "gridline": "#333", "selection_bg": "#334",
        "bg_header": "#243039", "fg_header": "#aaaacc",
        # Slider
        "slider_groove": "#333", "slider_handle": "#6688cc",
        # EME data colors (vives sur fond sombre)
        "eme_green": "#44ff44", "eme_orange": "#ffaa00", "eme_red": "#ff4444",
        # Ligne MAINTENANT
        "now_visible_hi": "#55ccff", "now_visible_bg": "#1a2a3a",
        "now_invisible_hi": "#666666", "now_invisible_bg": "#1a1a1a",
        # Info / légende
        "fg_info": "#aaaacc", "link_color": "#6699ff",
        # Dialogues
        "dlg_bg": "#1a2530", "dlg_fg": "#cccccc",
        "about_title_color": "#FFD700", "about_version_color": "#66aaff",
        "dlg_hr": "#334",
    },
    "light": {
        # Fond gris clair (pas blanc pur — lisibilité couleurs EME)
        "bg_main": "#F0F1F4", "bg_group": "#E4E6EB", "bg_input": "#FFFFFF",
        "fg_text": "#1a1a1a", "fg_input": "#000000", "fg_dim": "#666666",
        # Boutons
        "btn_bg": "#D8DCE2", "btn_hover": "#C8CDD5", "btn_checked": "#A0B0CC",
        "btn_border": "#AAAAAA", "btn_discrete_fg": "#666", "btn_discrete_border": "#BBB",
        "btn_discrete_hover_fg": "#222", "btn_discrete_hover_border": "#888",
        "compute_bg": "#3A8A4A", "compute_hover": "#2E7A3E",
        # Table
        "bg_table": "#F0F1F4", "gridline": "#CCCCCC", "selection_bg": "#C0D0E8",
        "bg_header": "#D0D4DC", "fg_header": "#333355",
        # Slider
        "slider_groove": "#BBBBBB", "slider_handle": "#5577BB",
        # EME data colors (assombries pour fond clair)
        "eme_green": "#1B8C1B", "eme_orange": "#CC7700", "eme_red": "#CC2222",
        # Ligne MAINTENANT
        "now_visible_hi": "#0066AA", "now_visible_bg": "#D8E8F4",
        "now_invisible_hi": "#888888", "now_invisible_bg": "#E0E0E0",
        # Info / légende
        "fg_info": "#444466", "link_color": "#2255AA",
        # Dialogues
        "dlg_bg": "#EAECF0", "dlg_fg": "#1a1a1a",
        "about_title_color": "#B8860B", "about_version_color": "#2255AA",
        "dlg_hr": "#BBBBBB",
    },
}

_current_theme = "dark"


def _theme() -> dict:
    return _THEMES[_current_theme]


def _set_theme(name: str):
    global _current_theme
    _current_theme = name



# ════════════════════════════════════════════
# Police monospace cross-platform
# ════════════════════════════════════════════

def _make_monospace_font(size: int) -> QFont:
    """Retourne une QFont monospace compatible Windows/Mac/Linux.

    Windows  : Consolas
    macOS    : Menlo
    Linux    : DejaVu Sans Mono / Liberation Mono
    Fallback : Qt TypeWriter (générique monospace)
    """
    font = QFont()
    font.setStyleHint(QFont.StyleHint.TypeWriter)
    # Liste de familles par ordre de préférence
    if hasattr(font, "setFamilies"):  # Qt 6.2+
        font.setFamilies([
            "Consolas",              # Windows
            "Menlo",                 # macOS
            "DejaVu Sans Mono",      # Linux (Debian/Ubuntu)
            "Liberation Mono",       # Linux (RedHat/Fedora)
            "Courier New",           # Fallback universel
            "monospace",             # Générique Qt
        ])
    else:
        font.setFamily("Consolas")
    font.setPointSize(size)
    font.setFixedPitch(True)
    return font


# ════════════════════════════════════════════
# Localisation dates (français, sans dépendance locale)
# ════════════════════════════════════════════

def _loc_date(dt):
    """Formatte une date localisée : 'Lun 01 Jan'."""
    day = tr(f"day_{dt.weekday()}")
    mon = tr(f"mon_{dt.month}")
    return f"{day} {dt.day:02d} {mon}"


def _loc_date_long(dt):
    """Formatte une date longue localisée : 'Lun 01 Jan 2026'."""
    day = tr(f"day_{dt.weekday()}")
    mon = tr(f"mon_{dt.month}")
    return f"{day} {dt.day:02d} {mon} {dt.year}"


def _eme_path_loss_perigee(freq_hz: float) -> float:
    """Path loss total EME aller-retour au périgée (dB)."""
    lam = _C_LIGHT / freq_hz
    num = (4.0 * math.pi) ** 3 * _D_PERIGEE ** 4
    den = _RHO_MOON * math.pi * _A_MOON ** 2 * lam ** 2
    return 10.0 * math.log10(num / den)


def _get_icon_path():
    """Retourne le chemin absolu vers moon.ico.

    Compatible Nuitka (exe compilé) et mode développement (.py).
    Sous Nuitka, __file__ peut pointer vers le source d'origine — on utilise
    sys.executable pour trouver le dossier d'installation.
    """
    if getattr(sys, 'frozen', False) or '__compiled__' in globals():
        base = os.path.dirname(sys.executable)
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, "moon.ico")


def _eme_color(value, green_max, orange_max, invert=False):
    t = _theme()
    if invert:
        if value <= green_max: return QColor(t["eme_green"])
        if value <= orange_max: return QColor(t["eme_orange"])
        return QColor(t["eme_red"])
    if value >= green_max: return QColor(t["eme_green"])
    if value >= orange_max: return QColor(t["eme_orange"])
    return QColor(t["eme_red"])


def _quality_score(max_el, duration_min, ploss, moon_sun=180.0,
                   lib_rate=0.0, freq_hz=10368e6):
    """Indice de qualité EME 0-10, adapté à la fréquence.

    Pondération VHF/UHF (< 1 GHz) :
      EL 30%, Durée 25%, Path loss 25%, Moon-Sun 20%

    Pondération microwave (>= 1 GHz) :
      Libration 30%, Path loss 25%, EL 20%, Moon-Sun 15%, Durée 10%
    """
    el_score = min(max_el / 9.0, 10.0)
    dur_score = min(duration_min / 60.0, 10.0)
    pl_score = max(10.0 - ploss * 4.0, 0.0)
    ms_score = min(moon_sun / 18.0, 10.0)

    # Libration score : 0 deg/h = 10 (excellent), 0.5 deg/h = 0 (mauvais)
    lib_score = max(10.0 - lib_rate * 20.0, 0.0)

    if freq_hz >= 1e9:
        # Microwave (1.2 GHz+) : libration est critique
        return (lib_score * 0.30 + pl_score * 0.25 + el_score * 0.20
                + ms_score * 0.15 + dur_score * 0.10)
    else:
        # VHF/UHF : libration a peu d'effet
        return (el_score * 0.30 + dur_score * 0.25
                + pl_score * 0.25 + ms_score * 0.20)


def _quality_squares(score):
    n = max(0, min(10, round(score)))
    return "\u25a0" * n + "\u25a1" * (10 - n)


def _quality_color(score):
    t = _theme()
    if score >= 7: return QColor(t["eme_green"])
    if score >= 4: return QColor(t["eme_orange"])
    return QColor(t["eme_red"])


def _utc_offset() -> timedelta:
    return datetime.now(timezone.utc).astimezone().utcoffset()


def _make_item(text, color=None):
    item = QTableWidgetItem(text)
    item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
    if color:
        item.setForeground(color)
    return item


# ════════════════════════════════════════════
# Fenêtre principale
# ════════════════════════════════════════════

class MoonPredictionsWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Moon Predictions \u2014 EME Pass Forecast")

        # Icône fenêtre (barre des tâches + titre)
        icon_path = _get_icon_path()
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        self.setMinimumSize(900, 500)

        self._settings = QSettings("ON7KGK", "MoonPredictions")
        self._passes_raw = []
        self._lat = 0.0
        self._lon = 0.0
        self._alt_m = 0
        self._periodIndex = 0
        # Conventions de calcul (defauts : EME)
        self._distRef = "topo"       # "topo" ou "geo"
        self._horizonMode = "geom"   # "geom" ou "visual"

        self._filterTimer = QTimer()
        self._filterTimer.setSingleShot(True)
        self._filterTimer.setInterval(150)
        self._filterTimer.timeout.connect(self._refreshTable)
        # Debounce pour EL min : recomputation complete (horizon mecanique)
        self._elMinTimer = QTimer()
        self._elMinTimer.setSingleShot(True)
        self._elMinTimer.setInterval(500)
        self._elMinTimer.timeout.connect(self._compute)
        # Auto-refresh de la ligne MAINTENANT toutes les 5 secondes
        self._nowRowTimer = QTimer()
        self._nowRowTimer.setInterval(5000)
        self._nowRowTimer.timeout.connect(self._refreshNowRow)

        self._buildUI()
        self._loadSettings()

    # ════════════════════════════════════════════
    # Thème
    # ════════════════════════════════════════════

    def _applyTheme(self):
        """Applique le stylesheet du thème actif à toute la fenêtre."""
        t = _theme()
        self.setStyleSheet(f"""
            QMainWindow {{ background-color: {t['bg_main']}; color: {t['fg_text']}; }}
            QWidget {{ color: {t['fg_text']}; }}
            QGroupBox {{
                background-color: {t['bg_group']};
                border: 1px solid {t['gridline']};
                border-radius: 6px;
                margin-top: 6px;
                padding-top: 10px;
            }}
            QLineEdit, QComboBox {{
                background-color: {t['bg_input']};
                border: 1px solid {t['btn_border']};
                border-radius: 3px;
                padding: 4px 6px;
                color: {t['fg_input']};
            }}
            QSpinBox {{
                background-color: {t['bg_input']};
                border: 1px solid {t['btn_border']};
                border-radius: 3px;
                padding: 2px 24px 2px 6px;
                color: {t['fg_input']};
                min-width: 40px;
            }}
            QSpinBox::up-button, QSpinBox::down-button {{
                width: 20px;
            }}
            QPushButton {{
                background-color: {t['btn_bg']};
                border: 1px solid {t['btn_border']};
                border-radius: 3px;
                padding: 6px 14px;
            }}
            QPushButton:hover {{ background-color: {t['btn_hover']}; }}
            QPushButton:checked {{ background-color: {t['btn_checked']}; }}
            QTableWidget {{
                background-color: {t['bg_table']};
                gridline-color: {t['gridline']};
                selection-background-color: {t['selection_bg']};
            }}
            QHeaderView::section {{
                background-color: {t['bg_header']};
                color: {t['fg_header']};
                border: 1px solid {t['gridline']};
                padding: 4px;
                font-weight: bold;
            }}
            QSlider::groove:horizontal {{
                background: {t['slider_groove']};
                height: 6px;
                border-radius: 3px;
            }}
            QSlider::handle:horizontal {{
                background: {t['slider_handle']};
                width: 16px;
                height: 16px;
                margin: -5px 0;
                border-radius: 8px;
            }}
        """)
        # Bouton Calculer — style spécifique
        self.btnCompute.setStyleSheet(
            f"QPushButton {{ background-color: {t['compute_bg']}; font-weight: bold; "
            f"color: #ffffff; }}"
            f"QPushButton:hover {{ background-color: {t['compute_hover']}; }}"
        )
        # Boutons discrets (Aide, About)
        _btn_discrete = (
            f"QPushButton {{ color: {t['btn_discrete_fg']}; "
            f"border: 1px solid {t['btn_discrete_border']}; padding: 4px 10px; }}"
            f"QPushButton:hover {{ color: {t['btn_discrete_hover_fg']}; "
            f"border-color: {t['btn_discrete_hover_border']}; }}"
        )
        self.btnHelp.setStyleSheet(_btn_discrete)
        self.btnAbout.setStyleSheet(_btn_discrete)
        self.btnConventions.setStyleSheet(_btn_discrete)
        # Labels à style spécifique
        self.labelTz.setStyleSheet(f"color: {t['fg_dim']};")
        self.labelInfo.setStyleSheet(f"color: {t['fg_info']};")
        self.labelFooter.setStyleSheet(f"color: {t['fg_dim']};")
        # Légende couleurs
        self.labelLegend.setText(
            f"<span style='color:{t['eme_green']};'>\u25a0</span> {tr('legend_excellent')}  "
            f"<span style='color:{t['eme_orange']};'>\u25a0</span> {tr('legend_medium')}  "
            f"<span style='color:{t['eme_red']};'>\u25a0</span> {tr('legend_poor')}"
        )
        # Lien EME Observer
        self.linkSked.setText(
            f"<a href='https://dxer.site/eme-observer/' "
            f"style='color: {t['link_color']}; text-decoration: none;'>"
            f"EME Observer (SA5IKN)</a>"
        )
        # Icône bouton thème
        if hasattr(self, 'btnTheme'):
            self.btnTheme.setText(
                "\u2600" if _current_theme == "dark" else "\u263d")
        # Rafraîchir la table si des données existent
        if self._passes_raw:
            self._refreshTable()

    def _onThemeToggle(self):
        new = "light" if _current_theme == "dark" else "dark"
        _set_theme(new)
        self._applyTheme()
        self._applyFontSize()
        self._settings.setValue("theme", new)
        self._settings.sync()

    # ════════════════════════════════════════════
    # Conventions de calcul
    # ════════════════════════════════════════════

    def _horizonDeg(self) -> float:
        """Retourne l'horizon en degres selon le mode choisi."""
        return -0.8333 if self._horizonMode == "visual" else 0.0

    def _effectiveHorizonDeg(self) -> float:
        """Retourne l'horizon effectif en degres pour les calculs de lever/coucher.

        Si l'utilisateur a defini EL min > 0 (obstacle mecanique : parabole
        limitee en elevation basse, batiment, etc.), on utilise EL min comme
        horizon au lieu de 0\u00b0/-0.83\u00b0. Le lever/coucher affiches
        correspondent alors au moment ou la Lune franchit son horizon utile.
        """
        el_min = float(self.sliderMinEl.value())
        # Si EL min > 0, il prend le pas sur l'horizon geometrique/visuel
        return max(self._horizonDeg(), el_min)

    def _showConventions(self):
        """Dialogue de choix des conventions de calcul."""
        t = _theme()
        dlg = QDialog(self)
        dlg.setWindowTitle(tr("conv_title"))
        dlg.setMinimumSize(640, 640)
        dlg.setStyleSheet(
            f"QDialog {{ background-color: {t['dlg_bg']}; color: {t['dlg_fg']}; }}"
            f"QLabel {{ color: {t['dlg_fg']}; }}"
            f"QGroupBox {{ border: 1px solid {t['btn_border']}; "
            f"border-radius: 4px; margin-top: 10px; padding-top: 14px; "
            f"font-weight: bold; }}"
            f"QGroupBox::title {{ subcontrol-origin: margin; "
            f"left: 10px; padding: 0 4px; }}"
            f"QRadioButton {{ color: {t['dlg_fg']}; padding: 6px 8px; "
            f"border-radius: 4px; border: 1px solid transparent; }}"
            f"QRadioButton:checked {{ background-color: {t['btn_checked']}; "
            f"border: 1px solid {t['slider_handle']}; font-weight: bold; "
            f"color: #ffffff; }}"
            f"QRadioButton::indicator {{ width: 16px; height: 16px; }}"
            f"QRadioButton::indicator:checked {{ "
            f"background-color: {t['slider_handle']}; "
            f"border: 3px solid #ffffff; border-radius: 8px; }}"
            f"QRadioButton::indicator:unchecked {{ "
            f"background-color: {t['bg_input']}; "
            f"border: 2px solid {t['btn_border']}; border-radius: 8px; }}"
        )
        icon_path = _get_icon_path()
        if os.path.exists(icon_path):
            dlg.setWindowIcon(QIcon(icon_path))

        lay = QVBoxLayout(dlg)
        lay.setSpacing(10)

        # Intro
        intro = QLabel(tr("conv_intro"))
        intro.setWordWrap(True)
        intro.setTextFormat(Qt.TextFormat.RichText)
        lay.addWidget(intro)

        # ── Groupe Distance ──
        distBox = QGroupBox(tr("conv_dist_group"))
        distLay = QVBoxLayout(distBox)
        self._radioDistTopo = QRadioButton(tr("conv_dist_topo"))
        self._radioDistGeo = QRadioButton(tr("conv_dist_geo"))
        self._radioDistTopo.setChecked(self._distRef == "topo")
        self._radioDistGeo.setChecked(self._distRef == "geo")
        distLay.addWidget(self._radioDistTopo)
        distLay.addWidget(self._radioDistGeo)
        distExplain = QLabel(tr("conv_dist_explain"))
        distExplain.setWordWrap(True)
        distExplain.setTextFormat(Qt.TextFormat.RichText)
        distLay.addWidget(distExplain)
        lay.addWidget(distBox)

        # ── Groupe Horizon ──
        horBox = QGroupBox(tr("conv_hor_group"))
        horLay = QVBoxLayout(horBox)
        self._radioHorGeom = QRadioButton(tr("conv_hor_geom"))
        self._radioHorVisual = QRadioButton(tr("conv_hor_visual"))
        self._radioHorGeom.setChecked(self._horizonMode == "geom")
        self._radioHorVisual.setChecked(self._horizonMode == "visual")
        horLay.addWidget(self._radioHorGeom)
        horLay.addWidget(self._radioHorVisual)
        horExplain = QLabel(tr("conv_hor_explain"))
        horExplain.setWordWrap(True)
        horExplain.setTextFormat(Qt.TextFormat.RichText)
        horLay.addWidget(horExplain)
        lay.addWidget(horBox)

        lay.addStretch()

        # Boutons OK / Cancel
        btnRow = QHBoxLayout()
        btnRow.addStretch()
        btnOk = QPushButton(tr("btn_apply"))
        btnOk.setStyleSheet(
            f"QPushButton {{ background-color: {t['compute_bg']}; "
            f"color: #ffffff; font-weight: bold; padding: 6px 20px; }}"
            f"QPushButton:hover {{ background-color: {t['compute_hover']}; }}"
        )
        btnOk.clicked.connect(dlg.accept)
        btnCancel = QPushButton(tr("btn_cancel"))
        btnCancel.setStyleSheet("QPushButton { padding: 6px 20px; }")
        btnCancel.clicked.connect(dlg.reject)
        btnRow.addWidget(btnCancel)
        btnRow.addWidget(btnOk)
        lay.addLayout(btnRow)

        # Forcer la taille de police utilisateur sur le dialog
        self._applyDialogFont(dlg)

        if dlg.exec() == QDialog.DialogCode.Accepted:
            new_dist = "topo" if self._radioDistTopo.isChecked() else "geo"
            new_hor = "geom" if self._radioHorGeom.isChecked() else "visual"
            changed = (new_dist != self._distRef
                       or new_hor != self._horizonMode)
            self._distRef = new_dist
            self._horizonMode = new_hor
            self._settings.setValue("dist_reference", self._distRef)
            self._settings.setValue("horizon_mode", self._horizonMode)
            self._settings.sync()
            if changed and self._passes_raw:
                # Recalculer avec les nouvelles conventions
                self._compute()

    # ════════════════════════════════════════════
    # UI
    # ════════════════════════════════════════════

    def _buildUI(self):

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setSpacing(8)

        # ── Bandeau station ──
        stationGroup = QGroupBox()
        stationLayout = QHBoxLayout(stationGroup)

        stationLayout.addWidget(QLabel(tr("lbl_callsign")))
        self.editCallsign = QLineEdit()
        self.editCallsign.setPlaceholderText("ON7KGK")
        stationLayout.addWidget(self.editCallsign)

        stationLayout.addSpacing(15)
        stationLayout.addWidget(QLabel(tr("lbl_locator")))
        self.editLocator = QLineEdit()
        self.editLocator.setPlaceholderText("JO20BM85")
        stationLayout.addWidget(self.editLocator)

        stationLayout.addSpacing(15)
        stationLayout.addWidget(QLabel(tr("lbl_altitude")))
        self.spinAltitude = QSpinBox()
        self.spinAltitude.setRange(0, 9000)
        self.spinAltitude.setSuffix(" m")
        stationLayout.addWidget(self.spinAltitude)

        stationLayout.addSpacing(15)
        self.btnCompute = QPushButton(tr("btn_compute"))
        self.btnCompute.clicked.connect(self._compute)
        stationLayout.addWidget(self.btnCompute)

        self.btnSave = QPushButton(tr("btn_save"))
        self.btnSave.setToolTip(tr("tip_save"))
        self.btnSave.clicked.connect(self._onSaveClicked)
        stationLayout.addWidget(self.btnSave)

        stationLayout.addStretch()

        self.btnTheme = QPushButton()
        self.btnTheme.setToolTip(tr("tip_theme"))
        self.btnTheme.setFixedWidth(36)
        self.btnTheme.clicked.connect(self._onThemeToggle)
        stationLayout.addWidget(self.btnTheme)

        self.btnConventions = QPushButton(tr("btn_conventions"))
        self.btnConventions.setToolTip(tr("tip_conventions"))
        self.btnConventions.clicked.connect(self._showConventions)
        stationLayout.addWidget(self.btnConventions)

        self.btnHelp = QPushButton(tr("btn_help"))
        self.btnHelp.clicked.connect(self._showHelp)
        stationLayout.addWidget(self.btnHelp)

        self.btnAbout = QPushButton(tr("btn_about"))
        self.btnAbout.clicked.connect(self._showAbout)
        stationLayout.addWidget(self.btnAbout)

        layout.addWidget(stationGroup)

        # ── Filtres — Ligne 1 : sliders + fréquence ──
        filterLine1 = QHBoxLayout()
        filterLine1.setSpacing(12)

        filterLine1.addWidget(QLabel(tr("lbl_el_min")))
        self.sliderMinEl = QSlider(Qt.Orientation.Horizontal)
        self.sliderMinEl.setRange(0, 45)
        self.sliderMinEl.setMinimumWidth(100)
        self.sliderMinEl.setToolTip(tr("tip_el_min"))
        self.sliderMinEl.valueChanged.connect(self._onElMinChanged)
        filterLine1.addWidget(self.sliderMinEl)
        self.labelMinEl = QLabel("0\u00b0")
        self.labelMinEl.setMinimumWidth(35)
        filterLine1.addWidget(self.labelMinEl)

        filterLine1.addSpacing(15)
        filterLine1.addWidget(QLabel(tr("lbl_score_min")))
        self.sliderMinScore = QSlider(Qt.Orientation.Horizontal)
        self.sliderMinScore.setRange(0, 80)
        self.sliderMinScore.setMinimumWidth(80)
        self.sliderMinScore.setToolTip(tr("tip_quality_filter"))
        self.sliderMinScore.valueChanged.connect(self._onFilterChanged)
        filterLine1.addWidget(self.sliderMinScore)
        self.labelMinScore = QLabel("0.0")
        self.labelMinScore.setMinimumWidth(30)
        filterLine1.addWidget(self.labelMinScore)

        filterLine1.addSpacing(15)
        filterLine1.addWidget(QLabel(tr("lbl_frequency")))
        self.comboFreq = QComboBox()
        for label, hz in _EME_FREQS:
            self.comboFreq.addItem(label, hz)
        self.comboFreq.setCurrentIndex(6)
        self.comboFreq.currentIndexChanged.connect(self._onFilterChanged)
        filterLine1.addWidget(self.comboFreq)

        filterLine1.addSpacing(15)
        self.btn1_30 = QPushButton("1-30 j")
        self.btn1_30.setCheckable(True)
        self.btn1_30.setChecked(True)
        self.btn1_30.clicked.connect(lambda: self._onPeriodChanged(0))
        filterLine1.addWidget(self.btn1_30)
        self.btn31_60 = QPushButton("31-60 j")
        self.btn31_60.setCheckable(True)
        self.btn31_60.clicked.connect(lambda: self._onPeriodChanged(1))
        filterLine1.addWidget(self.btn31_60)

        filterLine1.addStretch()
        layout.addLayout(filterLine1)

        # ── Filtres — Ligne 2 : checkboxes + police + lien + période ──
        filterLine2 = QHBoxLayout()
        filterLine2.setSpacing(12)

        self.chkPhase = QCheckBox(tr("lbl_phase"))
        self.chkPhase.setChecked(True)
        self.chkPhase.setToolTip(tr("tip_phase_chk"))
        self.chkPhase.stateChanged.connect(self._onFilterChanged)
        filterLine2.addWidget(self.chkPhase)

        filterLine2.addSpacing(10)
        self.chkLocalTime = QCheckBox(tr("lbl_local_time"))
        self.chkLocalTime.setToolTip(tr("tip_local_time"))
        self.chkLocalTime.stateChanged.connect(self._onFilterChanged)
        filterLine2.addWidget(self.chkLocalTime)
        self.labelTz = QLabel("")
        filterLine2.addWidget(self.labelTz)
        self._updateTzLabel()

        filterLine2.addSpacing(15)
        filterLine2.addWidget(QLabel(tr("lbl_font_size")))
        self.spinFontSize = QSpinBox()
        self.spinFontSize.setRange(8, 18)
        self.spinFontSize.setValue(10)
        self.spinFontSize.setSuffix(" pt")
        self.spinFontSize.setToolTip(tr("tip_font_size"))
        self.spinFontSize.valueChanged.connect(self._onFontSizeChanged)
        filterLine2.addWidget(self.spinFontSize)

        filterLine2.addSpacing(15)
        self.btnExportTxt = QPushButton(tr("btn_export_txt"))
        self.btnExportTxt.clicked.connect(self._exportTxt)
        filterLine2.addWidget(self.btnExportTxt)

        self.btnExportPdf = QPushButton(tr("btn_export_pdf"))
        self.btnExportPdf.clicked.connect(self._exportPdf)
        filterLine2.addWidget(self.btnExportPdf)

        filterLine2.addSpacing(15)
        filterLine2.addWidget(QLabel(tr("lbl_language")))
        self.comboLang = QComboBox()
        self.comboLang.addItem("Fran\u00e7ais", "fr")
        self.comboLang.addItem("Nederlands", "nl")
        self.comboLang.addItem("English", "en")
        self.comboLang.currentIndexChanged.connect(self._onLanguageChanged)
        filterLine2.addWidget(self.comboLang)

        filterLine2.addStretch()

        # Lien EME Observer (SA5IKN)
        self.linkSked = QLabel()
        self.linkSked.setOpenExternalLinks(True)
        self.linkSked.setToolTip(tr("tip_sked"))
        filterLine2.addWidget(self.linkSked)

        layout.addLayout(filterLine2)

        # ── Info + Légende (même ligne) ──
        infoBar = QHBoxLayout()
        self.labelInfo = QLabel(tr("info_enter_locator"))
        infoBar.addWidget(self.labelInfo)
        infoBar.addStretch()
        self.labelLegend = QLabel()
        infoBar.addWidget(self.labelLegend)
        layout.addLayout(infoBar)

        # ── Table ──
        self.table = QTableWidget()
        self.table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(False)
        self.table.verticalHeader().setVisible(False)  # pas de numéros de lignes
        # Clic sur une ligne de passage -> detail toutes les 30 min
        self.table.cellClicked.connect(self._onRowClicked)
        self.table.setToolTip(tr("tip_row_dblclick"))
        layout.addWidget(self.table)

        # ── Footer ──
        footerBar = QHBoxLayout()
        self.labelFooter = QLabel("")
        footerBar.addWidget(self.labelFooter)

        layout.addLayout(footerBar)

    # ════════════════════════════════════════════
    # Settings persistance
    # ════════════════════════════════════════════

    def _loadSettings(self):
        self.editCallsign.setText(
            self._settings.value("callsign", "", type=str))
        self.editLocator.setText(
            self._settings.value("locator", "", type=str))
        self.spinAltitude.setValue(
            self._settings.value("altitude", 0, type=int))
        self.chkLocalTime.setChecked(
            self._settings.value("local_time", False, type=bool))
        self.chkPhase.setChecked(
            self._settings.value("show_phase", True, type=bool))
        self.sliderMinEl.setValue(
            self._settings.value("slider_min_el", 0, type=int))
        self.sliderMinScore.setValue(
            self._settings.value("slider_min_score", 0, type=int))
        self.spinFontSize.setValue(
            self._settings.value("font_size", 10, type=int))
        self.comboFreq.setCurrentIndex(
            self._settings.value("freq_idx", 6, type=int))
        # Langue (bloquer le signal pour éviter le popup au chargement)
        lang = self._settings.value("language", "fr", type=str)
        idx = {"fr": 0, "nl": 1, "en": 2}.get(lang, 0)
        self.comboLang.blockSignals(True)
        self.comboLang.setCurrentIndex(idx)
        self.comboLang.blockSignals(False)
        # Thème (charger AVANT applyFontSize et applyTheme)
        theme = self._settings.value("theme", "dark", type=str)
        _set_theme(theme if theme in _THEMES else "dark")
        self._applyTheme()
        self._applyFontSize()
        # Conventions de calcul
        dist_ref = self._settings.value("dist_reference", "topo", type=str)
        self._distRef = dist_ref if dist_ref in ("topo", "geo") else "topo"
        hor_mode = self._settings.value("horizon_mode", "geom", type=str)
        self._horizonMode = hor_mode if hor_mode in ("geom", "visual") else "geom"

    def showEvent(self, event):
        """Auto-calcul au premier affichage si le locator est renseigné
        (minimum 6 caractères pour une précision raisonnable)."""
        super().showEvent(event)
        if not hasattr(self, '_autoCalcDone'):
            self._autoCalcDone = True
            locator = self.editLocator.text().strip()
            if locator and len(locator) >= 6:
                # Lancer le calcul 200ms après l'affichage (UI responsive)
                QTimer.singleShot(200, self._compute)

    def _saveSettings(self):
        self._settings.setValue("callsign", self.editCallsign.text())
        self._settings.setValue("locator", self.editLocator.text())
        self._settings.setValue("altitude", self.spinAltitude.value())
        self._settings.setValue(
            "local_time", self.chkLocalTime.isChecked())
        self._settings.setValue(
            "show_phase", self.chkPhase.isChecked())
        self._settings.setValue("slider_min_el", self.sliderMinEl.value())
        self._settings.setValue("slider_min_score", self.sliderMinScore.value())
        self._settings.setValue("font_size", self.spinFontSize.value())
        self._settings.setValue("freq_idx", self.comboFreq.currentIndex())
        self._settings.setValue("language", self.comboLang.currentData() or "fr")
        self._settings.sync()

    def _onSaveClicked(self):
        self._saveSettings()
        # Feedback visuel temporaire (texte fixe pour le retour)
        self.btnSave.setText(tr("btn_saved"))
        QTimer.singleShot(1500,
            lambda: self.btnSave.setText(tr("btn_save")))

    def _applyFontSize(self):
        """Applique la taille de police à TOUT l'interface."""
        size = self.spinFontSize.value()

        # Police de base — appliquée à la fenêtre + forcée sur tous les enfants
        ui_font = QFont()
        ui_font.setPointSize(size)
        self.setFont(ui_font)
        # Les infobulles ont leur propre police globale — la synchroniser
        QToolTip.setFont(ui_font)
        # Forcer sur CHAQUE widget enfant (le stylesheet peut bloquer la cascade)
        for child in self.findChildren(QWidget):
            child.setFont(ui_font)

        # Table et header : police monospace cross-platform
        # Windows=Consolas, Mac=Menlo, Linux=DejaVu Sans Mono
        self.table.setFont(_make_monospace_font(size))

        hdr_font = _make_monospace_font(max(size - 1, 8))
        hdr_font.setBold(True)
        self.table.horizontalHeader().setFont(hdr_font)

        # Hauteur des lignes ajustée à la taille de police
        self.table.verticalHeader().setDefaultSectionSize(int(size * 1.9) + 4)

        # Re-layout : forcer le recalcul des colonnes
        # ResizeToContents seul ne tient pas toujours compte des headers
        for c in range(self.table.columnCount()):
            hdr_width = self.table.horizontalHeader().sectionSizeHint(c)
            content_width = self.table.sizeHintForColumn(c)
            self.table.setColumnWidth(c, max(hdr_width, content_width) + 10)

    def _onLanguageChanged(self):
        lang = self.comboLang.currentData()
        if lang:
            set_language(lang)
            self._settings.setValue("language", lang)
            self._settings.sync()
            QMessageBox.information(
                self, "Moon Predictions", tr("msg_lang_restart"))

    def _onFontSizeChanged(self):
        self._applyFontSize()
        self._settings.setValue("font_size", self.spinFontSize.value())
        self._settings.sync()

    def closeEvent(self, event):
        self._saveSettings()
        super().closeEvent(event)

    # ════════════════════════════════════════════
    # Calcul
    # ════════════════════════════════════════════

    def _updateTzLabel(self):
        offset = _utc_offset()
        total_s = int(offset.total_seconds())
        h, m = divmod(abs(total_s), 3600)
        sign = "+" if total_s >= 0 else "-"
        self.labelTz.setText(f"(UTC{sign}{h}:{m // 60:02d})")

    def _compute(self):
        locator = self.editLocator.text().strip()
        if not locator:
            QMessageBox.warning(self, tr("msg_locator_missing_title"),
                                tr("msg_locator_missing"))
            return
        if len(locator) < 6:
            QMessageBox.warning(self, tr("msg_locator_short_title"),
                                tr("msg_locator_short"))
            return

        try:
            lat, lon = locator_to_latlon(locator)
        except ValueError as e:
            QMessageBox.warning(self, tr("msg_locator_invalid_title"),
                                f"{tr('msg_error')} : {e}")
            return

        self._lat, self._lon = lat, lon
        self._alt_m = self.spinAltitude.value()
        callsign = self.editCallsign.text().strip()

        # Position actuelle de la Lune (info)
        offset_hours = self._periodIndex * 30 * 24
        period_label = "1-30" if self._periodIndex == 0 else "31-60"
        self.labelInfo.setText(tr("info_computing", period=period_label))
        self.table.setRowCount(0)
        QApplication.processEvents()

        try:
            # EL min agit aussi comme horizon mecanique : lever/coucher
            # calcules au moment ou la Lune franchit cet horizon utile.
            passes = get_moon_passes(
                lat, lon, self._alt_m,
                hours=30 * 24, start_offset_hours=offset_hours,
                horizon_degrees=self._effectiveHorizonDeg())
        except Exception as e:
            QMessageBox.critical(
                self, tr("msg_error_calc"), f"Skyfield : {e}")
            return

        self._passes_raw = []
        for p in passes:
            d = dict(p)
            try:
                enrich_moon_pass(lat, lon, self._alt_m, d,
                                 dist_reference=self._distRef)
            except Exception:
                continue
            d["ploss"] = (40.0 * math.log10(d["dist_km"] / 356500.0)
                          if d["dist_km"] > 0 else 0)
            # Doppler spread à la fréquence sélectionnée
            freq = self.comboFreq.currentData() or 10368e6
            base_spread = d.get("doppler_spread", 0)
            d["doppler_spread_freq"] = round(
                base_spread * freq / 10.368e9, 0) if base_spread else 0
            # Score base sur le lib_rate au meilleur moment du passage
            # (spread minimum) plut\u00f4t que sur l'EL max — refl\u00e8te mieux
            # les "fen\u00eatres magiques" cherch\u00e9es par les op\u00e9rateurs EME.
            d["score"] = _quality_score(
                d["max_el"], d["duration_min"], d["ploss"],
                d.get("moon_sun", 180),
                d.get("lib_rate_min", d.get("lib_rate", 0)), freq)
            self._passes_raw.append(d)

        station = f"{callsign} " if callsign else ""
        self.labelInfo.setText(tr("info_result",
            station=station, locator=locator, alt=self._alt_m,
            count=len(self._passes_raw), period=period_label))

        self._saveSettings()
        self._refreshTable()
        # Demarrer l'auto-refresh de la ligne MAINTENANT (5 sec)
        if not self._nowRowTimer.isActive():
            self._nowRowTimer.start()

    def _onPeriodChanged(self, index):
        self._periodIndex = index
        self.btn1_30.setChecked(index == 0)
        self.btn31_60.setChecked(index == 1)
        if self._passes_raw or self.editLocator.text():
            self._compute()

    def _onFilterChanged(self):
        self.labelMinScore.setText(
            f"{self.sliderMinScore.value() / 10:.1f}")
        self._updateTzLabel()
        self._filterTimer.start()

    def _onElMinChanged(self, value):
        """Slider EL min change -> met \u00e0 jour le label immediatement,
        et debounce une recomputation complete (horizon mecanique)."""
        self.labelMinEl.setText(f"{value}\u00b0")
        # Si pas encore calcule (pas de locator), pas la peine de declencher
        if self.editLocator.text().strip() and self._passes_raw:
            self._elMinTimer.start()

    # ════════════════════════════════════════════
    # Affichage table
    # ════════════════════════════════════════════

    def _buildNowRow(self, freq, pl_perigee, show_phase):
        """Construit la ligne 'MAINTENANT' avec la position actuelle de la Lune.

        Returns list de tuples (text, QColor|None) pour chaque colonne.
        """
        from moon_calc import (compute_moon, compute_sun, compute_libration,
                               ts, _angular_sep_deg)

        # Lever/coucher de la Lune : utilise l'horizon effectif (= EL min
        # mecanique si defini > 0)
        moon = compute_moon(self._lat, self._lon, self._alt_m,
                            dist_reference=self._distRef,
                            horizon_degrees=self._effectiveHorizonDeg())
        # Le Soleil n'est pas concerne par l'horizon mecanique de la parabole
        sun = compute_sun(self._lat, self._lon, self._alt_m,
                          horizon_degrees=self._horizonDeg())
        lib = compute_libration(self._lat, self._lon, self._alt_m, ts.now())

        az = moon["az"]
        el = moon["el"]
        dist = moon["dist_km"]
        illum = moon["illumination"]
        phase = moon["phase_name"]
        ploss = 40.0 * math.log10(dist / 356500.0) if dist > 0 else 0
        total_pl = pl_perigee + ploss
        lib_rate = lib["lib_rate"]
        spread = lib["doppler_spread_hz"] * freq / 10.368e9

        # Prochain lever/coucher
        rise = moon.get("next_rise")
        sett = moon.get("next_set")
        use_local = self.chkLocalTime.isChecked()
        tz_offset = _utc_offset() if use_local else timedelta(0)

        rise_txt = (rise + tz_offset).strftime("%H:%M") if rise else "---"
        set_txt = (sett + tz_offset).strftime("%H:%M") if sett else "---"

        # Durée du passage actuel (si visible) ou prochain passage
        if rise and sett:
            dur_min = (sett - rise).total_seconds() / 60.0
            dur_h = int(abs(dur_min) // 60)
            dur_m = int(abs(dur_min) % 60)
            dur_txt = f"{dur_h}h{dur_m:02d}"
            dur_col = _eme_color(abs(dur_min), _DUR_GREEN, _DUR_ORANGE)
        else:
            dur_txt = "---"
            dur_col = None

        # Déclinaison actuelle
        from moon_calc import eph, wgs84
        location = wgs84.latlon(self._lat, self._lon, elevation_m=self._alt_m)
        observer = eph['earth'] + location
        t = ts.now()
        app_moon = observer.at(t).observe(eph['moon']).apparent()
        _, dec, _ = app_moon.radec()
        decl = dec.degrees

        # Angle Moon-Sun
        ms_angle = _angular_sep_deg(az, el, sun["az"], sun["el"])

        # Score qualité
        score = _quality_score(max(el, 0), abs(dur_min) if rise and sett else 0,
                               ploss, ms_angle, lib_rate, freq)

        # Lune visible ou sous horizon ?
        visible = el > 0

        t_colors = _theme()
        if visible:
            # Lune visible — couleurs normales, fond distinct
            hi = QColor(t_colors["now_visible_hi"])
            now_bg = QColor(t_colors["now_visible_bg"])
            dist_col = _eme_color(dist, _DIST_GREEN, _DIST_ORANGE, invert=True)
            pl_col = _eme_color(ploss, _PL_GREEN, _PL_ORANGE, invert=True)
            el_col = _eme_color(el, _EL_GREEN, _EL_ORANGE)
            if lib_rate < 0.10: lib_col = QColor(t_colors["eme_green"])
            elif lib_rate < 0.25: lib_col = QColor(t_colors["eme_orange"])
            else: lib_col = QColor(t_colors["eme_red"])
            if spread < 50: spr_col = QColor(t_colors["eme_green"])
            elif spread < 150: spr_col = QColor(t_colors["eme_orange"])
            else: spr_col = QColor(t_colors["eme_red"])
            if ms_angle < 5: ms_col = QColor(t_colors["eme_red"])
            elif ms_angle < 15: ms_col = QColor(t_colors["eme_orange"])
            else: ms_col = QColor(t_colors["eme_green"])
            sq = _quality_squares(score)
            qc = _quality_color(score)
            el_txt = f"{el:+.1f}\u00b0 {tr('now_visible')}"
        else:
            hi = QColor(t_colors["now_invisible_hi"])
            now_bg = QColor(t_colors["now_invisible_bg"])
            dist_col = hi
            pl_col = hi
            el_col = QColor(t_colors["eme_red"])
            lib_col = hi
            spr_col = hi
            ms_col = hi
            sq = ""
            qc = hi
            el_txt = f"{el:+.1f}\u00b0 {tr('now_below')}"

        # Ligne MAINTENANT : le spread est la valeur instantan\u00e9e actuelle,
        # dupliqu\u00e9e dans les 2 colonnes min/max (pas de plage pour une mesure
        # ponctuelle \u2014 seulement pour les passages futurs).
        now_time_local = datetime.now().strftime("%H:%M")
        spread_cell = f"{spread:.0f} Hz @ {now_time_local}" if visible else f"{spread:.0f} Hz"
        cells = [
            (tr("now_label") if visible else tr("now_label_off"), hi),
            (rise_txt, hi),
            (set_txt, hi),
            (dur_txt, hi if not visible else dur_col),
            (el_txt, el_col),
            (datetime.now(timezone.utc).strftime("%H:%M UTC"), hi),
            (f"{az:.0f}\u00b0", hi),
            ("---", hi),
            (f"{decl:+.1f}\u00b0", hi),
            (f"{dist:.0f} km", dist_col),
            (f"+{ploss:.1f} dB", pl_col),
            (f"{total_pl:.1f} dB", pl_col),
            (f"{ms_angle:.0f}\u00b0", ms_col),
            (f"{lib_rate:.2f}\u00b0/h", lib_col),
            (spread_cell, spr_col),  # Spread min (valeur courante)
            (spread_cell, spr_col),  # Spread max (idem pour MAINTENANT)
            (f"{sq} {score:.1f}" if visible else "---", qc),
        ]
        if show_phase:
            cells.append((f"{phase} ({illum:.0f}%)", hi))

        # Stocker le fond pour _refreshTable
        self._nowRowBg = now_bg
        return cells

    def _refreshNowRow(self):
        """Rafraichit uniquement la ligne MAINTENANT (row 0) toutes les 5 s.

        Evite de reconstruire toute la table et ses 30+ lignes. Met juste a
        jour les cellules de la row 0 avec les nouvelles valeurs instantanees.
        """
        if self._lat == 0 and self._lon == 0:
            return
        if self.table.rowCount() == 0:
            return
        # Il faut s'assurer que la row 0 est bien MAINTENANT (pas un passage)
        # Normalement c'est le cas quand lat/lon sont non nuls apres compute.
        freq = self.comboFreq.currentData() or 10368e6
        pl_perigee = _eme_path_loss_perigee(freq)
        show_phase = self.chkPhase.isChecked()
        try:
            now_cells = self._buildNowRow(freq, pl_perigee, show_phase)
        except Exception:
            return
        bg = getattr(self, '_nowRowBg',
                     QColor(_theme()["now_visible_bg"]))
        for c, (text, color) in enumerate(now_cells):
            if c >= self.table.columnCount():
                break
            item = _make_item(text, color or QColor(_theme()["fg_dim"]))
            item.setBackground(bg)
            self.table.setItem(0, c, item)

    def _refreshTable(self):
        min_el = self.sliderMinEl.value()
        min_score = self.sliderMinScore.value() / 10.0
        show_phase = self.chkPhase.isChecked()
        use_local = self.chkLocalTime.isChecked()
        tz_offset = _utc_offset() if use_local else timedelta(0)
        tz_suffix = "" if use_local else " UTC"

        filtered = [d for d in self._passes_raw
                    if d["max_el"] >= min_el and d["score"] >= min_score]

        freq = self.comboFreq.currentData() or 10368e6
        pl_perigee = _eme_path_loss_perigee(freq)
        freq_label = self.comboFreq.currentText()

        cols = [
            tr("col_date"),
            f"{tr('col_rise')}{tz_suffix}",
            f"{tr('col_set')}{tz_suffix}",
            tr("col_duration"),
            tr("col_el_max"),
            f"{tr('col_el_max_time')}{tz_suffix}",
            tr("col_az_rise"),
            tr("col_az_set"),
            tr("col_decl"),
            tr("col_distance"),
            tr("col_extra_pl"),
            tr("col_total_pl", freq=freq_label),
            tr("col_moon_sun"),
            tr("col_libration"),
            tr("col_spread_min", freq=freq_label),
            tr("col_spread_max", freq=freq_label),
            tr("col_quality"),
        ]
        if show_phase:
            cols.append(tr("col_phase"))

        self.table.setColumnCount(len(cols))
        self.table.setHorizontalHeaderLabels(cols)

        # Ligne "MAINTENANT" en row 0 si les données existent
        now_row = None
        if self._lat != 0 or self._lon != 0:
            try:
                now_row = self._buildNowRow(freq, pl_perigee, show_phase)
            except Exception:
                now_row = None

        total_rows = (1 if now_row else 0) + len(filtered)
        self.table.setRowCount(total_rows)

        # Tooltips sur les headers (comme dans l'app principale)
        def _set_tip(col_idx, tip):
            item = self.table.horizontalHeaderItem(col_idx)
            if item:
                item.setToolTip(tip)

        _set_tip(0, tr("tip_date"))
        _set_tip(1, tr("tip_rise"))
        _set_tip(2, tr("tip_set"))
        _set_tip(3, tr("tip_duration"))
        _set_tip(4, tr("tip_el_max"))
        _set_tip(5, tr("tip_el_max_time"))
        _set_tip(6, tr("tip_az_rise"))
        _set_tip(7, tr("tip_az_set"))
        _set_tip(8, tr("tip_decl"))
        _set_tip(9, tr("tip_distance"))
        _set_tip(10, tr("tip_extra_pl"))
        _set_tip(11, tr("tip_total_pl"))
        _set_tip(12, tr("tip_moon_sun"))
        _set_tip(13, tr("tip_libration"))
        _set_tip(14, tr("tip_spread_min"))
        _set_tip(15, tr("tip_spread_max"))
        _set_tip(16, tr("tip_quality"))

        hdr = self.table.horizontalHeader()
        # Interactive permet le resize manuel, on ajuste après remplissage
        hdr.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        hdr.setStretchLastSection(True)

        # ── Ligne "MAINTENANT" (row 0, fond distinct) ──
        row_offset = 0
        if now_row:
            bg = getattr(self, '_nowRowBg',
                         QColor(_theme()["now_visible_bg"]))
            for c, (text, color) in enumerate(now_row):
                item = _make_item(text, color or QColor(_theme()["fg_dim"]))
                item.setBackground(bg)
                self.table.setItem(0, c, item)
            row_offset = 1

        for idx, d in enumerate(filtered):
            row = idx + row_offset
            rise_dt = d["rise_time"] + tz_offset
            set_dt = d["set_time"] + tz_offset
            max_el_dt = d["max_el_time"] + tz_offset
            max_el = d["max_el"]
            duration_min = d["duration_min"]
            dist_km = d["dist_km"]
            ploss = d["ploss"]
            score = d["score"]
            dur_h = int(duration_min // 60)
            dur_m = int(duration_min % 60)

            col = 0
            self.table.setItem(row, col, _make_item(
                _loc_date(rise_dt))); col += 1
            self.table.setItem(row, col, _make_item(
                rise_dt.strftime("%H:%M"))); col += 1
            self.table.setItem(row, col, _make_item(
                set_dt.strftime("%H:%M"))); col += 1
            self.table.setItem(row, col, _make_item(
                f"{dur_h}h{dur_m:02d}",
                _eme_color(duration_min, _DUR_GREEN, _DUR_ORANGE))); col += 1
            self.table.setItem(row, col, _make_item(
                f"{max_el:.1f}\u00b0",
                _eme_color(max_el, _EL_GREEN, _EL_ORANGE))); col += 1
            self.table.setItem(row, col, _make_item(
                max_el_dt.strftime("%H:%M"))); col += 1
            self.table.setItem(row, col, _make_item(
                f"{d['az_rise']:.0f}\u00b0")); col += 1
            self.table.setItem(row, col, _make_item(
                f"{d['az_set']:.0f}\u00b0")); col += 1
            self.table.setItem(row, col, _make_item(
                f"{d.get('decl', 0):+.1f}\u00b0")); col += 1
            self.table.setItem(row, col, _make_item(
                f"{dist_km:.0f} km",
                _eme_color(dist_km, _DIST_GREEN, _DIST_ORANGE,
                           invert=True))); col += 1
            self.table.setItem(row, col, _make_item(
                f"+{ploss:.1f} dB",
                _eme_color(ploss, _PL_GREEN, _PL_ORANGE,
                           invert=True))); col += 1
            total_pl = pl_perigee + ploss
            self.table.setItem(row, col, _make_item(
                f"{total_pl:.1f} dB",
                _eme_color(ploss, _PL_GREEN, _PL_ORANGE,
                           invert=True))); col += 1

            ms_angle = d.get("moon_sun", 180)
            tc = _theme()
            if ms_angle < 5: ms_color = QColor(tc["eme_red"])
            elif ms_angle < 15: ms_color = QColor(tc["eme_orange"])
            else: ms_color = QColor(tc["eme_green"])
            self.table.setItem(row, col, _make_item(
                f"{ms_angle:.0f}\u00b0", ms_color)); col += 1

            # Libration rate (au moment du spread min — meilleur moment)
            lib_r = d.get("lib_rate_min", d.get("lib_rate", 0))
            if lib_r < 0.10: lib_col = QColor(tc["eme_green"])
            elif lib_r < 0.25: lib_col = QColor(tc["eme_orange"])
            else: lib_col = QColor(tc["eme_red"])
            self.table.setItem(row, col, _make_item(
                f"{lib_r:.2f}\u00b0/h", lib_col)); col += 1

            # Doppler spread MIN (meilleur moment du passage)
            spr_min = d.get("spread_min", d.get("doppler_spread", 0)) * freq / 10.368e9
            spr_min_dt = d.get("spread_min_time")
            if spr_min < 50: spr_min_col = QColor(tc["eme_green"])
            elif spr_min < 150: spr_min_col = QColor(tc["eme_orange"])
            else: spr_min_col = QColor(tc["eme_red"])
            if spr_min_dt is not None:
                t_txt = (spr_min_dt + tz_offset).strftime("%H:%M")
                min_txt = f"{spr_min:.0f} Hz @ {t_txt}"
            else:
                min_txt = f"{spr_min:.0f} Hz"
            self.table.setItem(row, col, _make_item(min_txt, spr_min_col)); col += 1

            # Doppler spread MAX (pire moment du passage)
            spr_max = d.get("spread_max", d.get("doppler_spread", 0)) * freq / 10.368e9
            spr_max_dt = d.get("spread_max_time")
            if spr_max < 50: spr_max_col = QColor(tc["eme_green"])
            elif spr_max < 150: spr_max_col = QColor(tc["eme_orange"])
            else: spr_max_col = QColor(tc["eme_red"])
            if spr_max_dt is not None:
                t_txt = (spr_max_dt + tz_offset).strftime("%H:%M")
                max_txt = f"{spr_max:.0f} Hz @ {t_txt}"
            else:
                max_txt = f"{spr_max:.0f} Hz"
            self.table.setItem(row, col, _make_item(max_txt, spr_max_col)); col += 1

            sq = _quality_squares(score)
            qc = _quality_color(score)
            self.table.setItem(row, col, _make_item(
                f"{sq} {score:.1f}", qc)); col += 1

            if show_phase:
                self.table.setItem(row, col, _make_item(
                    f"{d['phase']} ({d['illum']:.0f}%)")); col += 1

        total = len(self._passes_raw)
        shown = len(filtered)
        if shown < total:
            self.labelInfo.setText(
                self.labelInfo.text().split(" |")[0] +
                f" | {tr('info_filtered', shown=shown, total=total)}")

        if use_local:
            self.labelFooter.setText(
                tr("footer_calc",
                   time=f"{datetime.now().strftime('%Y-%m-%d %H:%M')}"
                        f" {self.labelTz.text()}"))
        else:
            self.labelFooter.setText(
                tr("footer_calc",
                   time=datetime.now(timezone.utc).strftime(
                       '%Y-%m-%d %H:%M UTC')))

        # Ajuster largeur des colonnes (header + contenu)
        for c in range(self.table.columnCount() - 1):  # -1 car dernière = stretch
            hdr_w = self.table.horizontalHeader().sectionSizeHint(c)
            cnt_w = self.table.sizeHintForColumn(c)
            self.table.setColumnWidth(c, max(hdr_w, cnt_w) + 8)

    # ════════════════════════════════════════════
    # Export
    # ════════════════════════════════════════════

    def _getExportRows(self):
        min_el = self.sliderMinEl.value()
        min_score = self.sliderMinScore.value() / 10.0
        use_local = self.chkLocalTime.isChecked()
        tz_offset = _utc_offset() if use_local else timedelta(0)
        freq = self.comboFreq.currentData() or 10368e6
        pl_perigee = _eme_path_loss_perigee(freq)

        rows = []
        for d in self._passes_raw:
            if d["max_el"] < min_el or d["score"] < min_score:
                continue
            rise_dt = d["rise_time"] + tz_offset
            set_dt = d["set_time"] + tz_offset
            max_el_dt = d["max_el_time"] + tz_offset
            dur_h = int(d["duration_min"] // 60)
            dur_m = int(d["duration_min"] % 60)
            total_pl = pl_perigee + d["ploss"]
            spr_min = d.get("spread_min", d.get("doppler_spread", 0)) * freq / 10.368e9
            spr_max = d.get("spread_max", d.get("doppler_spread", 0)) * freq / 10.368e9
            spr_min_dt = d.get("spread_min_time")
            spr_max_dt = d.get("spread_max_time")
            spr_min_txt = (
                f"{spr_min:.0f} @ {(spr_min_dt + tz_offset).strftime('%H:%M')}"
                if spr_min_dt else f"{spr_min:.0f}"
            )
            spr_max_txt = (
                f"{spr_max:.0f} @ {(spr_max_dt + tz_offset).strftime('%H:%M')}"
                if spr_max_dt else f"{spr_max:.0f}"
            )
            rows.append([
                _loc_date_long(rise_dt),
                rise_dt.strftime("%H:%M"),
                set_dt.strftime("%H:%M"),
                f"{dur_h}h{dur_m:02d}",
                f"{d['max_el']:.1f}",
                max_el_dt.strftime("%H:%M"),
                f"{d['az_rise']:.0f}",
                f"{d['az_set']:.0f}",
                f"{d.get('decl', 0):+.1f}",
                f"{d['dist_km']:.0f}",
                f"{d['ploss']:.1f}",
                f"{total_pl:.1f}",
                f"{d.get('moon_sun', 180):.0f}",
                spr_min_txt,
                spr_max_txt,
                f"{d['score']:.1f}",
                f"{d['phase']} ({d['illum']:.0f}%)",
            ])
        return rows

    def _showHelp(self):
        """Fenêtre d'aide utilisateur."""
        t = _theme()
        dlg = QDialog(self)
        dlg.setWindowTitle(tr("help_title"))
        dlg.setMinimumSize(600, 520)
        dlg.setStyleSheet(
            f"QDialog {{ background-color: {t['dlg_bg']}; color: {t['dlg_fg']}; }}"
            f"QLabel {{ color: {t['dlg_fg']}; }}"
        )
        icon_path = _get_icon_path()
        if os.path.exists(icon_path):
            dlg.setWindowIcon(QIcon(icon_path))

        lay = QVBoxLayout(dlg)

        help_text = QLabel(tr("help_content"))
        help_text.setWordWrap(True)
        help_text.setOpenExternalLinks(True)
        lay.addWidget(help_text)

        lay.addStretch()
        btnClose = QPushButton(tr("btn_close"))
        btnClose.clicked.connect(dlg.close)
        btnClose.setStyleSheet("QPushButton { padding: 6px 20px; }")
        lay.addWidget(btnClose, alignment=Qt.AlignmentFlag.AlignCenter)

        # Appliquer la taille de police utilisateur
        self._applyDialogFont(dlg)
        dlg.exec()

    def _applyDialogFont(self, dlg):
        """Force la taille de police utilisateur sur un dialogue et tous ses enfants."""
        size = self.spinFontSize.value()
        dlg_font = QFont()
        dlg_font.setPointSize(size)
        dlg.setFont(dlg_font)
        for child in dlg.findChildren(QWidget):
            child.setFont(dlg_font)

    def _onRowClicked(self, row, col):
        """Clic sur une ligne du tableau -> detail du passage ou MAINTENANT."""
        # Row 0 = ligne MAINTENANT -> ouvre le dialog NowDetail
        has_now_row = (self._lat != 0 or self._lon != 0) and self._passes_raw
        if has_now_row and row == 0:
            try:
                self._showNowDetail()
            except Exception as e:
                import traceback
                QMessageBox.critical(
                    self, tr("msg_error"),
                    f"{type(e).__name__}: {e}\n\n{traceback.format_exc()}"
                )
            return
        # Calcul de l'index dans _passes_raw (filtres appliques)
        min_el = self.sliderMinEl.value()
        min_score = self.sliderMinScore.value() / 10.0
        filtered = [d for d in self._passes_raw
                    if d["max_el"] >= min_el and d["score"] >= min_score]
        pass_idx = row - (1 if has_now_row else 0)
        if 0 <= pass_idx < len(filtered):
            try:
                self._showDayDetail(filtered[pass_idx])
            except Exception as e:
                import traceback
                QMessageBox.critical(
                    self, tr("msg_error"),
                    f"{type(e).__name__}: {e}\n\n{traceback.format_exc()}"
                )

    def _showNowDetail(self):
        """Affiche toutes les donnees temps-reel de la Lune (clic ligne MAINTENANT).

        Inclut AZ/EL/Dist/Phase + donnees EME avancees : DGR, TSky, Doppler,
        Home Echo, Spread, Libration, LHA/GHA, jours depuis perigee.
        Auto-refresh toutes les 5 secondes tant que la fenetre est ouverte.
        """
        if self._lat == 0 and self._lon == 0:
            return
        t = _theme()
        dlg = QDialog(self)
        dlg.setWindowTitle(tr("now_detail_title"))
        # Taille confortable
        parent_size = self.size()
        dlg.resize(int(parent_size.width() * 0.6),
                   int(parent_size.height() * 0.75))
        dlg.setMinimumSize(700, 620)
        dlg.setStyleSheet(
            f"QDialog {{ background-color: {t['bg_main']}; color: {t['fg_text']}; }}"
            f"QLabel {{ color: {t['fg_text']}; }}"
            f"QGroupBox {{ border: 1px solid {t['btn_border']}; "
            f"border-radius: 4px; margin-top: 12px; padding-top: 16px; "
            f"font-weight: bold; color: {t['fg_header']}; }}"
            f"QGroupBox::title {{ subcontrol-origin: margin; "
            f"left: 10px; padding: 0 6px; }}"
        )
        icon_path = _get_icon_path()
        if os.path.exists(icon_path):
            dlg.setWindowIcon(QIcon(icon_path))

        lay = QVBoxLayout(dlg)
        lay.setSpacing(8)

        # Creation des QLabels persistants (seront rafraichis par le timer)
        hdr_lbl = QLabel()
        lay.addWidget(hdr_lbl)

        pos_box = QGroupBox(tr("now_grp_position"))
        pos_lay = QVBoxLayout(pos_box)
        pos_lbl = QLabel()
        pos_lay.addWidget(pos_lbl)
        lay.addWidget(pos_box)

        rs_box = QGroupBox(tr("now_grp_riseset"))
        rs_lay = QVBoxLayout(rs_box)
        rs_lbl = QLabel()
        rs_lay.addWidget(rs_lbl)
        lay.addWidget(rs_box)

        eme_box = QGroupBox(tr("now_grp_eme"))
        eme_lay = QVBoxLayout(eme_box)
        eme_lbl = QLabel()
        eme_lay.addWidget(eme_lbl)
        lay.addWidget(eme_box)

        astro_box = QGroupBox(tr("now_grp_astro"))
        astro_lay = QVBoxLayout(astro_box)
        astro_lbl = QLabel()
        astro_lay.addWidget(astro_lbl)
        lay.addWidget(astro_box)

        lay.addStretch()

        # Indicateur de rafraichissement automatique
        refresh_lbl = QLabel(tr("refresh_hint"))
        refresh_lbl.setStyleSheet(
            f"color: {t['fg_dim']}; font-size: 9pt; font-style: italic;")
        refresh_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(refresh_lbl)

        # ── Bouton Fermer ──
        btnClose = QPushButton(tr("btn_close"))
        btnClose.clicked.connect(dlg.close)
        btnClose.setStyleSheet(
            f"QPushButton {{ padding: 6px 20px; background-color: {t['btn_bg']}; "
            f"border: 1px solid {t['btn_border']}; border-radius: 3px; }}"
            f"QPushButton:hover {{ background-color: {t['btn_hover']}; }}"
        )
        btnRow = QHBoxLayout()
        btnRow.addStretch()
        btnRow.addWidget(btnClose)
        lay.addLayout(btnRow)

        # Fonction de mise a jour : recalcule tout et met a jour les QLabels
        def update_content():
            from moon_calc import _angular_sep_deg
            freq = self.comboFreq.currentData() or 10368e6
            freq_label = self.comboFreq.currentText()
            t_now = _ts.now()
            moon = compute_moon(self._lat, self._lon, self._alt_m,
                                dist_reference=self._distRef,
                                horizon_degrees=self._effectiveHorizonDeg())
            sun = compute_sun(self._lat, self._lon, self._alt_m,
                              horizon_degrees=self._horizonDeg())
            lib = compute_libration(self._lat, self._lon, self._alt_m, t_now)
            deg = compute_degradation(self._lat, self._lon, self._alt_m,
                                        t_now, freq)
            ha = compute_hour_angles(self._lat, self._lon, self._alt_m, t_now)
            dsp = days_since_perigee(t_now)

            visible = moon["el"] > 0
            use_local = self.chkLocalTime.isChecked()
            tz_offset = _utc_offset() if use_local else timedelta(0)
            tz_suffix = "" if use_local else " UTC"

            # Horloge actuelle pour montrer que ca tourne
            if use_local:
                now_clock = datetime.now().strftime("%H:%M:%S")
            else:
                now_clock = datetime.now(timezone.utc).strftime("%H:%M:%S")

            status_color = t["eme_green"] if visible else t["eme_red"]
            status_txt = tr("now_visible") if visible else tr("now_below")
            hdr_lbl.setText(
                f"<div style='font-size: 16pt; font-weight: bold;'>"
                f"<span style='color:{t['now_visible_hi'] if visible else t['now_invisible_hi']};'>"
                f"\u25cf {tr('now_label') if visible else tr('now_label_off')}</span>"
                f"  <span style='color:{status_color};'>{status_txt}</span>"
                f"  <span style='font-size: 10pt; color:{t['fg_dim']}; font-weight: normal;'>"
                f"  \u2014  {now_clock}{tz_suffix}</span>"
                f"</div>"
            )
            pos_lbl.setText(
                f"<table cellpadding='4'>"
                f"<tr><td><b>AZ :</b></td><td><span style='font-size:14pt;'>{moon['az']:.1f}\u00b0</span></td>"
                f"<td width='30'></td>"
                f"<td><b>EL :</b></td><td><span style='font-size:14pt; color:{status_color};'>{moon['el']:+.1f}\u00b0</span></td></tr>"
                f"<tr><td><b>{tr('now_lbl_distance')} :</b></td><td>{moon['dist_km']:.0f} km</td>"
                f"<td></td>"
                f"<td><b>{tr('now_lbl_decl')} :</b></td><td>{ha['dec_deg']:+.2f}\u00b0</td></tr>"
                f"<tr><td><b>{tr('now_lbl_phase')} :</b></td><td colspan='4'>{moon['phase_name']} ({moon['illumination']:.0f}%)</td></tr>"
                f"</table>"
            )
            rise = moon.get("next_rise")
            sett = moon.get("next_set")
            rise_txt = ((rise + tz_offset).strftime("%H:%M") + tz_suffix) if rise else "---"
            set_txt = ((sett + tz_offset).strftime("%H:%M") + tz_suffix) if sett else "---"
            if rise and sett:
                dur_min = abs((sett - rise).total_seconds() / 60.0)
                dur_txt = f"{int(dur_min // 60)}h{int(dur_min % 60):02d}"
            else:
                dur_txt = "---"
            rs_lbl.setText(
                f"<table cellpadding='4'>"
                f"<tr><td><b>{tr('col_rise')} :</b></td><td>{rise_txt}</td>"
                f"<td width='30'></td>"
                f"<td><b>{tr('col_set')} :</b></td><td>{set_txt}</td>"
                f"<td width='30'></td>"
                f"<td><b>{tr('col_duration')} :</b></td><td>{dur_txt}</td></tr>"
                f"</table>"
            )
            eme_box.setTitle(f"{tr('now_grp_eme')} ({freq_label})")
            dgr_db = deg["degradation_db"]
            dgr_html = f"<span style='color:{t['eme_green'] if dgr_db < 1.0 else t['eme_orange'] if dgr_db < 3.0 else t['eme_red']};'>+{dgr_db:.2f} dB</span>"
            tsky = deg["sky_temp_k"]
            tsky_html = f"<span style='color:{t['eme_green'] if tsky < 10 else t['eme_orange'] if tsky < 50 else t['eme_red']};'>{tsky:.1f} K</span>"
            dop = deg["doppler_hz"]
            spread = lib["doppler_spread_hz"] * freq / 10.368e9
            spread_html = f"<span style='color:{t['eme_green'] if spread < 50 else t['eme_orange'] if spread < 150 else t['eme_red']};'>{spread:.0f} Hz</span>"
            lib_r = lib["lib_rate"]
            lib_html = f"<span style='color:{t['eme_green'] if lib_r < 0.10 else t['eme_orange'] if lib_r < 0.25 else t['eme_red']};'>{lib_r:.2f} \u00b0/h</span>"
            pl_extra = deg["path_loss_extra_db"]
            pl_html = f"<span style='color:{t['eme_green'] if pl_extra < 1.0 else t['eme_orange'] if pl_extra < 2.0 else t['eme_red']};'>+{pl_extra:.2f} dB</span>"
            ms_angle = _angular_sep_deg(moon["az"], moon["el"], sun["az"], sun["el"])
            ms_html = f"<span style='color:{t['eme_red'] if ms_angle < 5 else t['eme_orange'] if ms_angle < 15 else t['eme_green']};'>{ms_angle:.0f}\u00b0</span>"
            eme_lbl.setText(
                f"<table cellpadding='4'>"
                f"<tr><td><b>{tr('now_lbl_dgr')} :</b></td><td>{dgr_html}</td>"
                f"<td width='30'></td>"
                f"<td><b>{tr('now_lbl_tsky')} :</b></td><td>{tsky_html}</td></tr>"
                f"<tr><td><b>{tr('now_lbl_doppler')} :</b></td><td>{dop:+.0f} Hz</td>"
                f"<td></td>"
                f"<td><b>{tr('now_lbl_echo')} :</b></td><td>{dop:+.0f} Hz</td></tr>"
                f"<tr><td><b>{tr('now_lbl_spread')} :</b></td><td>{spread_html}</td>"
                f"<td></td>"
                f"<td><b>{tr('now_lbl_libration')} :</b></td><td>{lib_html}</td></tr>"
                f"<tr><td><b>{tr('now_lbl_pl_extra')} :</b></td><td>{pl_html}</td>"
                f"<td></td>"
                f"<td><b>{tr('now_lbl_moonsun')} :</b></td><td>{ms_html}</td></tr>"
                f"</table>"
            )
            astro_lbl.setText(
                f"<table cellpadding='4'>"
                f"<tr><td><b>{tr('now_lbl_lha')} :</b></td><td>{ha['lha_deg']:+.2f}\u00b0</td>"
                f"<td width='30'></td>"
                f"<td><b>{tr('now_lbl_gha')} :</b></td><td>{ha['gha_deg']:.2f}\u00b0</td></tr>"
                f"<tr><td><b>{tr('now_lbl_dsp')} :</b></td>"
                f"<td colspan='4'>{dsp:.1f} {tr('now_lbl_days')}</td></tr>"
                f"</table>"
            )

        # Rendu initial
        update_content()

        # Auto-refresh toutes les 5 secondes
        refresh_timer = QTimer(dlg)
        refresh_timer.setInterval(5000)
        refresh_timer.timeout.connect(update_content)
        refresh_timer.start()
        # Le timer est parent du dlg -> auto-destroyed a la fermeture

        # Appliquer la taille de police utilisateur
        self._applyDialogFont(dlg)
        dlg.exec()

    def _showDayDetail(self, pass_data):
        """Affiche le detail d'un passage par tranches de 30 minutes.

        Equivalent de la vue Sked Maker (GM4JJJ) : pour chaque tranche,
        AZ, EL, distance, Doppler, spread, TSky, degradation, moon-sun.
        """
        t = _theme()
        dlg = QDialog(self)
        # Titre avec la date du passage
        rise_dt = pass_data["rise_time"]
        date_str = _loc_date_long(rise_dt)
        dlg.setWindowTitle(f"{tr('day_detail_title')} — {date_str}")
        # Taille : 90% de la taille de la fenetre parente pour \u00e9viter
        # d'avoir a defiler — si trop grand on tronque aux bornes ecran
        parent_size = self.size()
        dlg.resize(int(parent_size.width() * 0.92),
                   int(parent_size.height() * 0.85))
        dlg.setMinimumSize(1100, 500)
        dlg.setStyleSheet(
            f"QDialog {{ background-color: {t['bg_main']}; color: {t['fg_text']}; }}"
            f"QLabel {{ color: {t['fg_text']}; }}"
            f"QTableWidget {{ background-color: {t['bg_table']}; "
            f"gridline-color: {t['gridline']}; "
            f"selection-background-color: {t['selection_bg']}; }}"
            f"QHeaderView::section {{ background-color: {t['bg_header']}; "
            f"color: {t['fg_header']}; border: 1px solid {t['gridline']}; "
            f"padding: 4px; font-weight: bold; }}"
        )
        icon_path = _get_icon_path()
        if os.path.exists(icon_path):
            dlg.setWindowIcon(QIcon(icon_path))

        lay = QVBoxLayout(dlg)

        # En-tete : resume du passage
        dur_h = int(pass_data["duration_min"] // 60)
        dur_m = int(pass_data["duration_min"] % 60)
        freq = self.comboFreq.currentData() or 10368e6
        freq_label = self.comboFreq.currentText()
        use_local = self.chkLocalTime.isChecked()
        tz_offset = _utc_offset() if use_local else timedelta(0)
        tz_suffix = " UTC" if not use_local else ""

        hdr_txt = (
            f"{date_str} — {tr('col_el_max')}: {pass_data['max_el']:.1f}° "
            f"@ {(pass_data['max_el_time'] + tz_offset).strftime('%H:%M')}{tz_suffix} — "
            f"{tr('col_duration')}: {dur_h}h{dur_m:02d} — "
            f"{tr('lbl_frequency')} {freq_label}"
        )
        hdr = QLabel(hdr_txt)
        hdr.setStyleSheet(f"color: {t['fg_info']}; padding: 4px 0;")
        lay.addWidget(hdr)

        # Echantillonnage du passage
        try:
            samples = sample_pass_timeline(
                self._lat, self._lon, self._alt_m, pass_data,
                interval_min=30, freq_hz=freq,
                dist_reference=self._distRef)
        except Exception as e:
            samples = []
            err = QLabel(f"Erreur : {e}")
            err.setStyleSheet(f"color: {t['eme_red']};")
            lay.addWidget(err)

        # Table
        cols = [
            f"{tr('col_day_time')}{tz_suffix}",
            tr("col_az"),
            tr("col_el"),
            tr("col_day_distance"),
            tr("col_day_pl_extra"),
            tr("col_day_decl"),
            tr("col_day_doppler", freq=freq_label),
            tr("col_day_spread", freq=freq_label),
            tr("col_day_tsky"),
            tr("col_day_dgr"),
            tr("col_day_libration"),
            tr("col_day_lha"),
            tr("col_day_ms"),
            tr("col_day_sun_az"),
            tr("col_day_sun_el"),
        ]
        table = QTableWidget(len(samples), len(cols))
        table.setHorizontalHeaderLabels(cols)
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.verticalHeader().setVisible(False)
        table.setFont(_make_monospace_font(self.spinFontSize.value()))
        hdr_font = _make_monospace_font(max(self.spinFontSize.value() - 1, 8))
        hdr_font.setBold(True)
        table.horizontalHeader().setFont(hdr_font)

        tc = _theme()
        for row, s in enumerate(samples):
            t_local = s["time"] + tz_offset
            col = 0
            table.setItem(row, col, _make_item(
                t_local.strftime("%H:%M"))); col += 1
            table.setItem(row, col, _make_item(
                f"{s['az']:.0f}\u00b0")); col += 1
            # EL avec couleur
            el = s['el']
            el_col = _eme_color(el, _EL_GREEN, _EL_ORANGE)
            table.setItem(row, col, _make_item(
                f"{el:.1f}\u00b0", el_col)); col += 1
            # Distance
            dist_col = _eme_color(s['dist_km'], _DIST_GREEN, _DIST_ORANGE,
                                   invert=True)
            table.setItem(row, col, _make_item(
                f"{s['dist_km']:.0f} km", dist_col)); col += 1
            # Path loss extra (dB)
            pl_extra = s['path_loss_extra_db']
            pl_col = _eme_color(pl_extra, _PL_GREEN, _PL_ORANGE, invert=True)
            table.setItem(row, col, _make_item(
                f"{pl_extra:+.2f} dB", pl_col)); col += 1
            # Declinaison
            table.setItem(row, col, _make_item(
                f"{s['decl']:+.1f}\u00b0")); col += 1
            # Doppler (signe explicite)
            dop = s['doppler_hz']
            dop_txt = f"{dop:+.0f} Hz"
            table.setItem(row, col, _make_item(dop_txt)); col += 1
            # Spread
            spr = s['spread_hz']
            if spr < 50: spr_col = QColor(tc["eme_green"])
            elif spr < 150: spr_col = QColor(tc["eme_orange"])
            else: spr_col = QColor(tc["eme_red"])
            table.setItem(row, col, _make_item(
                f"{spr:.0f} Hz", spr_col)); col += 1
            # TSky
            tsky = s['sky_temp_k']
            if tsky < 10: tsky_col = QColor(tc["eme_green"])
            elif tsky < 50: tsky_col = QColor(tc["eme_orange"])
            else: tsky_col = QColor(tc["eme_red"])
            table.setItem(row, col, _make_item(
                f"{tsky:.1f} K", tsky_col)); col += 1
            # DGR (degradation en dB)
            dgr = s['degradation_db']
            if dgr < 1.0: dgr_col = QColor(tc["eme_green"])
            elif dgr < 3.0: dgr_col = QColor(tc["eme_orange"])
            else: dgr_col = QColor(tc["eme_red"])
            table.setItem(row, col, _make_item(
                f"{dgr:+.2f} dB", dgr_col)); col += 1
            # Libration rate
            lib_r = s['lib_rate']
            if lib_r < 0.10: lib_col = QColor(tc["eme_green"])
            elif lib_r < 0.25: lib_col = QColor(tc["eme_orange"])
            else: lib_col = QColor(tc["eme_red"])
            table.setItem(row, col, _make_item(
                f"{lib_r:.2f}\u00b0/h", lib_col)); col += 1
            # LHA (Local Hour Angle)
            table.setItem(row, col, _make_item(
                f"{s['lha']:+.1f}\u00b0")); col += 1
            # Moon-Sun angle
            ms = s['moon_sun']
            if ms < 5: ms_col = QColor(tc["eme_red"])
            elif ms < 15: ms_col = QColor(tc["eme_orange"])
            else: ms_col = QColor(tc["eme_green"])
            table.setItem(row, col, _make_item(
                f"{ms:.0f}\u00b0", ms_col)); col += 1
            # Sun AZ / Sun EL — gris si le Soleil est sous l'horizon
            sun_el = s['sun_el']
            sun_color = None if sun_el > 0 else QColor(tc["fg_dim"])
            table.setItem(row, col, _make_item(
                f"{s['sun_az']:.0f}\u00b0", sun_color)); col += 1
            # Sun EL : rouge si > 0 (Soleil levé — risque interférence)
            if sun_el > 0:
                sel_color = QColor(tc["eme_orange"])
            else:
                sel_color = QColor(tc["fg_dim"])
            table.setItem(row, col, _make_item(
                f"{sun_el:+.0f}\u00b0", sel_color)); col += 1

        # Ajuster largeurs colonnes
        table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Interactive)
        for c in range(table.columnCount()):
            hw = table.horizontalHeader().sectionSizeHint(c)
            cw = table.sizeHintForColumn(c)
            table.setColumnWidth(c, max(hw, cw) + 8)
        # Pas de stretch : avec 15 colonnes la table est assez large

        lay.addWidget(table)

        # Bouton Fermer
        btnClose = QPushButton(tr("btn_close"))
        btnClose.clicked.connect(dlg.close)
        btnClose.setStyleSheet(
            f"QPushButton {{ padding: 6px 20px; background-color: {t['btn_bg']}; "
            f"border: 1px solid {t['btn_border']}; border-radius: 3px; }}"
            f"QPushButton:hover {{ background-color: {t['btn_hover']}; }}"
        )
        btnRow = QHBoxLayout()
        btnRow.addStretch()
        btnRow.addWidget(btnClose)
        lay.addLayout(btnRow)

        # Appliquer la taille de police utilisateur
        self._applyDialogFont(dlg)
        dlg.exec()

    def _showAbout(self):
        """Fenêtre À propos."""
        t = _theme()
        dlg = QDialog(self)
        dlg.setWindowTitle(tr("about_title"))
        dlg.setFixedSize(540, 540)
        dlg.setStyleSheet(
            f"QDialog {{ background-color: {t['dlg_bg']}; color: {t['dlg_fg']}; }}"
            f"QLabel {{ color: {t['dlg_fg']}; }}"
        )

        lay = QVBoxLayout(dlg)
        lay.setSpacing(12)

        icon_path = _get_icon_path()
        if os.path.exists(icon_path):
            dlg.setWindowIcon(QIcon(icon_path))

        title = QLabel(f"<h2 style='color: {t['about_title_color']};'>"
                       "\u263d Moon Predictions</h2>")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(title)

        version = QLabel(
            f"<p style='font-size: 14pt; color: {t['about_version_color']};'>"
            f"Version {APP_VERSION} — {APP_DATE}</p>")
        version.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(version)

        info = QLabel(
            f"<p style='text-align: center;'>{tr('about_desc')}</p>"
            f"<hr style='border-color: {t['dlg_hr']};'>"
            f"<p style='text-align: center;'>"
            f"{tr('about_author')} ON7KGK — Micha\u00ebl<br>"
            f"{tr('about_dev')} Claude Code (Anthropic)<br>"
            f"{tr('about_ephem')} NASA JPL DE440s via Skyfield<br>"
            f"{tr('about_icon')} Arkinasi — Flaticon</p>"
            f"<hr style='border-color: {t['dlg_hr']};'>"
            f"<p style='text-align: center;'>"
            f"{tr('about_thanks')}<br>{tr('about_thanks_text')}</p>"
            f"<hr style='border-color: {t['dlg_hr']};'>"
            f"<p style='text-align: center;'>{tr('about_opensource')}</p>"
            f"<hr style='border-color: {t['dlg_hr']};'>"
            f"<p style='text-align: center;'>{tr('about_license')}</p>"
        )
        info.setOpenExternalLinks(True)
        info.setWordWrap(True)
        info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(info)

        lay.addStretch()

        btnClose = QPushButton(tr("btn_close"))
        btnClose.clicked.connect(dlg.close)
        btnClose.setStyleSheet(
            "QPushButton { padding: 6px 20px; }"
        )
        lay.addWidget(btnClose, alignment=Qt.AlignmentFlag.AlignCenter)

        # Appliquer la taille de police utilisateur
        self._applyDialogFont(dlg)
        dlg.exec()

    def _exportPdf(self):
        """Export vers PDF via QTextDocument + QPrinter."""
        if not self._passes_raw:
            QMessageBox.information(self, "Export", tr("msg_no_data"))
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Export PDF", "moon_predictions.pdf",
            "PDF (*.pdf)")
        if not path:
            return

        callsign = self.editCallsign.text().strip()
        locator = self.editLocator.text().strip()
        freq_label = self.comboFreq.currentText()
        period_label = "1-30" if self._periodIndex == 0 else "31-60"
        show_phase = self.chkPhase.isChecked()

        # Valeurs des filtres actifs
        min_el = self.sliderMinEl.value()
        min_score = self.sliderMinScore.value() / 10.0
        total_passes = len(self._passes_raw)
        filtered_passes = sum(
            1 for d in self._passes_raw
            if d["max_el"] >= min_el and d["score"] >= min_score
        )

        headers = [
            tr("exp_col_date"), tr("exp_col_rise"), tr("exp_col_set"),
            tr("exp_col_duration"), tr("exp_col_el_max"),
            tr("exp_col_el_max_time"), tr("exp_col_az_rise"),
            tr("exp_col_az_set"), tr("exp_col_decl"),
            tr("exp_col_distance"), tr("exp_col_extra_pl"),
            tr("exp_col_total_pl", freq=freq_label),
            tr("exp_col_moon_sun"),
            tr("exp_col_spread_min", freq=freq_label),
            tr("exp_col_spread_max", freq=freq_label),
            tr("exp_col_quality"),
        ]
        if show_phase:
            headers.append(tr("exp_col_phase"))

        rows = self._getExportRows()
        if not show_phase:
            rows = [r[:-1] for r in rows]  # retirer colonne phase

        # Construction HTML
        html = (
            "<html><head><style>"
            "body { font-family: Consolas, monospace; font-size: 9pt; }"
            "table { border-collapse: collapse; width: 100%; }"
            "th { background-color: #D0D4DC; color: #1a1a1a; "
            "     border: 1px solid #999; padding: 4px; font-size: 8pt; }"
            "td { border: 1px solid #555; padding: 3px; "
            "     text-align: center; font-size: 8pt; }"
            "tr:nth-child(even) { background-color: #f0f0f8; }"
            "h2 { font-size: 11pt; margin-bottom: 4px; }"
            "p.info { font-size: 9pt; color: #444; margin-top: 0; }"
            "p.footer { font-size: 8pt; color: #888; margin-top: 10px; }"
            "</style></head><body>"
        )
        station = f"{callsign} " if callsign else ""
        html += f"<h2>Moon Predictions — {station}({locator}, {self._alt_m}m)</h2>"
        calc_time = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
        html += (
            f"<p class='info'>{tr('exp_period', period=period_label)} — "
            f"{tr('exp_frequency', freq=freq_label)} — "
            f"{tr('footer_calc', time=calc_time)}"
            f"</p>"
        )
        # Ligne filtres
        filter_parts = []
        if min_el > 0:
            filter_parts.append(f"EL min \u2265 {min_el}\u00b0")
        else:
            filter_parts.append(tr("exp_el_min_none"))
        if min_score > 0:
            filter_parts.append(f"Score min \u2265 {min_score:.1f}/10")
        else:
            filter_parts.append(tr("exp_score_min_none"))
        filter_parts.append(
            tr("exp_phase_yes") if show_phase else tr("exp_phase_no"))
        pl = "s" if filtered_passes > 1 else ""
        html += (
            f"<p class='info'>{tr('exp_filters')} : "
            f"{' \u2014 '.join(filter_parts)} "
            f"({tr('exp_passes_shown', n=filtered_passes, total=total_passes, s=pl, es=pl, en=pl)})</p>"
        )
        html += "<table><tr>"
        for h in headers:
            html += f"<th>{h}</th>"
        html += "</tr>"
        for row in rows:
            html += "<tr>"
            for cell in row:
                html += f"<td>{cell}</td>"
            html += "</tr>"
        html += "</table>"
        html += f"<p class='footer'>{tr('exp_footer')}</p>"
        html += "</body></html>"

        try:
            printer = QPrinter(QPrinter.PrinterMode.HighResolution)
            printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
            printer.setOutputFileName(path)
            printer.setPageOrientation(QPageLayout.Orientation.Landscape)

            doc = QTextDocument()
            doc.setHtml(html)
            doc.setPageSize(printer.pageRect(QPrinter.Unit.Point).size())
            doc.print(printer)

            # Ouvrir le PDF dans l'application par défaut
            os.startfile(path)

        except Exception as e:
            QMessageBox.critical(self, tr("msg_error"), str(e))

    def _exportTxt(self):
        if not self._passes_raw:
            QMessageBox.information(self, "Export", tr("msg_no_data"))
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Export TXT", "moon_predictions.txt",
            tr("exp_file_filter_txt"))
        if not path:
            return
        callsign = self.editCallsign.text().strip()
        locator = self.editLocator.text().strip()
        calc_time = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(f"Moon Predictions  -  {callsign} {locator}  "
                        f"alt {self._alt_m}m\n")
                f.write(f"{tr('exp_generated', time=calc_time)}\n")
                f.write("=" * 100 + "\n")
                for row in self._getExportRows():
                    # Indices : 0=date 1=rise 2=set 3=dur 4=EL 5=hEL 6=AZr 7=AZs
                    # 8=decl 9=dist 10=pl 11=tpl 12=m-s 13=spr_min 14=spr_max
                    # 15=score 16=phase
                    f.write(
                        f"{row[0]:14} | "
                        f"{row[1]:5} - {row[2]:5} ({row[3]:5}) | "
                        f"EL {row[4]:>5}deg @ {row[5]:5} | "
                        f"AZ {row[6]:>3}->{row[7]:>3} | "
                        f"D{row[8]:>5}deg | "
                        f"{row[9]:>6}km | "
                        f"PL+{row[10]:>4}dB | "
                        f"M-S {row[12]:>3}deg | "
                        f"Spr {row[13]:>14} / {row[14]:>14} Hz | "
                        f"Q{row[15]:>4} | {row[16]}\n"
                    )
            QMessageBox.information(self, "Export", tr("msg_saved", path=path))
        except Exception as e:
            QMessageBox.critical(self, tr("msg_error"), str(e))


def _parse_cli_args():
    """Parse optionnellement --callsign / --locator / --alt passes par un
    launcher externe (ex: app Rotator). Les valeurs ecrasent les prefs
    sauvegardees. Les args inconnus sont ignores pour compatibilite Qt.
    """
    import argparse
    parser = argparse.ArgumentParser(
        prog="MoonPredictions", add_help=False,
        description="EME Moon Pass Forecast")
    parser.add_argument("--callsign", type=str, default=None)
    parser.add_argument("--locator", type=str, default=None)
    parser.add_argument("--alt", type=float, default=None)
    # parse_known_args : ignore les args Qt (-style, etc.) sans erreur
    args, _unknown = parser.parse_known_args()
    return args


def main():
    cli_args = _parse_cli_args()
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    # Icône application — définie TRÈS TÔT pour éviter l'icône générique
    # Windows au premier lancement après installation (cache shell pas
    # encore rafraîchi). Appliqu\u00e9e avant SetCurrentProcessExplicitAppUserModelID.
    icon_path = _get_icon_path()
    app_icon = None
    if os.path.exists(icon_path):
        app_icon = QIcon(icon_path)
        app.setWindowIcon(app_icon)

    # Windows : identifier l'app pour que la barre des tâches
    # utilise notre icône (pas celle de Python). Doit être APRÈS setWindowIcon
    # pour que Windows associe immédiatement la bonne icône au taskbar group.
    try:
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
            "ON7KGK.MoonPredictions.1.0")
    except Exception:
        pass

    # Charger la langue AVANT la création de la fenêtre
    settings = QSettings("ON7KGK", "MoonPredictions")
    lang = settings.value("language", "fr", type=str)
    set_language(lang)

    window = MoonPredictionsWindow()

    # Args CLI : ecrasent les prefs sauvegardees et declenchent un calcul auto
    if cli_args.callsign is not None:
        window.editCallsign.setText(cli_args.callsign)
    if cli_args.locator is not None:
        window.editLocator.setText(cli_args.locator)
    if cli_args.alt is not None:
        window.spinAltitude.setValue(int(cli_args.alt))

    window.showMaximized()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
