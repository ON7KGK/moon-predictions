"""
Moon Predictions — Internationalisation (FR / NL / EN)

Les infobulles (clés tip_*) sont charg\u00e9es depuis les fichiers JSON externes
dans le dossier tooltips/ (fr.json, nl.json, en.json).
\u00c9ditez ces fichiers pour modifier le texte des infobulles sans toucher au code.
"""

import json
import os

_LANG = "fr"  # Langue par défaut

_STRINGS = {
    # ── Interface station ──
    "lbl_callsign": {"fr": "Indicatif :", "nl": "Roepnaam :", "en": "Callsign:"},
    "lbl_locator": {"fr": "Locator :", "nl": "Locator :", "en": "Locator:"},
    "lbl_altitude": {"fr": "Altitude :", "nl": "Hoogte :", "en": "Altitude:"},
    "btn_compute": {"fr": "\u25b6  Calculer", "nl": "\u25b6  Berekenen", "en": "\u25b6  Compute"},
    "btn_save": {"fr": "\U0001f4be  Sauvegarder", "nl": "\U0001f4be  Opslaan", "en": "\U0001f4be  Save"},
    "btn_saved": {"fr": "\u2713  Sauvegard\u00e9", "nl": "\u2713  Opgeslagen", "en": "\u2713  Saved"},
    "btn_help": {"fr": "Aide", "nl": "Help", "en": "Help"},
    "btn_about": {"fr": "About", "nl": "Over", "en": "About"},

    # ── Filtres ──
    "lbl_el_min": {"fr": "EL min :", "nl": "EL min :", "en": "EL min:"},
    "lbl_score_min": {"fr": "Score min :", "nl": "Score min :", "en": "Score min:"},
    "lbl_frequency": {"fr": "Fr\u00e9quence :", "nl": "Frequentie :", "en": "Frequency:"},
    "lbl_phase": {"fr": "Phase", "nl": "Fase", "en": "Phase"},
    "lbl_local_time": {"fr": "Heure locale", "nl": "Lokale tijd", "en": "Local time"},
    "lbl_font_size": {"fr": "Police :", "nl": "Lettertype :", "en": "Font:"},
    "lbl_language": {"fr": "Langue :", "nl": "Taal :", "en": "Language:"},
    "btn_export_txt": {"fr": "Export TXT", "nl": "Export TXT", "en": "Export TXT"},
    "btn_export_pdf": {"fr": "Export PDF", "nl": "Export PDF", "en": "Export PDF"},

    # ── L\u00e9gende ──
    "legend_excellent": {"fr": "Excellent", "nl": "Uitstekend", "en": "Excellent"},
    "legend_medium": {"fr": "Moyen", "nl": "Gemiddeld", "en": "Medium"},
    "legend_poor": {"fr": "Faible", "nl": "Zwak", "en": "Poor"},

    # ── Info ──
    "info_enter_locator": {
        "fr": "Entrez votre locator et cliquez sur Calculer.",
        "nl": "Voer uw locator in en klik op Berekenen.",
        "en": "Enter your locator and click Compute.",
    },
    "info_computing": {
        "fr": "Calcul en cours (jours {period})...",
        "nl": "Berekening bezig (dagen {period})...",
        "en": "Computing (days {period})...",
    },
    "info_result": {
        "fr": "{station}({locator}, {alt}m) \u2014 {count} passage(s) sur {period} jours",
        "nl": "{station}({locator}, {alt}m) \u2014 {count} doorgang(en) over {period} dagen",
        "en": "{station}({locator}, {alt}m) \u2014 {count} pass(es) over {period} days",
    },
    "info_filtered": {
        "fr": "{shown}/{total} affich\u00e9s",
        "nl": "{shown}/{total} weergegeven",
        "en": "{shown}/{total} shown",
    },
    "footer_calc": {
        "fr": "Calcul : {time}",
        "nl": "Berekening : {time}",
        "en": "Computed: {time}",
    },

    # ── En-t\u00eates de colonnes ──
    "col_date": {"fr": "Date", "nl": "Datum", "en": "Date"},
    "col_rise": {"fr": "Lever", "nl": "Opkomst", "en": "Rise"},
    "col_set": {"fr": "Coucher", "nl": "Ondergang", "en": "Set"},
    "col_duration": {"fr": "Dur\u00e9e", "nl": "Duur", "en": "Duration"},
    "col_el_max": {"fr": "EL max", "nl": "EL max", "en": "EL max"},
    "col_el_max_time": {"fr": "Heure EL max", "nl": "Tijd EL max", "en": "EL max time"},
    "col_az_rise": {"fr": "AZ lever", "nl": "AZ opkomst", "en": "AZ rise"},
    "col_az_set": {"fr": "AZ couch.", "nl": "AZ onderg.", "en": "AZ set"},
    "col_decl": {"fr": "D\u00e9cl.", "nl": "Decl.", "en": "Decl."},
    "col_distance": {"fr": "Distance", "nl": "Afstand", "en": "Distance"},
    "col_extra_pl": {"fr": "Extra PL", "nl": "Extra PL", "en": "Extra PL"},
    "col_total_pl": {"fr": "Total PL ({freq})", "nl": "Totaal PL ({freq})", "en": "Total PL ({freq})"},
    "col_moon_sun": {"fr": "Moon-Sun", "nl": "Maan-Zon", "en": "Moon-Sun"},
    "col_libration": {"fr": "Libration", "nl": "Libratie", "en": "Libration"},
    "col_spread": {"fr": "Spread ({freq})", "nl": "Spread ({freq})", "en": "Spread ({freq})"},
    "col_spread_min": {"fr": "Spread min ({freq})", "nl": "Spread min ({freq})", "en": "Spread min ({freq})"},
    "col_spread_max": {"fr": "Spread max ({freq})", "nl": "Spread max ({freq})", "en": "Spread max ({freq})"},
    "col_quality": {"fr": "Qualit\u00e9", "nl": "Kwaliteit", "en": "Quality"},

    # ── Fenetre detail d'une journee (double-clic sur ligne) ──
    "day_detail_title": {
        "fr": "D\u00e9tail du passage",
        "nl": "Passage detail",
        "en": "Pass detail",
    },

    # ── Fenetre detail MAINTENANT (clic ligne MAINTENANT) ──
    "now_detail_title": {
        "fr": "D\u00e9tail temps r\u00e9el — MAINTENANT",
        "nl": "Realtime detail — NU",
        "en": "Real-time detail — NOW",
    },
    "now_grp_position": {"fr": "Position actuelle", "nl": "Huidige positie", "en": "Current position"},
    "now_grp_riseset": {"fr": "Lever / Coucher", "nl": "Opkomst / Ondergang", "en": "Rise / Set"},
    "now_grp_eme": {"fr": "Donn\u00e9es EME", "nl": "EME-gegevens", "en": "EME data"},
    "now_grp_astro": {"fr": "Coordonn\u00e9es astronomiques", "nl": "Astronomische co\u00f6rdinaten", "en": "Astronomical coordinates"},
    "now_lbl_distance": {"fr": "Distance", "nl": "Afstand", "en": "Distance"},
    "now_lbl_decl": {"fr": "D\u00e9clinaison", "nl": "Declinatie", "en": "Declination"},
    "now_lbl_phase": {"fr": "Phase", "nl": "Fase", "en": "Phase"},
    "now_lbl_dgr": {"fr": "D\u00e9gradation (DGR)", "nl": "Degradatie (DGR)", "en": "Degradation (DGR)"},
    "now_lbl_tsky": {"fr": "Temp\u00e9rature de ciel", "nl": "Hemelsetemperatuur", "en": "Sky temperature"},
    "now_lbl_doppler": {"fr": "Doppler central", "nl": "Centrale Doppler", "en": "Central Doppler"},
    "now_lbl_echo": {"fr": "Home Echo", "nl": "Home Echo", "en": "Home Echo"},
    "now_lbl_spread": {"fr": "Doppler spread", "nl": "Doppler spread", "en": "Doppler spread"},
    "now_lbl_libration": {"fr": "Libration", "nl": "Libratie", "en": "Libration"},
    "now_lbl_pl_extra": {"fr": "Path loss extra", "nl": "Path loss extra", "en": "Path loss extra"},
    "now_lbl_moonsun": {"fr": "Angle Lune-Soleil", "nl": "Maan-Zon hoek", "en": "Moon-Sun angle"},
    "now_lbl_lha": {"fr": "LHA (local)", "nl": "LHA (lokaal)", "en": "LHA (local)"},
    "now_lbl_gha": {"fr": "GHA (Greenwich)", "nl": "GHA (Greenwich)", "en": "GHA (Greenwich)"},
    "now_lbl_dsp": {"fr": "Jours depuis le p\u00e9rig\u00e9e", "nl": "Dagen sinds perigeum", "en": "Days since perigee"},
    "now_lbl_days": {"fr": "jours", "nl": "dagen", "en": "days"},
    "col_day_time": {"fr": "Heure", "nl": "Tijd", "en": "Time"},
    "col_az": {"fr": "AZ", "nl": "AZ", "en": "AZ"},
    "col_el": {"fr": "EL", "nl": "EL", "en": "EL"},
    "col_day_distance": {"fr": "Distance", "nl": "Afstand", "en": "Distance"},
    "col_day_doppler": {
        "fr": "Doppler ({freq})",
        "nl": "Doppler ({freq})",
        "en": "Doppler ({freq})",
    },
    "col_day_spread": {
        "fr": "Spread ({freq})",
        "nl": "Spread ({freq})",
        "en": "Spread ({freq})",
    },
    "col_day_tsky": {"fr": "TSky", "nl": "TSky", "en": "TSky"},
    "col_day_dgr": {"fr": "DGR", "nl": "DGR", "en": "DGR"},
    "col_day_libration": {"fr": "Libration", "nl": "Libratie", "en": "Libration"},
    "col_day_ms": {"fr": "Moon-Sun", "nl": "Maan-Zon", "en": "Moon-Sun"},
    "col_day_pl_extra": {"fr": "PL extra", "nl": "PL extra", "en": "PL extra"},
    "col_day_decl": {"fr": "D\u00e9cl.", "nl": "Decl.", "en": "Decl."},
    "col_day_lha": {"fr": "LHA", "nl": "LHA", "en": "LHA"},
    "col_day_sun_az": {"fr": "Sun AZ", "nl": "Zon AZ", "en": "Sun AZ"},
    "col_day_sun_el": {"fr": "Sun EL", "nl": "Zon EL", "en": "Sun EL"},
    "col_phase": {"fr": "Phase", "nl": "Fase", "en": "Phase"},

    # ── Ligne MAINTENANT ──
    "now_label": {"fr": "\u25cf MAINTENANT", "nl": "\u25cf NU", "en": "\u25cf NOW"},
    "now_label_off": {"fr": "\u25cb MAINTENANT", "nl": "\u25cb NU", "en": "\u25cb NOW"},
    "now_visible": {"fr": "VISIBLE", "nl": "ZICHTBAAR", "en": "VISIBLE"},
    "now_below": {"fr": "sous horizon", "nl": "onder horizon", "en": "below horizon"},

    # ── Messages ──
    "msg_locator_missing_title": {"fr": "Locator manquant", "nl": "Locator ontbreekt", "en": "Missing locator"},
    "msg_locator_missing": {
        "fr": "Entrez votre QRA locator (6 ou 8 caract\u00e8res).\nExemple : JO20BM85",
        "nl": "Voer uw QRA locator in (6 of 8 tekens).\nVoorbeeld: JO20BM85",
        "en": "Enter your QRA locator (6 or 8 characters).\nExample: JO20BM85",
    },
    "msg_locator_short_title": {"fr": "Locator trop court", "nl": "Locator te kort", "en": "Locator too short"},
    "msg_locator_short": {
        "fr": (
            "Le locator doit avoir au minimum 6 caract\u00e8res.\n\n"
            "Un locator \u00e0 4 caract\u00e8res (ex: JO20) couvre une zone de\n"
            "~200\u00d7110 km, ce qui entra\u00eene des erreurs de plusieurs\n"
            "minutes sur les heures de lever/coucher de la Lune.\n\n"
            "Utilisez votre locator \u00e0 6 caract\u00e8res (pr\u00e9cision ~5 km)\n"
            "ou 8 caract\u00e8res (pr\u00e9cision ~800 m).\n\n"
            "Exemple : JO20BM ou JO20BM85"
        ),
        "nl": (
            "De locator moet minimaal 6 tekens bevatten.\n\n"
            "Een locator van 4 tekens (bv: JO20) beslaat een gebied van\n"
            "~200\u00d7110 km, wat fouten van meerdere minuten veroorzaakt\n"
            "bij de opkomst/ondergang van de Maan.\n\n"
            "Gebruik uw locator van 6 tekens (nauwkeurigheid ~5 km)\n"
            "of 8 tekens (nauwkeurigheid ~800 m).\n\n"
            "Voorbeeld: JO20BM of JO20BM85"
        ),
        "en": (
            "The locator must have at least 6 characters.\n\n"
            "A 4-character locator (e.g. JO20) covers an area of\n"
            "~200\u00d7110 km, causing errors of several minutes\n"
            "in moonrise/moonset times.\n\n"
            "Use your 6-character locator (accuracy ~5 km)\n"
            "or 8-character locator (accuracy ~800 m).\n\n"
            "Example: JO20BM or JO20BM85"
        ),
    },
    "msg_locator_invalid_title": {"fr": "Locator invalide", "nl": "Ongeldige locator", "en": "Invalid locator"},
    "msg_export": {"fr": "Export", "nl": "Export", "en": "Export"},
    "msg_no_data": {"fr": "Aucune donn\u00e9e.", "nl": "Geen gegevens.", "en": "No data."},
    "msg_saved": {"fr": "Sauvegard\u00e9 : {path}", "nl": "Opgeslagen: {path}", "en": "Saved: {path}"},
    "msg_error": {"fr": "Erreur", "nl": "Fout", "en": "Error"},
    "msg_error_calc": {"fr": "Erreur calcul", "nl": "Berekeningsfout", "en": "Calculation error"},
    "msg_error_pdf": {"fr": "Erreur PDF", "nl": "PDF-fout", "en": "PDF error"},
    "msg_lang_restart": {
        "fr": "Le changement de langue prendra effet au red\u00e9marrage.",
        "nl": "De taalwijziging wordt van kracht na herstart.",
        "en": "Language change will take effect on restart.",
    },

    # ── Phases lunaires (noms longs) ──
    "phase_new": {"fr": "Nouvelle Lune", "nl": "Nieuwe Maan", "en": "New Moon"},
    "phase_full": {"fr": "Pleine Lune", "nl": "Volle Maan", "en": "Full Moon"},
    "phase_fq": {"fr": "Premier Quartier", "nl": "Eerste Kwartier", "en": "First Quarter"},
    "phase_lq": {"fr": "Dernier Quartier", "nl": "Laatste Kwartier", "en": "Last Quarter"},
    "phase_wax_cres": {"fr": "Premier Croissant", "nl": "Wassende Sikkel", "en": "Waxing Crescent"},
    "phase_wax_gibb": {"fr": "Gibbeuse Croissante", "nl": "Wassende Maan", "en": "Waxing Gibbous"},
    "phase_wan_gibb": {"fr": "Gibbeuse D\u00e9croissante", "nl": "Afnemende Maan", "en": "Waning Gibbous"},
    "phase_wan_cres": {"fr": "Dernier Croissant", "nl": "Afnemende Sikkel", "en": "Waning Crescent"},

    # ── Phases lunaires (noms courts, table) ──
    "phase_s_new": {"fr": "Nouvelle", "nl": "Nieuw", "en": "New"},
    "phase_s_full": {"fr": "Pleine", "nl": "Vol", "en": "Full"},
    "phase_s_fq": {"fr": "Prem.Q.", "nl": "Eerste K.", "en": "1st Q."},
    "phase_s_lq": {"fr": "Dern.Q.", "nl": "Laatste K.", "en": "Last Q."},
    "phase_s_wax_cres": {"fr": "Croiss.", "nl": "Was.S.", "en": "Wax.Cr."},
    "phase_s_wax_gibb": {"fr": "Gibb.C.", "nl": "Was.M.", "en": "Wax.Gi."},
    "phase_s_wan_gibb": {"fr": "Gibb.D.", "nl": "Afn.M.", "en": "Wan.Gi."},
    "phase_s_wan_cres": {"fr": "Dern.Cr.", "nl": "Afn.S.", "en": "Wan.Cr."},

    # ── Jours de la semaine (courts) ──
    "day_0": {"fr": "Lun", "nl": "Ma", "en": "Mon"},
    "day_1": {"fr": "Mar", "nl": "Di", "en": "Tue"},
    "day_2": {"fr": "Mer", "nl": "Wo", "en": "Wed"},
    "day_3": {"fr": "Jeu", "nl": "Do", "en": "Thu"},
    "day_4": {"fr": "Ven", "nl": "Vr", "en": "Fri"},
    "day_5": {"fr": "Sam", "nl": "Za", "en": "Sat"},
    "day_6": {"fr": "Dim", "nl": "Zo", "en": "Sun"},

    # ── Mois (courts) ──
    "mon_1": {"fr": "Jan", "nl": "Jan", "en": "Jan"},
    "mon_2": {"fr": "F\u00e9v", "nl": "Feb", "en": "Feb"},
    "mon_3": {"fr": "Mar", "nl": "Mrt", "en": "Mar"},
    "mon_4": {"fr": "Avr", "nl": "Apr", "en": "Apr"},
    "mon_5": {"fr": "Mai", "nl": "Mei", "en": "May"},
    "mon_6": {"fr": "Juin", "nl": "Jun", "en": "Jun"},
    "mon_7": {"fr": "Juil", "nl": "Jul", "en": "Jul"},
    "mon_8": {"fr": "Ao\u00fbt", "nl": "Aug", "en": "Aug"},
    "mon_9": {"fr": "Sep", "nl": "Sep", "en": "Sep"},
    "mon_10": {"fr": "Oct", "nl": "Okt", "en": "Oct"},
    "mon_11": {"fr": "Nov", "nl": "Nov", "en": "Nov"},
    "mon_12": {"fr": "D\u00e9c", "nl": "Dec", "en": "Dec"},

    # ── Fen\u00eatre Aide ──
    "help_title": {"fr": "Aide \u2014 Moon Predictions", "nl": "Help \u2014 Moon Predictions", "en": "Help \u2014 Moon Predictions"},
    "help_content": {
        "fr": (
            "<h2 style='color: #FFD700;'>Comment utiliser Moon Predictions</h2>"
            "<h3 style='color: #66aaff;'>1. Configuration de la station</h3>"
            "<p>Renseignez votre <b>indicatif</b> (optionnel), votre <b>QRA locator</b> "
            "(6 ou 8 caract\u00e8res, ex: JO20CL) et votre <b>altitude</b> en m\u00e8tres. "
            "Cliquez <b>Sauvegarder</b> pour conserver ces informations.</p>"
            "<h3 style='color: #66aaff;'>2. Calcul des passages</h3>"
            "<p>Cliquez <b>Calculer</b> pour afficher les passages de la Lune "
            "au-dessus de l'horizon sur <b>30 jours</b>. "
            "Utilisez les boutons <b>1-30 j</b> / <b>31-60 j</b> pour naviguer.</p>"
            "<h3 style='color: #66aaff;'>3. Filtres</h3>"
            "<p>Ajustez les curseurs <b>EL min</b> et <b>Score min</b> pour "
            "ne garder que les meilleurs passages.</p>"
            "<p><b>EL min = votre horizon m\u00e9canique</b> : si votre "
            "parabole ne descend pas sous 25\u00b0 (obstacle, mont\u00e2ge), "
            "r\u00e9glez EL min \u00e0 25\u00b0. Les heures de lever/coucher "
            "affich\u00e9es seront recalcul\u00e9es au moment o\u00f9 la Lune "
            "franchit votre horizon utile, et la dur\u00e9e correspondra \u00e0 "
            "votre temps d'op\u00e9ration r\u00e9el. "
            "\u00c0 0\u00b0, comportement astronomique classique.</p>"
            "<h3 style='color: #66aaff;'>4. Comprendre la table</h3>"
            "<ul>"
            "<li><b>EL max</b> : \u00e9l\u00e9vation maximale de la Lune pendant le passage</li>"
            "<li><b>Distance</b> : distance Terre-Lune (p\u00e9rig\u00e9e ~356 500 km = meilleur signal)</li>"
            "<li><b>Extra PL</b> : perte suppl\u00e9mentaire vs p\u00e9rig\u00e9e (0 dB = optimal)</li>"
            "<li><b>Moon-Sun</b> : angle Lune-Soleil (&gt; 15\u00b0 = pas de bruit solaire)</li>"
            "<li><b>Libration</b> : taux de libration \u2014 "
            "<span style='color:#44ff44;'>vert</span> = signal propre, "
            "<span style='color:#ff4444;'>rouge</span> = signal \u00e9tal\u00e9. "
            "<b>Critique \u00e0 10 GHz et au-dessus !</b></li>"
            "<li><b>Spread</b> : \u00e9talement Doppler du signal r\u00e9fl\u00e9chi en Hz</li>"
            "<li><b>Qualit\u00e9</b> : score global 0-10 combinant tous les facteurs</li>"
            "</ul>"
            "<h3 style='color: #66aaff;'>5. Score de qualit\u00e9</h3>"
            "<p>Le score s'adapte \u00e0 la <b>fr\u00e9quence</b> s\u00e9lectionn\u00e9e :<br>"
            "- En <b>VHF/UHF</b> (&lt; 1 GHz) : \u00e9l\u00e9vation et dur\u00e9e dominent<br>"
            "- En <b>micro-ondes</b> (\u2265 1 GHz) : la <b>libration</b> devient le facteur "
            "le plus important (30% du score)</p>"
            "<h3 style='color: #66aaff;'>6. Export</h3>"
            "<p>Exportez vos pr\u00e9visions en <b>TXT</b> ou <b>PDF</b> "
            "pour les partager ou les imprimer. "
            "Le PDF s'ouvre automatiquement apr\u00e8s g\u00e9n\u00e9ration.</p>"
            "<h3 style='color: #66aaff;'>7. Th\u00e8me clair / sombre</h3>"
            "<p>Cliquez sur le bouton <b>\u2600 / \u263d</b> (en haut \u00e0 droite) "
            "pour basculer entre le th\u00e8me <b>sombre</b> et le th\u00e8me <b>clair</b>. "
            "Les couleurs EME (vert/orange/rouge) sont adapt\u00e9es \u00e0 chaque th\u00e8me "
            "pour rester bien lisibles. Le choix est sauvegard\u00e9 automatiquement.</p>"
            "<h3 style='color: #66aaff;'>8. D\u00e9tail d'un passage (clic sur une ligne)</h3>"
            "<p>Cliquez sur n'importe quelle <b>ligne de passage</b> "
            "pour ouvrir une fen\u00eatre listant, <b>toutes les 30 minutes</b>, "
            "tous les param\u00e8tres : AZ, EL, distance, Doppler, Spread, "
            "TSky, DGR, libration, angle Moon-Sun. C'est l'\u00e9quivalent "
            "de la vue Sked Maker (GM4JJJ) pour un op\u00e9rateur solo.</p>"
            "<h3 style='color: #66aaff;'>9. D\u00e9tail MAINTENANT (clic sur la premi\u00e8re ligne)</h3>"
            "<p>Cliquez sur la ligne <b>MAINTENANT</b> (1\u00e8re ligne du tableau) "
            "pour ouvrir une fen\u00eatre tableau de bord temps-r\u00e9el "
            "avec la position actuelle de la Lune et <b>tous les param\u00e8tres EME</b> : "
            "<ul>"
            "<li><b>DGR (D\u00e9gradation)</b> : perte totale en dB par rapport aux "
            "conditions optimales (combine path loss + bruit de ciel + bruit de Lune)</li>"
            "<li><b>TSky</b> : temp\u00e9rature de bruit de ciel derri\u00e8re la Lune. "
            "Monte pr\u00e8s du plan galactique et du centre galactique (Sagittaire)</li>"
            "<li><b>Doppler central / Home Echo</b> : d\u00e9calage en fr\u00e9quence "
            "de votre propre \u00e9cho (2\u00d7 aller-retour). Essentiel pour savoir "
            "o\u00f9 r\u00e9gler votre r\u00e9cepteur. \u00c0 10 GHz, varie de \u00b130 kHz "
            "sur un passage</li>"
            "<li><b>LHA / GHA</b> : angles horaires local et de Greenwich</li>"
            "<li><b>Jours depuis p\u00e9rig\u00e9e</b> : position dans le cycle "
            "anomalistique de 27,55 jours</li>"
            "</ul></p>"
            "<p style='color: #888;'>Survolez les en-t\u00eates de colonnes "
            "pour des explications d\u00e9taill\u00e9es.</p>"
        ),
        "nl": (
            "<h2 style='color: #FFD700;'>Hoe Moon Predictions te gebruiken</h2>"
            "<h3 style='color: #66aaff;'>1. Stationsinstellingen</h3>"
            "<p>Vul uw <b>roepnaam</b> (optioneel), uw <b>QRA locator</b> "
            "(6 of 8 tekens, bv: JO20CL) en uw <b>hoogte</b> in meters in. "
            "Klik op <b>Opslaan</b> om deze informatie te bewaren.</p>"
            "<h3 style='color: #66aaff;'>2. Berekening</h3>"
            "<p>Klik op <b>Berekenen</b> om de maanpassages boven de horizon "
            "over <b>30 dagen</b> weer te geven. "
            "Gebruik de knoppen <b>1-30 d</b> / <b>31-60 d</b> om te navigeren.</p>"
            "<h3 style='color: #66aaff;'>3. Filters</h3>"
            "<p>Pas de schuifregelaars <b>EL min</b> en <b>Score min</b> aan "
            "om alleen de beste passages te behouden.</p>"
            "<p><b>EL min = uw mechanische horizon</b>: als uw schotel niet "
            "onder 25\u00b0 kan (obstakel, montage), stel EL min in op 25\u00b0. "
            "De weergegeven opkomst/ondergang-tijden worden herberekend op "
            "het moment dat de Maan uw nuttige horizon kruist, en de duur "
            "komt overeen met uw werkelijke operatietijd. "
            "Bij 0\u00b0: klassiek astronomisch gedrag.</p>"
            "<h3 style='color: #66aaff;'>4. De tabel begrijpen</h3>"
            "<ul>"
            "<li><b>EL max</b>: maximale elevatie van de Maan tijdens de passage</li>"
            "<li><b>Afstand</b>: Aarde-Maan afstand (perigeum ~356.500 km = best signaal)</li>"
            "<li><b>Extra PL</b>: extra verlies t.o.v. perigeum (0 dB = optimaal)</li>"
            "<li><b>Maan-Zon</b>: hoek Maan-Zon (&gt; 15\u00b0 = geen zonsruis)</li>"
            "<li><b>Libratie</b>: libratiesnelheid \u2014 "
            "<span style='color:#44ff44;'>groen</span> = schoon signaal, "
            "<span style='color:#ff4444;'>rood</span> = verspreid signaal. "
            "<b>Kritisch bij 10 GHz en hoger!</b></li>"
            "<li><b>Spread</b>: Doppler-spreiding van het gereflecteerde signaal in Hz</li>"
            "<li><b>Kwaliteit</b>: globale score 0-10</li>"
            "</ul>"
            "<h3 style='color: #66aaff;'>5. Kwaliteitsscore</h3>"
            "<p>De score past zich aan de geselecteerde <b>frequentie</b> aan:<br>"
            "- In <b>VHF/UHF</b> (&lt; 1 GHz): elevatie en duur domineren<br>"
            "- In <b>microgolven</b> (\u2265 1 GHz): <b>libratie</b> wordt de "
            "belangrijkste factor (30% van de score)</p>"
            "<h3 style='color: #66aaff;'>6. Export</h3>"
            "<p>Exporteer uw voorspellingen als <b>TXT</b> of <b>PDF</b>. "
            "De PDF wordt automatisch geopend na generatie.</p>"
            "<h3 style='color: #66aaff;'>7. Licht / donker thema</h3>"
            "<p>Klik op de <b>\u2600 / \u263d</b> knop (rechtsboven) "
            "om te wisselen tussen het <b>donkere</b> en het <b>lichte</b> thema. "
            "De EME-kleuren (groen/oranje/rood) zijn aangepast per thema "
            "voor goede leesbaarheid. Uw keuze wordt automatisch opgeslagen.</p>"
            "<h3 style='color: #66aaff;'>8. Passage detail (klik op een regel)</h3>"
            "<p>Klik op een <b>passageregel</b> om een venster te openen met, "
            "<b>elke 30 minuten</b>, alle parameters: AZ, EL, afstand, Doppler, "
            "Spread, TSky, DGR, libratie, Maan-Zon hoek. Dit is het equivalent "
            "van de Sked Maker weergave (GM4JJJ) voor een solo operator.</p>"
            "<h3 style='color: #66aaff;'>9. NU detail (klik op de eerste regel)</h3>"
            "<p>Klik op de regel <b>NU</b> (eerste regel van de tabel) "
            "om een realtime dashboard te openen met de huidige maanpositie "
            "en <b>alle EME-parameters</b>:"
            "<ul>"
            "<li><b>DGR (Degradatie)</b>: totaal verlies in dB t.o.v. optimale "
            "omstandigheden (path loss + hemelruis + maanruis)</li>"
            "<li><b>TSky</b>: ruistemperatuur van de hemel achter de Maan. "
            "Stijgt bij het galactisch vlak en galactisch centrum (Boogschutter)</li>"
            "<li><b>Centrale Doppler / Home Echo</b>: frequentieverschuiving "
            "van uw eigen echo (2\u00d7 heen-en-terug). Essentieel voor "
            "ontvangerafstemming. Bij 10 GHz varieert het \u00b130 kHz over een passage</li>"
            "<li><b>LHA / GHA</b>: lokale en Greenwich uurhoeken</li>"
            "<li><b>Dagen sinds perigeum</b>: positie in de anomalistische "
            "cyclus van 27,55 dagen</li>"
            "</ul></p>"
            "<p style='color: #888;'>Beweeg over de kolomkoppen voor uitleg.</p>"
        ),
        "en": (
            "<h2 style='color: #FFD700;'>How to use Moon Predictions</h2>"
            "<h3 style='color: #66aaff;'>1. Station setup</h3>"
            "<p>Enter your <b>callsign</b> (optional), your <b>QRA locator</b> "
            "(6 or 8 characters, e.g. JO20CL) and your <b>altitude</b> in meters. "
            "Click <b>Save</b> to store this information.</p>"
            "<h3 style='color: #66aaff;'>2. Computation</h3>"
            "<p>Click <b>Compute</b> to display moon passes above the horizon "
            "over <b>30 days</b>. "
            "Use the <b>1-30 d</b> / <b>31-60 d</b> buttons to navigate.</p>"
            "<h3 style='color: #66aaff;'>3. Filters</h3>"
            "<p>Adjust the <b>EL min</b> and <b>Score min</b> sliders to "
            "keep only the best passes.</p>"
            "<p><b>EL min = your mechanical horizon</b>: if your dish can't "
            "go below 25\u00b0 (obstacle, mount), set EL min to 25\u00b0. "
            "The displayed rise/set times will be recomputed at the moment "
            "the Moon crosses your usable horizon, and the duration will "
            "match your actual operating time. "
            "At 0\u00b0: standard astronomical behavior.</p>"
            "<h3 style='color: #66aaff;'>4. Understanding the table</h3>"
            "<ul>"
            "<li><b>EL max</b>: maximum elevation of the Moon during the pass</li>"
            "<li><b>Distance</b>: Earth-Moon distance (perigee ~356,500 km = best signal)</li>"
            "<li><b>Extra PL</b>: additional loss vs perigee (0 dB = optimal)</li>"
            "<li><b>Moon-Sun</b>: Moon-Sun angle (&gt; 15\u00b0 = no solar noise)</li>"
            "<li><b>Libration</b>: libration rate \u2014 "
            "<span style='color:#44ff44;'>green</span> = clean signal, "
            "<span style='color:#ff4444;'>red</span> = spread signal. "
            "<b>Critical at 10 GHz and above!</b></li>"
            "<li><b>Spread</b>: Doppler spread of reflected signal in Hz</li>"
            "<li><b>Quality</b>: overall score 0-10</li>"
            "</ul>"
            "<h3 style='color: #66aaff;'>5. Quality score</h3>"
            "<p>The score adapts to the selected <b>frequency</b>:<br>"
            "- In <b>VHF/UHF</b> (&lt; 1 GHz): elevation and duration dominate<br>"
            "- In <b>microwave</b> (\u2265 1 GHz): <b>libration</b> becomes the "
            "most important factor (30% of the score)</p>"
            "<h3 style='color: #66aaff;'>6. Export</h3>"
            "<p>Export your predictions as <b>TXT</b> or <b>PDF</b>. "
            "The PDF opens automatically after generation.</p>"
            "<h3 style='color: #66aaff;'>7. Light / dark theme</h3>"
            "<p>Click the <b>\u2600 / \u263d</b> button (top right) "
            "to switch between the <b>dark</b> and <b>light</b> theme. "
            "EME colors (green/orange/red) are adapted per theme "
            "for readability. Your choice is saved automatically.</p>"
            "<h3 style='color: #66aaff;'>8. Pass detail (click on a row)</h3>"
            "<p>Click any <b>pass row</b> to open a window listing, "
            "<b>every 30 minutes</b>, all parameters: AZ, EL, distance, Doppler, "
            "Spread, TSky, DGR, libration, Moon-Sun angle. This is the "
            "equivalent of the Sked Maker (GM4JJJ) view for a solo operator.</p>"
            "<h3 style='color: #66aaff;'>9. NOW detail (click on the first row)</h3>"
            "<p>Click the <b>NOW</b> row (first row of the table) "
            "to open a real-time dashboard with the current Moon position "
            "and <b>all EME parameters</b>:"
            "<ul>"
            "<li><b>DGR (Degradation)</b>: total dB loss vs optimal conditions "
            "(path loss + sky noise + Moon noise combined)</li>"
            "<li><b>TSky</b>: sky noise temperature behind the Moon. "
            "Rises near the galactic plane and galactic center (Sagittarius)</li>"
            "<li><b>Central Doppler / Home Echo</b>: frequency shift of your "
            "own echo (2\u00d7 round-trip). Essential to tune your receiver. "
            "At 10 GHz, varies by \u00b130 kHz over a pass</li>"
            "<li><b>LHA / GHA</b>: local and Greenwich hour angles</li>"
            "<li><b>Days since perigee</b>: position in the 27.55-day "
            "anomalistic cycle</li>"
            "</ul></p>"
            "<p style='color: #888;'>Hover column headers for detailed explanations.</p>"
        ),
    },

    # ── Fen\u00eatre About ──
    "about_title": {"fr": "About \u2014 Moon Predictions", "nl": "Over \u2014 Moon Predictions", "en": "About \u2014 Moon Predictions"},
    "about_desc": {
        "fr": "Pr\u00e9vision des passages lunaires pour les<br>radioamateurs pratiquant l'EME (Earth-Moon-Earth).",
        "nl": "Voorspelling van maanpassages voor<br>radioamateurs die EME (Earth-Moon-Earth) beoefenen.",
        "en": "Lunar pass forecasting for<br>amateur radio operators practicing EME (Earth-Moon-Earth).",
    },
    "about_author": {"fr": "<b>Auteur :</b>", "nl": "<b>Auteur :</b>", "en": "<b>Author:</b>"},
    "about_dev": {"fr": "<b>D\u00e9veloppement :</b>", "nl": "<b>Ontwikkeling :</b>", "en": "<b>Development:</b>"},
    "about_ephem": {"fr": "<b>\u00c9ph\u00e9m\u00e9rides :</b>", "nl": "<b>Efemerides :</b>", "en": "<b>Ephemerides:</b>"},
    "about_icon": {"fr": "<b>Ic\u00f4ne :</b>", "nl": "<b>Icoon :</b>", "en": "<b>Icon:</b>"},
    "about_thanks": {
        "fr": "<b>Remerciements :</b>",
        "nl": "<b>Met dank aan :</b>",
        "en": "<b>Thanks to:</b>",
    },
    "about_thanks_text": {
        "fr": "Eric ON5TA et Michel ON7FI<br>pour leurs retours experts et suggestions d'am\u00e9lioration",
        "nl": "Eric ON5TA en Michel ON7FI<br>voor hun deskundige feedback en verbetersuggesties",
        "en": "Eric ON5TA and Michel ON7FI<br>for their expert feedback and improvement suggestions",
    },
    "about_license": {"fr": "<b>Licence :</b> GNU GPL v3 \u2014 Open Source", "nl": "<b>Licentie :</b> GNU GPL v3 \u2014 Open Source", "en": "<b>License:</b> GNU GPL v3 \u2014 Open Source"},
    "btn_close": {"fr": "Fermer", "nl": "Sluiten", "en": "Close"},
    "btn_apply": {"fr": "Appliquer", "nl": "Toepassen", "en": "Apply"},
    "btn_cancel": {"fr": "Annuler", "nl": "Annuleren", "en": "Cancel"},

    # ── Export PDF / TXT ──
    "exp_period": {
        "fr": "Période : jours {period}",
        "nl": "Periode : dagen {period}",
        "en": "Period: days {period}",
    },
    "exp_frequency": {
        "fr": "Fréquence : {freq}",
        "nl": "Frequentie : {freq}",
        "en": "Frequency: {freq}",
    },
    "exp_filters": {
        "fr": "Filtres",
        "nl": "Filters",
        "en": "Filters",
    },
    "exp_el_min_none": {
        "fr": "EL min : aucun",
        "nl": "EL min : geen",
        "en": "EL min: none",
    },
    "exp_score_min_none": {
        "fr": "Score min : aucun",
        "nl": "Score min : geen",
        "en": "Score min: none",
    },
    "exp_phase_yes": {"fr": "Phase : oui", "nl": "Fase : ja", "en": "Phase: yes"},
    "exp_phase_no": {"fr": "Phase : non", "nl": "Fase : nee", "en": "Phase: no"},
    "exp_passes_shown": {
        "fr": "{n}/{total} passage{s} affiché{s}",
        "nl": "{n}/{total} doorgang{en} weergegeven",
        "en": "{n}/{total} pass{es} shown",
    },
    "exp_footer": {
        "fr": "Réf. périgée : 356 500 km | Score = f(élévation, durée, distance, moon-sun) | Calculs : Skyfield + JPL DE440s",
        "nl": "Ref. perigeum : 356 500 km | Score = f(elevatie, duur, afstand, maan-zon) | Berekening : Skyfield + JPL DE440s",
        "en": "Ref. perigee: 356,500 km | Score = f(elevation, duration, distance, moon-sun) | Calculations: Skyfield + JPL DE440s",
    },
    "exp_generated": {
        "fr": "Généré : {time}",
        "nl": "Gegenereerd : {time}",
        "en": "Generated: {time}",
    },
    "exp_col_date": {"fr": "Date", "nl": "Datum", "en": "Date"},
    "exp_col_rise": {"fr": "Lever", "nl": "Opkomst", "en": "Rise"},
    "exp_col_set": {"fr": "Coucher", "nl": "Ondergang", "en": "Set"},
    "exp_col_duration": {"fr": "Durée", "nl": "Duur", "en": "Duration"},
    "exp_col_el_max": {"fr": "EL max", "nl": "EL max", "en": "EL max"},
    "exp_col_el_max_time": {"fr": "H. EL max", "nl": "Tijd EL max", "en": "EL max time"},
    "exp_col_az_rise": {"fr": "AZ lever", "nl": "AZ opkomst", "en": "AZ rise"},
    "exp_col_az_set": {"fr": "AZ couch.", "nl": "AZ onderg.", "en": "AZ set"},
    "exp_col_decl": {"fr": "Décl.", "nl": "Decl.", "en": "Decl."},
    "exp_col_distance": {"fr": "Distance", "nl": "Afstand", "en": "Distance"},
    "exp_col_extra_pl": {"fr": "Extra PL", "nl": "Extra PL", "en": "Extra PL"},
    "exp_col_total_pl": {"fr": "Total PL ({freq})", "nl": "Totaal PL ({freq})", "en": "Total PL ({freq})"},
    "exp_col_moon_sun": {"fr": "Moon-Sun", "nl": "Maan-Zon", "en": "Moon-Sun"},
    "exp_col_spread_min": {"fr": "Spread min ({freq})", "nl": "Spread min ({freq})", "en": "Spread min ({freq})"},
    "exp_col_spread_max": {"fr": "Spread max ({freq})", "nl": "Spread max ({freq})", "en": "Spread max ({freq})"},
    "exp_col_quality": {"fr": "Qualité", "nl": "Kwaliteit", "en": "Quality"},
    "exp_col_phase": {"fr": "Phase", "nl": "Fase", "en": "Phase"},
    "exp_file_filter_txt": {"fr": "Texte (*.txt)", "nl": "Tekst (*.txt)", "en": "Text (*.txt)"},

    "btn_conventions": {"fr": "Conventions", "nl": "Conventies", "en": "Conventions"},
}


