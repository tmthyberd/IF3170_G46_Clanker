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
│   ├── app/               # Aplikasi web interaktif 3D (Dash & Plotly)
│   └── core/              # Model data 3D, validator kendala, objective, moves
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── README.md
└── .gitignore
```

## Cara Menjalankan Program

### 1. Menjalankan WebApp

Install **docker** dan tinggal dijalankan dengan,
```
docker compose up --build
```

Atau bisa langsung menggunakan lingkungan Python tanpa container dengan
```
pip3 install -r requirements.txt
python3 src/app/app.py
```

Aplikasi dapat diakses melalui browser di `http://localhost:8080`


### 2. Menjalankan Unit Test Core
Untuk memverifikasi bahwa aplikasi dapat dijalankan untuk fungsionalitas 3D dan model dasar:
```bash
python -m src.app.app
```


## Pembagian Tugas Kelompok (3 Anggota)

| Anggota | NIM | Peran & Tanggung Jawab |
| :--- | :--- | :--- |
| **Daniel Anindito Nugroho** | 13524002 | 3D Interactive Visualizer, Plotting Engine, Simulated Annealing Algorithm. |
| **Muhammad Fatih Irkham Mauludi** | 13524004 | Genetic Algorithm (Chromosome, Crossover, Mutation, Selection), Benchmark Runner & Output Logging, Analisis Komparatif. |
| **Timothy Bernard Soeharto** | 13524092 | Core Architecture, 3D Constraint & Physics Engine, Move Operators, Hill-Climbing Algorithms (Steepest Ascent, Stochastic, Sideways Move, Random Restart). |
