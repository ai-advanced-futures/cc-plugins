---
name: partnerships-architect
description: Design the technical and software architecture for a strategic partnership integration using Gawer's 4-lever platform leadership framework and Parker's openness decision model. Use when the user wants to design partner API integrations, plan SDK development, architect multi-tenant or white-label infrastructure, decide on interface openness levels, structure open source contribution workflows, or plan technical onboarding for partners.
argument-hint: "[session id, or product name, category, target market, existing integrations, partnership goals]"
allowed-tools: Bash(uv run ${CLAUDE_PLUGIN_ROOT}/scripts/*)
---

## Routing

**Quick interactive** (the person explores, gives no session id, and asks for no scored analysis): apply the framework of this skill in this conversation, and ask the person for missing facts.

**Full quality** (the person gives a session id, or asks for a scored analysis):

1. Take the session id from `$ARGUMENTS`. With no session id, ask the person for the missing product context fields. Then run `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/session_manager.py --init`. It prints the new session id.
2. Run `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/simulate_phase.py --phase architect --session-id <session id>`. When a script exits 2 (the session id is not a plain name), show its message and stop. Dispatch no agent, and read no file. On LOW confidence, name the missing earlier phases. Then take the quick interactive path.
3. With a session id and no new context, take `product_context` from `.sp-tmp/<session id>/assess.md`. A run with `claude -p` has no person to ask.
4. Otherwise always dispatch `strategic-partnerships:architect-agent` with the `Agent` tool, also when the phase file exists, because the person asked for a new result. Give it `session_id` and `product_context`. Show the path `.sp-tmp/<session id>/architect.md`.

# Partnership Technical Architecture

This skill designs the software architecture and technical integration strategy required to support and operationalize a strategic partnership — grounding architectural decisions in Gawer's 4-lever platform leadership framework and Parker's platform openness model.

> **Frameworks used:** Gawer's 4 Levers of Platform Leadership (D), Parker's Platform Openness Framework (F), Jansen's Power Dynamics (I). See `${CLAUDE_PLUGIN_ROOT}/frameworks.md` for full attribution.

## When to Use

- "How should we architect our partner integrations?"
- "Design an API strategy for our partner program"
- "Plan the technical structure for white-labeling our product"
- "What SDK should we build for partners?"
- "Should our API be open or private?"
- "Design the marketplace listing integration"
- "How should we structure multi-tenant infrastructure for OEM partners?"
- "Plan technical onboarding for partners"
- "Architecture for an open source + commercial model"

---

## Phase 1: Apply Gawer's 4-Lever Framework to Architecture (Framework D)

Every major technical architecture decision in a partnership maps to one of Gawer's 4 levers. Work through each lever before drawing architecture:

### Lever 1 — Scope of the Firm: What Do You Build vs. What Do Partners Build?

The most consequential architectural decision. Getting this wrong either kills the ecosystem (you build everything, leaving nothing for partners) or cedes value (partners build things you should own).

**Decision matrix:**

| Capability | Build Internally | Let Partners Build | Rationale |
|-----------|-----------------|-------------------|-----------|
| Core product functionality | ✓ | | Competitive moat; partners can't replicate |
| Vertical-specific customization | | ✓ | Partners have domain expertise you lack |
| Adjacent integrations | | ✓ | Long tail; not worth building all |
| Industry certifications | | ✓ | Partners carry the compliance burden |
| Last-mile implementation | | ✓ | Partners closer to customer |
| [Custom row for your product] | | | |

**Gawer's warning:** Internalizing too much antagonizes complementors and kills ecosystem participation. The healthy pattern is a stable core (yours) + vibrant complement layer (partners').

### Lever 2 — Product Technology Design: Interface Architecture

**Decide the interface structure — which boundaries to open and how:**

```
Interface Architecture Decision Tree

Is this a competitive moat capability?
  YES → Keep internal; expose through limited, metered API
  NO → Is standardization valuable (multiple partners need it)?
      YES → Define open standard; publish OpenAPI spec
      NO → Is it a partner-specific integration?
           YES → Build partner-specific connector
           NO → Expose through generic webhook/event system
```

**Interface inventory** — for each technical boundary, decide:

| Interface | Type | Openness Level | Auth Model | Rate Limits | Versioning Policy |
|-----------|------|---------------|-----------|-------------|------------------|
| [API endpoint 1] | REST/GraphQL/gRPC | Public / Partner-only / Private | OAuth 2.0 / API key / mTLS | [req/min] | SemVer; min 12-month deprecation |
| [Webhook events] | Event stream | Public / Partner-only | HMAC signature | N/A | Event schema versioning |
| [Data export] | Batch / streaming | Partner-only | API key + IP allowlist | [GB/day] | Schema versioning |

### Lever 3 — Complementor Relationships: Managing Technical Co-opetition

When partners also compete (or could compete), the technical architecture manages this tension:

**Co-opetition architecture patterns:**

| Scenario | Architecture Pattern |
|----------|---------------------|
| Partner could build competing product using your APIs | Scope API access to exclude core features; grant read but not write on strategic data |
| Partner integrates at data layer (risky) | Data portability standards let you replicate the data if the partnership ends |
| Partner becomes dominant in your ecosystem | Design for multi-homing (keep each technical dependency open to more than one partner) |
| You compete with one partner in some segments | Segment API tiers by use case; allow partner access only to non-competing scope |

**Jansen's multi-homing principle (Framework I):** Reduce mutual dependency at the technical level. Neither party depends on the other's technical implementation so much that switching causes catastrophic disruption. Design clean separation layers.

### Lever 4 — Internal Organization: Technical Ownership

| Responsibility | Owner | Governance |
|---------------|-------|-----------|
| Public API roadmap | Platform Engineering + Partnership Team | Quarterly review; partner input via advisory board |
| Partner onboarding tooling | Developer Experience (DX) team | SLA: sandbox provisioned in < 1 business day |
| Certification test suite | QA + Platform Engineering | Annual review; partners notified 90 days before changes |
| SDK maintenance | Platform Engineering | SemVer; patch releases on security issues within 48h |
| Partner integration support | Partner Engineering / Solutions Engineering | SLA per tier (Gold: 4h; Silver: 1BD; Registered: 3BD) |

---

## Phase 2: Apply Parker's Openness Framework (Framework F)

Three dimensions of openness need an explicit decision; the combination determines your ecosystem strategy:

| Dimension | Option A | Option B | Option C | Your Decision |
|-----------|----------|----------|----------|--------------|
| **Platform governance** | Proprietary (you control all rules and roadmap) | Shared governance (partner advisory board has input) | Open foundation (independent governance body) | |
| **Developer access** | Closed (approved partners only; no public API) | Controlled open (public API; rate-limited; ToS) | Fully open (OSS; no approval required) | |
| **User access** | Restricted (apply to become a partner) | Verified self-serve (sign up; auto-approve; sandbox immediate) | Fully public (no approval; instant access) | |

**Strategic profiles:**

| Profile | Openness Combination | Best For |
|---------|---------------------|---------|
| **Closed Platform** | Proprietary + Closed + Restricted | Enterprise SaaS with high-value, certified integrations; OEM focus |
| **Controlled Ecosystem** | Proprietary + Controlled Open + Verified self-serve | Mid-market SaaS building integration marketplace; reseller + certified model |
| **Open Platform** | Shared/Open governance + Fully open + Public | Developer-first products; OSS strategy; standards-building plays |
| **Hybrid** | Shared governance + Controlled open + Verified self-serve | Most mature SaaS partnerships; recommended default |

---

## Phase 3: Reference Architectures by Partnership Model

### Technology Integration / Marketplace Architecture
```
Partner Integration Stack
├── API Gateway (Kong, AWS API Gateway, Apigee)
│   ├── Rate limiting (per partner tier)
│   ├── Auth enforcement (OAuth 2.0 / API key)
│   └── Analytics (per-partner usage metering)
├── Public API Layer
│   ├── REST API (versioned: /v1/, /v2/)
│   ├── GraphQL (optional; complex queries)
│   └── Webhooks (event-driven; HMAC-signed payloads)
├── Identity & Authorization
│   ├── OAuth 2.0 + PKCE (user-delegated flows)
│   ├── API key management (scoped, rotatable, per-partner)
│   └── Permission scopes (least privilege; partner-specific)
├── Developer Experience Layer
│   ├── OpenAPI spec (machine-readable; auto-generated docs)
│   ├── Official SDKs (TypeScript/JS, Python — minimum)
│   ├── Sandbox environment (isolated; pre-seeded data; instant provisioning)
│   └── Partner portal (key mgmt, logs, usage analytics, deal registration)
└── Integration Registry
    ├── OAuth app registration and review pipeline
    ├── Marketplace listing metadata and certification status
    └── Partner directory (public-facing)
```

### OEM / White-label Architecture
```
Multi-tenant White-label Stack
├── Tenant Isolation Layer
│   ├── Database: Row-level security (RLS) or separate schemas per tier
│   ├── Compute: Shared pods (Silver) / Dedicated pods (Gold OEM)
│   └── Storage: Tenant-namespaced object storage (S3 prefix isolation)
├── Branding & Customization
│   ├── Theme engine (CSS custom properties / design tokens)
│   ├── Custom domain (CNAME → partner.theirproduct.com; TLS auto-provisioned)
│   ├── Feature flags per tenant (enable/disable modules)
│   └── White-label transactional email (partner's FROM domain via SendGrid/SES)
├── Partner Admin API
│   ├── POST /tenants — provision new customer environment
│   ├── GET /tenants/{id}/usage — usage metrics for invoicing
│   ├── PATCH /tenants/{id}/features — feature flag management
│   └── DELETE /tenants/{id} — deactivation (data retention policy applies)
└── Compliance & Isolation
    ├── Data residency controls (per tenant; region selection)
    ├── Audit logging (all admin actions; per-tenant audit trail)
    └── GDPR data export / deletion API
```

### Reseller / VAR Architecture
```
Channel Partner Portal Stack
├── Partner Portal (web app — Next.js or similar)
│   ├── Customer provisioning (partner-managed tenant creation)
│   ├── License management (seat assignment, feature bundle selection)
│   ├── Usage and billing dashboards (partner's view of all customers)
│   └── Deal registration and pipeline visibility
├── Identity Federation
│   ├── SAML 2.0 or OIDC for partner admin SSO
│   └── Delegated admin (partner admin can manage their customers' RBAC)
└── Reseller API
    ├── POST /customers — provision customer under partner account
    ├── GET /customers/{id}/usage — metered usage for invoicing
    └── PATCH /customers/{id}/licenses — seat count adjustments
```

### Open Source + Commercial Architecture
```
Open Core Stack
├── OSS Core (public GitHub repository)
│   ├── Apache 2.0 or MIT license
│   ├── Core functionality: CLI, self-hosted mode, basic features
│   ├── Contribution workflow: CLA, PR review, CODEOWNERS
│   └── Community infrastructure: GitHub Discussions, Discord
├── Enterprise Layer (private/commercial repository)
│   ├── SSO (SAML, OIDC), RBAC, advanced audit logging
│   ├── Advanced analytics, compliance reporting
│   └── Priority support integrations and SLA-backed uptime
├── Distribution
│   ├── OSS: GitHub releases, Docker Hub, Homebrew, package registries
│   ├── Enterprise self-hosted: Helm chart, Kubernetes operator
│   └── Cloud-managed (your infrastructure): subscription + usage billing
└── Ecosystem Infrastructure
    ├── Plugin/extension registry (partner ecosystem; community-maintained)
    ├── Documentation site (Docusaurus / GitBook — versioned with releases)
    └── Security disclosure process (CVE policy; HackerOne or similar)
```

---

## Phase 4: Partner Developer Experience (DX) Checklist

A partner's first 15 minutes determines whether they continue. Design for rapid time-to-value:

```
Partner DX Requirements Checklist

Getting Started (target: working integration in < 15 minutes)
  [ ] Sandbox auto-provisioned on signup (no manual approval for Registered tier)
  [ ] Pre-seeded sandbox data (realistic; covers common use cases)
  [ ] "Hello World" quickstart in docs (< 10 steps; tested in CI)
  [ ] Postman / Bruno collection published (importable; up-to-date)
  [ ] API key self-service (generate, rotate, revoke in portal without support ticket)

Documentation
  [ ] OpenAPI spec (machine-readable; drives both docs and SDK generation)
  [ ] Conceptual guides (not just reference; explain WHY, not just WHAT)
  [ ] Code examples in TypeScript/JS and Python (minimum)
  [ ] Changelog with deprecation notices (90-day minimum notice on breaking changes)
  [ ] Error reference (every error code with cause and remediation)

SDKs
  [ ] Official SDK for TypeScript/JS (published to npm)
  [ ] Official SDK for Python (published to PyPI)
  [ ] SemVer + automated release notes
  [ ] SDK test suite (partners can run locally against sandbox)

Support
  [ ] Partner Slack / Discord channel (response SLA by tier)
  [ ] Partner engineering contact (named, for Gold tier)
  [ ] Office hours (weekly or biweekly async Q&A)
  [ ] Bug report path (separate from customer support; partner priority)
```

---

## Phase 5: Technical Onboarding Stages

```
Partner Technical Onboarding Pipeline

Stage 1 — Sandbox & Exploration (Day 0–14)
  Trigger: Agreement signed or self-serve signup
  Actions:
    → Sandbox provisioned automatically
    → Docs access + SDK download
    → Welcome email with quickstart guide
  Support: Async (docs, forum, email)

Stage 2 — Integration Development (Day 15–60)
  Trigger: Partner completes "Hello World" milestone
  Actions:
    → Technical kickoff call (Gold/Silver tiers)
    → Weekly async Slack support
    → Optional: code review of integration design
  Support: Partner Slack channel; escalation to partner engineering

Stage 3 — Certification (Day 60–90)
  Trigger: Partner submits integration for review
  Actions:
    → Security checklist review
    → Performance testing (rate limits, error handling, retry logic)
    → Listing review (marketplace metadata, screenshots, descriptions)
  Output: Certified partner badge; marketplace listing live

Stage 4 — Production & Monitoring (Day 90+)
  Actions:
    → Production launch with runbook
    → API monitoring dashboards (uptime, error rates, usage trends)
    → Quarterly integration health reviews (Gold tier: monthly)
  SLA: API availability per tier (Gold: 99.9%; Silver: 99.5%; Registered: best-effort)
```

---

## Phase 6: Security & Compliance Architecture

| Concern | Solution | Standard |
|---------|---------|---------|
| Authentication | OAuth 2.0 + PKCE for user flows; API keys for server-to-server | RFC 6749, RFC 7636 |
| Authorization | Scoped tokens; per-partner permission sets; least privilege | OWASP API Security |
| Tenant isolation | Tenant-aware queries; no cross-tenant data; RLS enforced at DB level | SOC 2 Type II |
| Audit logging | All partner API calls logged: partner ID, timestamp, resource, result | GDPR Art. 30 |
| Rate limiting | Per-partner quotas by tier (requests/min, data volume/day) | Protect platform stability |
| Data residency | Per-tenant region selection; no data crosses region boundaries | GDPR Art. 46 |
| Dependency isolation | Neither party's architecture creates irrecoverable technical lock-in | Jansen multi-homing principle |

---

## Output Format

```
# Technical Architecture: [Partnership Model] — [Partner Name]

## Gawer's 4-Lever Decisions
[Table: lever → decision → rationale]

## Openness Profile (Parker)
[3 dimensions + strategic profile selected]

## Architecture Diagram
[ASCII or description of key system components]

## Key Components — Build vs. Buy vs. Configure
| Component | Decision | Tool/Service | Effort |
|-----------|----------|-------------|--------|

## Partner DX Gap Analysis
[Current state vs. required state; gaps ranked by priority]

## Engineering Effort Estimate
| Component | Complexity | Est. Weeks |

## Recommended Next Steps
- Run /strategic-partnerships:partnerships-monetize to model ROI on engineering investment
- Run /strategic-partnerships:partnerships-recommend for final prioritized action plan
```
