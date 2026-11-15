# XENON

**A modular web security assessment platform.**

XENON is an evolving Python-based project focused on web security testing, automation, and AI-assisted analysis. The platform is being developed incrementally, with each phase adding and validating a defined set of capabilities.

## Project Overview

XENON is designed as a modular, security-first web security assessment platform. Its long-term direction is to provide a comprehensive framework for automated vulnerability discovery, assessment, and reporting — with strong security guarantees, deterministic behavior, and clear phase-wise progression. The architecture emphasizes modularity, testability, and defense-in-depth, ensuring that each capability builds on a stable, well-tested foundation.

## Project Status

**Phase 01 — Foundation & Target Management:** **COMPLETED**

**Current focus:** Phase 02 — Reconnaissance & Asset Discovery — **ARCHITECTURE PLANNING** (implementation not yet started)

### Phase 01 Scope

- Target and scope management
- Centralized logging
- Sensitive-data redaction in logs
- Secure handling of parameterized log messages
- Automated regression tests for logging security

Phase 01 is a foundation module. Active scanning and vulnerability detection are outside its current scope.

## Phase Roadmap

### Phase 01 — Foundation & Target Management ✅ COMPLETED
- Target and scope management
- Centralized logging with sensitive-data redaction
- Secure file/output utilities
- Common exception handling
- Foundation-level testing (124 tests passing)

### Phase 02 — Reconnaissance & Asset Discovery 📋 ARCHITECTURE PLANNING
- Subdomain enumeration
- DNS intelligence
- Port scanning
- Technology detection
- HTTP client infrastructure

### Future Phases — Proposed
- Endpoint Discovery
- Parameter Discovery
- Vulnerability Assessment
- Evidence Collection
- Reporting
- AI-driven security reasoning
- Tool orchestration

## Documentation Navigation

- **Phase 01 Documentation:** [phase01/README.md](phase01/README.md)
- **Phase 02 Documentation:** Not yet available (architecture planning in progress)

## Technology Stack

- Python
- Regular expressions and Python logging
- `unittest` for automated testing
- Git for version control

Additional technologies may be introduced as later modules are developed.

## Repository Structure

```text
Xenon/
├── phase01/
│   ├── config/
│   │   ├── defaults.py
│   │   └── settings.py
│   ├── core/
│   │   ├── exceptions.py
│   │   ├── logger.py
│   │   ├── scope_manager.py
│   │   └── target_manager.py
│   ├── main.py
│   ├── models/
│   │   ├── scope.py
│   │   └── target.py
│   ├── output/
│   │   └── .gitkeep
│   ├── tests/
│   │   ├── test_file_utils.py
│   │   ├── test_logger_security.py
│   │   ├── test_scope_manager.py
│   │   ├── test_target_manager.py
│   │   └── test_validation.py
│   ├── utils/
│   │   ├── file_utils.py
│   │   └── validation.py
│   └── README.md
├── README.md
├── requirements.txt
├── schemas/
│   ├── attack-chain.yaml
│   ├── compensating-controls.yaml
│   ├── coverage-checklists.yaml
│   ├── finding.yaml
│   ├── infographic.yaml
│   ├── input.yaml
│   ├── output.yaml
│   ├── report.yaml
│   ├── risk-scoring.yaml
│   ├── security-report.yaml
│   └── taxonomy/
│       ├── crosswalk.yaml
│       ├── cwe.yaml
│       ├── mitre-atlas.yaml
│       ├── mitre-attack.yaml
│       ├── nist-ai-600-1.yaml
│       ├── nist-ai-rmf.yaml
│       ├── owasp.yaml
│       ├── tachi-control-category.yaml
│       └── tachi-stride-ai-category.yaml
├── scripts/
│   ├── extract-infographic-data.py
│   ├── extract-report-data.py
│   └── tachi_parsers.py
├── templates/
│   └── tachi/
│       ├── infographics/
│       │   ├── infographic-baseball-card.md
│       │   ├── infographic-maestro-heatmap.md
│       │   ├── infographic-maestro-stack.md
│       │   ├── infographic-risk-funnel.md
│       │   ├── infographic-system-architecture.md
│       │   └── INFOGRAPHIC_TEMPLATES.md
│       ├── output-schemas/
│       │   ├── compensating-controls.md
│       │   ├── risk-scores.md
│       │   ├── threat-report.md
│       │   └── threats.md
│       └── security-report/
│           └── README.md
└── .vscode/
    └── settings.json
```

*This structure reflects the current state of the repository. Internal virtual environments (e.g., `myenv/`) and cache directories are omitted.*

## Run Phase 01 Tests

From the repository root, run:

```bash
python3 -m unittest discover -s phase01/tests -v
```

The command runs the Phase 01 tests discovered by Python's `unittest` framework.

## Development Status

XENON is under active development. Capabilities and security-testing coverage must be validated against the relevant implementation and test results before being considered production-ready.

## License

This repository is private. No public license is currently specified.
