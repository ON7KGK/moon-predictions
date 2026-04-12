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
)
from PyQt6.QtCore import Qt, QSettings, QTimer
from PyQt6.QtGui import QColor, QFont, QIcon, QTextDocument, QPageLayout
from PyQt6.QtPrintSupport import QPrinter

from moon_calc import (
    locator_to_latlon, get_moon_passes, enrich_moon_pass, compute_moon
)

APP_VERSION = "1.0.0"
APP_DATE = "2026-04-12"


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
# Tooltips (français)
# ════════════════════════════════════════════

TIP_DECL = (
    "DÉCLINAISON LUNAIRE\n"
    "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    "Angle de la Lune par rapport au plan équatorial céleste.\n\n"
    "  Positive (+) = Lune au nord de l'équateur\n"
    "  Négative (−) = Lune au sud de l'équateur\n\n"
    "Influence la hauteur maximale de la Lune :\n"
    "  Décl. élevée + latitude nord → EL max plus haute\n"
    "  Varie de −28.6° à +28.6° sur un cycle de 18.6 ans."
)

TIP_DISTANCE = (
    "DISTANCE TERRE-LUNE (km)\n"
    "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    "Distance topocentrique au moment de l'élévation maximale.\n\n"
    "  Périgée (min.) : ~356 500 km\n"
    "  Apogée (max.)  : ~406 700 km\n"
    "  Moyenne         : ~384 400 km\n\n"
    "PRÉCISION DU MODÈLE\n"
    "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    "Calculs Skyfield + JPL DE440s (éphémérides NASA,\n"
    "précision sub-km). Distance topocentrique identique\n"
    "au calcul de WSJT-X."
)

TIP_EXTRA_PL = (
    "EXTRA PATH LOSS — Perte supplémentaire vs périgée\n"
    "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    "Perte additionnelle par rapport au périgée (356 500 km) :\n\n"
    "  Extra PL = 40 × log₁₀(d / 356 500)\n\n"
    "  +0.0 dB = périgée (conditions optimales)\n"
    "  +5.8 dB = apogée (conditions défavorables)\n\n"
    "Le facteur 40 (et non 20) vient du trajet aller-retour\n"
    "et de la dépendance en d⁴ dans l'équation radar."
)

TIP_TOTAL_PL = (
    "TOTAL PATH LOSS — Atténuation EME complète\n"
    "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    "Total = Path loss au périgée + Extra Path Loss\n\n"
    "  Path loss au périgée (selon fréquence choisie)\n"
    "  + Extra Path Loss (fonction de la distance)\n"
    "  = Atténuation totale aller-retour Terre-Lune-Terre\n\n"
    "Changez la fréquence dans la liste déroulante\n"
    "au-dessus de la table pour recalculer."
)

TIP_MOON_SUN = (
    "ANGLE LUNE-SOLEIL\n"
    "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    "Séparation angulaire entre la Lune et le Soleil.\n\n"
    "  180° = opposition (pleine lune, pas de bruit solaire)\n"
    "  0°   = conjonction (nouvelle lune, bruit solaire max)\n\n"
    "IMPACT SUR L'EME :\n"
    "  > 15° : aucune dégradation\n"
    "  5-15° : dégradation possible du rapport S/N\n"
    "  < 5°  : bruit solaire important, EME très difficile\n\n"
    "Le Soleil est la source de bruit radio la plus forte\n"
    "du ciel. Quand il est proche de la Lune, le bruit\n"
    "de fond augmente et dégrade la réception EME."
)

TIP_QUALITY = (
    "INDICE DE QUALITÉ EME (0 à 10)\n"
    "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    "Score composite qui combine quatre facteurs :\n\n"
    "  Élévation maximale  (30% du score)\n"
    "    90° = 10 pts — Lune au zénith, trajet minimal\n"
    "    0°  =  0 pts — Lune à l'horizon\n\n"
    "  Durée du passage    (25% du score)\n"
    "    10h+ = 10 pts — Long passage, plus de temps EME\n"
    "    0h  =  0 pts\n\n"
    "  Extra Path Loss     (25% du score)\n"
    "    0.0 dB = 10 pts — Périgée, signal maximum\n"
    "    2.5 dB =  0 pts — Apogée, signal affaibli\n\n"
    "  Angle Moon-Sun      (20% du score)\n"
    "    180° = 10 pts — Lune opposée au Soleil\n"
    "    0°   =  0 pts — Bruit solaire maximum\n\n"
    "ÉCHELLE :\n"
    "  ■■■■■■■■■■ 10  Excellent (vert)\n"
    "  ■■■■■■■□□□  7  Bon\n"
    "  ■■■■□□□□□□  4  Moyen (orange)\n"
    "  ■■□□□□□□□□  2  Médiocre (rouge)\n\n"
    "Le score s'adapte à la fréquence :\n"
    "  < 1 GHz : libration ignorée (peu d'effet en VHF/UHF)\n"
    "  ≥ 1 GHz : libration = 30% du score (facteur dominant)"
)

TIP_LIBRATION = (
    "TAUX DE LIBRATION LUNAIRE (deg/h)\n"
    "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    "Vitesse de variation de la position apparente\n"
    "du sous-point terrestre sur la surface lunaire.\n\n"
    "IMPACT SUR L'EME (surtout > 1 GHz) :\n"
    "  < 0.10 deg/h : EXCELLENT — signal propre et concentré\n"
    "  0.10-0.25 deg/h : BON — faible étalement Doppler\n"
    "  0.25-0.40 deg/h : MOYEN — Doppler spread notable\n"
    "  > 0.40 deg/h : MAUVAIS — signal très étalé\n\n"
    "À 10 GHz, un taux de libration élevé étale le signal\n"
    "réfléchi par la Lune sur une bande de fréquence plus\n"
    "large (Doppler spread), réduisant le pic de signal\n"
    "et rendant la détection plus difficile.\n\n"
    "À 144 MHz/432 MHz, l'effet est négligeable car la\n"
    "surface lunaire est « lisse » à ces longueurs d'onde."
)

TIP_DOPPLER = (
    "DOPPLER SPREAD EME (Hz)\n"
    "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    "Étalement en fréquence du signal réfléchi par la Lune\n"
    "dû au mouvement apparent de la surface (libration).\n\n"
    "Calculé à la fréquence sélectionnée :\n"
    "  Spread = 2 × v_tangentielle × f / c\n\n"
    "Plus le spread est faible, plus le pic de signal\n"
    "est concentré et facile à détecter.\n\n"
    "Valeurs typiques à 10 GHz :\n"
    "  < 50 Hz  : excellent\n"
    "  50-150 Hz : bon\n"
    "  > 150 Hz  : difficile"
)

TIP_PHASE_CHK = (
    "Afficher la phase lunaire (purement visuel,\n"
    "pas d'effet sur l'EME radio)"
)

TIP_LOCAL_TIME = "Afficher en heure locale au lieu d'UTC"

TIP_QUALITY_FILTER = (
    "Filtrer les passages par indice de qualité EME\n"
    "minimum (0 à 8)"
)

TIP_FONT_SIZE = (
    "Taille de la police de la table et du texte.\n"
    "Sauvegardée automatiquement."
)

TIP_SAVE = (
    "Sauvegarder l'indicatif, le locator, l'altitude\n"
    "et les préférences. La sauvegarde est également\n"
    "automatique lors du calcul et à la fermeture."
)


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

_FR_DAYS = ["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"]
_FR_MONTHS = ["Jan", "Fév", "Mar", "Avr", "Mai", "Juin",
              "Juil", "Août", "Sep", "Oct", "Nov", "Déc"]


def _fr_date(dt):
    """Formatte une date en français : 'Lun 01 Jan'."""
    return f"{_FR_DAYS[dt.weekday()]} {dt.day:02d} {_FR_MONTHS[dt.month - 1]}"


def _fr_date_long(dt):
    """Formatte une date longue en français : 'Lun 01 Jan 2026'."""
    return f"{_FR_DAYS[dt.weekday()]} {dt.day:02d} {_FR_MONTHS[dt.month - 1]} {dt.year}"


def _eme_path_loss_perigee(freq_hz: float) -> float:
    """Path loss total EME aller-retour au périgée (dB)."""
    lam = _C_LIGHT / freq_hz
    num = (4.0 * math.pi) ** 3 * _D_PERIGEE ** 4
    den = _RHO_MOON * math.pi * _A_MOON ** 2 * lam ** 2
    return 10.0 * math.log10(num / den)


def _eme_color(value, green_max, orange_max, invert=False):
    if invert:
        if value <= green_max: return QColor("#44ff44")
        if value <= orange_max: return QColor("#ffaa00")
        return QColor("#ff4444")
    if value >= green_max: return QColor("#44ff44")
    if value >= orange_max: return QColor("#ffaa00")
    return QColor("#ff4444")


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
    if score >= 7: return QColor("#44ff44")
    if score >= 4: return QColor("#ffaa00")
    return QColor("#ff4444")


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
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "moon.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        self.setMinimumSize(900, 500)

        self._settings = QSettings("ON7KGK", "MoonPredictions")
        self._passes_raw = []
        self._lat = 0.0
        self._lon = 0.0
        self._alt_m = 0
        self._periodIndex = 0

        self._filterTimer = QTimer()
        self._filterTimer.setSingleShot(True)
        self._filterTimer.setInterval(150)
        self._filterTimer.timeout.connect(self._refreshTable)

        self._buildUI()
        self._loadSettings()

    # ════════════════════════════════════════════
    # UI
    # ════════════════════════════════════════════

    def _buildUI(self):
        # Stylesheet : couleurs uniquement, AUCUN font-size
        # Les tailles de police sont contrôlées par setFont() dans _applyFontSize
        self.setStyleSheet("""
            QMainWindow { background-color: #19232D; color: #cccccc; }
            QWidget { color: #cccccc; }
            QGroupBox {
                background-color: #1e2a36;
                border: 1px solid #334;
                border-radius: 6px;
                margin-top: 10px;
                padding-top: 14px;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 6px;
                color: #aaaacc;
            }
            QLineEdit, QSpinBox, QComboBox {
                background-color: #2a3742;
                border: 1px solid #445;
                border-radius: 3px;
                padding: 4px 6px;
                color: #ffffff;
            }
            QPushButton {
                background-color: #2E3D47;
                border: 1px solid #555;
                border-radius: 3px;
                padding: 6px 14px;
            }
            QPushButton:hover { background-color: #3A4D59; }
            QPushButton:checked { background-color: #4a6080; }
            QTableWidget {
                background-color: #19232D;
                gridline-color: #333;
                selection-background-color: #334;
            }
            QHeaderView::section {
                background-color: #243039;
                color: #aaaacc;
                border: 1px solid #333;
                padding: 4px;
                font-weight: bold;
            }
            QSlider::groove:horizontal {
                background: #333;
                height: 6px;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #6688cc;
                width: 16px;
                height: 16px;
                margin: -5px 0;
                border-radius: 8px;
            }
        """)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setSpacing(8)

        # ── Bandeau station ──
        stationGroup = QGroupBox("Station")
        stationLayout = QHBoxLayout(stationGroup)

        stationLayout.addWidget(QLabel("Indicatif :"))
        self.editCallsign = QLineEdit()
        self.editCallsign.setMaximumWidth(120)
        self.editCallsign.setPlaceholderText("ON7KGK")
        stationLayout.addWidget(self.editCallsign)

        stationLayout.addSpacing(15)
        stationLayout.addWidget(QLabel("Locator :"))
        self.editLocator = QLineEdit()
        self.editLocator.setMaximumWidth(120)
        self.editLocator.setPlaceholderText("JO20BM85")
        stationLayout.addWidget(self.editLocator)

        stationLayout.addSpacing(15)
        stationLayout.addWidget(QLabel("Altitude :"))
        self.spinAltitude = QSpinBox()
        self.spinAltitude.setRange(0, 9000)
        self.spinAltitude.setSuffix(" m")
        self.spinAltitude.setMaximumWidth(100)
        stationLayout.addWidget(self.spinAltitude)

        stationLayout.addSpacing(15)
        self.btnCompute = QPushButton("\u25b6  Calculer")
        self.btnCompute.setStyleSheet(
            "QPushButton { background-color: #2a5a3a; font-weight: bold; }"
            "QPushButton:hover { background-color: #3a7a4a; }"
        )
        self.btnCompute.clicked.connect(self._compute)
        stationLayout.addWidget(self.btnCompute)

        self.btnSave = QPushButton("\U0001f4be  Sauvegarder")
        self.btnSave.setToolTip(TIP_SAVE)
        self.btnSave.clicked.connect(self._onSaveClicked)
        stationLayout.addWidget(self.btnSave)

        stationLayout.addStretch()

        stationLayout.addStretch()

        _btn_discrete = (
            "QPushButton { color: #888; border: 1px solid #444; "
            "padding: 4px 10px; }"
            "QPushButton:hover { color: #ccc; border-color: #666; }"
        )
        self.btnHelp = QPushButton("Aide")
        self.btnHelp.setStyleSheet(_btn_discrete)
        self.btnHelp.clicked.connect(self._showHelp)
        stationLayout.addWidget(self.btnHelp)

        self.btnAbout = QPushButton("About")
        self.btnAbout.setStyleSheet(_btn_discrete)
        self.btnAbout.clicked.connect(self._showAbout)
        stationLayout.addWidget(self.btnAbout)

        layout.addWidget(stationGroup)

        # ── Filtres — Ligne 1 : sliders + fréquence ──
        filterLine1 = QHBoxLayout()
        filterLine1.setSpacing(12)

        filterLine1.addWidget(QLabel("EL min :"))
        self.sliderMinEl = QSlider(Qt.Orientation.Horizontal)
        self.sliderMinEl.setRange(0, 45)
        self.sliderMinEl.setMinimumWidth(100)
        self.sliderMinEl.valueChanged.connect(self._onFilterChanged)
        filterLine1.addWidget(self.sliderMinEl)
        self.labelMinEl = QLabel("0\u00b0")
        self.labelMinEl.setMinimumWidth(35)
        filterLine1.addWidget(self.labelMinEl)

        filterLine1.addSpacing(15)
        filterLine1.addWidget(QLabel("Score min :"))
        self.sliderMinScore = QSlider(Qt.Orientation.Horizontal)
        self.sliderMinScore.setRange(0, 80)
        self.sliderMinScore.setMinimumWidth(80)
        self.sliderMinScore.setToolTip(TIP_QUALITY_FILTER)
        self.sliderMinScore.valueChanged.connect(self._onFilterChanged)
        filterLine1.addWidget(self.sliderMinScore)
        self.labelMinScore = QLabel("0.0")
        self.labelMinScore.setMinimumWidth(30)
        filterLine1.addWidget(self.labelMinScore)

        filterLine1.addSpacing(15)
        filterLine1.addWidget(QLabel("Fréquence :"))
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

        self.chkPhase = QCheckBox("Phase")
        self.chkPhase.setChecked(True)
        self.chkPhase.setToolTip(TIP_PHASE_CHK)
        self.chkPhase.stateChanged.connect(self._onFilterChanged)
        filterLine2.addWidget(self.chkPhase)

        filterLine2.addSpacing(10)
        self.chkLocalTime = QCheckBox("Heure locale")
        self.chkLocalTime.setToolTip(TIP_LOCAL_TIME)
        self.chkLocalTime.stateChanged.connect(self._onFilterChanged)
        filterLine2.addWidget(self.chkLocalTime)
        self.labelTz = QLabel("")
        self.labelTz.setStyleSheet("color: #888;")
        filterLine2.addWidget(self.labelTz)
        self._updateTzLabel()

        filterLine2.addSpacing(15)
        filterLine2.addWidget(QLabel("Police :"))
        self.spinFontSize = QSpinBox()
        self.spinFontSize.setRange(8, 18)
        self.spinFontSize.setValue(10)
        self.spinFontSize.setSuffix(" pt")
        self.spinFontSize.setToolTip(TIP_FONT_SIZE)
        self.spinFontSize.setMaximumWidth(80)
        self.spinFontSize.valueChanged.connect(self._onFontSizeChanged)
        filterLine2.addWidget(self.spinFontSize)

        filterLine2.addSpacing(15)
        self.btnExportTxt = QPushButton("Export TXT")
        self.btnExportTxt.clicked.connect(self._exportTxt)
        filterLine2.addWidget(self.btnExportTxt)

        self.btnExportPdf = QPushButton("Export PDF")
        self.btnExportPdf.clicked.connect(self._exportPdf)
        filterLine2.addWidget(self.btnExportPdf)

        filterLine2.addStretch()

        # Lien EME Observer (SA5IKN)
        self.linkSked = QLabel(
            "<a href='https://dxer.site/eme-observer/' "
            "style='color: #6699ff; text-decoration: none;'>"
            "EME Observer (SA5IKN)</a>")
        self.linkSked.setOpenExternalLinks(True)
        self.linkSked.setToolTip(
            "Outil en ligne de planification de QSO EME\n"
            "par SA5IKN — skeds, visibilité mutuelle, etc."
        )
        filterLine2.addWidget(self.linkSked)

        layout.addLayout(filterLine2)

        # ── Info ──
        self.labelInfo = QLabel("Entrez votre locator et cliquez sur Calculer.")
        self.labelInfo.setStyleSheet("color: #aaaacc;")
        layout.addWidget(self.labelInfo)

        # ── Légende ──
        self.labelLegend = QLabel(
            "<span style='color:#44ff44;'>\u25a0</span> Excellent  "
            "<span style='color:#ffaa00;'>\u25a0</span> Moyen  "
            "<span style='color:#ff4444;'>\u25a0</span> Faible"
        )
        layout.addWidget(self.labelLegend)

        # ── Table ──
        self.table = QTableWidget()
        self.table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(False)
        self.table.verticalHeader().setVisible(False)  # pas de numéros de lignes
        layout.addWidget(self.table)

        # ── Footer ──
        footerBar = QHBoxLayout()
        self.labelFooter = QLabel("")
        self.labelFooter.setStyleSheet("color: #888;")
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
        self._applyFontSize()

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
        self._settings.sync()

    def _onSaveClicked(self):
        self._saveSettings()
        # Feedback visuel temporaire (texte fixe pour le retour)
        self.btnSave.setText("\u2713  Sauvegard\u00e9")
        QTimer.singleShot(1500,
            lambda: self.btnSave.setText("\U0001f4be  Sauvegarder"))

    def _applyFontSize(self):
        """Applique la taille de police à TOUT l'interface."""
        size = self.spinFontSize.value()

        # Police de base (UI générale) — Qt default family
        ui_font = QFont()
        ui_font.setPointSize(size)
        # Appliquer au widget central → cascade à tous les enfants
        central = self.centralWidget()
        if central:
            central.setFont(ui_font)

        # Forcer la police sur chaque sous-widget (certains ne cascadent pas
        # bien si le stylesheet a overridé — par sécurité)
        for w in (self.editCallsign, self.editLocator, self.spinAltitude,
                  self.comboFreq, self.spinFontSize,
                  self.btnCompute, self.btnSave, self.btnExportTxt,
                  self.btnExportPdf, self.btnHelp, self.btnAbout,
                  self.btn1_30, self.btn31_60,
                  self.chkPhase, self.chkLocalTime,
                  self.labelInfo, self.labelLegend,
                  self.labelFooter, self.labelTz, self.labelMinEl,
                  self.labelMinScore, self.linkSked):
            w.setFont(ui_font)

        # Table et header : police monospace cross-platform
        # Windows=Consolas, Mac=Menlo, Linux=DejaVu Sans Mono
        self.table.setFont(_make_monospace_font(size))

        hdr_font = _make_monospace_font(max(size - 1, 8))
        hdr_font.setBold(True)
        self.table.horizontalHeader().setFont(hdr_font)

        # Hauteur des lignes ajustée à la taille de police
        self.table.verticalHeader().setDefaultSectionSize(int(size * 1.9) + 4)

        # Re-layout : forcer le recalcul des colonnes et la mise à jour visuelle
        self.table.resizeColumnsToContents()
        self.updateGeometry()

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
            QMessageBox.warning(
                self, "Locator manquant",
                "Entrez votre locator Maidenhead (6 ou 8 caractères).\n"
                "Exemple : JO20BM85"
            )
            return
        if len(locator) < 6:
            QMessageBox.warning(
                self, "Locator trop court",
                "Le locator doit avoir au minimum 6 caractères.\n\n"
                "Un locator à 4 caractères (ex: JO20) couvre une zone de\n"
                "~200×110 km, ce qui entraîne des erreurs de plusieurs\n"
                "minutes sur les heures de lever/coucher de la Lune.\n\n"
                "Utilisez votre locator à 6 caractères (précision ~5 km)\n"
                "ou 8 caractères (précision ~800 m).\n\n"
                "Exemple : JO20BM ou JO20BM85"
            )
            return

        try:
            lat, lon = locator_to_latlon(locator)
        except ValueError as e:
            QMessageBox.warning(
                self, "Locator invalide", f"Erreur : {e}")
            return

        self._lat, self._lon = lat, lon
        self._alt_m = self.spinAltitude.value()
        callsign = self.editCallsign.text().strip()

        # Position actuelle de la Lune (info)
        offset_hours = self._periodIndex * 30 * 24
        period_label = "1-30" if self._periodIndex == 0 else "31-60"
        self.labelInfo.setText(f"Calcul en cours (jours {period_label})...")
        self.table.setRowCount(0)
        QApplication.processEvents()

        try:
            passes = get_moon_passes(
                lat, lon, self._alt_m,
                hours=30 * 24, start_offset_hours=offset_hours)
        except Exception as e:
            QMessageBox.critical(
                self, "Erreur calcul", f"Skyfield : {e}")
            return

        self._passes_raw = []
        for p in passes:
            d = dict(p)
            try:
                enrich_moon_pass(lat, lon, self._alt_m, d)
            except Exception:
                continue
            d["ploss"] = (40.0 * math.log10(d["dist_km"] / 356500.0)
                          if d["dist_km"] > 0 else 0)
            # Doppler spread à la fréquence sélectionnée
            freq = self.comboFreq.currentData() or 10368e6
            base_spread = d.get("doppler_spread", 0)
            d["doppler_spread_freq"] = round(
                base_spread * freq / 10.368e9, 0) if base_spread else 0
            d["score"] = _quality_score(
                d["max_el"], d["duration_min"], d["ploss"],
                d.get("moon_sun", 180),
                d.get("lib_rate", 0), freq)
            self._passes_raw.append(d)

        station = f"{callsign} " if callsign else ""
        self.labelInfo.setText(
            f"{station}({locator}, {self._alt_m}m) \u2014 "
            f"{len(self._passes_raw)} passage(s) sur {period_label} jours"
        )

        self._saveSettings()
        self._refreshTable()

    def _onPeriodChanged(self, index):
        self._periodIndex = index
        self.btn1_30.setChecked(index == 0)
        self.btn31_60.setChecked(index == 1)
        if self._passes_raw or self.editLocator.text():
            self._compute()

    def _onFilterChanged(self):
        self.labelMinEl.setText(f"{self.sliderMinEl.value()}\u00b0")
        self.labelMinScore.setText(
            f"{self.sliderMinScore.value() / 10:.1f}")
        self._updateTzLabel()
        self._filterTimer.start()

    # ════════════════════════════════════════════
    # Affichage table
    # ════════════════════════════════════════════

    def _buildNowRow(self, freq, pl_perigee, show_phase):
        """Construit la ligne 'MAINTENANT' avec la position actuelle de la Lune.

        Returns list de tuples (text, QColor|None) pour chaque colonne.
        """
        from moon_calc import (compute_moon, compute_sun, compute_libration,
                               ts, _angular_sep_deg)

        moon = compute_moon(self._lat, self._lon, self._alt_m)
        sun = compute_sun(self._lat, self._lon, self._alt_m)
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

        # Couleurs
        hi = QColor("#55ccff")
        dist_col = _eme_color(dist, _DIST_GREEN, _DIST_ORANGE, invert=True)
        pl_col = _eme_color(ploss, _PL_GREEN, _PL_ORANGE, invert=True)
        el_col = _eme_color(el, _EL_GREEN, _EL_ORANGE) if el > 0 else QColor("#ff4444")

        if lib_rate < 0.10: lib_col = QColor("#44ff44")
        elif lib_rate < 0.25: lib_col = QColor("#ffaa00")
        else: lib_col = QColor("#ff4444")

        if spread < 50: spr_col = QColor("#44ff44")
        elif spread < 150: spr_col = QColor("#ffaa00")
        else: spr_col = QColor("#ff4444")

        if ms_angle < 5: ms_col = QColor("#ff4444")
        elif ms_angle < 15: ms_col = QColor("#ffaa00")
        else: ms_col = QColor("#44ff44")

        sq = _quality_squares(score)
        qc = _quality_color(score)

        cells = [
            ("\u25cf MAINTENANT", hi),
            (rise_txt, hi),
            (set_txt, hi),
            (dur_txt, dur_col),
            (f"{el:+.1f}\u00b0", el_col),
            (datetime.now(timezone.utc).strftime("%H:%M UTC"), hi),
            (f"{az:.0f}\u00b0", hi),
            ("---", None),
            (f"{decl:+.1f}\u00b0", None),
            (f"{dist:.0f} km", dist_col),
            (f"+{ploss:.1f} dB", pl_col),
            (f"{total_pl:.1f} dB", pl_col),
            (f"{ms_angle:.0f}\u00b0", ms_col),
            (f"{lib_rate:.2f}\u00b0/h", lib_col),
            (f"{spread:.0f} Hz", spr_col),
            (f"{sq} {score:.1f}", qc),
        ]
        if show_phase:
            cells.append((f"{phase} ({illum:.0f}%)", hi))

        return cells

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
            "Date",
            f"Lever{tz_suffix}",
            f"Coucher{tz_suffix}",
            "Durée",
            "EL max",
            f"Heure EL max{tz_suffix}",
            "AZ lever",
            "AZ couch.",
            "Décl.",
            "Distance",
            "Extra PL",
            f"Total PL ({freq_label})",
            "Moon-Sun",
            "Libration",
            f"Spread ({freq_label})",
            "Qualité",
        ]
        if show_phase:
            cols.append("Phase")

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

        _set_tip(8, TIP_DECL)          # Décl.
        _set_tip(9, TIP_DISTANCE)      # Distance
        _set_tip(10, TIP_EXTRA_PL)     # Extra PL
        _set_tip(11, TIP_TOTAL_PL)     # Total PL
        _set_tip(12, TIP_MOON_SUN)     # Moon-Sun
        _set_tip(13, TIP_LIBRATION)    # Libration
        _set_tip(14, TIP_DOPPLER)      # Doppler spread
        _set_tip(15, TIP_QUALITY)      # Qualité

        hdr = self.table.horizontalHeader()
        hdr.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(15, QHeaderView.ResizeMode.Stretch)

        # ── Ligne "MAINTENANT" (row 0, fond distinct) ──
        row_offset = 0
        if now_row:
            now_bg = QColor("#1a2a3a")
            now_txt = QColor("#55ccff")
            for c, (text, color) in enumerate(now_row):
                item = _make_item(text, color or now_txt)
                item.setBackground(now_bg)
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
                _fr_date(rise_dt))); col += 1
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
            if ms_angle < 5: ms_color = QColor("#ff4444")
            elif ms_angle < 15: ms_color = QColor("#ffaa00")
            else: ms_color = QColor("#44ff44")
            self.table.setItem(row, col, _make_item(
                f"{ms_angle:.0f}\u00b0", ms_color)); col += 1

            # Libration rate
            lib_r = d.get("lib_rate", 0)
            if lib_r < 0.10: lib_col = QColor("#44ff44")
            elif lib_r < 0.25: lib_col = QColor("#ffaa00")
            else: lib_col = QColor("#ff4444")
            self.table.setItem(row, col, _make_item(
                f"{lib_r:.2f}\u00b0/h", lib_col)); col += 1

            # Doppler spread (à la fréquence sélectionnée)
            spr = d.get("doppler_spread", 0) * freq / 10.368e9
            if spr < 50: spr_col = QColor("#44ff44")
            elif spr < 150: spr_col = QColor("#ffaa00")
            else: spr_col = QColor("#ff4444")
            self.table.setItem(row, col, _make_item(
                f"{spr:.0f} Hz", spr_col)); col += 1

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
                f" | {shown}/{total} affichés")

        self.labelFooter.setText(
            f"Calcul : {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}"
        )

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
            rows.append([
                _fr_date_long(rise_dt),
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
                f"{d['score']:.1f}",
                f"{d['phase']} ({d['illum']:.0f}%)",
            ])
        return rows

    def _showHelp(self):
        """Fenêtre d'aide utilisateur."""
        dlg = QDialog(self)
        dlg.setWindowTitle("Aide — Moon Predictions")
        dlg.setMinimumSize(600, 520)
        dlg.setStyleSheet(
            "QDialog { background-color: #1a2530; color: #cccccc; }"
            "QLabel { color: #cccccc; }"
        )
        icon_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "moon.ico")
        if os.path.exists(icon_path):
            dlg.setWindowIcon(QIcon(icon_path))

        lay = QVBoxLayout(dlg)

        help_text = QLabel(
            "<h2 style='color: #FFD700;'>Comment utiliser Moon Predictions</h2>"

            "<h3 style='color: #66aaff;'>1. Configuration de la station</h3>"
            "<p>Renseignez votre <b>indicatif</b> (optionnel), votre <b>QRA locator</b> "
            "(6 ou 8 caractères, ex: JO20CL) et votre <b>altitude</b> en mètres. "
            "Cliquez <b>Sauvegarder</b> pour conserver ces informations.</p>"

            "<h3 style='color: #66aaff;'>2. Calcul des passages</h3>"
            "<p>Cliquez <b>Calculer</b> pour afficher les passages de la Lune "
            "au-dessus de l'horizon sur <b>30 jours</b>. "
            "Utilisez les boutons <b>1-30 j</b> / <b>31-60 j</b> pour naviguer.</p>"

            "<h3 style='color: #66aaff;'>3. Filtres</h3>"
            "<p>Ajustez les curseurs <b>EL min</b> et <b>Score min</b> pour "
            "ne garder que les meilleurs passages. Les filtres s'appliquent "
            "en temps réel sans recalcul.</p>"

            "<h3 style='color: #66aaff;'>4. Comprendre la table</h3>"
            "<ul>"
            "<li><b>EL max</b> : élévation maximale de la Lune pendant le passage</li>"
            "<li><b>Distance</b> : distance Terre-Lune (périgée ~356 500 km = meilleur signal)</li>"
            "<li><b>Extra PL</b> : perte supplémentaire vs périgée (0 dB = optimal)</li>"
            "<li><b>Moon-Sun</b> : angle Lune-Soleil (> 15° = pas de bruit solaire)</li>"
            "<li><b>Libration</b> : taux de libration — <span style='color:#44ff44;'>vert</span> = "
            "signal propre, <span style='color:#ff4444;'>rouge</span> = signal étalé. "
            "<b>Critique à 10 GHz et au-dessus !</b></li>"
            "<li><b>Spread</b> : étalement Doppler du signal réfléchi en Hz</li>"
            "<li><b>Qualité</b> : score global 0-10 combinant tous les facteurs</li>"
            "</ul>"

            "<h3 style='color: #66aaff;'>5. Score de qualité</h3>"
            "<p>Le score s'adapte à la <b>fréquence</b> sélectionnée :<br>"
            "- En <b>VHF/UHF</b> (< 1 GHz) : élévation et durée dominent<br>"
            "- En <b>micro-ondes</b> (≥ 1 GHz) : la <b>libration</b> devient le facteur "
            "le plus important (30% du score)</p>"

            "<h3 style='color: #66aaff;'>6. Code couleur</h3>"
            "<p><span style='color:#44ff44;'>■</span> Excellent — "
            "<span style='color:#ffaa00;'>■</span> Moyen — "
            "<span style='color:#ff4444;'>■</span> Faible</p>"

            "<h3 style='color: #66aaff;'>7. Export</h3>"
            "<p>Exportez vos prévisions en <b>TXT</b> (texte brut) ou <b>PDF</b> "
            "(tableau formaté en paysage) pour les partager ou les imprimer.</p>"

            "<p style='color: #888; margin-top: 15px;'>"
            "Survolez les en-têtes de colonnes avec la souris pour des "
            "explications détaillées sur chaque paramètre.</p>"
        )
        help_text.setWordWrap(True)
        help_text.setOpenExternalLinks(True)
        lay.addWidget(help_text)

        lay.addStretch()
        btnClose = QPushButton("Fermer")
        btnClose.clicked.connect(dlg.close)
        btnClose.setStyleSheet("QPushButton { padding: 6px 20px; }")
        lay.addWidget(btnClose, alignment=Qt.AlignmentFlag.AlignCenter)

        dlg.exec()

    def _showAbout(self):
        """Fenêtre À propos."""
        dlg = QDialog(self)
        dlg.setWindowTitle("About Moon Predictions")
        dlg.setFixedSize(480, 360)
        dlg.setStyleSheet(
            "QDialog { background-color: #1a2530; color: #cccccc; }"
            "QLabel { color: #cccccc; }"
        )

        lay = QVBoxLayout(dlg)
        lay.setSpacing(12)

        # Icône + titre
        icon_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "icon.ico")
        if os.path.exists(icon_path):
            dlg.setWindowIcon(QIcon(icon_path))

        title = QLabel(f"<h2 style='color: #FFD700;'>"
                       f"\u263d Moon Predictions</h2>")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(title)

        version = QLabel(
            f"<p style='font-size: 14pt; color: #66aaff;'>"
            f"Version {APP_VERSION} — {APP_DATE}</p>")
        version.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(version)

        info = QLabel(
            "<p style='text-align: center;'>"
            "Prévision des passages lunaires pour les<br>"
            "radioamateurs pratiquant l'EME (Earth-Moon-Earth).</p>"
            "<hr style='border-color: #334;'>"
            "<p style='text-align: center;'>"
            "<b>Auteur :</b> ON7KGK — Michaël<br>"
            "<b>Développement :</b> Claude Code (Anthropic)<br>"
            "<b>Éphémérides :</b> NASA JPL DE440s via Skyfield<br>"
            "<b>Icône :</b> Arkinasi — Flaticon</p>"
            "<hr style='border-color: #334;'>"
            "<p style='text-align: center;'>"
            "<b>Licence :</b> GNU GPL v3 — Open Source</p>"
        )
        info.setOpenExternalLinks(True)
        info.setWordWrap(True)
        info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(info)

        lay.addStretch()

        btnClose = QPushButton("Fermer")
        btnClose.clicked.connect(dlg.close)
        btnClose.setStyleSheet(
            "QPushButton { padding: 6px 20px; }"
        )
        lay.addWidget(btnClose, alignment=Qt.AlignmentFlag.AlignCenter)

        dlg.exec()

    def _exportPdf(self):
        """Export vers PDF via QTextDocument + QPrinter."""
        if not self._passes_raw:
            QMessageBox.information(self, "Export", "Aucune donnée.")
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
            "Date", "Lever", "Coucher", "Durée", "EL max",
            "H. EL max", "AZ lever", "AZ couch.", "Décl.",
            "Distance", "Extra PL", f"Total PL ({freq_label})",
            "Moon-Sun", "Qualité",
        ]
        if show_phase:
            headers.append("Phase")

        rows = self._getExportRows()
        if not show_phase:
            rows = [r[:-1] for r in rows]  # retirer colonne phase

        # Construction HTML
        html = (
            "<html><head><style>"
            "body { font-family: Consolas, monospace; font-size: 9pt; }"
            "table { border-collapse: collapse; width: 100%; }"
            "th { background-color: #243039; color: #000; "
            "     border: 1px solid #555; padding: 4px; font-size: 8pt; }"
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
        html += (
            f"<p class='info'>Période : jours {period_label} — "
            f"Fréquence : {freq_label} — "
            f"Calcul : {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}"
            f"</p>"
        )
        # Ligne filtres
        filter_parts = []
        if min_el > 0:
            filter_parts.append(f"EL min ≥ {min_el}°")
        else:
            filter_parts.append("EL min : aucun")
        if min_score > 0:
            filter_parts.append(f"Score min ≥ {min_score:.1f}/10")
        else:
            filter_parts.append("Score min : aucun")
        filter_parts.append(f"Phase : {'oui' if show_phase else 'non'}")
        html += (
            f"<p class='info'>Filtres : {' — '.join(filter_parts)} "
            f"({filtered_passes}/{total_passes} passage{'s' if filtered_passes > 1 else ''} "
            f"affiché{'s' if filtered_passes > 1 else ''})</p>"
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
        html += (
            "<p class='footer'>Réf. périgée : 356 500 km | "
            "Score = f(élévation, durée, distance, moon-sun) | "
            "Calculs : Skyfield + JPL DE440s</p>"
        )
        html += "</body></html>"

        try:
            printer = QPrinter(QPrinter.PrinterMode.HighResolution)
            printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
            printer.setOutputFileName(path)
            printer.setPageOrientation(QPageLayout.Orientation.Landscape)

            doc = QTextDocument()
            doc.setHtml(html)
            doc.print(printer)

            QMessageBox.information(self, "Export", f"Sauvegardé : {path}")
        except Exception as e:
            QMessageBox.critical(self, "Erreur PDF", str(e))

    def _exportTxt(self):
        if not self._passes_raw:
            QMessageBox.information(self, "Export", "Aucune donnée.")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Export TXT", "moon_predictions.txt",
            "Texte (*.txt)")
        if not path:
            return
        callsign = self.editCallsign.text().strip()
        locator = self.editLocator.text().strip()
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(f"Moon Predictions  -  {callsign} {locator}  "
                        f"alt {self._alt_m}m\n")
                f.write(f"Genere : "
                        f"{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}\n")
                f.write("=" * 100 + "\n")
                for row in self._getExportRows():
                    f.write(
                        f"{row[0]:14} | "
                        f"{row[1]:5} - {row[2]:5} ({row[3]:5}) | "
                        f"EL {row[4]:>5}deg @ {row[5]:5} | "
                        f"AZ {row[6]:>3}->{row[7]:>3} | "
                        f"D{row[8]:>5}deg | "
                        f"{row[9]:>6}km | "
                        f"PL+{row[10]:>4}dB | "
                        f"M-S {row[12]:>3}deg | "
                        f"Q{row[13]:>4} | {row[14]}\n"
                    )
            QMessageBox.information(self, "Export", f"Sauvegardé : {path}")
        except Exception as e:
            QMessageBox.critical(self, "Erreur", str(e))


def main():
    # Windows : identifier l'app pour que la barre des tâches
    # utilise notre icône (pas celle de Python)
    try:
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
            "ON7KGK.MoonPredictions.1.0")
    except Exception:
        pass

    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    # Icône application (barre des tâches Windows)
    icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "moon.ico")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    window = MoonPredictionsWindow()
    window.showMaximized()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
