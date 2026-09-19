import io, sys, urllib.request, pandas as pd

def get(url, timeout=40):
    req = urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0"})
    return urllib.request.urlopen(req, timeout=timeout).read()

SOURCES = {
  "diabetes": [
     "https://raw.githubusercontent.com/plotly/datasets/master/diabetes.csv",
     "https://raw.githubusercontent.com/jbrownlee/Datasets/master/pima-indians-diabetes.data.csv",
  ],
  "heart": [
     "https://raw.githubusercontent.com/anikannal/predicting-heart-disease/master/heart.csv",
     "https://raw.githubusercontent.com/sharmaroshan/Heart-UCI-Dataset/master/heart.csv",
     "https://raw.githubusercontent.com/rashida048/Datasets/master/heart.csv",
  ],
  "stroke": [
     "https://raw.githubusercontent.com/rashida048/Datasets/master/healthcare-dataset-stroke-data.csv",
     "https://raw.githubusercontent.com/Mihir-ML/Stroke-Prediction/main/healthcare-dataset-stroke-data.csv",
     "https://raw.githubusercontent.com/GreatUncle/stroke/master/healthcare-dataset-stroke-data.csv",
  ],
}

for name, urls in SOURCES.items():
    ok=False
    for u in urls:
        try:
            raw = get(u)
            df = pd.read_csv(io.BytesIO(raw))
            df.to_csv(f"ml/data/{name}.csv", index=False)
            print(f"[OK] {name}: {u} -> shape {df.shape}; cols={list(df.columns)[:15]}")
            ok=True; break
        except Exception as e:
            print(f"[..] {name}: failed {u} ({type(e).__name__}: {str(e)[:80]})")
    if not ok:
        print(f"[XX] {name}: ALL SOURCES FAILED")
