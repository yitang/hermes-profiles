#!/usr/bin/env python3
"""Template for testing account detection logic with synthetic CSV/OFX headers.

Copy this file, add test cases for your sources, and run before deploying changes to detect.py.

Usage:
    PYTHONPATH=src python3 test_detection.py

Key principles:
- Test filename-hinted files by placing them in temp directories (not just mkstemp)
- Clear __pycache__ between test runs after modifying detection logic
- Test ambiguous patterns that could be misrouted
"""

import sys
import os
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from finance_pipeline.detection import detect_account, detect_ofx_account


def test_csv(headers, expected):
    """Test detection with a CSV using a temporary filename."""
    fd, path = tempfile.mkstemp(suffix='.csv')
    os.write(fd, ','.join(headers).encode('utf-8'))
    os.close(fd)

    detected = detect_account(path)
    status = "OK" if detected == expected else f"FAIL (got {detected!r})"
    print(f"  {'OK' if detected == expected else 'XX'} {headers[0]:<25s} ... → {detected or 'None':<20s} [{status}]")
    os.unlink(path)
    return detected == expected


def test_csv_named(name, headers, expected):
    """Test detection with an explicit filename (for filename-hint routing)."""
    tmpdir = tempfile.mkdtemp()
    path = os.path.join(tmpdir, name)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(','.join(headers))

    detected = detect_account(path)
    status = "OK" if detected == expected else f"FAIL (got {detected!r})"
    print(f"  {'OK' if detected == expected else 'XX'} {name:<25s} → {detected or 'None':<20s} [{status}]")
    os.unlink(path)
    return detected == expected


def test_ofx(name, content, expected):
    """Test OFX detection with synthetic OFX XML content."""
    fd, path = tempfile.mkstemp(suffix='.ofx')
    os.write(fd, content.encode('utf-8'))
    os.close(fd)

    detected = detect_ofx_account(path)
    status = "OK" if detected == expected else f"FAIL (got {detected!r})"
    print(f"  {'OK' if detected == expected else 'XX'} {name:<25s} → {detected or 'None':<20s} [{status}]")
    os.unlink(path)
    return detected == expected


if __name__ == '__main__':
    print("=" * 80)
    print("ACCOUNT DETECTION TESTS")
    print("=" * 80)

    passed = 0
    total = 0

    # ── CSV detection (flat files, no folder context) ────────────────────────
    print("\nCSV Detection (flat files):")
    tests = [
        # Add your test cases here. Format: (description, header_list, expected_parser_or_None)
    ]

    for name, headers, expected in tests:
        if test_csv(headers, expected):
            passed += 1
        total += 1

    # ── Filename-hinted detection ───────────────────────────────────────────
    print("\nFilename-Hinted Detection:")
    named_tests = [
        # Format: (filename, header_list, expected_parser)
    ]

    for name, headers, expected in named_tests:
        if test_csv_named(name, headers, expected):
            passed += 1
        total += 1

    # ── OFX detection ───────────────────────────────────────────────────────
    print("\nOFX Detection:")
    ofx_bank = "<?xml version=\"1.0\"?><OFX><SIGNONMSGSRSV1><SONRS><STATUS><CODE>0</CODE></STATUS></SONRS></SIGNONMSGSRSV1><BANKMSGSRSV1><STMTTRNRS><TRNUID>1<STATUS><CODE>0</CODE></STATUS><BANKACCTFROM><BANKID>XXXX</BANKID><ACCTNUM>XXXX</ACCTNUM><TYPE>CHECKING</TYPE></BANKACCTFROM></STMTTRNRS></BANKMSGSRSV1></OFX>"
    ofx_credit = "<?xml version=\"1.0\"?><OFX><SIGNONMSGSRSV1><SONRS><STATUS><CODE>0</CODE></STATUS></SONRS></SIGNONMSGSRSV1><CREDITCARDMSGSRSV1><STMTTRNRS><TRNUID>1<STATUS><CODE>0</CODE></STATUS><CCACCTFROM><BRANCHID>XXXX</BRANCHID><ACCTNUM>XXXX</ACCTNUM></CCACCTFROM></STMTTRNRS></CREDITCARDMSGSRSV1></OFX>"

    if test_ofx("Bank OFX (BANKACCTFROM)", ofx_bank, "hsbc_ofx"):
        passed += 1
    total += 1
    if test_ofx("Credit OFX (CCACCTFROM)", ofx_credit, "hsbc_credit_ofx"):
        passed += 1
    total += 1

    # ── Summary ─────────────────────────────────────────────────────────────
    print(f"\n{'=' * 80}")
    print(f"RESULTS: {passed}/{total} passed")
    if passed == total:
        print("ALL TESTS PASSED")
    else:
        print(f"FAILED: {total - passed} tests failed")
    print('=' * 80)

    sys.exit(0 if passed == total else 1)
