# Batch Financial Statement Extraction (pdftotext + regex)

Extract structured data from multiple annual PDF statements where the
template changes over time.

## Pattern

1. **Batch extract** all PDFs with `pdftotext`
2. **Detect format** per file (old vs new template) by testing for a
   marker phrase unique to one format
3. **Anchor regex** to surrounding text, not position — numeric values
   drift across templates but descriptive text (`"How much money you
   already have in your plan"` vs `"Your pension pot value"`) stays stable
4. **Deduplicate** by statement end-date: if two statements cover
   overlapping periods, keep the one with the later end-date

## Format detection (example: L&G pension statements)

```python
text = subprocess.run(['pdftotext', path, '-'],
                      capture_output=True, text=True).stdout

if 'How much money you already have in your plan' in text:
    # New format (2023+)
    current = re.search(
        r'How much money you already have in your plan\n£([\d,]+\.\d{2})',
        text
    )
    period = re.search(r'This year \(([^)]+)\)', text)
else:
    # Old format (2017-2022)
    current = re.search(
        r'pension pot value.*?£([\d,]+\.\d{2})',
        text, re.DOTALL
    )
    period = re.search(r'STATEMENT PERIOD:\s*(.+?)(?:\n|$)', text)
```

## Deduplication

When statement periods shift (e.g. April→September→March→April),
keep one per year:

```python
by_year = {}
for r in results:
    year = r['end_date'][:4]
    if year not in by_year or r['end_date'] > by_year[year]['end_date']:
        by_year[year] = r
```

## Pitfalls

- **Bullet points in PDFs** render as `l` characters — they interfere
  with greedy regex patterns. Prefer anchored lookahead over `.*?` when
  bullets appear between values.
- **Annuity cost vs pot value** — financial statements often show both
  the pot value AND "£X to buy £1,000/year income". Anchor to the
  section header, not just the largest number on the page.
- **Format changes at boundary years** — 2022 L&G statements exist in
  BOTH old and new formats. Always test for the new format marker first.
- **pdftotext mangles tables** — multi-column layouts become
  interleaved text. For table-heavy PDFs, prefer pymupdf.
