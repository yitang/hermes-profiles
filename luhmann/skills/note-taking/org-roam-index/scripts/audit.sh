#!/bin/bash
# Zettelkasten vault audit script
# Usage: bash scripts/audit.sh [notes_dir]
# Defaults to: ~/matrix/tools/meta-tools/notes
#
# Reports: file count, fleet/literature/permanent split, orphans,
#   oversized notes, tiny notes, linking stats, filetags, source tracking.

VAULT="${1:-$HOME/matrix/tools/meta-tools/notes}"

if [ ! -d "$VAULT" ]; then
    echo "ERROR: vault not found at $VAULT"
    echo "Usage: $0 [path-to-org-roam-notes-directory]"
    exit 1
fi

cd "$VAULT"

echo "VAULT: $VAULT"
echo ""

# ── 1. FILE COUNT ──
total=$(ls *.org 2>/dev/null | wc -l)
echo "=== 1. FILE COUNT ==="
echo "Total .org files: $total"

# ── 2. FLEET NOTES ──
echo ""
echo "=== 2. FLEET NOTES (unprocessed) ==="
fleet_count=0
for f in *.org; do
    if grep -q "filetags.*fleet" "$f" 2>/dev/null; then
        fleet_count=$((fleet_count + 1))
        echo "  $f"
    fi
done
[ "$fleet_count" -eq 0 ] && echo "  (none)"

# Old-format fleet tag
old_fleet=0
for f in *.org; do
    if grep -q ":fleet:" "$f" 2>/dev/null && ! grep -q "filetags" "$f" 2>/dev/null; then
        old_fleet=$((old_fleet + 1))
    fi
done
echo "  Old-format :fleet: (no filetags): $old_fleet"

# ── 3. LITERATURE NOTES ──
echo ""
echo "=== 3. LITERATURE NOTES ==="
lit_count=0
for f in *.org; do
    if grep -q "filetags.*literature" "$f" 2>/dev/null; then
        lit_count=$((lit_count + 1))
        echo "  $f"
    fi
done
[ "$lit_count" -eq 0 ] && echo "  (none)"

# ── 4. SOURCE TRACKING ──
echo ""
echo "=== 4. SOURCE TRACKING ==="
echo "Notes with #+source:"
src_count=$(grep -rl "^#+source:" *.org 2>/dev/null | wc -l)
echo "  $src_count"
echo "Notes with #+bibliography:"
bib_count=$(grep -rl "^#+bibliography:" *.org 2>/dev/null | wc -l)
echo "  $bib_count"

# ── 5. FILETAGS ──
echo ""
echo "=== 5. FILETAGS IN USE ==="
grep "^#+filetags:" *.org 2>/dev/null | sort | uniq -c | sort -rn | head -30
tagged_count=$(grep "^#+filetags:" *.org 2>/dev/null | wc -l)
echo ""
echo "Total notes with filetags: $tagged_count"

# ── 6. INTERNAL LINKS ──
echo ""
echo "=== 6. INTERNAL LINKS ==="
echo "Notes with [[id:...]] links:"
id_count=0
id_notes=0
for f in *.org; do
    c=$(grep -c '\[\[id:' "$f" 2>/dev/null)
    if [ "$c" -gt 0 ]; then
        id_notes=$((id_notes + 1))
        id_count=$((id_count + c))
        echo "  $f ($c)"
    fi
done
echo "Total [[id:]] links: $id_count across $id_notes notes"
echo ""
echo "Notes with [[file:...]] links:"
file_count=0
file_notes=0
for f in *.org; do
    c=$(grep -c '\[\[file:' "$f" 2>/dev/null)
    if [ "$c" -gt 0 ]; then
        file_notes=$((file_notes + 1))
        file_count=$((file_count + c))
        echo "  $f ($c)"
    fi
done
echo "Total [[file:]] links: $file_count across $file_notes notes"

