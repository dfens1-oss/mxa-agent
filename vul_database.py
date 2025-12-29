import os
from rag.store import store_text

# 1. Pad naar je documenten
docs_map = "rag/docs"

print("Bezig met het vullen van de database...")

# 2. Check of de map bestaat
if not os.path.exists(docs_map):
    print(f"FOUT: De map {docs_map} bestaat niet!")
else:
    # 3. Loop door alle bestanden in die map
    bestanden = os.listdir(docs_map)
    for bestandsnaam in bestanden:
        if bestandsnaam.endswith(".txt"):  # Hij pakt nu alle .txt bestanden
            pad = os.path.join(docs_map, bestandsnaam)
            with open(pad, 'r', encoding='utf-8') as f:
                inhoud = f.read()
                # Zet de tekst in de database
                store_text(name=bestandsnaam, text=inhoud)
                print(f"✅ Toegevoegd: {bestandsnaam}")

print("\nKlaar! De database is nu gevuld.")