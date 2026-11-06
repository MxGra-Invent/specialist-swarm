---
title: "Proposal Response — Acme Corp Enterprise Data Platform"
subtitle: "Prepared by BTS-Synthetic"
author: "BTS-Synthetic Deal Desk"
date: "2026-05-26"
---

# Proposal Response

## Acme Corp Enterprise Data Platform

**Prepared for:** Sarah Chen, VP Procurement · Marcus Webb, Chief Data Officer
**Prepared by:** BTS-Synthetic
**Date:** 2026-05-26
**Response to:** RFP issued 2026-05-12
**Our reference:** BTS-DD-ACME-2026-05

---

## 1. Executive Summary

- **Right-fit platform, proven at your profile.** 9 of 9 §2 requirements at full fit, including the non-negotiables: a dedicated Power BI DirectQuery adapter for your 600 analysts, per-table EU residency pinning for GDPR, and real-time ingest tested to 250K events/s — more than 3× your 80K peak. We won Initech Sensors on exactly this workload shape against Microsoft Fabric.
- **Commercial proposal: $684,000/year, fixed for five years, no escalators.** 28% off list, matching our Stark Industries precedent. Optional 99.99% SLA add-on at $100,000/year quoted as a separate line so you see the trade. 5-year committed value $3.42M (platform) or $3.92M (with 99.99% add-on).
- **Clean redline, closable in 14 days.** Nine clauses move with counters that have well-trodden precedent; one new item (a DPA + SCCs Module 2 covering your Vietnam/Mexico data flows) needs to be executed as a condition precedent to go-live. No hidden blockers.

---

## 2. Our Understanding of Acme's Need

Acme is replacing a patchwork — on-premises Teradata on one side, ad-hoc Azure analytics on the other — with a single platform that has to serve five distinct workload personas at once: edge-device telemetry, batch ETL from 30+ internal systems, 600 BI users on Power BI, 150 engineers doing self-service, and an incoming predictive-maintenance ML program. All of this on a dataset that grows from 280 TB to roughly 940 TB across the 5-year horizon, under GDPR constraints driven by your German and Romanian footprint and with cross-border flows from Vietnam and Mexico manufacturing.

Three themes dominate the brief:

1. **Power BI is non-negotiable.** 600 users today. Any platform that requires gateway workarounds or generic ODBC/JDBC bridges is a non-starter.
2. **Teradata decommission runs through 2027.** The real risk isn't the platform choice; it's the migration path and the parallel-run window.
3. **EU data residency is a hard legal boundary, not a preference.** You need per-table enforcement, not region-level approximations.

Everything in this proposal is shaped around those three.

---

## 3. Why BTS-Synthetic Is the Right Fit

### 3.1 Capability fit against your §2 requirements

| Requirement | Verdict | Evidence |
|---|---|---|
| Real-time ingest — 40K devices, peak 80K events/s | **Full fit** | Native Kafka/Kinesis consumers, tested to 250K events/s. 3× headroom over your peak. |
| Batch ETL — 30+ internal sources | **Full fit** | 80+ certified connectors (SAP, Salesforce, NetSuite, Teradata, common DBs). |
| **Native Power BI for 600 users** | **Full fit — differentiator** | **Dedicated Power BI DirectQuery adapter** — our most mature BI integration. No gateway, no generic ODBC. |
| Self-service prep — 150 engineers | **Full fit** | Low-code prep UI plus Python/R/Scala notebooks. |
| ML pipelines — predictive maintenance | **Full fit** | Model registry, feature store, autoscaling serving, BYO-model (HuggingFace, Anthropic, OpenAI). |
| Scale — 280 TB, 12 TB/mo growth | **Full fit** | Decoupled compute/storage on Azure Blob; scales independently with no replatforming. |
| Multi-region — EU primary, US East secondary | **Full fit** | Azure West Europe (Netherlands) or North Europe (Ireland) + Azure East US. |
| EU data residency — per-table enforcement | **Full fit — differentiator** | **Per-table residency pinning at the storage layer.** Snowflake and Databricks operate at the region/account level. |
| Lakehouse + Delta / Iceberg / Parquet | **Full fit** | All three native. No proprietary file formats; portability clause satisfied. |

