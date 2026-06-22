# Bank Export Format Patterns

Encountered during personal finance data consolidation (UK banks).
Each entry includes the header, dedup strategy, and detection rules.

## Barclays Premier (Current Account)

**CSV format (Barclays native export):**
```
Number,Date,Account,Amount,Subcategory,Memo
,2017-12-15,Barclays Premier Account,600,Income/Rental Income/Rental income (whole property),LIN S KATIE LIN-RENT FT
```

- 6 columns by header name
- Debited amounts are negative
- `Number` column is sparsely populated (~1376/1549 rows)
- Dates in YYYY-MM-DD or DD/MM/YYYY
- Dedup: `(date, amount, description_lower)` where description = memo column

**Detection:** 6+ cols with `number`, `date`, `account`, `amount`, `memo`

**OFX format (Barclays OFX download — ~1 year, confirmed on 2026-06-05):**
- Uses `<BANKACCTFROM>` tag, same structure as HSBC OFX
- `<STMTTRN>` fields: `TRNTYPE`, `DTPOSTED`, `TRNAMT`, `FITID`, `NAME`
- `DTPOSTED` uses `[-5:EST]` timezone suffix (e.g. `20260526000000[-5:EST]`)
- No `<MEMO>` field in Barclays OFX transactions (unlike HSBC which includes MEMO)
- No per-transaction balance — only `<LEDGERBAL>` closing balance at end of file
- Dedup by FITID (exact)
- File example: `~/Downloads/barclays_2025_07_05_2026_06_05.ofx` — 2,389 lines, covers 2025-07-05 to 2026-06-02
- Detection: content contains `<STMTTRN>` AND `FITID` but no `<MEMO>` within transactions (distinguishes from HSBC OFX)
- **Not a CSV** — detect by failing CSV header check

**Balance strategy for Barclays:**
One OFX download provides the `<LEDGERBAL>` anchor. The CSV history (`barclays-premier.csv`, 2017→present) provides a continuous transaction chain. Backward-wind from the OFX anchor through the CSV gives running balances for every transaction back to 2017. No format barrier — the formula `balance_before = balance_after - amount` works on any data with an `Amount` field.

## AMEX Gold (Preferred Rewards Gold)

**CRITICAL: Sign convention flip at 2022-01-01.** Amex UK changed their CSV export format at the year boundary. Detect this by inspecting the first and last few rows of the CSV:
- Pre-2022: spend is **negative** (e.g. `-129.61`), payments are **positive** (e.g. `+2873`)
- Post-2022: spend is **positive** (e.g. `4.99`), payments are **negative** (e.g. `-1691.27`)

**Root cause of the flip:** The source of the data changed. Pre-2022 data was downloaded via **MoneyHub** (a third-party aggregator), which used the standard OFX sign convention (negative = spend). Post-2022 data came from **direct Amex CSV downloads**, which Amex exports with inverted signs (positive = spend). The two sources also differ in metadata: MoneyHub downloads included categorised `Category`/`Subcategory` fields, while direct Amex CSVs have empty or sparse category columns. The import pipeline stored both sources verbatim without normalising.

The import pipeline must normalise one period to match the other. The QBO convention (negative = spend, positive = payment) matches the pre-2022 format. Fix: negate all post-2021 amounts (`WHERE date >= '2022-01-01'`).

**Note on balance:** Amex UK offers **QBO (QuickBooks) format** as a download option — this is OFX under the hood and confirmed to contain `<LEDGERBAL>` / `<BALAMT>` inside a `<CCSTMTTRNRS>` block. Downloaded and verified on 2026-06-05 (`~/Downloads/activity.qbo`). The balance anchor lets the backward-wind method apply to the existing CSV history the same way it does for Barclays. See §Backward-Wind Method below.

**QBO format details (confirmed):**
- File extension `.qbo` but is OFX XML/SGML under the hood
- OFXHEADER: 200, VERSION: 202 (not 102 like Barclays/HSBC)
- Uses `<CREDITCARDMSGSRSV1>` / `<CCSTMTTRNRS>` / `<CCSTMTRS>` container tags
- `<CCACCTFROM>` with `<ACCTID>` (uses pipe-delimited format like `CK8A4P07KKYRZHJ|61007`)
- `<BANKTRANLIST>` with `<DTSTART>` / `<DTEND>` tags (same as bank OFX)
- Per-transaction fields: `TRNTYPE` (DEBIT/CREDIT), `DTPOSTED`, `TRNAMT`, `FITID`, `REFNUM`, `NAME`, `MEMO`
- **Confirmed `<LEDGERBAL>` block:**
  ```xml
  <LEDGERBAL>
    <BALAMT>-1327.24</BALAMT>
    <DTASOF>20260605000000.000[-7:MST]</DTASOF>
  </LEDGERBAL>
  ```
