
import numpy as np



def knee_threshold(scores):
    """
    Assumes scores are sorted descending.
    Finds the knee point using max deviation from straight line.
    """
    s = np.asarray(scores, dtype=float)
    n = len(s)
    x = np.linspace(0, 1, n)
    s_norm = (s - s.min()) / (s.max() - s.min() + 1e-12)
    line = s_norm[0] + (s_norm[-1] - s_norm[0]) * x
    idx = int(np.argmax(s_norm - line))
    return idx

def cumulative_mass_threshold(scores, mass=0.95):
    """
    Assumes scores are sorted descending.
    Returns threshold where cumulative sum reaches 'mass' fraction of total.
    """
    s = np.asarray(scores, dtype=float)
    fracs = np.cumsum(s) / sum(s)
    idx=sum(fracs<=mass)
    return idx-1
