from uefa.paths import RESOURCE_DIR as BASE_DIR, USER_DIR   # noqa: F401


APPEARANCE = "dark"         
COLOR_THEME = "dark-blue"    

WINDOW_TITLE = "UEFA Predictor"
START_WIDTH = 1180          
START_HEIGHT = 820
MIN_WIDTH = 980
MIN_HEIGHT = 660

# --- Paths ------------------------------------------------------------
IMAGES_DIR = BASE_DIR / "assets" / "images"
FLAGS_DIR = IMAGES_DIR / "flags"
COMPET_LOGOS_DIR = IMAGES_DIR / "compets"

FLAG_FILES = {
    "en": FLAGS_DIR / "UK_US_flag.png",
    "fr": FLAGS_DIR / "Flag_of_France.png",
}
COMP_FILES = {
    "UCL": COMPET_LOGOS_DIR / "UCL_logo.png",
    "UEL": COMPET_LOGOS_DIR / "UEL_logo.png",
    "UECL": COMPET_LOGOS_DIR / "UECL_logo.png",
}

# --- Palette per competition -----------------------------------------
COMP = {
    "UCL":  {"accent": "#3E7BFA", "accent_hover": "#2F62CC"},
    "UEL":  {"accent": "#E8833A", "accent_hover": "#C06A2C"},
    "UECL": {"accent": "#2FA96B", "accent_hover": "#248455"},   # the Conference green
}
DEFAULT_COMP = "UCL"
DEFAULT_LANG = "en"

MODES = ("draw", "simulate")
DEFAULT_MODE = "draw"

# --- UEFA associations ------------------------------------------------
# The 55 members, written as in data/processed/countries_filled_25.csv
# where the CSV already has an opinion ("Ireland", "Czechia", "Türkiye").
# This list is ONLY used to fill the drop-down of the "replace a club"
# box: the engine accepts any string, because the rule "two opponents at
# most per association" only compares strings for equality. A name that
# is not in the list therefore stays valid; it is just flagged.
UEFA_ASSOCIATIONS = (
    "Albania", "Andorra", "Armenia", "Austria", "Azerbaijan", "Belarus",
    "Belgium", "Bosnia and Herzegovina", "Bulgaria", "Croatia", "Cyprus",
    "Czechia", "Denmark", "England", "Estonia", "Faroe Islands", "Finland",
    "France", "Georgia", "Germany", "Gibraltar", "Greece", "Hungary",
    "Iceland", "Ireland", "Israel", "Italy", "Kazakhstan", "Kosovo",
    "Latvia", "Liechtenstein", "Lithuania", "Luxembourg", "Malta",
    "Moldova", "Montenegro", "Netherlands", "North Macedonia",
    "Northern Ireland", "Norway", "Poland", "Portugal", "Romania",
    "Russia", "San Marino", "Scotland", "Serbia", "Slovakia", "Slovenia",
    "Spain", "Sweden", "Switzerland", "Türkiye", "Ukraine", "Wales",
)

# --- Neutral colours --------------------------------------------------
# Always a (light, dark) pair: CTk switches by itself when the appearance
# mode changes. A plain colour would stay frozen.
BG = ("#EEF1F6", "#0A0C11")          # window background
SURFACE = ("#F6F8FB", "#0E1117")     # background of the views
SURFACE_2 = ("#E9EDF4", "#161A22")   # secondary blocks, table headers
CARD = ("#FFFFFF", "#141820")
CARD_HOVER = ("#F2F5FA", "#1B202B")
BORDER = ("#DDE2EB", "#242A36")
TEXT = ("#0F131A", "#EEF1F6")
TEXT_MUTED = ("#5A6272", "#8B93A5")   # contrast >= 4.5:1 on CARD, in both modes
TEXT_FAINT = ("#8A91A0", "#5E6678")   # text separators, zeros, never the only carrier of information

# Result colours: W / D / L, and the winner's gold.
WIN = ("#1E9A62", "#3CC486")
DRAW_C = ("#8A91A0", "#6B7385")
LOSS = ("#D04444", "#F06A6A")
GOLD = ("#B07F1F", "#E6BE5A")

# --- Spacing scale (px) -----------------------------------------------
# Every gap comes from this list: it is what gives a regular rhythm.
SPACE = {"xs": 4, "s": 8, "m": 12, "l": 16, "xl": 24, "xxl": 32}
RADIUS_S = 8
RADIUS_M = 12

