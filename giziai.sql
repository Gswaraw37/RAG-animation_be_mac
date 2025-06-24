-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Host: localhost:8889
-- Waktu pembuatan: 18 Jun 2025 pada 13.50
-- Versi server: 8.0.40
-- Versi PHP: 8.3.14

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `giziai`
--

-- --------------------------------------------------------

--
-- Struktur dari tabel `chat_logs`
--

CREATE TABLE `chat_logs` (
  `id` int NOT NULL,
  `session_uuid` varchar(255) NOT NULL,
  `user_query` text,
  `bot_response` text,
  `model_used` varchar(255) DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- --------------------------------------------------------

--
-- Struktur dari tabel `uploaded_files`
--

CREATE TABLE `uploaded_files` (
  `id` int NOT NULL,
  `filename` varchar(255) NOT NULL,
  `filepath` varchar(512) NOT NULL,
  `file_type` varchar(50) DEFAULT NULL,
  `uploaded_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `processed_at` timestamp NULL DEFAULT NULL,
  `uploader_id` int DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Dumping data untuk tabel `uploaded_files`
--

INSERT INTO `uploaded_files` (`id`, `filename`, `filepath`, `file_type`, `uploaded_at`, `processed_at`, `uploader_id`) VALUES
(1, '172231123666a86244b83fd8.51637104.pdf', './static/uploads/17eec525-3c84-443a-a9f0-801191cd4b4d_172231123666a86244b83fd8.51637104.pdf', 'pdf', '2025-06-10 01:52:09', '2025-06-10 02:01:45', 1),
(2, 'Konsep_Gizi_Lengkap_-_Knowledge_Base.pdf', './static/uploads/6e2ab412-a200-4989-bfd1-6e5391630542_Konsep_Gizi_Lengkap_-_Knowledge_Base.pdf', 'pdf', '2025-06-10 09:05:08', '2025-06-10 09:05:13', 1),
(3, 'BUKU_DASAR-DASAR_ILMU_GIZI_DALAM_KEPERAWATAN.pdf', './static/uploads/30b9f5bd-5c64-4b51-bdf5-61e13044a0fc_BUKU_DASAR-DASAR_ILMU_GIZI_DALAM_KEPERAWATAN.pdf', 'pdf', '2025-06-10 09:38:32', '2025-06-10 09:38:50', 1),
(4, 'UpayaPencegahanStuntingPadaBalitaReview1.pdf', './static/uploads/03210997-ecf8-41db-8d6b-d8567248e538_UpayaPencegahanStuntingPadaBalitaReview1.pdf', 'pdf', '2025-06-18 11:21:35', '2025-06-18 11:21:39', 1),
(5, '8.375.online.pdf', './static/uploads/26ccae51-4d81-480b-b4af-1d61d16a8596_8.375.online.pdf', 'pdf', '2025-06-18 11:21:50', '2025-06-18 11:21:53', 1),
(6, '28_PEDOMAN_GIZI_SEIMBANG.pdf', './static/uploads/43bfa8b6-1ab3-4fca-9ca9-990625d34a88_28_PEDOMAN_GIZI_SEIMBANG.pdf', 'pdf', '2025-06-18 11:22:26', '2025-06-18 11:22:40', 1),
(7, '51ec6e00992052910795e636c85e391d.pdf', './static/uploads/d880600a-f595-41d6-b5a8-c8dca81e7b6d_51ec6e00992052910795e636c85e391d.pdf', 'pdf', '2025-06-18 11:22:47', '2025-06-18 11:22:50', 1),
(8, '85-Article_Text-142-147-10-20170210.pdf', './static/uploads/458a3b94-9d1c-4045-839b-db16c9b15c89_85-Article_Text-142-147-10-20170210.pdf', 'pdf', '2025-06-18 11:23:00', '2025-06-18 11:23:02', 1),
(9, '179-Article_Text-1113-1-10-20200630.pdf', './static/uploads/84853fa5-d4e5-438a-b257-cf4ae24ce5a9_179-Article_Text-1113-1-10-20200630.pdf', 'pdf', '2025-06-18 11:23:12', '2025-06-18 11:23:14', 1),
(10, '316-1250-1-SP.docx', './static/uploads/f3aa135f-5299-41a9-adeb-084a995ced02_316-1250-1-SP.docx', 'docx', '2025-06-18 11:23:38', '2025-06-18 11:23:40', 1),
(11, '6681-Article_Text-21338-1-10-20240425.pdf', './static/uploads/7aed2540-6a43-463c-b4bf-674a5428670f_6681-Article_Text-21338-1-10-20240425.pdf', 'pdf', '2025-06-18 11:23:47', '2025-06-18 11:23:50', 1),
(12, '35397-77180-1-SP.docx', './static/uploads/2200dea3-2b47-4ec5-84a1-1fe088e3647f_35397-77180-1-SP.docx', 'docx', '2025-06-18 11:23:59', '2025-06-18 11:24:01', 1),
(13, 'Agropustaka.id_Buku-Saku_Panduan-Gizi-Seimbang-di-Masa-Pandemi-Kemenkes-RI.pdf', './static/uploads/88a52f8c-a2b1-41a8-8e06-ed6d74452aa0_Agropustaka.id_Buku-Saku_Panduan-Gizi-Seimbang-di-Masa-Pandemi-Kemenkes-RI.pdf', 'pdf', '2025-06-18 11:24:08', '2025-06-18 11:24:09', 1),
(14, 'Buku-Laporan-Teknis-SSGBI-OK.pdf', './static/uploads/a00a54b7-b02c-4335-a265-fd7d2929715c_Buku-Laporan-Teknis-SSGBI-OK.pdf', 'pdf', '2025-06-18 11:24:22', '2025-06-18 12:09:13', 1),
(15, 'JihanFauziah.pdf', './static/uploads/a9e38977-267a-4e19-83ab-d27cbd5aadc4_JihanFauziah.pdf', 'pdf', '2025-06-18 12:11:10', '2025-06-18 12:11:21', 1),
(16, 'Mayang_Nurma_Yesinta_1610104045_D4_Kebidanan_Naspub_-_Mayang_Nurma.pdf', './static/uploads/182a16a3-787a-45ae-b665-78a41b7d69f7_Mayang_Nurma_Yesinta_1610104045_D4_Kebidanan_Naspub_-_Mayang_Nurma.pdf', 'pdf', '2025-06-18 12:13:19', '2025-06-18 12:13:23', 1),
(17, 'PEDOMAN_PE_KLB_FINAL.pdf', './static/uploads/68c054d7-5111-419c-b956-5aa57c8b1a5f_PEDOMAN_PE_KLB_FINAL.pdf', 'pdf', '2025-06-18 12:13:39', '2025-06-18 12:14:32', 1),
(18, 'PGS_Ibu_Hamil_dan_Ibu_Menyusui_-_Merge-1.pdf', './static/uploads/5815eff4-e0d5-4179-9f4f-b8a43fe73172_PGS_Ibu_Hamil_dan_Ibu_Menyusui_-_Merge-1.pdf', 'pdf', '2025-06-18 12:14:42', '2025-06-18 12:15:11', 1),
(19, 'PMK_No._41_ttg_Pedoman_Gizi_Seimbang.pdf', './static/uploads/26290978-019f-4053-b9b7-33991464b390_PMK_No._41_ttg_Pedoman_Gizi_Seimbang.pdf', 'pdf', '2025-06-18 12:15:31', '2025-06-18 12:15:46', 1);

-- --------------------------------------------------------

--
-- Struktur dari tabel `users`
--

CREATE TABLE `users` (
  `id` int NOT NULL,
  `username` varchar(255) NOT NULL,
  `password_hash` varchar(255) NOT NULL,
  `is_admin` tinyint(1) DEFAULT '1',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Dumping data untuk tabel `users`
--

INSERT INTO `users` (`id`, `username`, `password_hash`, `is_admin`, `created_at`) VALUES
(1, 'admin', '$2b$12$OjrfiMOm45/tkeeGO5799eKCnzHrvQenxiZN7cEbOkaLe4AJqQBIW', 1, '2025-06-10 01:28:02');

--
-- Indexes for dumped tables
--

--
-- Indeks untuk tabel `chat_logs`
--
ALTER TABLE `chat_logs`
  ADD PRIMARY KEY (`id`);

--
-- Indeks untuk tabel `uploaded_files`
--
ALTER TABLE `uploaded_files`
  ADD PRIMARY KEY (`id`),
  ADD KEY `uploader_id` (`uploader_id`);

--
-- Indeks untuk tabel `users`
--
ALTER TABLE `users`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `username` (`username`);

--
-- AUTO_INCREMENT untuk tabel yang dibuang
--

--
-- AUTO_INCREMENT untuk tabel `chat_logs`
--
ALTER TABLE `chat_logs`
  MODIFY `id` int NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=23;

--
-- AUTO_INCREMENT untuk tabel `uploaded_files`
--
ALTER TABLE `uploaded_files`
  MODIFY `id` int NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=20;

--
-- AUTO_INCREMENT untuk tabel `users`
--
ALTER TABLE `users`
  MODIFY `id` int NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;

--
-- Ketidakleluasaan untuk tabel pelimpahan (Dumped Tables)
--

--
-- Ketidakleluasaan untuk tabel `uploaded_files`
--
ALTER TABLE `uploaded_files`
  ADD CONSTRAINT `uploaded_files_ibfk_1` FOREIGN KEY (`uploader_id`) REFERENCES `users` (`id`);
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