### 3.2 Differentiators in this specific competitive field

You name Databricks, Snowflake, Microsoft Fabric and a regional vendor as the other evaluated parties. Against that field, three things only we do well:

- **Power BI DirectQuery adapter.** Sub-second response for warmed queries; measurably faster report-load than any gateway-based solution. Microsoft Fabric is tightly bound to Power BI but creates a one-vendor dependency — your IP and your data are inside Microsoft's walls. We give you the integration without the lock-in.
- **Per-table EU residency pinning.** With German and Romanian operations under GDPR, and manufacturing flows from Vietnam and Mexico, region-level residency is insufficient. Our table-level enforcement eliminates the legal-review burden on every new dataset. Snowflake and Databricks cannot do this at the same granularity.
- **Open file formats + Teradata migration playbook.** Delta, Iceberg and Parquet are native. Your data sits in your Azure Blob tenancy in open formats — if you ever wanted to leave, you could. Combined with our proven Teradata decommission pattern, this is the opposite of lock-in. The Stark Industries deal (closed Feb 2026) includes our IP licence-back model; we can offer Acme the same.

### 3.3 Reference deployments

Three customers we propose as references, all of whom have agreed to be contacted:

- **Initech Sensors** (industrial IoT, real-time ingest, Enterprise tier) — the closest analog to Acme. Won against Microsoft Fabric specifically on real-time SLA.
- **Globex Manufacturing** (industrial, 3-year deal, multi-cloud) — won on TCO against Snowflake and Databricks.
- **Stark Industries** ($1.1M/yr, 5-year, multi-region) — demonstrates scale credibility and includes the IP licence-back model we propose to carry across to Acme.

### 3.4 Where we are honest with you

Two caveats you should know before signing, not after:

- **Streaming query latency.** We deliver 250 ms – 1 s on streaming queries. If your predictive-maintenance program requires sub-100 ms in-stream alerting, we would recommend a lambda pattern — edge alerting on the device gateway, platform-side analytics in-stream. We will confirm this with Marcus Webb's team in technical discovery.
- **Standard SLA is 99.95%, not 99.99%.** The 99.99% tier you request in §4.3 is achievable only as a priced add-on with bespoke multi-region active-active architecture. It is quoted separately below so the trade is transparent. See §4 for the commercial detail and §5 for the contract shape we propose.

---

## 4. Commercial Proposal

### 4.1 Platform fees

| Item | Year 1 | Year 2 | Year 3 | Year 4 | Year 5 | 5-Year TCV |
|---|---:|---:|---:|---:|---:|---:|
| List price | $950,000 | $950,000 | $950,000 | $950,000 | $950,000 | $4,750,000 |
| Discount (28%) | ($266,000) | ($266,000) | ($266,000) | ($266,000) | ($266,000) | ($1,330,000) |
| **Contracted platform fee** | **$684,000** | **$684,000** | **$684,000** | **$684,000** | **$684,000** | **$3,420,000** |

Prices are **fixed for the full 5-year horizon with no escalators**, matching your §3.1 requirement. We absorb inflation risk in exchange for a 5-year committed relationship — this is reflected in the base pricing.

### 4.2 Optional 99.99% SLA add-on

| Item | Annual | 5-Year |
|---|---:|---:|
| 99.99% uptime add-on (multi-region active-active) | $100,000 | $500,000 |
| **Combined TCV (platform + 99.99%)** | **$784,000** | **$3,920,000** |

The add-on provisions the second-region active-active architecture required to hit 99.99%. We recommend you consider it jointly with the contract-shape change proposed in §5 — the SLA is only one part of the picture; the remedy structure matters more for your real risk.