CARD_RADIUS = 16

STRINGS = {
    "en": {
        "tagline": "Draw and simulation engine for the European nights",
        "step": "Step {n} of 3",
        "s_welcome": "Welcome",
        "s_draw": "Draw",
        "language_q": "Choose your language",
        "language_h": "The whole app will follow this choice.",
        "competition_q": "Choose a competition",
        "competition_h": "Every competition has its own draw rules.",
        "mode_q": "What do you want to run?",
        "mode_h": "Pick what the engine should produce, then start.",
        "UCL": "Champions League",
        "UEL": "Europa League",
        "UECL": "Conference League",
        "UCL_sub": "36 clubs  |  8 matchdays",
        "UEL_sub": "36 clubs  |  8 matchdays",
        "UECL_sub": "36 clubs  |  6 matchdays",
        "mode_draw": "Draw only",
        "mode_draw_d": "Build the league phase pairings, then stop.",
        "mode_simulate": "Draw + full simulation",
        "mode_simulate_d": "Draw, then predict every match through to the final.",
        "your_picks": "Your picks",
        "back": "Back",
        "start": "Start",
        "dark_mode": "Dark mode",
        "keys_hint": "Esc: back     Enter: continue",

        # --- screen 4: the draw ----------------------------------------
        "s_pots": "Pots",
        "pots_q": "Check the pots",
        "pots_h": "Click any club to replace it with one of your own.",
        "pots_h_ro": "These are the pots the engine will use.",
        "pot_n": "Pot {n}",
        "continue": "Continue",
        "replace_title": "Replace a club",
        "replace_h": "The new club keeps the same pot and the same slot.",
        "replace_current": "Leaving the draw",
        "f_name": "Club name",
        "f_country": "Association",
        "f_image": "Badge",
        "choose_image": "Choose an image",
        "no_image": "No image chosen",
        "confirm": "Replace",
        "cancel": "Cancel",
        "restore": "Undo the replacement",
        "err_name": "Give the club a name.",
        "err_dupe": "That name is already somewhere in the pots.",
        "err_country": "Give the club an association.",
        "err_image": "That file is not an image Pillow can open.",
        "swapped": "replaced",
        "swaps_n": "{n} replaced",
        "swap_hint": "{key} + click two clubs to swap them between pots.",
        "swap_pick2": "Now click the club that swaps places with {club}. Esc cancels.",
        "swap_done": "{a} and {b} have swapped places.",
        "moves_n": "{n} swap(s)",
        "err_swap_self": "Pick two different clubs.",
        "err_swap_same_pot": "Both clubs are in pot {pot}: swapping them changes nothing.",
        "swap_bad_title": "Swap refused",
        "err_swap_country": ("Pot {pot} would hold {k} clubs from {country}. With {m} "
                             "clubs from {country} in the competition, the draw could "
                             "not give each of them enough opponents from that pot."),
        "how_q": "How should the draw run?",
        "how_h": "Same fixtures either way. Only the reveal changes.",
        "run_instant": "All at once",
        "run_instant_d": "The whole league phase resolved in one go, no ceremony.",
        "run_live": "Live ceremony",
        "run_live_d": "Ball by ball, pot by pot, the way Monaco does it.",
        "drawing": "Drawing the league phase",
        "scheduling": "Splitting it into matchdays",
        "draw_failed": "The draw failed",
        "retry": "Try again",
        "stage_hint": "The software picks the opponents",
        "club_of": "Club {i} of {total}",
        "home": "Home",
        "away": "Away",
        "speed": "Speed",
        "pause": "Pause",
        "resume": "Resume",
        "skip": "Skip to the end",
        "results_q": "League phase drawn",
        "results_h": "{matches} matches over {days} matchdays.",
        "tab_matchdays": "Matchdays",
        "tab_clubs": "By club",
        "md_short": "MD{i}",
        "matchday_n": "Matchday {i}",
        "draw_again": "Draw again",
        "to_menu": "Back to the menu",
        "not_ready": "This competition has no pots yet.",

        # --- JSON template ----------------------------------------------
        "load_template": "Load a template",
        "tpl_title": "Load a pots template",
        "tpl_pick": "Choose a JSON template",
        "tpl_ok_title": "Template loaded",
        "tpl_ok": "{n} clubs read from {file}.",
        "tpl_bad_title": "Template refused",
        "tpl_bad": "Nothing was changed. {n} problem(s) found:",
        "tpl_warn": "Loaded anyway, but worth a look:",
        "close": "Close",
        "tpl_not_json": "This is not valid JSON: {detail}",
        "tpl_not_object": "The top level must be an object of pots, not {kind}.",
        "tpl_pot_count": "Expected {want} pots for the {comp}, found {got}.",
        "tpl_pot_unknown": "Unrecognised pot key: {name}. Write \"Pot 1\" to \"Pot {want}\".",
        "tpl_pot_missing": "Pot {n} is missing.",
        "tpl_pot_not_object": "Pot {n} must be an object of clubs, not {kind}.",
        "tpl_pot_size": "Pot {n} holds {got} clubs, expected {want}.",
        "tpl_total": "{got} clubs in total, expected {want}.",
        "tpl_club_blank": "Pot {n} has a club with a blank name.",
        "tpl_club_dupe": "{club} appears more than once.",
        "tpl_club_not_object": "{club} must be an object with Country and Image.",
        "tpl_no_country": "{club} has no Country.",
        "tpl_no_image_key": "{club} has no Image key. Use \"\" if it has no badge.",
        "tpl_image_missing": "{club}: no file at {path}",
        "tpl_image_bad": "{club}: Pillow cannot open {path}",
        "tpl_w_country": "{club}: {country} is not a UEFA association I know.",
        "tpl_w_no_badge": "{club}: no badge given, initials will be used.",

        # --- save a template --------------------------------------------
        "save_template": "Save these pots",
        "sv_ok_title": "Template saved",
        "sv_ok": "{n} clubs written to {file}.",
        "sv_bad_title": "Nothing was saved",
        "sv_bad": "The file could not be written:",
        "sv_failed": "{detail}",
        "sv_w_copied": "{n} imported badge(s) copied into badges/{folder}/.",
        "sv_w_no_badge": "{n} club(s) have no badge on disk, saved with an empty Image.",
        "sv_w_gone": "{club}: {path} has disappeared, saved with an empty Image.",

        # --- constraints -------------------------------------------------
        # A constraint is an ORDERED pair (host, guest): the first club
        # does not host the second. The reverse remains allowed.
        "cst_btn": "Constraints",
        "cst_btn_n": "Constraints ({n})",
        "cst_title": "Forbidden home fixtures",
        "cst_h": "The club on the left will never host the club on the right. The reverse fixture stays legal.",
        "cst_host": "Home club",
        "cst_guest": "Never receives",
        "cst_add": "Add",
        "cst_none": "No constraint. Every fixture is allowed.",
        "cst_count": "{n} constraint(s) in force.",
        "cst_bad_title": "Constraints refused",
        "cst_bad": "Nothing was changed. {n} problem(s) in the constraints:",
        "err_cst_unknown": "That club is not in the pots.",
        "err_cst_self": "A club cannot play itself.",
        "err_cst_dupe": "That constraint is already there.",
        "tpl_cst_not_list": "\"constraints\" must be a list of pairs, not {kind}.",
        "tpl_cst_pair": "Constraint {n} must be a pair of two club names, not {kind}.",
        "tpl_cst_name": "Constraint {n}: a club name must be a non-empty string, not {kind}.",
        "tpl_cst_unknown": "Constraint {n}: {club} is not in the pots.",

        # --- screen 5: the simulation -----------------------------------
        "s_sim": "Simulation",
        "simulate_btn": "Simulate the season",
        "sim_setup_q": "Set up the simulation",
        "sim_setup_h": "Every match is predicted by the logistic regression on the Elo gap. Choose how two-legged ties are settled.",
        "sim_method": "Two-legged ties",
        "sim_m_legs": "Leg results",
        "sim_m_legs_d": "Win = 1, draw = 0.5 per leg. Level after two legs: a penalty shoot-out whose winner is weighted by the Elo expected score.",
        "sim_m_aggregate": "Aggregate goals",
        "sim_m_aggregate_d": "Goals added over both legs, like the real rule. Level: extra time, then a shoot-out kicked one penalty at a time.",
        "sim_m_oneshot": "One-shot probability",
        "sim_m_oneshot_d": "No legs. P(A goes through) = p_A / (p_A + p_B), one random draw per tie.",
        "sim_default_tag": "DEFAULT",
        "sim_expert_short": "Expert mode",
        "sim_runs_big": "10 000 seasons run on every processor core.",
        "sim_mc_rate": "{rate:,.0f} seasons per second",
        "sim_champion_over": "CHAMPIONS  ·  {comp}",
        "sim_final_line": "Beat {opp} {score} in the final",
        "sim_final_aet": ", after extra time",
        "sim_final_pens": ", {a}-{b} on penalties",
        "stat_matches": "Matches",
        "stat_time": "Run time",
        "stat_method": "Two-leg method",
        "stat_seed": "Seed",
        "col_form": "Form",
        "form_letters": "WDL",
        "ko_hint": "Click any tie to see how it was decided.",
        "tie_leg1": "First leg",
        "tie_leg2": "Second leg",
        "tie_final": "Final, neutral venue",
        "tie_et": "Extra time",
        "tie_pens": "Penalties",
        "tie_first": "{club} kicked first",
        "tie_through": "{club} go through",
        "tie_champions": "{club} are champions",
        "tie_legs_pts": "Leg points {a}-{b}",
        "tie_agg": "Aggregate {a}-{b}",
        "tie_oneshot": "No legs played. P({club} goes through) = {p:.1%}",
        "tie_elo_pick": "Level on leg points: the Elo expected score gave {club} a {p:.0%} chance of winning the shoot-out.",
        "probs_sort": "Click a column header to sort.",
        "sim_expert": "Expert mode: log every operation",
        "sim_expert_h": "Ratings, x, z, probabilities, the random number, the scoreline and the Elo step of every match.",
        "sim_runs": "Monte Carlo",
        "sim_runs_0": "Off",
        "sim_runs_n": "{n} seasons",
        "sim_runs_h": "Replays the whole tournament N times to estimate each club's chances.",
        "sim_seed": "Seed (optional)",
        "sim_seed_h": "Same seed, same season. Leave blank for a new one.",
        "sim_run": "Run",
        "sim_model_line": "Classifier: {rows} matches, seasons {seasons}. Holdout log loss {ll:.3f} (no skill {ns:.3f}).",
        "sim_model_missing": "The classifier weights are missing. Run: python -m model.predictor --train",
        "simulating": "Playing the season",
        "sim_mc_progress": "Monte Carlo: season {i} of {n}",
        "sim_failed": "The simulation failed",
        "sim_champion": "Champions: {club}",
        "sim_results_h": "{matches} matches in {ms} ms  |  two-leg method: {method}  |  seed {seed}",
        "tab_table": "Table",
        "tab_knockout": "Knockout",
        "tab_probs": "Probabilities",
        "tab_expert": "Expert",
        "col_club": "Club",
        "zone_r16": "1-8: round of 16",
        "zone_po": "9-24: play-offs",
        "zone_out": "25-36: out",
        "ko_playoff": "Knockout play-offs",
        "ko_r16": "Round of 16",
        "ko_qf": "Quarter-finals",
        "ko_sf": "Semi-finals",
        "ko_final": "Final",
        "ko_leg": "leg {n}",
        "ko_agg": "agg {a}-{b}",
        "ko_legs": "legs {a}-{b}",
        "ko_aet": "aet {a}-{b}",
        "ko_pens": "won {a}-{b} on pens",
        "ko_oneshot": "P = {p:.3f}",
        "probs_h": "Share of {n} simulated seasons in which the club reached each stage.",
        "probs_off": "Monte Carlo was off. Run again with a number of seasons to see the probabilities.",
        "probs_pts": "Pts",
        "p_top8": "Top 8",
        "p_top24": "Top 24",
        "p_r16": "R16",
        "p_qf": "QF",
        "p_sf": "SF",
        "p_final": "Final",
        "p_winner": "Win",
        "expert_h": "{n} lines. Type to filter.",
        "expert_off": "Expert mode was off for this run. Switch it on in the settings and run again.",
        "expert_filter": "Filter",
        "sim_again": "Run again",
        "sim_settings": "Settings",
        "sim_save": "Save the log",
        "sim_saved_title": "Log saved",
        "sim_saved": "Written to {file}.",
        "sim_save_bad_title": "Nothing was saved",
        "sim_not_found": "{club}: not in the Elo file, started at 1500.",
    },
    "fr": {
        "tagline": "Moteur de tirage et de simulation des soirées européennes",
        "step": "Étape {n} sur 3",
        "s_welcome": "Bienvenue",
        "s_draw": "Tirage",
        "language_q": "Choisis ta langue",
        "language_h": "Toute l'application suivra ce choix.",
        "competition_q": "Choisis une compétition",
        "competition_h": "Chaque compétition a ses propres règles de tirage.",
        "mode_q": "Que veux-tu lancer ?",
        "mode_h": "Choisis ce que le moteur doit produire, puis lance.",
        "UCL": "Ligue des champions",
        "UEL": "Ligue Europa",
        "UECL": "Ligue Conférence",
        "UCL_sub": "36 clubs  |  8 journées",
        "UEL_sub": "36 clubs  |  8 journées",
        "UECL_sub": "36 clubs  |  6 journées",
        "mode_draw": "Tirage seul",
        "mode_draw_d": "Construit les affiches de la phase de ligue, puis s'arrête.",
        "mode_simulate": "Tirage + simulation complète",
        "mode_simulate_d": "Tirage, puis prédiction de chaque match jusqu'à la finale.",
        "your_picks": "Tes choix",
        "back": "Retour",
        "start": "Commencer",
        "dark_mode": "Mode sombre",
        "keys_hint": "Échap : retour     Entrée : continuer",

        # --- screen 4: the draw ----------------------------------------
        "s_pots": "Chapeaux",
        "pots_q": "Vérifie les chapeaux",
        "pots_h": "Clique sur un club pour le remplacer par le tien.",
        "pots_h_ro": "Voici les chapeaux que le moteur va utiliser.",
        "pot_n": "Chapeau {n}",
        "continue": "Continuer",
        "replace_title": "Remplacer un club",
        "replace_h": "Le nouveau club garde le même chapeau et la même place.",
        "replace_current": "Quitte le tirage",
        "f_name": "Nom du club",
        "f_country": "Fédération",
        "f_image": "Écusson",
        "choose_image": "Choisir une image",
        "no_image": "Aucune image choisie",
        "confirm": "Remplacer",
        "cancel": "Annuler",
        "restore": "Annuler le remplacement",
        "err_name": "Donne un nom au club.",
        "err_dupe": "Ce nom est déjà quelque part dans les chapeaux.",
        "err_country": "Donne une fédération au club.",
        "err_image": "Pillow n'arrive pas à ouvrir ce fichier.",
        "swapped": "remplacé",
        "swaps_n": "{n} remplacé(s)",
        "swap_hint": "{key} + clic sur deux clubs pour les échanger de chapeau.",
        "swap_pick2": "Clic maintenant sur le club qui prend la place de {club}. Échap annule.",
        "swap_done": "{a} et {b} ont échangé leur place.",
        "moves_n": "{n} échange(s)",
        "err_swap_self": "Choisir deux clubs différents.",
        "err_swap_same_pot": "Les deux clubs sont dans le chapeau {pot} : les échanger ne change rien.",
        "swap_bad_title": "Échange refusé",
        "err_swap_country": ("Le chapeau {pot} aurait {k} clubs de la fédération {country}. "
                             "Avec {m} clubs de cette fédération dans la compétition, le "
                             "tirage ne pourrait plus leur trouver assez d'adversaires dans ce chapeau."),
        "how_q": "Comment lancer le tirage ?",
        "how_h": "Les mêmes affiches dans les deux cas. Seule la révélation change.",
        "run_instant": "Tout d'un coup",
        "run_instant_d": "Toute la phase de ligue résolue d'un seul coup, sans cérémonie.",
        "run_live": "Cérémonie en direct",
        "run_live_d": "Boule par boule, chapeau par chapeau, comme à Monaco.",
        "drawing": "Tirage de la phase de ligue",
        "scheduling": "Répartition en journées",
        "draw_failed": "Le tirage a échoué",
        "retry": "Réessayer",
        "stage_hint": "Le logiciel choisit les adversaires",
        "club_of": "Club {i} sur {total}",
        "home": "Domicile",
        "away": "Extérieur",
        "speed": "Vitesse",
        "pause": "Pause",
        "resume": "Reprendre",
        "skip": "Aller à la fin",
        "results_q": "Phase de ligue tirée",
        "results_h": "{matches} matchs sur {days} journées.",
        "tab_matchdays": "Journées",
        "tab_clubs": "Par club",
        "md_short": "J{i}",
        "matchday_n": "Journée {i}",
        "draw_again": "Retirer au sort",
        "to_menu": "Retour au menu",
        "not_ready": "Cette compétition n'a pas encore de chapeaux.",

        # --- JSON template ----------------------------------------------
        "load_template": "Charger un modèle",
        "tpl_title": "Charger un modèle de chapeaux",
        "tpl_pick": "Choisir un modèle JSON",
        "tpl_ok_title": "Modèle chargé",
        "tpl_ok": "{n} clubs lus dans {file}.",
        "tpl_bad_title": "Modèle refusé",
        "tpl_bad": "Rien n'a été changé. {n} problème(s) trouvé(s) :",
        "tpl_warn": "Chargé quand même, mais à vérifier :",
        "close": "Fermer",
        "tpl_not_json": "Ce n'est pas du JSON valide : {detail}",
        "tpl_not_object": "Le niveau du haut doit être un objet de chapeaux, pas {kind}.",
        "tpl_pot_count": "Il faut {want} chapeaux pour la {comp}, il y en a {got}.",
        "tpl_pot_unknown": "Clé de chapeau inconnue : {name}. Écris \"Pot 1\" à \"Pot {want}\".",
        "tpl_pot_missing": "Le chapeau {n} manque.",
        "tpl_pot_not_object": "Le chapeau {n} doit être un objet de clubs, pas {kind}.",
        "tpl_pot_size": "Le chapeau {n} contient {got} clubs, il en faut {want}.",
        "tpl_total": "{got} clubs en tout, il en faut {want}.",
        "tpl_club_blank": "Le chapeau {n} contient un club sans nom.",
        "tpl_club_dupe": "{club} apparaît plusieurs fois.",
        "tpl_club_not_object": "{club} doit être un objet avec Country et Image.",
        "tpl_no_country": "{club} n'a pas de Country.",
        "tpl_no_image_key": "{club} n'a pas de clé Image. Mets \"\" s'il n'a pas d'écusson.",
        "tpl_image_missing": "{club} : aucun fichier à {path}",
        "tpl_image_bad": "{club} : Pillow n'arrive pas à ouvrir {path}",
        "tpl_w_country": "{club} : {country} n'est pas une fédération UEFA que je connais.",
        "tpl_w_no_badge": "{club} : pas d'écusson fourni, les initiales seront utilisées.",

        # --- save a template --------------------------------------------
        "save_template": "Enregistrer ces chapeaux",
        "sv_ok_title": "Modèle enregistré",
        "sv_ok": "{n} clubs écrits dans {file}.",
        "sv_bad_title": "Rien n'a été enregistré",
        "sv_bad": "Le fichier n'a pas pu être écrit :",
        "sv_failed": "{detail}",
        "sv_w_copied": "{n} écusson(s) importé(s) copié(s) dans badges/{folder}/.",
        "sv_w_no_badge": "{n} club(s) sans écusson sur le disque, Image laissée vide.",
        "sv_w_gone": "{club} : {path} a disparu, Image laissée vide.",

        # --- constraints -------------------------------------------------
        "cst_btn": "Contraintes",
        "cst_btn_n": "Contraintes ({n})",
        "cst_title": "Affiches interdites à domicile",
        "cst_h": "Le club de gauche ne recevra jamais celui de droite. Le match retour, lui, reste permis.",
        "cst_host": "Club à domicile",
        "cst_guest": "Ne reçoit jamais",
        "cst_add": "Ajouter",
        "cst_none": "Aucune contrainte. Toutes les affiches sont permises.",
        "cst_count": "{n} contrainte(s) en vigueur.",
        "cst_bad_title": "Contraintes refusées",
        "cst_bad": "Rien n'a été changé. {n} problème(s) dans les contraintes :",
        "err_cst_unknown": "Ce club n'est pas dans les chapeaux.",
        "err_cst_self": "Un club ne joue pas contre lui-même.",
        "err_cst_dupe": "Cette contrainte existe déjà.",
        "tpl_cst_not_list": "\"constraints\" doit être une liste de paires, pas {kind}.",
        "tpl_cst_pair": "La contrainte {n} doit être une paire de deux noms de clubs, pas {kind}.",
        "tpl_cst_name": "Contrainte {n} : un nom de club doit être une chaîne non vide, pas {kind}.",
        "tpl_cst_unknown": "Contrainte {n} : {club} n'est pas dans les chapeaux.",

        # --- screen 5: the simulation -----------------------------------
        "s_sim": "Simulation",
        "simulate_btn": "Simuler la saison",
        "sim_setup_q": "Règle la simulation",
        "sim_setup_h": "Chaque match est prédit par la régression logistique sur l'écart d'Elo. Choisis comment trancher les matchs aller-retour.",
        "sim_method": "Matchs aller-retour",
        "sim_m_legs": "Résultat des manches",
        "sim_m_legs_d": "Victoire = 1, nul = 0,5 par manche. Égalité après deux manches : une séance de tirs au but dont le vainqueur est pondéré par le score attendu Elo.",
        "sim_m_aggregate": "Buts cumulés",
        "sim_m_aggregate_d": "Les buts des deux manches s'additionnent, comme la vraie règle. Égalité : prolongation, puis tirs au but, un par un.",
        "sim_m_oneshot": "Probabilité unique",
        "sim_m_oneshot_d": "Pas de manches. P(A passe) = p_A / (p_A + p_B), un seul tirage par confrontation.",
        "sim_default_tag": "PAR DÉFAUT",
        "sim_expert_short": "Mode expert",
        "sim_runs_big": "10 000 saisons tournent sur tous les cœurs du processeur.",
        "sim_mc_rate": "{rate:,.0f} saisons par seconde",
        "sim_champion_over": "CHAMPION  ·  {comp}",
        "sim_final_line": "Vainqueur de {opp} {score} en finale",
        "sim_final_aet": ", après prolongation",
        "sim_final_pens": ", {a}-{b} aux tirs au but",
        "stat_matches": "Matchs",
        "stat_time": "Durée",
        "stat_method": "Aller-retour",
        "stat_seed": "Graine",
        "col_form": "Forme",
        "form_letters": "VND",
        "ko_hint": "Clique sur une confrontation pour voir comment elle s'est jouée.",
        "tie_leg1": "Match aller",
        "tie_leg2": "Match retour",
        "tie_final": "Finale, terrain neutre",
        "tie_et": "Prolongation",
        "tie_pens": "Tirs au but",
        "tie_first": "{club} a tiré en premier",
        "tie_through": "{club} qualifié",
        "tie_champions": "{club} champion",
        "tie_legs_pts": "Points des manches {a}-{b}",
        "tie_agg": "Cumul {a}-{b}",
        "tie_oneshot": "Aucune manche jouée. P({club} passe) = {p:.1%}",
        "tie_elo_pick": "Égalité aux points : le score attendu Elo donnait à {club} {p:.0%} de chances de gagner la séance.",
        "probs_sort": "Clique sur un en-tête de colonne pour trier.",
        "sim_expert": "Mode expert : journal de chaque opération",
        "sim_expert_h": "Cotes, x, z, probabilités, le nombre aléatoire, le score et le pas Elo de chaque match.",
        "sim_runs": "Monte Carlo",
        "sim_runs_0": "Désactivé",
        "sim_runs_n": "{n} saisons",
        "sim_runs_h": "Rejoue tout le tournoi N fois pour estimer les chances de chaque club.",
        "sim_seed": "Graine (facultatif)",
        "sim_seed_h": "Même graine, même saison. Vide pour en tirer une nouvelle.",
        "sim_run": "Lancer",
        "sim_model_line": "Classifieur : {rows} matchs, saisons {seasons}. Log loss sur la saison test {ll:.3f} (sans modèle {ns:.3f}).",
        "sim_model_missing": "Les poids du classifieur manquent. Lance : python -m model.predictor --train",
        "simulating": "La saison se joue",
        "sim_mc_progress": "Monte Carlo : saison {i} sur {n}",
        "sim_failed": "La simulation a échoué",
        "sim_champion": "Champion : {club}",
        "sim_results_h": "{matches} matchs en {ms} ms  |  aller-retour : {method}  |  graine {seed}",
        "tab_table": "Classement",
        "tab_knockout": "Phase finale",
        "tab_probs": "Probabilités",
        "tab_expert": "Expert",
        "col_club": "Club",
        "zone_r16": "1-8 : huitièmes",
        "zone_po": "9-24 : barrages",
        "zone_out": "25-36 : éliminés",
        "ko_playoff": "Barrages",
        "ko_r16": "Huitièmes de finale",
        "ko_qf": "Quarts de finale",
        "ko_sf": "Demi-finales",
        "ko_final": "Finale",
        "ko_leg": "manche {n}",
        "ko_agg": "cumul {a}-{b}",
        "ko_legs": "manches {a}-{b}",
        "ko_aet": "a.p. {a}-{b}",
        "ko_pens": "gagné {a}-{b} aux t.a.b.",
        "ko_oneshot": "P = {p:.3f}",
        "probs_h": "Part des {n} saisons simulées où le club atteint chaque étape.",
        "probs_off": "Le Monte Carlo était désactivé. Relance avec un nombre de saisons pour voir les probabilités.",
        "probs_pts": "Pts",
        "p_top8": "Top 8",
        "p_top24": "Top 24",
        "p_r16": "8es",
        "p_qf": "Quarts",
        "p_sf": "Demis",
        "p_final": "Finale",
        "p_winner": "Titre",
        "expert_h": "{n} lignes. Tape pour filtrer.",
        "expert_off": "Le mode expert était désactivé pour ce lancement. Active-le dans les réglages et relance.",
        "expert_filter": "Filtrer",
        "sim_again": "Relancer",
        "sim_settings": "Réglages",
        "sim_save": "Enregistrer le journal",
        "sim_saved_title": "Journal enregistré",
        "sim_saved": "Écrit dans {file}.",
        "sim_save_bad_title": "Rien n'a été enregistré",
        "sim_not_found": "{club} : absent du fichier Elo, parti de 1500.",
    },
}
LANG_NAMES = {"en": "English", "fr": "Français"}

