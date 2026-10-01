# Data Quality & Leakage Audit Report: EDGE_IIOTSET

- **Generated At:** 2026-09-25T15:51:45.490588+00:00 UTC
- **Dataset:** `edge_iiotset`
- **Split Seed:** `13`
- **Split Hash:** `19816155e6812e42`
- **Held-Out Attack Family:** `Malware`

## 1. Split Distribution & Firewall Audit

| Partition | Sample Count | Percentage | Class Breakdown (Top Families) |
|---|---|---|---|
| **Train** | 88,487 | 56.1% | DDoS: 34,577, Web: 21,246, Benign: 17,011, Recon: 14,803, ... (+1 more) |
| **Validation** | 12,641 | 8.0% | DDoS: 4,940, Web: 3,035, Benign: 2,430, Recon: 2,115, ... (+1 more) |
| **Test** | 56,672 | 35.9% | Malware: 31,389, DDoS: 9,879, Web: 6,071, Benign: 4,860, ... (+2 more) |
| **Total** | 157,800 | 100.0% | |

### Held-Out Attack Family Verification

- **Target Held-Out Family:** `Malware`
- **Count in Train:** `0` (Required: 0) -> **PASS**
- **Count in Validation:** `0` (Required: 0) -> **PASS**
- **Count in Test:** `31389` (Required: > 0 for unseen-to-model test) -> **PASS**

## 2. Feature Schema & Column Audit

- **Active Model Features:** `39` (39 numeric, 0 categorical)
- **Excluded / Dropped Columns:** `28`

### Dropped & Leakage Columns

| Column Name | Rationale |
|---|---|
| `Attack_label` | Target / label metadata (firewalled to evaluation only) |
| `Attack_type` | Target / label metadata (firewalled to evaluation only) |
| `arp.dst.proto_ipv4` | Direct leakage / non-generalizable identifier or timestamp |
| `arp.src.proto_ipv4` | Direct leakage / non-generalizable identifier or timestamp |
| `canonical_label` | Target / label metadata (firewalled to evaluation only) |
| `dns.qry.name` | Direct leakage / non-generalizable identifier or timestamp |
| `dns.qry.type` | Zero variance (constant feature) |
| `dns.retransmit_request_in` | Zero variance (constant feature) |
| `family` | Target / label metadata (firewalled to evaluation only) |
| `frame.time` | Direct leakage / non-generalizable identifier or timestamp |
| `http.file_data` | Direct leakage / non-generalizable identifier or timestamp |
| `http.referer` | Direct leakage / non-generalizable identifier or timestamp |
| `http.request.full_uri` | Direct leakage / non-generalizable identifier or timestamp |
| `http.request.version` | Direct leakage / non-generalizable identifier or timestamp |
| `http.tls_port` | Zero variance (constant feature) |
| `icmp.unused` | Zero variance (constant feature) |
| `ip.dst_host` | Direct leakage / non-generalizable identifier or timestamp |
| `ip.src_host` | Direct leakage / non-generalizable identifier or timestamp |
| `is_attack` | Target / label metadata (firewalled to evaluation only) |
| `mbtcp.len` | Zero variance (constant feature) |
| `mbtcp.trans_id` | Zero variance (constant feature) |
| `mbtcp.unit_id` | Zero variance (constant feature) |
| `mqtt.msg` | Direct leakage / non-generalizable identifier or timestamp |
| `mqtt.msg_decoded_as` | Zero variance (constant feature) |
| `target_id` | Target / label metadata (firewalled to evaluation only) |
| `tcp.options` | Direct leakage / non-generalizable identifier or timestamp |
| `tcp.payload` | Direct leakage / non-generalizable identifier or timestamp |
| `tcp.srcport` | Direct leakage / non-generalizable identifier or timestamp |

### Audited Active Columns

| Column | Type | Missing Values | Infinite Values | Unique Count |
|---|---|---|---|---|
| `arp.hw.size` | `float64` | 0 | 0 | 2 |
| `arp.opcode` | `float64` | 0 | 0 | 3 |
| `dns.qry.name.len` | `str` | 0 | 0 | 8 |
| `dns.qry.qu` | `float64` | 0 | 0 | 66 |
| `dns.retransmission` | `float64` | 0 | 0 | 4 |
| `dns.retransmit_request` | `float64` | 0 | 0 | 2 |
| `http.content_length` | `float64` | 0 | 0 | 33 |
| `http.request.method` | `str` | 0 | 0 | 6 |
| `http.request.uri.query` | `str` | 0 | 0 | 1665 |
| `http.response` | `float64` | 0 | 0 | 2 |
| `icmp.checksum` | `float64` | 0 | 0 | 13187 |
| `icmp.seq_le` | `float64` | 0 | 0 | 13824 |
| `icmp.transmit_timestamp` | `float64` | 0 | 0 | 84 |
| `mqtt.conack.flags` | `str` | 0 | 0 | 3 |
| `mqtt.conflag.cleansess` | `float64` | 0 | 0 | 2 |
| `mqtt.conflags` | `float64` | 0 | 0 | 2 |
| `mqtt.hdrflags` | `float64` | 0 | 0 | 5 |
| `mqtt.len` | `float64` | 0 | 0 | 4 |
| `mqtt.msgtype` | `float64` | 0 | 0 | 5 |
| `mqtt.proto_len` | `float64` | 0 | 0 | 2 |
| `mqtt.protoname` | `str` | 0 | 0 | 3 |
| `mqtt.topic` | `str` | 0 | 0 | 3 |
| `mqtt.topic_len` | `float64` | 0 | 0 | 2 |
| `mqtt.ver` | `float64` | 0 | 0 | 2 |
| `tcp.ack` | `float64` | 0 | 0 | 27929 |
| `tcp.ack_raw` | `float64` | 0 | 0 | 94716 |
| `tcp.checksum` | `float64` | 0 | 0 | 55513 |
| `tcp.connection.fin` | `float64` | 0 | 0 | 2 |
| `tcp.connection.rst` | `float64` | 0 | 0 | 2 |
| `tcp.connection.syn` | `float64` | 0 | 0 | 2 |
| `tcp.connection.synack` | `float64` | 0 | 0 | 2 |
| `tcp.dstport` | `float64` | 0 | 0 | 23188 |
| `tcp.flags` | `float64` | 0 | 0 | 9 |
| `tcp.flags.ack` | `float64` | 0 | 0 | 2 |
| `tcp.len` | `float64` | 0 | 0 | 786 |
| `tcp.seq` | `float64` | 0 | 0 | 18199 |
| `udp.port` | `float64` | 0 | 0 | 32 |
| `udp.stream` | `float64` | 0 | 0 | 14492 |
| `udp.time_delta` | `float64` | 0 | 0 | 39 |

## 3. Notes & Observations

ML-EdgeIIoT-dataset (157,800 rows) and DNN-EdgeIIoT-dataset (2,219,201 rows) verified.