- `<BALAMT>` is negative because it's a credit card (balance owed), positive would mean credit on account
- `DTASOF` uses `[-7:MST]` timezone (vs Barclays `[-5:EST]` and HSBC plain UTC)
- Detection: content contains `<CREDITCARDMSGSRSV1>` and `<CCACCTFROM>` (distinct from bank OFX)

**Format 1 — Native 13-col (older):**
```
Date,DateProcessed,Description,Cardmember,Amount,ForeignSpendAmount,NonSterlingFee,ExchangeRate,DoingBusinessAs,MerchantAddress,AdditionalInfo,Category,Subcategory
```

**Format 2 — Short 5-col:**
```
Date,Description,Card Member,Account #,Amount
```

**Format 3 — MoneyHub 9-col:**
```
Account,Date,Original Date,Description,Original Description,Amount,Currency,Category,Budget
```

**Format 4 — New 11-13 col with Reference (current):**
```
Date,Description,Card Member,Account #,Amount,Extended Details,Appears On Your Statement As,Address,Town/City,Postcode,Country,Reference,Category
```
- Dates in DD/MM/YYYY
- Amount column straight (positive for debits, post-2022)
- `Reference` field has unique transaction ID but not used for dedup
- `Category` uses `Category-Subcategory` format (e.g. `Entertainment-Restaurants`)
- AMEX convention (post-2022): negative amounts = credits/refunds

**Detection by format:**
- Native: 12+ cols with `dateprocessed` and `cardmember`
- Short: 5 cols with `date`, `description`, `amount`
- MoneyHub: 8+ cols with `account`, `original date`, `category`, `amount`
- New: 11+ cols with `reference`, `extended details`, `category`, `appears on your statement as`
  - Differentiate Gold vs BA: Gold has `card member` and `account #` in header

## AMEX BA Premium (Companion Voucher)

**Note on balance:** Same situation as AMEX Gold — Amex QBO format includes `<LEDGERBAL>`. Credit cards use `<CCACCTFROM>` (not `<BANKACCTFROM>`) in OFX/QBO, but the `<LEDGERBAL>` structure is the same. Note that Amex balance is \\\"amount owed\\\" (negative = debit owed, positive = credit on the account). For credit cards, forward-accumulation from £0 is simpler than backward-wind (see §Credit Card Shortcut below).

**QBO confirmation (downloaded 2026-06-05):** `~/Downloads/amex_ba.qbo`, 399 transactions, period from 2025-07-09 to 2026-06-05:
```xml
<LEDGERBAL>
  <BALAMT>-179.40</BALAMT>
  <DTASOF>20260605000000.000[-7:MST]</DTASOF>
</LEDGERBAL>
```
Current outstanding balance: **-£179.40**. The QBO period net sum is +£440.60 (net payments > spend in this period).

**Gap in database vs QBO:** Backward-wind from the QBO `<BALAMT>` (-£179.40) through the QBO transactions gives an opening balance of -£620.00 at 2025-07-09. The database's summed transactions before 2025-07-09 (converted to QBO sign convention) give £1,130.37 — a gap of ~£1,750. This means the DB does NOT have a complete history for BA. The pre-QBO-period data in the DB is incomplete or has aged-out transactions. Always verify DB completeness by comparing backward-wound opening balance against the DB's pre-period cumulative sum — if they don't match, the DB is missing data.

**Sign convention:** Same Amex format flip applies — post-2022 amounts are inverted vs pre-2022. Normalise both to QBO convention (negative = spend, positive = payment) during import.

**Format 1 — Old 6-col:**
```
Date,Description,Amount,Type,Category,Notes
```
- `Type` field contains routing info (multi-line)
- `Notes` field has verbose details

**Format 2 — New 11-col with Reference:**
```
Date,Description,Amount,Extended Details,Appears On Your Statement As,Address,Town/City,Postcode,Country,Reference,Category
```
- No `Card Member` or `Account #` columns (unlike Gold)
- `Extended Details` maps to `notes` column in the DB

## HSBC Premier (Current Account)

