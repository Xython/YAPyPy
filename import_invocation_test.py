# use yapypy run
from yapypy.extended_python import pycompat
pycompat.is_debug = True
from sklearn.datasets import load_iris
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import KFold
from sklearn.metrics import classification_report

rfc = RandomForestClassifier()
data = load_iris()
X = data.data
y = data.target

kf = KFold(5, shuffle=True)
for tr_idx, te_idx in kf.split(X):
    x1, x2, y1, y2 = X[tr_idx], X[te_idx], y[tr_idx], y[te_idx]
    rfc.fit(x1, y1)
    print(classification_report(y2, rfc.predict(x2)))
