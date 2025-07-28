import os, re, json
import numpy as np
import matplotlib.pyplot as plt
from collections import Counter

def generate_zipf_plot():
    # --- CONFIGURATION ---
    with open('/content/drive/Shareddrives/Sanskrit-Data/unique_token_dictionary.json', 'r', encoding='utf-8') as f:
        token_frequency = json.load(f)

    # --- SORT BY FREQUENCY DESC ---
    frequencies = sorted(token_frequency.values(), reverse=True)
    ranks = np.arange(1, len(frequencies) + 1)

    # --- PLOT ZIPF'S LAW GRAPH ---
    s = 1.0                  # Exponent in Zipf's law
    C = frequencies[0]       # Frequency of the most common token

    plt.figure(figsize=(10,6))
    plt.loglog(ranks, frequencies, marker=".", label="Sanskrit tokens")
    plt.title("Zipf's Law: Token Frequency vs Rank (log-log scale)")
    plt.xlabel("Rank of token")
    plt.ylabel("Frequency of token")
    plt.grid(True, which="both", ls="--", lw=0.5)
    ideal = C / ranks ** s
    plt.loglog(ranks, ideal, linestyle="-", color="red", alpha=0.5, label="Ideal ~1/r")
    plt.legend()
    plt.savefig('static/zipf_plot.png')
    plt.close()