# ── 7. ORPHANS ──
echo ""
echo "=== 7. ORPHAN NOTES (0 [[id:]] + 0 [[file:]]) ==="
orphan_count=0
linked_count=0
orphan_list=""
while IFS= read -r f; do
    id_links=$(grep -c '\[\[id:' "$f" 2>/dev/null)
    file_links=$(grep -c '\[\[file:' "$f" 2>/dev/null)
    if [ "$id_links" -eq 0 ] && [ "$file_links" -eq 0 ]; then
        orphan_count=$((orphan_count + 1))
        title=$(grep "^#+title:" "$f" | sed 's/#+title: *//')
        wc_raw=$(grep -v "^#" "$f" | grep -v "^:PROPERTIES:" | grep -v "^:END:" | wc -w)
        echo "  $f | title: ${title:-?} | wc: $wc_raw"
    else
        linked_count=$((linked_count + 1))
    fi
done < <(ls *.org)
echo ""
echo "Summary: $orphan_count orphans, $linked_count with links, $total total"
echo "Orphan rate: $((orphan_count * 100 / total))%"

# ── 8. OVERSIZED NOTES (>300 words, potential splits) ──
echo ""
echo "=== 8. NOTES > 300 WORDS (potential splits) ==="
oversized=0
while IFS= read -r f; do
    wc_raw=$(grep -v "^#" "$f" | grep -v "^:PROPERTIES:" | grep -v "^:END:" | wc -w)
    if [ "$wc_raw" -gt 300 ]; then
        oversized=$((oversized + 1))
        title=$(grep "^#+title:" "$f" | sed 's/#+title: *//')
        echo "  $f | ${title:-?} | ${wc_raw} words"
    fi
done < <(ls *.org | sort)
echo "Total oversized: $oversized"

# ── 9. TINY NOTES (<50 words) ──
echo ""
echo "=== 9. NOTES < 50 WORDS ==="
small_count=0
while IFS= read -r f; do
    wc_raw=$(grep -v "^#" "$f" | grep -v "^:PROPERTIES:" | grep -v "^:END:" | wc -w)
    if [ "$wc_raw" -lt 50 ]; then
        small_count=$((small_count + 1))
    fi
done < <(ls *.org)
echo "Total: $small_count ($((small_count * 100 / total))%)"

# ── 10. STRUCTURE NOTES ──
echo ""
echo "=== 10. STRUCTURE/HUB NOTES ==="
for f in index.org ZETTELKASTEN_AUDIT.org WORKFLOW.org keywords.org; do
    if [ -f "$f" ]; then
        lines=$(wc -l < "$f")
        echo "  $f ($lines lines)"
    fi
done

# ── 11. WORD COUNT DISTRIBUTION ──
echo ""
echo "=== 11. WORD COUNT DISTRIBUTION ==="
b0_50=0; b51_100=0; b101_200=0; b201_300=0; b301_500=0; b501p=0
while IFS= read -r f; do
    wc_raw=$(grep -v "^#" "$f" | grep -v "^:PROPERTIES:" | grep -v "^:END:" | wc -w)
    if [ "$wc_raw" -le 50 ]; then b0_50=$((b0_50+1))
    elif [ "$wc_raw" -le 100 ]; then b51_100=$((b51_100+1))
    elif [ "$wc_raw" -le 200 ]; then b101_200=$((b101_200+1))
    elif [ "$wc_raw" -le 300 ]; then b201_300=$((b201_300+1))
    elif [ "$wc_raw" -le 500 ]; then b301_500=$((b301_500+1))
    else b501p=$((b501p+1))
    fi
done < <(ls *.org)
echo "  0-50:    $b0_50 ($((b0_50*100/total))%)"
echo "  51-100:  $b51_100 ($((b51_100*100/total))%)"
echo "  101-200: $b101_200 ($((b101_200*100/total))%)"
echo "  201-300: $b201_300 ($((b201_300*100/total))%)"
echo "  301-500: $b301_500 ($((b301_500*100/total))%)"
echo "  501+:    $b501p ($((b501p*100/total))%)"

echo ""
echo "=== DONE ==="