# --- Animations -------------------------------------------------------
TRANSITION = "slide_left"    # "slide_left" | "slide_right" | "fade" | "none"
TRANS_DURATION_MS = 300
HOVER_MS = 140


# =====================================================================
#  DRAW SCREEN
# =====================================================================
# Format of each competition. The engine already knows all of this, but
# the interface has to draw the grid of pots BEFORE any draw has been
# launched: hence this table, read when the view is built. It must stay
# consistent with model/draw_ucl.py and draw_uecl.py.
FORMAT = {
    "UCL":  {"pots": 4, "per_pot": 9, "opponents": 8, "matchdays": 8},
    "UEL":  {"pots": 4, "per_pot": 9, "opponents": 8, "matchdays": 8},
    "UECL": {"pots": 6, "per_pot": 6, "opponents": 6, "matchdays": 6},
}

# --- Draw screen colours ----------------------------------------------
# Same rule as above: always a (light, dark) pair, except when the colour
# is drawn into a Pillow image, which has no appearance mode and so takes
# a plain hex.
STAGE = ("#E4E9F2", "#0A0C11")        # background of the ceremony stage
POT_HEADER = ("#DCE2EE", "#222834")   # banner at the top of a pot
CHIP = ("#FFFFFF", "#191D25")         # a club at rest
CHIP_HOVER = ("#F0F3F9", "#222836")
CHIP_DRAWN = ("#E6EAF1", "#111419")   # club already drawn from the pot
CHIP_BORDER = ("#DCE1EB", "#272E3A")
CHIP_RADIUS = 10