**CSV format:**
```
Date,Account,Amount,Subcategory,Memo
```
- 3-col variant: `date, description, amount` (no headers)
- Dates in DD/MM/YYYY or YYYY-MM-DD
- Amounts may have commas as thousands separators when quoted (critical for dedup!)
  - E.g. `\"4,976.01\"` — must strip commas or dedup key won't match clean versions
- Debited amounts negative

**OFX format (preferred):**
- Uses `<BANKACCTFROM>` tag
- Contains FITID (unique transaction ID)
- TRNTYPE values: OTHER, CREDIT, DEBIT
- NAME field is the payee, MEMO is additional context
- No per-transaction balance — only `<LEDGERBAL>` closing balance at end of file
- Dedup by FITID

## HSBC Credit Card

**OFX only (no CSV encountered):**
- Uses `<CCACCTFROM>` tag
- Same OFX structure as current account (under `<CREDITCARDMSGSRSV1>`)
- TRNTYPE values: CREDIT (payments), DEBIT (spend)
- No per-transaction balance — only `<LEDGERBAL>` closing balance at end
- `<LEDGERBAL>` confirmed present but very small (-£7.21 as of last download, only 3 transactions)
- Dedup by FITID

**Balance note:** For credit cards, forward-accumulation from £0 is simpler than backward-wind (see §Credit Card Shortcut). The `<LEDGERBAL>` is a validation check against the accumulated total.

## Lloyds (Legacy, Closed)

**CSV format:**
```
Transaction Date,Transaction Type,Sort Code,Account Number,Transaction Description,Debit Amount,Credit Amount,Balance
```
- 21 monthly/yearly files
- Dual-column amount (Debit/Credit) instead of single signed amount
- Sort codes have leading apostrophe in CSV data (`'30-99-83`)
- Dates in DD/MM/YYYY
- Legacy account, no new imports expected

## OFX/QBO Common Structure

OFX comes in two header versions, and QBO (QuickBooks) is a variant:

**OFX v.102 (Barclays, HSBC):**
```
OFXHEADER:100
DATA:OFXSGML
VERSION:102
...
<OFX>
  <SIGNONMSGSRSV1>...</SIGNONMSGSRSV1>
  <BANKMSGSRSV1>  <!-- or <CREDITCARDMSGSRSV1> -->
    <STMTTRNRS>
      <STMTRS>
        <BANKACCTFROM>  <!-- or <CCACCTFROM> for credit card -->
          <BANKID>401100</BANKID>
          <ACCTID>40110004439252</ACCTID>
          <ACCTTYPE>CHECKING</ACCTTYPE>
        </BANKACCTFROM>
        <BANKTRANLIST>
          <STMTTRN>
            <TRNTYPE>OTHER</TRNTYPE>
            <DTPOSTED>20260522000000</DTPOSTED>  <!-- YYYYMMDDHHMMSS -->
            <TRNAMT>7229.45</TRNAMT>
            <FITID>2026052212026141025143910030000</FITID>  <!-- unique ID -->
            <NAME>B        E</NAME>
            <MEMO>CR</MEMO>
          </STMTTRN>
        </BANKTRANLIST>
      </STMTRS>
    </STMTTRNRS>
  </BANKMSGSRSV1>
</OFX>
```

**QBO (QuickBooks) variant — Amex uses this instead of raw OFX:**
- Single-line XML (not pretty-printed with newlines like raw OFX)
- OFXHEADER: 200, VERSION: 202 (vs 102 for raw OFX)
- Uses `<CREDITCARDMSGSRSV1>` / `<CCSTMTTRNRS>` / `<CCSTMTRS>` for credit card accounts
- Uses `<CCACCTFROM>` instead of `<BANKACCTFROM>`
- Still uses `<STMTTRN>` blocks internally — same extraction regex works
- `<LEDGERBAL>` / `<BALAMT>` structure is identical
- Detection: look for `<CREDITCARDMSGSRSV1>` or check header version >= 200

- Extract `<STMTTRN>` blocks with regex: `r'<STMTTRN>(.*?)</STMTTRN>'`
- Date format: `YYYYMMDDHHMMSS` → `YYYY-MM-DD`
- FITID is the dedup key for OFX sources

### `<LEDGERBAL>` — Closing Balance (and Balance Anchor)

After `</BANKTRANLIST>`, OFX files include a single `<LEDGERBAL>` block:

```xml
<LEDGERBAL>
  <BALAMT>4020.87</BALAMT>
  <DTASOF>20260602000000[-5:EST]</DTASOF>
</LEDGERBAL>
```

