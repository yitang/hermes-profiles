# arXiv Paper Search — Reference

Search and retrieve academic papers from arXiv via their free REST API. No API key, no dependencies — just curl.

## Quick Reference

| Action | Command |
|--------|---------|
| Search papers | `curl "https://export.arxiv.org/api/query?search_query=all:QUERY&max_results=5"` |
| Get specific paper | `curl "https://export.arxiv.org/api/query?id_list=2402.03300"` |
| Read abstract | `web_extract(urls=["https://arxiv.org/abs/2402.03300"])` |
| Read full paper (PDF) | `web_extract(urls=["https://arxiv.org/pdf/2402.03300"])` |

## Search Query Fields

| Prefix | Field | Example |
|--------|-------|---------|
| `au:` | Author | `au:goodfellow` |
| `ti:` | Title | `ti:generative+adversarial` |
| `abs:` | Abstract | `abs:reinforcement+learning` |
| `cat:` | Category | `cat:cs.LG AND cat:stat.ML` |
| `all:` | All fields | `all:transformer+attention` |

Combine with `AND`, `OR`, `ANDNOT`. Use `+` for spaces. URL-encode special chars.

## Parsing Results

The API returns Atom XML. Parse with python3:

```bash
curl -s "https://export.arxiv.org/api/query?search_query=all:transformer&max_results=3" | python3 -c "
import sys, xml.etree.ElementTree as ET
ns = {'a': 'http://www.w3.org/2005/Atom'}
for entry in ET.parse(sys.stdin).findall('a:entry', ns):
    title = entry.find('a:title', ns).text.strip().replace(chr(10), ' ').replace('  ', ' ')
    authors = ', '.join(a.find('a:name', ns).text for a in entry.findall('a:author', ns))
    link = entry.find(\"a:link[@title='pdf']\", ns)
    pdf = link.attrib['href'] if link is not None else 'N/A'
    summary = entry.find('a:summary', ns).text.strip()[:200]
    print(f'{title}\\n  Authors: {authors}\\n  PDF: {pdf}\\n')
```

## Getting Full Text

```bash
# Read PDF content via web_extract (converts to markdown)
web_extract(urls=["https://arxiv.org/pdf/2402.03300"])

# Or download the PDF
curl -o paper.pdf "https://arxiv.org/pdf/2402.03300"
```

## Category Search

Common cs categories: `cs.AI`, `cs.LG`, `cs.CL`, `cs.CV`, `cs.NE`, `cs.IR`, `cs.SE`
All categories: https://arxiv.org/category_taxonomy

```bash
curl "https://export.arxiv.org/api/query?search_query=cat:cs.LG+AND+abs:attention&max_results=10&sortBy=submittedDate&sortOrder=descending"
```
