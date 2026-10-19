from __future__ import annotations
import os
from typing import Any, Dict, List, Optional
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def plot_ga_convergence(
    history_max: List[float],
    history_avg: List[float],
    title: str,
    output_path: str,
    x_label: str = "Iterasi (Generasi)",
    y_label: str = "Nilai Objective Function",
) -> str:
    """
    Membuat grafik konvergensi fitness maksimum dan rata-rata populasi terhadap iterasi.
    """
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

    fig, ax = plt.subplots(figsize=(9, 5), dpi=150)
    iterations = list(range(1, len(history_max) + 1))

    ax.plot(
        iterations,
        history_max,
        label="Fitness Maksimum (Best)",
        color="#1f77b4",
        linewidth=2.2,
    )

    ax.plot(
        iterations,
        history_avg,
        label="Fitness Rata-rata Populasi (Avg)",
        color="#ff7f0e",
        linewidth=1.8,
        linestyle="--",
    )

    ax.set_title(title, fontsize=13, fontweight="bold", pad=12)
    ax.set_xlabel(x_label, fontsize=11)
    ax.set_ylabel(y_label, fontsize=11)
    ax.grid(True, linestyle=":", alpha=0.6, color="#cccccc")
    ax.legend(loc="lower right", frameon=True, framealpha=0.9)

    plt.tight_layout()
    plt.savefig(output_path)
    plt.close(fig)

    return os.path.abspath(output_path)


def plot_parameter_analysis(
    summary_data: Dict[str, Any],
    output_path: str,
) -> str:
    """
    Membuat perbandingan grafik hasil eksperimen:
    1. Pengaruh Variasi Iterasi (Populasi Terkontrol)
    2. Pengaruh Variasi Populasi (Iterasi Terkontrol)
    """
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5), dpi=150)

    ctrl_pop = summary_data.get("control_population", {})
    pop_fixed = ctrl_pop.get("fixed_population", "N/A")
    runs_by_iter = ctrl_pop.get("variations", {})

    iter_keys = sorted([int(k) for k in runs_by_iter.keys()])
    avg_scores_iter = [runs_by_iter[str(k)]["mean_objective"] for k in iter_keys]
    avg_times_iter = [runs_by_iter[str(k)]["mean_duration"] for k in iter_keys]

    ax1.plot(iter_keys, avg_scores_iter, marker="o", color="#1f77b4", linewidth=2, label="Mean Objective")
    ax1.set_title(f"Kontrol Populasi (N = {pop_fixed})", fontsize=12, fontweight="bold")
    ax1.set_xlabel("Banyak Iterasi (Generasi)", fontsize=10)
    ax1.set_ylabel("Rata-rata Objective Akhir", fontsize=10, color="#1f77b4")
    ax1.grid(True, linestyle=":", alpha=0.6)

    ax1_twin = ax1.twinx()
    ax1_twin.plot(iter_keys, avg_times_iter, marker="s", color="#d62728", linestyle="--", label="Durasi (s)")
    ax1_twin.set_ylabel("Rata-rata Durasi (detik)", fontsize=10, color="#d62728")

    ctrl_gen = summary_data.get("control_generations", {})
    gen_fixed = ctrl_gen.get("fixed_generations", "N/A")
    runs_by_pop = ctrl_gen.get("variations", {})

    pop_keys = sorted([int(k) for k in runs_by_pop.keys()])
    avg_scores_pop = [runs_by_pop[str(k)]["mean_objective"] for k in pop_keys]
    avg_times_pop = [runs_by_pop[str(k)]["mean_duration"] for k in pop_keys]

    ax2.plot(pop_keys, avg_scores_pop, marker="o", color="#2ca02c", linewidth=2, label="Mean Objective")
    ax2.set_title(f"Kontrol Iterasi (Iterasi = {gen_fixed})", fontsize=12, fontweight="bold")
    ax2.set_xlabel("Jumlah Populasi", fontsize=10)
    ax2.set_ylabel("Rata-rata Objective Akhir", fontsize=10, color="#2ca02c")
    ax2.grid(True, linestyle=":", alpha=0.6)

    ax2_twin = ax2.twinx()
    ax2_twin.plot(pop_keys, avg_times_pop, marker="s", color="#9467bd", linestyle="--", label="Durasi (s)")
    ax2_twin.set_ylabel("Rata-rata Durasi (detik)", fontsize=10, color="#9467bd")

    plt.tight_layout()
    plt.savefig(output_path)
    plt.close(fig)

    return os.path.abspath(output_path)
