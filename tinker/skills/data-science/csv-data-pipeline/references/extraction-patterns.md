# Statement Extraction Patterns

Real-world regex patterns that successfully extracted data from specific
financial documents. Reference for future parsing work.

## L&G Workplace Pension — Benefit Statements

### Old format (2018-2020)

```
STATEMENT PERIOD: 6 April 2017 to 5 April 2018

THE VALUE OF YOUR PENSION POT AT 5/4/2018

£0.00          ← previous year value
£7,172.05      ← amount paid in
£7,092.43      ← current pot value
```

Extraction:
```python
# Period end date
period_end = re.search(r'STATEMENT PERIOD:.*?to (.+)', text)

# Pot values — three £ amounts after "YOUR PENSION POT"
pot_match = re.search(
    r'Your pension pot value.*?\n.*?£([\d,]+\.\d{2})'
    r'.*?\n.*?£([\d,]+\.\d{2})'
    r'.*?\n.*?£([\d,]+\.\d{2})',
    text, re.DOTALL
)
# pot_match.group(1) = previous year, group(2) = paid in, group(3) = current

# Investment gain/loss
inv = re.search(r'investment (gain|loss)', text)
```

### New format (2023-2026)

```
How much money you already have in your plan
£167,196.87

This year (6 April 2025 - 5 April 2026)

£141,993.35    ← previous year value

Your employer has added*
£7,130.13      ← contributions

Your investments have increased in value by
£18,621.98     ← investment change

Charges paid†
£548.59
```

Extraction:
```python
# Current pot value
pot = re.search(r'How much money you already have in your plan\n£([\d,]+\.\d{2})', text)

# Period: "This year (6 April XXXX - 5 April XXXX)"
period = re.search(r'This year \(([^)]+)\)', text)
end_date = period.group(1).split(' - ')[1]  # "5 April 2026"

# Previous year value
prev = re.search(r'This year \([^)]+\)\n\n£([\d,]+\.\d{2})', text)

# Employer contributions
contrib = re.search(r'employer has added\*\n\n£([\d,]+\.\d{2})', text)

# Investment change
inv = re.search(r'investments have (increased|decreased) in value by\n\n£([\d,]+\.\d{2})', text)
```

## Barclays Mortgage Offer PDF

```
Value of the property to prepare this Offer: £820,000.00
Maximum available loan amount relative to the value of the property 75.00%
Amount and currency of the loan to be granted: £461,054.79
```

Extraction:
```python
valuation = re.search(r'Value of the property[^£]*£([\d,]+\.\d{2})', text)
loan = re.search(r'Amount and currency of the loan[^£]*£([\d,]+\.\d{2})', text)
ltv_max = re.search(r'Maximum available loan amount relative[^.]*?(\d+\.\d+)%', text)
```

## NatWest ESIS (European Standardised Information Sheet)

```
Value of the property assumed to prepare this information sheet: £670,000.00
Maximum available loan amount relative to the value of the property: 85.00%
Amount and currency of the loan to be granted: £545,000.00
```

Extraction:
```python
valuation = re.search(r'Value of the property assumed[^£]*£([\d,]+\.\d{2})', text)
loan = re.search(r'Amount and currency of the loan to be granted[^£]*£([\d,]+\.\d{2})', text)
ltv_max = re.search(r'Maximum available loan amount relative[^:]*:\s*(\d+\.\d+)%', text)
```

## Vanguard XLSX — Cash + Investment Transactions

Sheet structure:
- Sheet 1: Summary (closing balances)
- Sheet 2: ISA — two sections: "Cash Transactions" then "Investment Transactions"
- Sheet 3: Pension — same two-section pattern

Cash Transactions columns: Date, Details, Amount, Balance
Investment Transactions columns: Date, InvestmentName, TransactionDetails, Quantity, Price, Cost

Section detection: match first column text against "Cash Transactions" / "Investment Transactions".
Filter out summary rows where first column = "Cost" or "Balance".

## L&G Transaction CSV

```
Date,Transaction description,Payments in,Payments out,Unit Investments,Fund name,Units bought,Units sold,Price per unit (p)
2026-05-27,Your Employer's regular contribution,1200,0,1200,L&G PMC 2050-2055 Target Date Fund 3,59.092,0,2030.73
```

Notes:
- Price is in PENCE (2030.73 = £20.3073 per unit)
- Fund name changed over time (Diversified Fund 3B → Target Date 2050-2055)
- CSV exports can overlap — pick the broadest date range
