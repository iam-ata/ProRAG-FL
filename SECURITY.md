# Security Policy

## Supported Versions

| Version | Supported | Security Updates |
|---|:---:|---|
| 0.1.x | Yes | Active maintenance & patches |
| < 0.1.0 | No | End of life |

---

## Reporting a Security Vulnerability

The ProRAG-FL research team takes security, privacy, and responsible vulnerability disclosure seriously. If you discover a potential vulnerability in this framework, Hyperledger Fabric chaincode, or data processing pipelines, please follow this disclosure process:

1. **Do NOT open a public GitHub Issue** for security vulnerabilities.
2. Email the maintainer directly with detailed technical reproduction steps:
   - Contact: **Ata Mohammadi** (`ata.mohammadi@alumni.ac.ir` / project maintainer email).
   - Please include:
     * Vulnerability description and impact assessment
     * Minimal code reproduction script or network packet trace
     * Any potential remediation suggestions
3. We will acknowledge receipt of your report within 48 hours and coordinate a coordinated remediation release.

---

## Adversarial AI & Research Scope

ProRAG-FL includes implementations of adversarial attacks (e.g., federated label-flipping, sign-inversion, gradient replacement, tabular backdoor watermarks, Merkle proof tampering, and CTI knowledge injection) located under `src/prorag_fl/attacks/`.

These attack modules are provided **strictly for defensive benchmarking, academic resilience evaluation, and robustness verification** against standardized threat models. They are designed to operate solely on synthetic or local datasets and must not be used against live production networks or third-party infrastructure.

---

## API Keys & Credentials Safety

- ProRAG-FL enforces an automatic secret redaction firewall (`src/prorag_fl/core/environment.py`) that sanitizes sensitive environment variables matching `KEY`, `SECRET`, `TOKEN`, `PASSWORD`, or `AUTH`.
- **Never commit live OpenAI API keys, blockchain private keys, or MinIO admin credentials to the repository.**
- Use `.env.example` as a template and ensure `.env` remains in `.gitignore`.
