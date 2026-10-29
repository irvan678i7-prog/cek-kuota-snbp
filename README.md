# SNBP Insight — Website Online

Website untuk memasukkan nilai rapor semester 1–5, TKA, membandingkan dua pilihan PTN/prodi, dan melihat grafik nilai. Data siswa disimpan di browser (localStorage), bukan di server.

## Deploy
Aktifkan GitHub Pages di Settings → Pages → Deploy from a branch → `main` / `(root)`.
Alamat website setelah diaktifkan: https://irvan678i7-prog.github.io/cek-kuota-snbp/

## Status data SNPMB
Saat ini `data/snbp.json` masih kosong. Tidak ada angka prodi fiktif. Data PTN/prodi dan peminat/daya tampung harus berasal dari sumber resmi yang diverifikasi sebelum dipublikasikan. Workflow GitHub Actions yang terpasang hanya memvalidasi format file JSON setiap hari, **belum** melakukan scraping atau pembaruan otomatis data SNPMB.

## Format dataset
`{"data":[{"tahun":2026,"ptn":"NAMA PTN","prodi":"NAMA PRODI","daya_tampung":40,"peminat":1500}],"source":"URL sumber terverifikasi","updated_at":"ISO 8601"}` — hanya contoh skema, bukan data faktual.

Rasio peminat/kuota bukan persentase peluang diterima. Keputusan SNBP ditentukan mekanisme resmi dan data seleksi yang tidak seluruhnya terbuka.