# ════════════════════════════════════════════
# Chargement des infobulles externes (tooltips/*.json)
# ════════════════════════════════════════════

def _load_tooltips():
    """Charge tooltips/fr.json, nl.json, en.json et les fusionne dans _STRINGS.

    Chaque fichier contient {cle_tip: "texte"}.
    Les cl\u00e9s commen\u00e7ant par '_' (ex: _comment) sont ignor\u00e9es.
    """
    base = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tooltips")
    if not os.path.isdir(base):
        return
    for lang in ("fr", "nl", "en"):
        path = os.path.join(base, f"{lang}.json")
        if not os.path.isfile(path):
            continue
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            print(f"[i18n] Erreur lecture {path}: {e}")
            continue
        for key, text in data.items():
            if key.startswith("_"):
                continue
            entry = _STRINGS.setdefault(key, {})
            entry[lang] = text


_load_tooltips()


def set_language(lang: str):
    """D\u00e9finit la langue active (fr, nl, en)."""
    global _LANG
    if lang in ("fr", "nl", "en"):
        _LANG = lang


def get_language() -> str:
    """Retourne la langue active."""
    return _LANG


def tr(key: str, **kwargs) -> str:
    """Retourne la cha\u00eene traduite pour la cl\u00e9 donn\u00e9e.

    Les kwargs sont format\u00e9s dans la cha\u00eene (ex: tr("info_result", count=5)).
    """
    entry = _STRINGS.get(key)
    if entry is None:
        return f"[{key}]"
    text = entry.get(_LANG, entry.get("en", f"[{key}]"))
    if kwargs:
        try:
            text = text.format(**kwargs)
        except (KeyError, IndexError):
            pass
    return text
