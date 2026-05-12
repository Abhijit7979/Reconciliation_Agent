# Problem Statement — Automated Bank Reconciliation Agent

**Working title:** ReconAgent — an AI-native bank reconciliation agent for small businesses.

---

## 1. Background

Every small business owner or solo bookkeeper performs the same monthly ritual: open the bank statement, open the folder of customer invoices issued, open the folder of vendor bills received, and manually tie every bank line to the document that explains it. Anything that doesn't tie becomes an exception to investigate.

This work is:
- **Repetitive** — the same pattern of matching, every month, for every business.
- **Slow** — typically 5–10 hours per month for a small business, more for accounting firms running multiple clients.
- **Error-prone** — a missed match becomes a misstated book and, at year-end, a tax-prep problem.
- **Done late** — it gets pushed after the "real" work, which compounds the error rate.

Existing tools (QuickBooks bank rules, Xero, Dext, Ramp) reduce the burden but still leave meaningful manual residue, especially when source documents are a mix of digital PDFs and phone-scanned receipts, and when the user wants a clean audit trail rather than just a green checkmark in the ledger.

## 2. Problem

> Given (a) a folder of customer invoices, (b) a folder of vendor bills, and (c) a bank statement PDF for the same period, automatically reconcile each bank statement line to the document that explains it, and produce an Excel audit report that conforms to a provided template.

## 3. Primary user

**SMB owner or solo bookkeeper** who:
- Manages 1–3 sets of books.
- Receives invoices and bills as PDFs (some digital, some scanned).
- Downloads bank statements as PDFs.
- Needs a defensible audit trail, not just a "matched / not matched" verdict.

## 4. Why this is the #1 problem to solve

1. **Universal pain.** Every business with a bank account does this — the addressable surface is enormous, and the workflow is nearly identical across industries.
2. **Crisp input/output contract.** Folders of PDFs in, one Excel report out. The task is well-defined, which makes correctness verifiable.
3. **Verifiable correctness.** A reconciliation either ties or it doesn't. Unlike open-ended generation tasks, this problem has a ground truth, which makes performance honest to measure.
4. **AI-native fit.** The task naturally combines OCR, document understanding (extracting amount / reference / date / counterparty from heterogeneous layouts), entity normalization, and structured output generation — exactly the surface AI agents are well-suited for.
5. **Demonstrable ROI.** Hours saved per month is a number the user already knows, so the value proposition needs no education.

## 5. Inputs

| Input | Format | Notes |
|---|---|---|
| `invoices/` | Folder of PDFs | Customer invoices issued (accounts receivable). Mix of digital-born and scanned. |
| `bills/` | Folder of PDFs | Vendor bills received (accounts payable). Mix of digital-born and scanned. |
| `bank_statement.pdf` | Single PDF | Period statement from the user's bank. Credits = inflows, debits = outflows. |
| `sample_template.xlsx` | Excel | Reference schema for the audit report. The agent's output must conform to this layout. |

## 6. Output

A single `audit_report.xlsx` that matches the structure of `sample_template.xlsx`, containing at minimum:
- **Matched section** — bank line ↔ invoice/bill pairs, with amount, date, reference number, and counterparty.
- **Unmatched bank lines** — money moved without a supporting document on file.
- **Unmatched documents** — invoices/bills with no corresponding bank line in the period.
- **Summary** — counts and totals per category.

## 7. Reconciliation logic (v1)

**Scope:** two-way matching.
- Bank **credits** (inflows) → matched against **invoices** (AR).
- Bank **debits** (outflows) → matched against **bills** (AP).

**Match rule (strict):** a bank line is considered matched to a document **iff**
1. The amounts are exactly equal, **and**
2. The reference number on the document appears in the bank line's description / memo field.

No fuzzy matching, no amount tolerance, no name-similarity scoring in v1. A line that doesn't satisfy both conditions is left **unmatched** and surfaced in the report — a human reviews it. This favors precision over recall, which is the right tradeoff for an audit artifact.

## 8. Out of scope (v1)

- Multi-currency / FX conversion.
- Partial payments and split allocations (one invoice paid in two installments).
- Fuzzy / probabilistic matching with confidence scores.
- Direct write-back to QuickBooks, Xero, or any ledger system.
- General journal entries (only payments are reconciled).
- Bank statements in formats other than PDF (CSV / OFX / MT940 deferred).

## 9. Success criteria

| Metric | Target |
|---|---|
| Precision on declared matches | ≥ 99% (a declared match is almost never wrong) |
| Recall on a clean digital-PDF test set | ≥ 95% |
| Recall on a mixed digital+scanned test set | ≥ 80% |
| Wall-clock time on a 100-line statement | ≤ 5 minutes |
| Output conforms to template schema | 100% |
| Sensitive inputs never logged or transmitted to third-party APIs without user opt-in | always |

## 10. Constraints and assumptions

- Documents are in English.
- Single currency per run.
- Reference numbers are present and unique within the period (this is what makes strict matching viable).
- Bank statements have a parseable line-item table (most do).
- The user runs the agent locally; no cloud upload of financial documents is required.

## 11. Open questions

- [ ] Should the agent attempt to infer reference numbers from bank-line free text when the bank cleaned them up (e.g., `INV-1234` shows as `INV1234` or `1234`)? — leaning yes, normalized-form comparison still counts as "strict."
- [ ] How should the report handle a single bank line that appears to match more than one document with the same amount + reference? — proposed: flag as ambiguous, list all candidates, do not auto-pick.
- [ ] What is the canonical column set the template expects? (Deferred until the template is reviewed.)