HOME = ("#2E9E64", "#45C083")         # home fixture
AWAY = ("#D2762F", "#EC9A55")         # away fixture
REPLACED = ("#A9741A", "#E3B84F")     # "replaced club" badge

BALL_BODY = "#F6F8FC"                 # drawn by Pillow: plain hex
BALL_EDGE = "#C9D2E0"
BALL_TEXT = "#12151A"

# --- Ceremony pacing --------------------------------------------------
# All these durations are divided by the chosen speed (x1, x2, x4).
BALL_FLY_MS = 520        # the ball leaves the bowl and reaches the centre
BALL_OPEN_MS = 340       # the ball fades away, the club appears
OPPONENT_MS = 190        # each opponent settling into place
OPPONENT_GAP_MS = 90     # delay between two opponents
CLUB_HOLD_MS = 620       # reading time before the next ball
POT_BREAK_MS = 900       # breathing space between two pots
DRAW_SPEEDS = (0.5 ,1 , 2, 4)
DEFAULT_SPEED = 1

# --- Badge paths ------------------------------------------------------
CLUB_LOGOS_DIR = IMAGES_DIR / "clubs"     # clubs/UCL/, clubs/UEL/, clubs/UECL/
LOGO_SUFFIX = "_logo.png"

# --- Simulation screen ------------------------------------------------
ZONE_R16 = ("#2E9E64", "#45C083")     # ranks 1 to 8: straight to the round of 16
ZONE_PO = ("#A9741A", "#E3B84F")      # ranks 9 to 24: play-offs
ZONE_OUT = ("#9AA1AE", "#5B6270")     # ranks 25 to 36: eliminated
MC_RUNS = (0, 200, 1000, 10000)            # choice of the number of Monte Carlo seasons
