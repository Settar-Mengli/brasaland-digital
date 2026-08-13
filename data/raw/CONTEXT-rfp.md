# CONTEXT — RFP Workflow (Milestone 9)

## 1. Purpose & scope
Governs the agentic RFP intake/response/approval workflow (M9 Parts 1–3). This is the RFP
spec ONLY; the agent-arc specs (CONTEXT-company / CONTEXT-guardrails / CONTEXT-memory) are
separate and unrelated. All RFP entities persist to PostgreSQL/Supabase (project
brasaland-m5) via SQLModel — never TinyDB/JSON. HTTP lives in services/rfp (port 8017);
the graph lives in data/pipelines/rfp_intake/; uploaded PDFs are stored under data/raw/.

## 2. Business framing
Brasaland has no Sales department. Corporate RFPs (catering contracts, co-branding, resort
concessions) arrive to Camila Ospina (Marketing). The agentic workflow replaces the manual
WhatsApp-and-wait process. KPI: RFP upload → final document in under 2 business days.

### 2.1 Departments (exact ids — use verbatim in code + graph state)
- marketing — Camila Ospina — brand terms, exclusivity, co-branding, offer validity. OWNS the ticket.
- operaciones — Felipe Guerrero — operational feasibility: kitchen/staff capacity, setup times, cost per event.
- procurement — Lucía Fernández — ingredient cost by volume, supplier lead times.
- training — Jake Morrison — if a new recipe/standard is needed: development + certification time.
Not every RFP needs all four — the classifier/orchestrator decides which apply from the document.

### 2.2 Entities (SQLModel → Supabase)
- Ticket: ticket_id, rfp_id, status, raw_pdf_path, created_at, updated_at
- RFP metadata: client_name, location, service_type, scope, deadline, budget_range (optional), departments_needed, readability metrics
- DepartmentSection: department_id, key_aspects (P1), draft_content (P2), evaluation_results, approval_status (pending|approved|rejected), approver, approved_at
- FinalDocument: ticket_id, sections, total_estimated_value, generated_at
Missing figures (volume/budget/diner count) → record under open_questions; NEVER invent numbers not in the document.

### 2.3 Ticket lifecycle (7 statuses — same ticket P1→P3)
analyzing → discarded | intake_complete (P1) → drafting → under_evaluation (P2) → waiting_for_approval → done (P3).

### 2.4 FinalDocument format
One FinalDocument per ticket. Rendered shape (synthesis must match):

- Header: client_name, location, service_type, generated_at, ticket_id.
- Sections in FIXED order marketing → operaciones → procurement → training (omit
  departments not on the ticket). Each section: department id + owner from §2.1;
  the approved draft_content; stamp `approved by {owner} at {approved_at}`.
- Arbitration outcomes: any §7 trigger that fired (cost-vs-feasibility,
  setup-sla-breach, ceo-threshold) and the resolution taken.
- CEO line: only when the contract is above $50,000 USD/year —
  `CEO approval: Mariana Restrepo, {approved_at}`.
- total_estimated_value: dual-currency string `USD X / COP Y` (§5). DERIVED FROM
  metadata budget_range — NOT a sum of per-section cost keys. If budget_range is
  missing/unstated, omit the value (do not invent); record under open_questions.

## 5. Business constraints (compliance evaluator rulebook)
- Every price in BOTH COP and USD.
- Every proposal mentions the 3 brand pillars at least once: consistent quality, warm experience, speed of service.
- No section promises setup/delivery under 10 business days.
- No proposal names competitors.
- Every proposal includes an offer validity period (30 days from issuance).
- Contracts above $50,000 USD/year require extra CEO (Mariana Restrepo) approval before the final document.

## 7. Conflict triggers (arbitration node — fixed arbiter, NOT an LLM)
- cost-vs-feasibility: procurement's ingredient/cost estimate can't support the per-cover price implied by operaciones → arbiter Camila → raise price or reduce scope; force request_changes.
- setup-sla-breach: any section promises setup/delivery under 10 business days → Felipe rejects, Camila escalates → force request_changes until ≥10 days everywhere.
- ceo-threshold: estimated annual value > $50,000 USD and CEO approval pending → Mariana → block final synthesis until CEO approves; reject path if CEO rejects.

## Seed RFPs (test fixtures under data/raw/seed/)
- sunset-bay-resorts.pdf — FORMAL, valid → ACCEPT. Co-branded concession across 3 Florida resorts, exclusivity + new signature menu, ~$60–75k USD/yr. Triggers all four departments (incl. training for the new menu). >$50k → CEO approval required in P3.
- andes-tech-solutions.pdf — INFORMAL email, valid → ACCEPT. Weekly catering for 220 employees in Medellín, 12-month contract, standard menu. Triggers marketing/operaciones/procurement; NOT training. Budget unstated → open_questions.
- franchise-inquiry.pdf — INVALID → DISCARD. Franchise question with no scope, budget, or deadline.
