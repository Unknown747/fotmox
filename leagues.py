# Sumber tunggal daftar liga. Format: nama: (id FotMob, slug)
LEAGUES = {
    "epl": (47, "premier-league"),
    "laliga": (87, "laliga"),
    "bundesliga": (54, "bundesliga"),
    "seriea": (55, "serie"),
    "ligue1": (53, "ligue-1"),
    "championship": (48, "championship"),
    "eredivisie": (57, "eredivisie"),
    "primeira": (61, "liga-portugal"),
    "belgia": (40, "pro-league"),
    "superlig": (71, "super-lig"),
    "skotlandia": (64, "premiership"),
}
KANDIDAT = {}

TIER_A = ["epl", "laliga", "bundesliga", "seriea", "ligue1"]

# Perkiraan kasar rata-rata gol/laga jangka panjang (dari ingatan, bukan hitungan data).
# Boleh kamu ubah kalau punya angka yang lebih akurat.
PRIOR_GPM = {
    "epl": 2.8, "laliga": 2.6, "bundesliga": 3.1, "seriea": 2.7, "ligue1": 2.8,
    "championship": 2.55, "eredivisie": 3.15, "primeira": 2.6,
    "belgia": 2.9, "superlig": 2.9, "skotlandia": 2.7,
}
W_PRIOR = 100      # bobot prior, setara 100 laga
HOME_SHARE = 0.55  # porsi gol kandang dari total gol laga

# kunci liga di The Odds API (sudah dicek dari daftar /v4/sports)
ODDS_KEYS = {
    "epl": "soccer_epl",
    "laliga": "soccer_spain_la_liga",
    "bundesliga": "soccer_germany_bundesliga",
    "seriea": "soccer_italy_serie_a",
    "ligue1": "soccer_france_ligue_one",
    "championship": "soccer_efl_champ",
    "eredivisie": "soccer_netherlands_eredivisie",
    "primeira": "soccer_portugal_primeira_liga",
    "belgia": "soccer_belgium_first_div",
    "superlig": "soccer_turkey_super_league",
    "skotlandia": "soccer_spl",
}
