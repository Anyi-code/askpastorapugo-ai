import pandas as pd

def clean_answer(text):
    text = str(text).strip()

    # Remove "Dear ..."
    if text.lower().startswith("dear"):
        if "," in text:
            text = text.split(",", 1)[-1].strip()

    # Remove closing
    text = text.replace("Remain blessed.", "").strip()

    return text  # 🔥 ONLY PURE CONTENT

df = pd.read_csv("qa_dataset.csv").fillna("")
df["answer"] = df["answer"].apply(clean_answer)
df.to_csv("qa_dataset.csv", index=False)

print("✅ Dataset cleaned to neutral format.")