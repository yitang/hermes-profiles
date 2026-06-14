# Audit Script — Reusable Python Analysis

This is the core analysis script used in Workflow 2 (Zettelkasten Audit). Copy it into execute_code and adjust the `notes_dir` path for the vault you're auditing.

```python
import os, re, pathlib

notes_dir = os.path.expanduser("~/matrix/tools/meta-tools/notes")
notes = sorted(pathlib.Path(notes_dir).glob("*.org"))

# Parse all notes
all_notes = {}
for f in notes:
    if f.name == "index.org" or f.name.startswith("ZETTELKASTEN"):
        continue
    content = f.read_text()
    m = re.search(r'#\+title:\s*(.*)', content)
    title = m.group(1).strip() if m else f.stem
    m2 = re.search(r':CREATED:\s*\[([^\]]+)\]', content)
    created = m2.group(1).strip() if m2 else ""
    m3 = re.search(r':matrix:\s*(.*)', content)
    tag = m3.group(1).strip() if m3 else ""
    internal_links = re.findall(r'\[\[id:([^\]]+?)\]\[([^\]]*?)\]\]', content)
    file_links = re.findall(r'\[\[file:([^\]]+)\]\[([^\]]*)\]\]', content)
    external_urls = re.findall(r'\[\[(https?://[^\]]+?)\]\[([^\]]*?)\]\]', content)
    has_bib = bool(re.search(r'#\+bibliography|#\+source|#\+reference', content, re.IGNORECASE))
    body = re.sub(r':PROPERTIES:.*?:END:', '', content, flags=re.DOTALL)
    body = re.sub(r'#\+.*', '', body)
    wc = len(body.split())
    all_notes[f.stem] = {
        'filename': f.name, 'title': title, 'created': created,
        'tag': tag, 'wc': wc,
        'internal_links': internal_links, 'file_links': file_links,
        'external_urls': external_urls, 'has_bib': has_bib,
    }

print(f"Total notes: {len(all_notes)}")

# --- ATOMICITY ---
print(f"\n--- ATOMICITY ---")
wc_buckets = {"0-50": 0, "51-100": 0, "101-200": 0, "201-300": 0, "301-500": 0, "501+": 0}
for n in all_notes.values():
    w = n['wc']
    if w <= 50: wc_buckets["0-50"] += 1
    elif w <= 100: wc_buckets["51-100"] += 1
    elif w <= 200: wc_buckets["101-200"] += 1
    elif w <= 300: wc_buckets["201-300"] += 1
    elif w <= 500: wc_buckets["301-500"] += 1
    else: wc_buckets["501+"] += 1
for k, v in wc_buckets.items():
    print(f"  {k:10s}: {v:3d} notes ({v*100//len(all_notes)}%)")

# --- LINKING ---
total_internal = sum(len(n['internal_links']) for n in all_notes.values())
total_file = sum(len(n['file_links']) for n in all_notes.values())
linked_notes = sum(1 for n in all_notes.values() if n['internal_links'] or n['file_links'])
orphans = [n for n in all_notes.values() if not n['internal_links'] and not n['file_links']]
print(f"\n--- LINKING ---")
print(f"  Notes with links: {linked_notes} ({linked_notes*100//len(all_notes)}%)")
print(f"  Orphan notes:    {len(orphans)} ({len(orphans)*100//len(all_notes)}%)")
print(f"  Avg [[id:...]]:   {total_internal/max(len(all_notes),1):.1f}/note")

# --- BROKEN LINKS ---
all_ids = {}
for f in pathlib.Path(notes_dir).glob("*.org"):
    c = f.read_text()
    m = re.search(r':ID:\s*([^\s]+)', c)
    if m:
        all_ids[m.group(1).lower()] = f.name
broken = []
for n in all_notes.values():
    for link_id, _ in n['internal_links']:
        if link_id.lower() not in all_ids:
            broken.append((n['title'], link_id))
print(f"\n  Broken links: {len(broken)}")

# --- SOURCES ---
with_sources = sum(1 for n in all_notes.values() if n['external_urls'] or n['has_bib'])
print(f"\n--- SOURCE TRACKING ---")
print(f"  Notes with external sources: {with_sources} ({with_sources*100//len(all_notes)}%)")
```

## How to use

1. Copy the script above into execute_code({})
2. Adjust notes_dir to the vault path
3. Run — the output gives you raw data for a ZETTELKASTEN_AUDIT.org document
