import io, urllib.request, pandas as pd
def get(url, t=40):
    req=urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0"})
    return urllib.request.urlopen(req, timeout=t).read()
cands=[
 "https://raw.githubusercontent.com/education454/stroke_dataset/master/healthcare-dataset-stroke-data.csv",
 "https://raw.githubusercontent.com/priyanka-maz/machine-learning-stroke-prediction/main/healthcare-dataset-stroke-data.csv",
 "https://raw.githubusercontent.com/Chando0185/stroke_prediction/main/healthcare-dataset-stroke-data.csv",
 "https://raw.githubusercontent.com/kb22/Heart-Disease-Prediction/master/healthcare-dataset-stroke-data.csv",
 "https://raw.githubusercontent.com/sagnikghoshcr7/Stroke-Prediction/main/healthcare-dataset-stroke-data.csv",
 "https://raw.githubusercontent.com/plotly/datasets/master/stroke-data.csv",
 "https://raw.githubusercontent.com/vaitybharati/Dataset/master/healthcare-dataset-stroke-data.csv",
 "https://raw.githubusercontent.com/anujdutt9/Stroke-Prediction/master/healthcare-dataset-stroke-data.csv",
]
for u in cands:
    try:
        raw=get(u); df=pd.read_csv(io.BytesIO(raw))
        cols=[c.lower() for c in df.columns]
        if "stroke" in cols and "avg_glucose_level" in cols:
            df.to_csv("ml/data/stroke.csv", index=False)
            print(f"[OK] {u} -> {df.shape}; cols={list(df.columns)}"); break
        else:
            print(f"[skip wrong-cols] {u} cols={list(df.columns)[:6]}")
    except Exception as e:
        print(f"[..] {u} ({type(e).__name__})")