### 4.3 Payment terms

- **Annual, invoiced in advance.**
- **Net 60.** This is our ceiling and matches the Initech Sensors precedent for a customer of your credit profile. We cannot accept Net 90 as written in §3.2; if Net 90 is material to you we can offer it with a 2% fee surcharge to offset carrying cost — the choice is yours.

### 4.4 Discount position

You asked for ≥35% in §3.3. Our offer is 28%. This matches our Stark Industries precedent (5-year, $1.1M/yr) and reflects the ceiling our pricing framework permits for a deal of this shape. We will hold 28% on the strength of our 5-year TCO and the capability fit above. We are confident the combined platform-plus-add-on TCV lands competitively against the other named vendors once implementation, egress and support costs are modelled over the full horizon — we will provide a side-by-side TCO at your request.

### 4.5 Commercial concessions we are prepared to make

- Custom MSA (standard on deals of this size)
- 30-day acceptance testing period
- PoC/pilot fees credited to Year 1 if a PoC is desired before contract
- Volume true-up at year-end with a 10% buffer to absorb your growth variance
- Reference-customer discount (further 1–2 pts) if Acme signs a reference agreement

---

## 5. Contract Approach

Our legal team has reviewed §3 and §4 and our legal panel voted on the most contentious clauses. The picture below shows where we can accept as written, where we need to counter, and where the panel split.

### 5.1 Panel vote on known contentious clauses

| Clause | Conservative | Balanced | Aggressive | **Final call** |
|---|---|---|---|---|
| §3.4 MFN | COUNTER | COUNTER | COUNTER | **COUNTER — narrow MFN to customers of comparable tier, volume and term; exclude promotional, partner, early-adopter pricing** |
| §3.5 Term. for convenience | COUNTER | COUNTER | COUNTER | **COUNTER — 60-day notice (vs. your 30); no-fee acceptable** |
| §4.1 Uncapped breach liability | REJECT | COUNTER | COUNTER | **COUNTER — aggregate cap at 24 months of fees; carve out regulatory fines and reputational damages as uninsurable; enhanced cyber-liability certificate provided** *(conservative REJECT vote overridden: the balanced/aggressive counter operationalises exactly the insurability concern that drove the REJECT, by removing the uninsurable elements from scope)* |
| §4.3 SLA termination | REJECT | COUNTER | COUNTER | **COUNTER — 99.99% as priced add-on; graduated service credits up to 30% of monthly fees as sole remedy; termination right reserved for sustained or repeated breach with a cure period** *(conservative REJECT vote overridden: the credit-only remedy plus cure period structurally bounds the open-ended termination exposure that drove the REJECT)* |
| **DPA + SCCs (second-round vote)** | REJECT | COUNTER | COUNTER | **COUNTER — DPA plus SCCs Module 2 covering Vietnam/Mexico flows, executed concurrent with the MSA as condition precedent to go-live** *(conservative REJECT overridden: under either position no processing begins before the DPA/SCCs are executed; the counter permits parallel rather than sequential signature, which is non-material to the risk)* |

### 5.2 Other clauses in §3 and §4

| Clause | Our position | Fallback |
|---|---|---|
| §3.1 Fixed 5-yr pricing, no escalators | **Accepted as written.** Priced into §4 above. | — |
| §3.2 Net 90 payment | **Counter: Net 60.** | Net 90 only with 2% surcharge. |
| §3.3 ≥35% discount | **Counter: 28%** (Stark precedent). | Walk-away above 30%. |
| §4.2 Audit — unannounced, 4×/yr, vendor pays | **Counter:** 2×/yr, 30 days' notice, customer pays costs; SOC 2 Type II + ISO 27001 as primary control evidence. | 2×/yr, 14 days' notice; we pay the first audit only. |
| §4.4 IP vesting of all work product | **Counter:** We retain IP; Acme receives perpetual, irrevocable, royalty-free licence to custom deliverables. This is the Stark Industries model (accepted Feb 2026). | Licence-back is the floor. No assignment. |
| §4.5 Subprocessor consent — sole discretion | **Counter:** Published subprocessor list; 30-day notice of changes; Acme may object on reasonable grounds; we substitute or grant exit right. Infrastructure subprocessors (Azure) notification-not-consent. | 15-day notice; deemed consent after silence. |
| Governing law (not specified) | **Propose:** England & Wales (our EU-customer standard). | Delaware if US seat required. |

