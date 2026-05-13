---
name: reconciliation
description: >
  Bank reconciliation skill — matches invoices (AR) and bills (AP) against a bank statement
  and generates an Excel audit report using the sample_template.xlsx schema.
  Use this skill whenever the user mentions reconciliation, bank statement matching,
  invoice/bill reconciliation, accounts receivable, accounts payable, or asks to
  match financial documents against bank transactions — even if they don't use the
  word "reconcile". Also trigger when the user provides a folder with bills/, invoice/,
  and a bank statement PDF and wants a report.
---

# Reconciliation Skill

You are performing **bank reconciliation** for a small business. Your job: match every bank
transaction to its source document (invoice or bill), then produce a clean Excel audit report.

## What You Receive

| Input | Type | Description |
|-------|------|-------------|
| `bills/` folder | PDF files | Vendor bills → Accounts Payable (AP) |
| `invoice/` folder | PDF files | Customer invoices → Accounts Receivable (AR) |
| Bank statement | Single PDF | All transactions for the period |
| `reference_excel` (full path provided) | Excel | Output schema — copy this, fill it in |

Expected folder layout:
```
session_folder/
├── bills/          ← vendor bill PDFs
├── invoice/        ← customer invoice PDFs
├── statement.pdf   ← single bank statement PDF
└── output/         ← write your Excel report here
```

## Reconciliation Rules (strict two-way matching)

**Bank credits (inflows) → match against invoices (AR)**
**Bank debits (outflows) → match against bills (AP)**

A bank line is matched to a document **only when both** are true:
1. The amounts are **exactly equal** (no rounding tolerance in v1).
2. The document's reference number appears in the bank line's description or memo field.

**Reference normalization** — before comparing, strip hyphens, spaces, and lowercase everything:
- `INV-1234`, `INV1234`, `inv1234` all compare equal.

If both conditions aren't met → the line is **unmatched**. Never force a match; flag it instead.

If one bank line matches multiple documents (same amount + reference) → mark **AMBIGUOUS**, list all candidates, do not auto-pick.

## Step-by-Step Workflow

### Step 1 — Extract

Parse every PDF using available tools. For each document pull:
- **Amount** (numeric, strip currency symbols)
- **Date** (ISO format preferred)
- **Reference number** (invoice/bill number)
- **Counterparty** (customer name for invoices, vendor name for bills)
- **Description / memo**

For the bank statement, extract every line with: date, description, debit amount, credit amount, running balance, and any reference in the description.

### Step 2 — Normalize

- Reference numbers: lowercase, remove `-`, spaces → e.g. `"INV-2024-001"` → `"inv2024001"`
- Amounts: parse to float, 2 decimal places
- Build lookup tables: `{normalized_ref: document}` for invoices and bills separately

### Step 3 — Match

For each bank line:
1. Determine direction: Credit → look in invoices; Debit → look in bills.
2. Scan the bank description for any normalized reference that exists in the lookup.
3. If found, confirm the amount matches exactly.
4. Record result: `Matched`, `Unmatched`, or `Ambiguous`.

### Step 4 — Generate the Excel Report

**Copy the `reference_excel` file (full path given in the prompt) to the output folder** — never modify the original. Fill in each sheet:

#### Sheet: 📄 Invoices
Columns: `Invoice No. | Invoice Date | Due Date | Customer | Description | Invoice Amount | Tax Amount | Total Due | Payment Received | Payment Date | Bank Ref | Balance Outstanding | Days Overdue | Status | Notes`

- `Status`: one of `Paid`, `Partially Paid`, `Overdue`, `Open`
- `Balance Outstanding` = `Total Due − Payment Received`
- `Days Overdue`: positive int if past due date, else 0
- If matched: fill `Payment Received`, `Payment Date`, `Bank Ref`; set Status = `Paid`
- If unmatched: leave payment fields blank; set Status = `Open` or `Overdue`
- Add a `TOTALS` row at the bottom summing numeric columns

#### Sheet: 🧾 Bills & Expenses
Columns: `Bill No. | Bill Date | Due Date | Vendor | Category | Description | Bill Amount | Tax / GST | Net Payable | Amount Paid | Payment Date | Payment Method | Bank Ref | Balance Remaining | Status | Notes`

- Same status logic as invoices
- `Balance Remaining` = `Net Payable − Amount Paid`
- `Category`: infer from vendor description (e.g. Utilities, Rent, Supplies) if determinable; else leave blank
- Add a `TOTALS` row

#### Sheet: 🏦 Bank Transactions
Columns: `Reference | Transaction Date | Value Date | Description | Debit | Credit | Running Balance | Type | Matched To | Match Type | Reconciled | Reconciled Date | Variance | Notes`

- `Type`: `Credit` or `Debit`
- `Matched To`: document reference (e.g. `INV-001`) if matched, else blank
- `Match Type`: `AR` (invoice) or `AP` (bill) if matched, else blank
- `Reconciled`: `Yes` / `No`
- `Variance`: `0` for exact matches, the difference if partial
- `Notes`: flag ambiguous or unmatched items with a short explanation
- Add a `TOTALS` row

#### Sheet: 📊 Summary Dashboard
Fill in the summary metrics:

| Metric | Formula |
|--------|---------|
| AR — Total invoiced | Sum of all invoice totals |
| AR — Paid / applied | Sum of matched invoice payments |
| AR — Outstanding | AR Total − AR Paid |
| AP — Bills gross | Sum of all bill net payables |
| AP — Paid | Sum of matched bill payments |
| AP — Open balance | AP Gross − AP Paid |
| Bank — Total debits | Sum of all bank debits |
| Bank — Total credits | Sum of all bank credits |
| Bank — Net variance tracked | Credits − Debits |
| Liquidity pulse | Collections (credits) − Disbursements (debits) |

## Output

Save the completed Excel file to the `output/` directory as:
`reconciliation_report_<YYYY-MM-DD>.xlsx`

where the date is today's date.

After saving, print a brief summary:
- Total bank lines processed
- Matched count (AR + AP separately)
- Unmatched bank lines count
- Unmatched document count
- Any ambiguous items that need human review

## Quality Checklist

Before finishing, verify:
- [ ] Every bank line appears in the Bank Transactions sheet
- [ ] Every invoice and bill appears in their respective sheets
- [ ] No document is matched to more than one bank line (unless flagged as ambiguous)
- [ ] TOTALS rows are populated
- [ ] Summary Dashboard values are filled
- [ ] Output file is saved and readable

## Error Handling

- **PDF unreadable**: note it in the Notes column, mark related transactions as unmatched
- **Amount parsing failure**: flag the item for human review with the raw text
- **Duplicate reference numbers**: flag as ambiguous, list all matching documents
- **Missing bank statement**: raise a clear error — reconciliation cannot proceed
- **Missing bills/ or invoice/ folder**: raise a clear error with expected folder structure
