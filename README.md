# ⚡ 100 Python Automation Arsenal

[![Python Version](https://img.shields.io/badge/python-3.9%20%7C%203.10%20%7C%203.11%20%7C%203.12-blue.svg)](https://www.python.org/)
[![Status](https://img.shields.io/badge/suite%20status-20%2F100%20operational-success.svg)](#roadmap-to-100-tools)
[![Platform](https://img.shields.io/badge/platform-windows%20%7C%20linux%20%7C%20macos-lightgrey.svg)](#)
[![Zero-SaaS](https://img.shields.io/badge/architecture-100%25%20self--hosted-orange.svg)](#)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> **Industrial-grade, standalone Python utilities solving real everyday engineering, sysadmin, cybersecurity, recon, office data, and AI automation problems.**  
> Zero third-party cloud lock-in. Zero paid API subscriptions. 100% local sovereignty.

---

## 🎯 Executive Vision | رؤية المشروع

Modern engineering workflows have become fragmented across expensive SaaS micro-tools, telemetry-heavy desktop apps, and fragile browser extensions. 

**100 Python Automation Arsenal** is a curated suite of **100 battle-tested, modular automation tools** organized across **10 high-value engineering domains**. Every tool is designed to run completely standalone or unified through the interactive master terminal launcher (`arsenal.py`).

> **رؤية الترسانة**: تهدف هذه المنظومة إلى بناء أكبر مكتبة برمجية مفتوحة وعملية تضم 100 مشروع وأداة بايثون جاهزة للتنفيذ الفوري بدون تعقيدات أو اشتراكات شهرية، تشمل أدمن ويندوز، الاستطلاع السيبراني، بروتوكولات الشبكات، هندسة البيانات، أدوات الذكاء الاصطناعي المحلي، ومعالجة الوسائط.

---

## 🏗️ Architecture & Domain Taxonomy

The suite is systematically organized into **10 core domains** (10 tools per domain at full capacity):

| # | Domain Category | Focus & Automation Scope | Status |
|---|---|---|---|
| **01** | `01_windows_sysadmin` | Service healing, crash recovery, storage hygiene, duplicate elimination | `Active (2/10)` |
| **02** | `02_cybersecurity_recon` | Port auditing, service banner grabbing, OSINT, subdomain & DNS attack surface mapping | `Active (2/10)` |
| **03** | `03_network_protocols` | SMTP handshakes, deliverability scoring, SPF/DMARC audit, HTTP/SSL SLA profiling | `Active (2/10)` |
| **04** | `04_data_office_automation` | Large CSV/Excel cleansing, E.164 phone & email standardization, JSON lint & repair | `Active (2/10)` |
| **05** | `05_pdf_document_tools` | Fast PDF merging/slicing, page rotation, zero-telemetry metadata & privacy scrubbing | `Active (2/10)` |
| **06** | `06_web_scraping_leads` | Multi-threaded contact & email extraction, social handle discovery, On-Page SEO audit | `Active (2/10)` |
| **07** | `07_local_ai_utilities` | Ollama inference benchmark (tok/s, latency), polymorphic Spintax & prompt generators | `Active (2/10)` |
| **08** | `08_file_storage_systems` | Cryptographic SHA-256 integrity manifests, bit-rot detection, smart folder tidy-up | `Active (2/10)` |
| **09** | `09_developer_productivity` | Git commit velocity & code churn analytics, `.env` auto-generation, secret leak audits | `Active (2/10)` |
| **10** | `10_media_image_processing` | Batch high-efficiency WebP conversion, Lanczos image resizing, GPS EXIF redactor | `Active (2/10)` |

---

## ⚡ Master Command Center (`arsenal.py`)

All scripts can be invoked directly, or orchestrated through the interactive TUI launcher:

```bash
# 1. Launch the interactive menu
python arsenal.py

# 2. List all available tools
python arsenal.py list

# 3. Search tools by keyword, tag, or domain
python arsenal.py search deliverability
python arsenal.py search exif

# 4. Directly run any tool by ID or name
python arsenal.py run 5 gmail.com
python arsenal.py run port_vulnerability_scanner 127.0.0.1 -p 80,443,3389

# 5. Run automated diagnostic health gate across the entire suite
python arsenal.py test-all
```

---

## 📦 Tool Directory & Usage Handbook

### Category 01: Windows Sysadmin & System Health

#### 1. Windows Service Watchdog (`01_windows_sysadmin/service_watchdog.py`)
- **Keywords**: `windows sysadmin`, `service monitor`, `auto-restart`, `process watchdog`, `self-healing`
- **Capabilities**: Continuously audits critical Windows services (`Spooler`, `wuauserv`, `MSSQLSERVER`, etc.) and processes. Logs failure events and triggers automated restarts without user intervention.
```bash
# One-shot audit of services and target processes
python 01_windows_sysadmin/service_watchdog.py audit --processes python.exe chrome.exe

# Continuous monitoring with auto-restart on crash
python 01_windows_sysadmin/service_watchdog.py watch --services Spooler wuauserv --interval 10 --auto-restart
```

#### 2. Disk Space Guard & Clutter Analyzer (`01_windows_sysadmin/disk_space_guard.py`)
- **Keywords**: `disk cleaner`, `duplicate finder`, `storage analyzer`, `temp bloat`, `sysadmin`
- **Capabilities**: Locates largest storage hogs, analyzes extension volume distribution, audits system temp bloat, and finds exact duplicate files via two-stage hashing (file size pre-filter + SHA256).
```bash
# Scan directory for largest files and filetype footprint
python 01_windows_sysadmin/disk_space_guard.py scan --path C:/Users/nuns/Downloads --top 15

# Safe duplicate file detection
python 01_windows_sysadmin/disk_space_guard.py duplicates --path C:/Projects --min-dup-kb 50
```

---

### Category 02: Cybersecurity Recon & OSINT

#### 3. Multi-Threaded Port Scanner & Banner Grabber (`02_cybersecurity_recon/port_vulnerability_scanner.py`)
- **Keywords**: `port scanner`, `cybersecurity recon`, `banner grabber`, `network penetration`, `infosec`
- **Capabilities**: High-speed parallel TCP connect scanner with automatic service fingerprinting, banner grabbing, and round-trip latency calculation.
```bash
# Scan common ports on target host
python 02_cybersecurity_recon/port_vulnerability_scanner.py 192.168.1.1 --ports common --threads 50

# Scan custom range with JSON output
python 02_cybersecurity_recon/port_vulnerability_scanner.py scanme.org -p 21,22,80,443,8080 --json
```

#### 4. Subdomain & DNS Recon Enumerator (`02_cybersecurity_recon/subdomain_dns_enum.py`)
- **Keywords**: `subdomain enumeration`, `dns recon`, `osint`, `attack surface`, `cybersecurity`
- **Capabilities**: Discovers active subdomains, queries root A, AAAA, MX, TXT, and NS records, handles wildcard DNS detection with fallback public resolvers.
```bash
# Enumerate target domain subdomains
python 02_cybersecurity_recon/subdomain_dns_enum.py example.com --threads 30
```

---

### Category 03: Network Protocols & Communications

#### 5. SMTP Handshake & Deliverability Checker (`03_network_protocols/smtp_deliverability_checker.py`)
- **Keywords**: `smtp deliverability`, `mx checker`, `email verification`, `spf audit`, `dmarc policy`
- **Capabilities**: Resolves MX priority rankings, inspects SPF and DMARC DNS policies, and conducts live pre-flight SMTP handshakes (`EHLO`, `STARTTLS`, `RCPT TO`) without sending actual spam.
```bash
# Check domain mail authentication and MX records
python 03_network_protocols/smtp_deliverability_checker.py company.com

# Conduct live recipient mailbox probe
python 03_network_protocols/smtp_deliverability_checker.py contact@company.com --probe-mailbox
```

#### 6. HTTP/HTTPS SLA Monitor & SSL Inspector (`03_network_protocols/http_latency_monitor.py`)
- **Keywords**: `http latency`, `ttfb`, `ssl expiration`, `uptime monitor`, `sla profiler`
- **Capabilities**: Measures granular network timing breakdowns (DNS lookup, TCP connect, TLS handshake, Time To First Byte) and audits SSL certificate expiration dates.
```bash
python 03_network_protocols/http_latency_monitor.py https://api.github.com https://google.com
```

---

### Category 04: Data & Office Automation

#### 7. Universal CSV/Excel Deduplicator & Transformer (`04_data_office_automation/csv_excel_deduper_transformer.py`)
- **Keywords**: `csv cleaner`, `excel deduplication`, `e164 phone normalizer`, `data pipeline`, `leads`
- **Capabilities**: Cleans messy datasets, strips whitespace, removes duplicate rows by custom columns, normalizes email casing and formats phone numbers to international digits.
```bash
python 04_data_office_automation/csv_excel_deduper_transformer.py leads.csv \
  --dedup email --clean-email email --clean-phone phone --drop-empty name -o clean_leads.csv
```

#### 8. JSON Lint, Schema Validator & Auto-Repair Engine (`04_data_office_automation/json_schema_validator_formatter.py`)
- **Keywords**: `json validator`, `json linter`, `auto repair`, `minify json`, `data automation`
- **Capabilities**: Heuristically fixes broken JSON (single quotes, trailing commas, unquoted keys, Python literals), validates structural schemas, and supports minification or beautification.
```bash
# Auto-repair malformed JSON
python 04_data_office_automation/json_schema_validator_formatter.py broken.json --repair -o fixed.json

# Minify for production APIs
python 04_data_office_automation/json_schema_validator_formatter.py config.json --minify -o config.min.json
```

---

### Category 05: PDF & Document Processing

#### 9. High-Speed PDF Merger, Splitter & Page Extractor (`05_pdf_document_tools/pdf_merge_splitter.py`)
- **Keywords**: `pdf merger`, `pdf splitter`, `extract pdf pages`, `rotate pdf`, `office tools`
- **Capabilities**: Combines multiple PDFs, extracts specific page ranges (e.g. `1-3,5,10-end`), and rotates pages by 90/180/270 degrees 100% locally.
```bash
# Merge documents
python 05_pdf_document_tools/pdf_merge_splitter.py merge doc1.pdf doc2.pdf -o combined.pdf

# Extract page range with rotation
python 05_pdf_document_tools/pdf_merge_splitter.py extract invoice.pdf --pages 1-3,5 --rotate 90 -o summary.pdf
```

#### 10. PDF Metadata & Privacy Scrubber (`05_pdf_document_tools/pdf_metadata_scrubber.py`)
- **Keywords**: `pdf metadata`, `privacy scrubber`, `anonymize pdf`, `redact metadata`, `security`
- **Capabilities**: Audits embedded author trails, creator software, and printer footprints, and completely scrubs metadata dictionaries before document publication.
```bash
# Audit metadata
python 05_pdf_document_tools/pdf_metadata_scrubber.py audit sensitive_doc.pdf

# Sanitize document
python 05_pdf_document_tools/pdf_metadata_scrubber.py scrub sensitive_doc.pdf -o sanitized.pdf
```

---

### Category 06: Web Scraping & Lead Discovery

#### 11. High-Speed Web Lead & Contact Extractor (`06_web_scraping_leads/lead_contact_extractor.py`)
- **Keywords**: `lead generator`, `email extractor`, `phone harvester`, `social scraper`, `osint`
- **Capabilities**: Multi-threaded web page crawler extracting email addresses (with false-positive filters), international phone numbers, and LinkedIn/Twitter/GitHub social profile links.
```bash
python 06_web_scraping_leads/lead_contact_extractor.py https://targetsite.com --depth 2 -o leads.csv
```

#### 12. On-Page SEO, OpenGraph & Metadata Auditor (`06_web_scraping_leads/meta_seo_auditor.py`)
- **Keywords**: `seo auditor`, `on-page seo`, `opengraph checker`, `meta description`, `digital marketing`
- **Capabilities**: Analyzes title/description lengths, canonical tags, H1-H6 structure, robots directives, image `alt` attributes, and computes an automated SEO health score (0-100).
```bash
python 06_web_scraping_leads/meta_seo_auditor.py https://example.com
```

---

### Category 07: Local AI & Prompt Utilities

#### 13. Local LLM & Ollama Performance Benchmarker (`07_local_ai_utilities/ollama_model_benchmarker.py`)
- **Keywords**: `ollama benchmark`, `local ai`, `tokens per second`, `llm inference`, `vram profiler`
- **Capabilities**: Benchmarks local Ollama endpoints across coding, reasoning, and extraction prompts. Measures exact Tokens-per-Second (`tok/s`), prompt eval speed, and hardware latency.
```bash
python 07_local_ai_utilities/ollama_model_benchmarker.py --models llama3:8b mistral:7b
```

#### 14. Smart Polymorphic Prompt & Spintax Generator (`07_local_ai_utilities/smart_prompt_spintax_generator.py`)
- **Keywords**: `spintax generator`, `prompt engineering`, `polymorphic text`, `jaccard diversity`, `cold email`
- **Capabilities**: Generates thousands of polymorphic variations from nested spintax `{hello|hi}`, injects dynamic runtime variables, and evaluates Jaccard uniqueness diversity scores.
```bash
python 07_local_ai_utilities/smart_prompt_spintax_generator.py \
  "{Super-fast|Rapid|Instant} {audit|check} of server {v1|v2} on {date}" --count 5
```

---

### Category 08: File Storage & System Integrity

#### 15. Directory Cryptographic Hash Manifest & Verifier (`08_file_storage_systems/hash_integrity_verifier.py`)
- **Keywords**: `hash manifest`, `integrity verifier`, `sha256 checksum`, `file tampering`, `incident response`
- **Capabilities**: Generates cryptographic SHA256/SHA512 baselines of directories and verifies integrity, detecting modified, corrupted, missing, or newly inserted files with strict CI/CD exit codes.
```bash
# Generate reference baseline
python 08_file_storage_systems/hash_integrity_verifier.py generate C:/Projects/App -o baseline.json

# Audit integrity against baseline
python 08_file_storage_systems/hash_integrity_verifier.py verify C:/Projects/App -m baseline.json
```

#### 16. Smart Rule-Based File Organizer (`08_file_storage_systems/smart_file_organizer.py`)
- **Keywords**: `file organizer`, `auto sort`, `folder cleaner`, `tidy up`, `storage management`
- **Capabilities**: Cleans messy folders (Downloads, Desktop) by categorizing files into structured directories (Documents, Images, Archives, Code, Media) with safe dry-run preview and duplicate renaming.
```bash
# Preview organization (Dry-Run)
python 08_file_storage_systems/smart_file_organizer.py ~/Downloads

# Execute actual organization
python 08_file_storage_systems/smart_file_organizer.py ~/Downloads --execute --by-date
```

---

### Category 09: Developer Productivity & DevOps

#### 17. Git Repository Activity & Velocity Analyzer (`09_developer_productivity/git_repo_activity_analyzer.py`)
- **Keywords**: `git analytics`, `developer velocity`, `code churn`, `git hotspots`, `productivity`
- **Capabilities**: Analyzes commit history, identifies top contributors, discovers file churn hotspots (frequently modified buggy files), and plots commit velocity by weekday and hour.
```bash
python 09_developer_productivity/git_repo_activity_analyzer.py . --limit 500
```

#### 18. Environment Config Generator & Secret Leak Auditor (`09_developer_productivity/env_config_generator_vault.py`)
- **Keywords**: `env generator`, `secret leak auditor`, `api key detection`, `devops security`, `entropy keys`
- **Capabilities**: Discovers environment variables in codebase to generate `.env.example`, audits files for exposed API keys/tokens, and produces cryptographically secure random secrets.
```bash
# Auto-generate .env.example
python 09_developer_productivity/env_config_generator_vault.py gen-example . -o .env.example

# Audit for leaked secrets
python 09_developer_productivity/env_config_generator_vault.py audit-leaks .

# Generate 256-bit cryptographic keys
python 09_developer_productivity/env_config_generator_vault.py gen-secret
```

---

### Category 10: Media & Image Processing

#### 19. High-Speed Batch Image Compressor & WebP Converter (`10_media_image_processing/batch_image_optimizer.py`)
- **Keywords**: `image compression`, `webp converter`, `batch resize`, `lanczos`, `web performance`
- **Capabilities**: Multi-threaded batch compressor converting PNG/JPG/TIFF assets to modern WebP with 60-80% file size reduction while preserving perceptual clarity.
```bash
python 10_media_image_processing/batch_image_optimizer.py ./raw_photos -o ./optimized --format webp --quality 80
```

#### 20. Image EXIF Privacy Sanitizer & Geotag Redactor (`10_media_image_processing/image_exif_sanitizer.py`)
- **Keywords**: `exif sanitizer`, `gps geotag remover`, `photo privacy`, `metadata scrubber`, `osint defense`
- **Capabilities**: Reads and purges GPS latitude/longitude tags, camera device serials, and timestamps from images before publishing.
```bash
# Audit photo for GPS coordinates
python 10_media_image_processing/image_exif_sanitizer.py audit vacation.jpg

# Strip all metadata
python 10_media_image_processing/image_exif_sanitizer.py strip vacation.jpg -o safe_vacation.jpg
```

---

## 🚀 Quickstart & Installation

```bash
# Clone the repository
git clone https://github.com/abdelrahmanabuzed-onepice/100-python-automation-arsenal.git
cd 100-python-automation-arsenal

# Install lightweight dependencies
pip install -r requirements.txt

# Launch the unified Command Center
python arsenal.py
```

---

## 🗺️ Roadmap to 100 Tools

```
[████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░] 20 / 100 Tools Deployed

 Phase 1: Foundation (Tools 01 - 20)  ──> [COMPLETED] Core Sysadmin, Recon, Data, Office, Media
 Phase 2: Growth     (Tools 21 - 40)  ──> Cloud DevOps, Database Backups, SSH & SOCKS5 Relays
 Phase 3: Expansion  (Tools 41 - 60)  ──> Advanced Local LLMs, Web Automation & Headless Crawlers
 Phase 4: Security   (Tools 61 - 80)  ──> Malware Triage, Forensics, Blue Team Hardening
 Phase 5: Mastery    (Tools 81 - 100) ──> Enterprise Workflow Orchestration & Automated ETL
```

---

## 📄 License & Attribution

Distributed under the **MIT License**. Created and maintained by [Abdelrahman Abuzed](mailto:abdelrahman.abuzed@gmail.com). Free for commercial and private use.
