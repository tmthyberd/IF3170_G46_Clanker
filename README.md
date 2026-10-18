# IF3170 Tugas Besar 1: 3D Bin Packing Optimization (Mejiro Express)

Program optimasi pemuatan peti kemas 3D (*3D Bin Packing Problem*) untuk logistik darat Mejiro Express menggunakan algoritma *Local Search*.

## Deskripsi Singkat
Permasalahan ini memodelkan penataan paket-paket kubus/balok ke dalam peti kemas truk dengan tujuan memaksimalkan nilai (*total value*) paket yang berhasil diangkut ke dalam truk tanpa melanggar batasan-batasan fisik:
1. **Dimensi Peti Kemas:** Seluruh paket dalam truk tidak boleh menembus dinding peti kemas.
2. **Tabrakan (Overlap):** Tidak boleh ada dua paket yang bertumpukan atau saling menembus di ruang 3D.
3. **Gravitasi & Support:** Kardus tidak boleh melayang; alas paket harus berada di lantai truk ($z=0$) atau didukung oleh permukaan atas paket lain.
4. **Barang Pecah Belah (*Fragile*):** Paket pecah belah tidak boleh diletakkan di bawah paket lain (tidak boleh menjadi penopang).
5. **Kapasitas Beban:** Total berat paket di dalam truk tidak boleh melebihi kapasitas maksimum truk (`MaxCapacity`).

## Struktur Direktori
```text
.
├── data/                  # File input kasus uji (JSON)
├── docs/                  # Laporan tugas besar (.pdf)
├── output/                # Hasil eksekusi algoritma (.json)
├── src/
│   ├── algorithms/        # Implementasi algoritma local search
│   │   ├── hill_climbing/
│   │   ├── simulated_annealing/
│   │   └── genetic_algorithm/
│   ├── core/              # Model data 3D, validator kendala, objective, moves
│   └── visualization/     # Visualisasi 3D dan plotting grafik
├── tests/                 # Unit test verifikasi sistem
├── README.md
└── .gitignore
```

## Persyaratan Lingkungan
- Python 3.10+
- Library pendukung (opsional / untuk visualisasi jika menggunakan visualizer grafis):
  ```bash
  pip install -r requirements.txt  # jika tersedia
  ```

## Cara Menjalankan Program

### 1. Menjalankan Unit Test Core
Untuk memverifikasi keabsahan mesin kendala 3D dan model dasar:
```bash
python -m unittest discover tests
```

### 2. Menjalankan Algoritma (CLI)
Contoh pemanggilan runner (disediakan per modul algoritma):
```bash
python -m src.core.models
```

## Pembagian Tugas Kelompok (3 Anggota)

| Anggota | NIM | Peran & Tanggung Jawab |
| :--- | :--- | :--- |
| **Anggota 1** | - | Core Architecture, 3D Constraint & Physics Engine, Move Operators, Hill-Climbing Algorithms (Steepest Ascent, Stochastic, Sideways Move, Random Restart). |
| **Anggota 2** | - | 3D Interactive Visualizer, Plotting Engine, Simulated Annealing Algorithm. |
| **Anggota 3** | - | Genetic Algorithm (Chromosome, Crossover, Mutation, Selection), Benchmark Runner & Output Logging, Analisis Komparatif. |