- `<BALAMT>`: closing balance as of the statement date
- `<DTASOF>`: date balance is as-of (same `YYYYMMDDHHMMSS` format as `DTPOSTED`)

**Critical: this is a single point-in-time figure, not a per-transaction balance.** Neither Barclays nor HSBC OFX includes per-transaction balance fields. However, this single figure is sufficient to derive running balances via the backward-wind method (see §Backward-Wind Method below).

**Lloyds was the only UK bank in this dataset** whose CSV exports included a `Balance` column per row — that account is now closed.

### Backward-Wind Method — Deriving Running Balances from Any Transaction Data

Since `<LEDGERBAL>` gives a single closing balance, and every transaction row has an Amount (regardless of format), you can derive running balances for every transaction:

**The formula:**
```
balance_before = balance_after - amount
```

**Step by step:**
1. Take `<BALAMT>` as the balance **after** the last transaction
2. Sort all transactions by date ascending (oldest → newest)
3. Walk in **reverse** (newest → oldest): for each transaction with amount `X`, compute `balance_before = current_balance - X`
4. Repeat until the first transaction — the last step gives you the **opening balance** for that date range

**Key insight — format-agnostic:** The backward-wind formula works on CSV data too, not just OFX. CSV rows have an `Amount` field. The only requirements are:
- **An anchor** — a known closing balance at some point (e.g. `<LEDGERBAL>` from an OFX download)
- **A continuous transaction chain** — no gaps connecting the anchor back to the point you care about

**Practical example — Barclays from 2017:**
- OFX download `barclays_2025_07_05_2026_06_05.ofx` provides `<LEDGERBAL> £4,020.87`
- CSV history `barclays-premier.csv` has continuous transactions from 2017
- Backward-wind from the OFX anchor through the CSV gives running balances for every transaction back to 2017
- No format barrier, no gaps needed — just continuous data

**Verification — backward-wind should converge to ~£0 at account opening:**  
After fixing sign conventions (e.g. negating post-2021 Amex amounts), backward-wind from the most recent QBO/OFX `<BALAMT>` through the complete corrected transaction history should produce a running balance of approximately £0 at the account opening date. If it doesn't, there are:
1. Missing payments or transactions in the chain (gaps in export history)
2. A sign convention still not normalised
3. The DB has incomplete history (common for accounts added later that weren't backfilled)

**Convergence drift check:** When you download fresh QBO data for a period the DB already covers (e.g. the last year), you can cross-check:
- Backward-wind from new QBO `<BALAMT>` through QBO transactions to get the opening balance at QBO period start
- The DB's cumulative sum for transactions before that date (in QBO sign convention)
- If these two figures differ significantly, the DB has data gaps

**Example (Amex BA):** QBO balance -£179.40 → backward-wound opening balance at 2025-07-09 = -£620.00. DB pre-period sum = £1,130.37 (flipped). Gap of ~£1,750 = missing transactions in DB.

### Credit Card Shortcut — Forward Accumulation

For **credit cards**, you don't even need an anchor. A credit card's running balance is simply the accumulated sum of all transactions from the card's opening (or from £0):

```
running_balance = SUM(all transactions up to this point)
```

- This is simpler than backward-wind — no anchor needed
- Works because credit cards start at £0 balance (no opening deposit)
- The running balance represents **amount owed** (positive = debt, negative = credit on account)
- `<LEDGERBAL>` from QBO/OFX serves as a **validation check**: the accumulated sum should match the `<BALAMT>` (within the statement period)
- Applies to all credit cards: Amex Gold, Amex BA, HSBC Credit Card

**Practical use:** For Amex Gold with 2,099 transactions in the CSV, simply accumulating from the first row gives the running balance at every point. The QBO `<LEDGERBAL>` of -£1,327.24 validates that the most recent period's transactions + carry-over are consistent.

**Note on credit cards and backward-wind:** Same math applies but sign convention matters:
- Debits (spend) *increase* the balance owed
- Credits (payments/refunds) *decrease* the balance owed
- Normalise to your app's sign convention before applying either method

**Practical impact for the pipeline:**
1. **Derive running balances on import** — during import, extract `<LEDGERBAL>` as the anchor, then backward-wind through the imported transaction set to populate a `running_balance` column
2. **Validation** — the net sum of all `<STMTTRN>` amounts should equal the difference between consecutive `<LEDGERBAL>` values (or between zero and the first one for new accounts)
3. **Net worth computation** — `<BALAMT>` from the most recent OFX download for each account gives current account balance without needing running balance
