# Swiss cantons: ortId 1–26 (standard two-letter codes)
CANTON_TO_ORT_ID: dict[str, int] = {
    "ZH": 1,   # Zürich
    "BE": 2,   # Bern
    "LU": 3,   # Luzern
    "UR": 4,   # Uri
    "SZ": 5,   # Schwyz
    "OW": 6,   # Obwalden
    "NW": 7,   # Nidwalden
    "GL": 8,   # Glarus
    "ZG": 9,   # Zug
    "FR": 10,  # Fribourg
    "SO": 11,  # Solothurn
    "BS": 12,  # Basel-Stadt
    "BL": 13,  # Basel-Landschaft
    "SH": 14,  # Schaffhausen
    "AR": 15,  # Appenzell Ausserrhoden
    "AI": 16,  # Appenzell Innerrhoden
    "SG": 17,  # St. Gallen
    "GR": 18,  # Graubünden
    "AG": 19,  # Aargau
    "TG": 20,  # Thurgau
    "TI": 21,  # Ticino
    "VD": 22,  # Vaud
    "VS": 23,  # Valais
    "NE": 24,  # Neuchâtel
    "GE": 25,  # Genève
    "JU": 26,  # Jura
}

VALID_CANTONS = frozenset(CANTON_TO_ORT_ID.keys())
