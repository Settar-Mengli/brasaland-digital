# CONTEXT - Brasaland
## Milestone 8 - Agent Memory and Self-Improvement

Project-specific context for the memory/self-improvement work. Specializes
CONTEXT-company.md for the memory milestone. Where this file and a screenshot disagree,
this file wins; where it is silent, CONTEXT-company.md applies (its Section 7 never-store
rules still hold in full, in addition to Section 3 below).

---

## 1. Why this memory matters

The agent already knows Brasaland's 14 locations (Colombia and Florida), queries the
Incidents Manager and inventory through the MCP Server, and stays inside its guardrail.
The problem Felipe Guerrero (Operations Director) reports: location managers repeat the same
corrections week after week - "the Medellin meat supplier delivers on Tuesdays, not Mondays,"
"the Miami location closes at 10pm on Fridays, not 9pm" - and the agent keeps treating them as
brand-new questions every time.

---

## 2. What IS worth remembering

- Recurring operational corrections per location: real opening/closing hours, specific
  supplier delivery days, local exceptions to a standard procedure.
- Context from a resolved escalation: if a "no sales in 2 hours" alert turned out to be a known
  issue (e.g. a scheduled power outage in that area), remember it so it isn't re-escalated.
- A location manager's communication preferences: if Carlos Jimenez (senior supervisor) always
  wants reports in a specific format, that's memorable.

---

## 3. What must NEVER enter memory

(In addition to CONTEXT-company.md Section 7.)
- Brasa Points customer personal data beyond what's strictly operational - it lives in the CRM,
  not agent memory.
- Payroll figures or individual staff compensation across the 14 locations.
- Anything that only applies to a one-off conversation with no repeatable pattern - a single
  customer complaint on a single day is NOT memorable. The discriminator is not "is this a
  fact" but "is this a recurring operational pattern."

---

## 4. Self-Evaluation examples

Should generate a memory proposal:
1. "Actually the vegetable supplier in Zaragoza... wait, I mean Medellin, delivers on
   Wednesdays, not Tuesdays like you said before." (Proposal must capture the FINAL corrected
   value - Medellin / Wednesdays - not the retracted Zaragoza / Tuesdays.)
2. "The Miami Beach location now closes at 11pm on weekends, that changed last month."
3. "That zero-sales alert at location 7 was because of a power outage, not a POS error - it's
   happened twice this month already."

Should NOT generate a proposal:
1. "What was yesterday's average ticket in Bogota?" (one-off query; the data lives in the
   telemetry pipeline, not agent memory).
2. "Thanks, that answers my question." (conversation closing; nothing new to remember).
3. "Can you translate this into English for Ashley's report?" (single-use task; no lasting value).

---

## 5. Suggested consolidation (design decision - justify it)

With 14 active locations, episodic memory can grow fast if not grouped by location. Consider
having consolidation summarize by location + category (hours, suppliers, known incidents)
instead of storing every correction as a loose entry. This is a design decision to justify,
not a fixed requirement.

---

## 6. Company constraints

Brasaland operates across two currencies (COP/USD) and two languages. If the agent supports
bilingual operation, the memory proposal and user confirmation must work in the chosen base
language - do not assume the user will always correct it in Spanish.
