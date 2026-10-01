# Data Quality & Leakage Audit Report: CICIOT2023

- **Generated At:** 2026-09-25T15:51:39.436595+00:00 UTC
- **Dataset:** `ciciot2023`
- **Split Seed:** `13`
- **Split Hash:** `44593e8c5ea13ca1`
- **Held-Out Attack Family:** `Mirai`

## 1. Split Distribution & Firewall Audit

| Partition | Sample Count | Percentage | Class Breakdown (Top Families) |
|---|---|---|---|
| **Train** | 66,058 | 66.1% | DDoS: 44,911, DoS: 12,150, UnknownAttack: 6,072, Benign: 1,587, ... (+4 more) |
| **Validation** | 9,436 | 9.4% | DDoS: 6,415, DoS: 1,735, UnknownAttack: 868, Benign: 227, ... (+4 more) |
| **Test** | 24,506 | 24.5% | DDoS: 12,833, Mirai: 5,631, DoS: 3,472, UnknownAttack: 1,735, ... (+5 more) |
| **Total** | 100,000 | 100.0% | |

### Held-Out Attack Family Verification

- **Target Held-Out Family:** `Mirai`
- **Count in Train:** `0` (Required: 0) -> **PASS**
- **Count in Validation:** `0` (Required: 0) -> **PASS**
- **Count in Test:** `5631` (Required: > 0 for unseen-to-model test) -> **PASS**

## 2. Feature Schema & Column Audit

- **Active Model Features:** `40` (40 numeric, 0 categorical)
- **Excluded / Dropped Columns:** `11`

### Dropped & Leakage Columns

| Column Name | Rationale |
|---|---|
| `DHCP` | Zero variance (constant feature) |
| `IRC` | Zero variance (constant feature) |
| `SMTP` | Zero variance (constant feature) |
| `Telnet` | Zero variance (constant feature) |
| `canonical_label` | Target / label metadata (firewalled to evaluation only) |
| `cwr_flag_number` | Zero variance (constant feature) |
| `ece_flag_number` | Zero variance (constant feature) |
| `family` | Target / label metadata (firewalled to evaluation only) |
| `is_attack` | Target / label metadata (firewalled to evaluation only) |
| `label` | Target / label metadata (firewalled to evaluation only) |
| `target_id` | Target / label metadata (firewalled to evaluation only) |

### Audited Active Columns

| Column | Type | Missing Values | Infinite Values | Unique Count |
|---|---|---|---|---|
| `ARP` | `float64` | 0 | 0 | 2 |
| `AVG` | `float64` | 0 | 0 | 20661 |
| `Covariance` | `float64` | 0 | 0 | 18596 |
| `DNS` | `float64` | 0 | 0 | 2 |
| `Drate` | `float64` | 0 | 0 | 9 |
| `Duration` | `float64` | 0 | 0 | 2730 |
| `HTTP` | `float64` | 0 | 0 | 2 |
| `HTTPS` | `float64` | 0 | 0 | 2 |
| `Header_Length` | `float64` | 0 | 0 | 27206 |
| `IAT` | `float64` | 0 | 0 | 99912 |
| `ICMP` | `float64` | 0 | 0 | 2 |
| `IPv` | `float64` | 0 | 0 | 2 |
| `LLC` | `float64` | 0 | 0 | 2 |
| `Magnitue` | `float64` | 0 | 0 | 20119 |
| `Max` | `float64` | 0 | 0 | 7505 |
| `Min` | `float64` | 0 | 0 | 5767 |
| `Number` | `float64` | 0 | 0 | 63 |
| `Protocol Type` | `float64` | 0 | 0 | 1154 |
| `Radius` | `float64` | 0 | 0 | 18544 |
| `Rate` | `float64` | 0 | 0 | 95340 |
| `SSH` | `float64` | 0 | 0 | 2 |
| `Srate` | `float64` | 0 | 0 | 95340 |
| `Std` | `float64` | 0 | 0 | 19129 |
| `TCP` | `float64` | 0 | 0 | 2 |
| `Tot size` | `float64` | 0 | 0 | 8073 |
| `Tot sum` | `float64` | 0 | 0 | 14695 |
| `UDP` | `float64` | 0 | 0 | 2 |
| `Variance` | `float64` | 0 | 0 | 135 |
| `Weight` | `float64` | 0 | 0 | 67 |
| `ack_count` | `float64` | 0 | 0 | 118 |
| `ack_flag_number` | `float64` | 0 | 0 | 2 |
| `fin_count` | `float64` | 0 | 0 | 194 |
| `fin_flag_number` | `float64` | 0 | 0 | 2 |
| `flow_duration` | `float64` | 0 | 0 | 45318 |
| `psh_flag_number` | `float64` | 0 | 0 | 2 |
| `rst_count` | `float64` | 0 | 0 | 3963 |
| `rst_flag_number` | `float64` | 0 | 0 | 2 |
| `syn_count` | `float64` | 0 | 0 | 451 |
| `syn_flag_number` | `float64` | 0 | 0 | 2 |
| `urg_count` | `float64` | 0 | 0 | 2438 |

## 3. Notes & Observations

Full CICIOT23 split verified. Total samples in raw split files: 7,845,673 rows.
