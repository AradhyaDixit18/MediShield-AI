import io, urllib.request, pandas as pd
def get(url, t=45):
    req=urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0"})
    return urllib.request.urlopen(req, timeout=t).read()
cands=[
 "https://huggingface.co/datasets/Kubermatic/stroke-prediction/resolve/main/healthcare-dataset-stroke-data.csv",
 "https://huggingface.co/datasets/mstz/stroke/resolve/main/stroke.csv",
 "https://huggingface.co/datasets/scikit-learn/stroke-prediction/resolve/main/healthcare-dataset-stroke-data.csv",
 "https://raw.githubusercontent.com/datasciencedojo/datasets/master/healthcare-dataset-stroke-data.csv",
 "https://raw.githubusercontent.com/nchaudh1/stroke-prediction/master/healthcare-dataset-stroke-data.csv",
 "https://raw.githubusercontent.com/gy910210/stroke-prediction/master/healthcare-dataset-stroke-data.csv",
 "https://raw.githubusercontent.com/rohan-paul/MachineLearning-DeepLearning-Code-for-my-YouTube-Channel/master/Kaggle_Competitions/Stroke_Prediction/healthcare-dataset-stroke-data.csv",
]
done=False
for u in cands:
    try:
        raw=get(u); df=pd.read_csv(io.BytesIO(raw))
        cols=[c.lower() for c in df.columns]
        if "stroke" in cols:
            df.to_csv("ml/data/stroke.csv", index=False)
            print(f"[OK] {u} -> {df.shape}; cols={list(df.columns)}"); done=True; break
        print(f"[skip] {u} cols={list(df.columns)[:6]}")
    except Exception as e:
        print(f"[..] {u} ({type(e).__name__}: {str(e)[:60]})")
print("FOUND" if done else "STILL MISSING")
