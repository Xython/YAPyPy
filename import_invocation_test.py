import yapypy.extended_python.pycompat
from greet import Greet
import numpy as np


arr = np.array([1, 2, 3])
print(arr)

Greet.greet()

print(Greet.destruct({'yapypy': 'take away!'}))
