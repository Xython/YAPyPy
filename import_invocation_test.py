import yapypy.extended_python.pycompat as pycompat
pycompat.is_debug = True

from sklearn.ensemble import RandomForestClassifier
rfc = RandomForestClassifier()
print(rfc)
