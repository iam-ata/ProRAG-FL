# Locked Proposed Method — ProRAG-FL

This file is the authoritative implementation specification.

## 1. Problem decomposition
ProRAG-FL treats three trust surfaces separately:
- **model trust:** authenticity/integrity/freshness of FL updates;
- **knowledge trust:** source/version/integrity of RAG evidence;
- **decision trust:** evidence-grounded structured LLM reasoning.

No single mechanism is allowed to substitute for all three.

## 2. Datasets
Evaluate independently:
- CICIoT2023;
- Edge-IIoTset.

Never merge feature spaces/taxonomies.

Unseen-to-model hold-outs:
- CICIoT2023 → Mirai;
- Edge-IIoTset → Malware.

These families must be excluded from classifier training, calibration fitting, and OOD class statistics, while remaining in final evaluation. External CTI may know them; therefore the claim is **unseen-to-model**, not globally unknown/zero-day.

## 3. Local IDS
PyTorch 1D-CNN:

```text
[B,F] → [B,1,F]
Conv1D 64 → BN → ReLU
Conv1D 128 → BN → ReLU → MaxPool
Conv1D 256 → ReLU
Global Average Pool
FC 128 → ReLU → Dropout 0.30
Classifier head
```

The 128-D representation is also used by OOD detection.

Implementation defaults unless a documented compatibility issue arises:
- kernels 3;
- stride 1;
- padding preserving length where possible;
- pool kernel 2.

Training defaults:
- AdamW;
- lr `1e-3`;
- weight decay `1e-4`;
- batch `256`;
- class-weighted cross entropy unless validation demonstrates instability.

Do not apply softmax inside the network before cross-entropy.

## 4. Federated learning
Framework: Flower.

Primary:
- K=10 clients;
- 50 rounds;
- 2 local epochs.

Scalability: K={5,10,20}.  
Partitions: IID and Dirichlet alpha={1.0,0.5,0.3,0.1}.

### Proposed update rule
Let `V_i^M` be hard model-provenance validity.

```text
theta_(t+1) = FedTrimmedAvg({Delta theta_i^t | V_i^M=1}, beta=0.20)
```

Provenance validates:
- client identity;
- signature/authorization;
- FL round;
- global-model version;
- update digest;
- timestamp where policy applies;
- nonce/replay state;
- lifecycle status.

Invalid updates are removed **before** aggregation.

A signed update can still be poisoned. Blockchain proves provenance/integrity/freshness, while robust aggregation handles numerical Byzantine behavior.

## 5. Calibration
Fit temperature T on validation logits only:

```text
P_T(y|x) = softmax(z(x)/T)
C(x) = max_y P_T(y|x)
```

Fit/select `tau_C` only through a declared validation protocol.

## 6. OOD
Use 128-D embedding `h(x)` and class-conditional Mahalanobis distance:

```text
M(x)=min_c sqrt((h-mu_c)^T Sigma^-1 (h-mu_c))
```

Fit means/covariance on known training representations. Select `tau_M` on validation only.

## 7. Escalation gate

```text
G(x) = I[ C(x) < tau_C OR M(x) > tau_M ]
```

If `G=0`, return direct IDS prediction. If `G=1`, invoke the sanitized RAG/LLM path.

## 8. Sanitized event
Allowed conceptual fields:
- pseudonymous event ID;
- classifier prediction;
- calibrated confidence;
- OOD score;
- protocol/device coarse context;
- temporal context;
- selected abnormal feature descriptions.

For numeric abnormality, a training-benign z-score can be used:

```text
z_f=(x_f-mu_f_benign)/(sigma_f_benign+epsilon)
```

Send only Top-m meaningful abnormal features, not the full raw record.

Never send raw PCAP/payload, secrets, private keys, model tensors, hidden ground-truth labels, or unnecessary direct identifiers.

## 9. Blockchain
Target Hyperledger Fabric 2.5 LTS-compatible deployment:
- 3 organizations/3 peers;
- 3-node Raft ordering;
- 2-of-3 endorsement for consortium incident-memory admission.

Two logical registries:
- `ModelUpdateRegistry`;
- `KnowledgeProvenanceRegistry`.

On-chain only compact provenance metadata: hashes, IDs, versions, nonces, timestamps, status, identity/endorsement/audit metadata, Merkle roots.

Off-chain: traffic, full updates, checkpoints, documents, embeddings, prompts.

## 10. Knowledge provenance
Canonical CTI documents in MinIO.

For each document version:
1. canonicalize;
2. deterministically chunk;
3. hash chunks;
4. construct Merkle tree;
5. anchor document root on-chain;
6. store document/version/proof metadata with indexed chunks.

Retrieved chunk must satisfy:

```text
VerifyMerkle(chunk, proof, Root(document_version)) = true
```

## 11. RAG
- BGE-M3 dense+sparse representations;
- Qdrant vector/sparse store;
- RRF fusion;
- initial candidate pool Top-20;
- hard provenance/source/status/version/Merkle filter;
- verified reranking;
- final verified Top-5.

Hard eligible set:

```text
K_V = {d | provenance_valid(d)=1 AND status=active AND source in AuthorizedSources}
```

An invalid item is removed, not merely downweighted.

Post-verification score may combine validation-frozen:
- normalized RRF;
- freshness;
- independent corroboration.

## 12. OpenAI reasoning
Use the OpenAI API through an adapter configured by:
- `OPENAI_API_KEY`;
- `OPENAI_MODEL`.

Do not hardcode a model snapshot into business logic. Record the exact model identifier used per experiment and synchronize the final manuscript to the actually used model.

Controlled experiment:
- no web browsing;
- no external file search;
- no arbitrary tools/code execution;
- input = sanitized event + verified Top-5 only.

Strict structured result:
- `attack_family`;
- `mitre_techniques[]`;
- `evidence_ids[]`;
- `evidence_sufficient`;
- `reasoning_summary`;
- `recommended_action`.

Do not use model-generated confidence as a calibrated probability.

## 13. Prompt-injection defense
Retrieved evidence is untrusted data, never instruction. Delimit it structurally, disable tools, require evidence IDs, reject unsupported IDs, and explicitly instruct the model not to obey commands found inside evidence.

## 14. Federated Threat Memory
Authoritative CTI:
`fetch → normalize → chunk → Merkle → anchor → index`.

Consortium incident memory additionally requires:
- sanitization;
- verified supporting evidence;
- schema checks;
- at least 2-of-3 independent organization endorsements.

LLM output can never auto-admit future knowledge.

## 15. Final conceptual decision

```text
Decision(x) = f_theta(x)                                if G(x)=0
Decision(x) = LLM(e_x, TopK(K_V,q_x))                  if G(x)=1
```

## 16. Core novelty to preserve
1. dual model/knowledge provenance;
2. provenance gate before robust FL aggregation;
3. calibrated/OOD selective RAG;
4. Merkle chunk verification with compact on-chain root;
5. evidence-verified multi-organization threat memory.
