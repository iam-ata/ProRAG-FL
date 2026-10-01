# FL Client Partitioning

Partition only the global **training** split.

## IID
Deterministically shuffle training indices with the experiment seed and divide into K near-equal partitions.

## Dirichlet non-IID
For each class:
1. collect its training indices;
2. sample proportions from `Dirichlet(alpha * ones(K))`;
3. allocate class indices to clients;
4. enforce a declared minimum client size;
5. if invalid, retry with a deterministic retry sequence, not ad-hoc random reruns.

Alpha values: `1.0, 0.5, 0.3, 0.1`.

## Manifest
Store:
- dataset/split hashes;
- K;
- method;
- alpha;
- seed;
- sample indices/IDs per client;
- class counts per client;
- sample totals;
- simple heterogeneity/entropy summary.

## Fairness invariant
For fixed `dataset + K + alpha + seed`, every comparable FL method uses the exact same partition manifest.

## Tests
- every training sample assigned exactly once;
- no validation/test sample assigned;
- no duplicates;
- client minimum-size rule satisfied;
- deterministic regeneration gives same manifest/hash.

Generate class-distribution tables/heatmaps from manifests, not from manual counting.
