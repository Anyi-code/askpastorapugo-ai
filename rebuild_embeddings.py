import pandas as pd
import json
from utils import get_embedding

FILE = "qa_dataset.csv"

print("🔄 Rebuilding embeddings...")

df = pd.read_csv(FILE).fillna("")

# Ensure embedding column exists
if "embedding" not in df.columns:
    df["embedding"] = ""

updated = 0

for i, row in df.iterrows():
    if row["embedding"]:
        continue  # skip already processed

    question = str(row["question"])

    print(f"Processing {i+1}/{len(df)}")

    emb = get_embedding(question)

    if emb:
        df.at[i, "embedding"] = json.dumps(emb)
        updated += 1

# Save updated file
df.to_csv(FILE, index=False)

print(f"✅ Done. {updated} embeddings added.")