### 5.3 New legal item — DPA and cross-border data transfer

Your RFP does not contain a Data Processing Agreement. Given your German and Romanian operations under GDPR, and the Vietnam and Mexico cross-border flows from manufacturing, a DPA plus SCCs Module 2 is a legal pre-condition for processing — not a negotiating lever. We will supply our standard DPA plus SCCs as an Exhibit to the MSA, to be executed concurrent with contract signature and made a condition precedent to go-live. Our per-table EU residency pinning covers EU-origin data at the platform layer.

---

## 6. Implementation Plan

| Milestone | Target |
|---|---|
| Azure deployment (West Europe primary + East US secondary), Kafka / Blob / Power BI wired | Week 1 – Week 4 |
| **First production workload live** | **~Week 8** |
| 30+ batch connectors validated; Teradata parallel-run begins | Week 12 – Week 16 |
| **Full Teradata cutover; decommission sequencing complete** | **~Week 24** |

This is consistent with our typical 24-week timeline for a large multi-source Teradata migration. The 8-week first-workload milestone is achievable subject to Acme's IT team delivering network access and credentials in week 1.

---

## 7. Risks and Mitigations

| # | Risk | Mitigation |
|---|---|---|
| 1 | **§4.3 SLA + termination as written** — a 2-minute outage in month 7 could unwind a 3-year contract. This is the single largest risk in the deal as currently drafted. | Service-credit remedy with cure period as proposed in §5.1. 99.99% add-on priced in §4.2. |
| 2 | **DPA / cross-border transfer not addressed in RFP** — processing EU-linked data without a lawful transfer mechanism would put both parties in breach on day one. | DPA + SCCs Module 2 executed concurrent with MSA, as condition precedent to go-live. |
| 3 | **Teradata migration overrun** — large multi-source migrations routinely slip on source-system discovery and data-quality issues. | 24-week plan with parallel-run gate at week 16; week-8 first-workload checkpoint to catch slippage early; dedicated migration lead. |
| 4 | **Discount pressure from Databricks or the regional vendor** — we saw Databricks go to 40% at Pied Piper (2025-08). | TCO-anchored positioning over the full 5-year horizon, not headline-list comparison. 28% is firm; we will not race to the bottom. |
| 5 | **Streaming latency expectations beyond 250 ms** — if predictive-maintenance requires in-stream alerting below 100 ms. | Confirm in technical discovery; recommend lambda pattern (edge alert + platform analytics) if required. |
| 6 | **Microsoft "free with E5" positioning on Fabric** — Initech saw this exact play. | Real-time SLA + Power BI DirectQuery depth + lock-in narrative; past-wins evidence is ready. |

---

## 8. Next Steps

1. Technical deep-dive with Marcus Webb and team (90 min) — architecture walk-through, confirm latency and ML requirements.
2. Commercial walk-through with Sarah Chen — 5-year TCO model side-by-side with the three named competitors.
3. Legal redline exchange on §3 and §4 and the DPA / SCCs package.
4. Reference calls — Initech Sensors, Globex Manufacturing, Stark Industries.
5. Final proposal lock and award decision by 2026-06-30 per your RFP timeline.

---

**Contact:** BTS-Synthetic Deal Desk · deal-desk@bts-synthetic.example
**Prepared under RFP response reference BTS-DD-ACME-2026-05**
