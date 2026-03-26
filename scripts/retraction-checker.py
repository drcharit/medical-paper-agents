#!/usr/bin/env python3
"""
retraction-checker.py — Check references against retraction databases

Part of the medical-paper-agents skill.
Used by Agent 9 (Reference), Agent 14 (Scoring, H8), and Agent 16 (Claim Verifier).

Checks each DOI/PMID against:
1. CrossRef API — "update-to" records of type "retraction"
2. PubMed E-utilities — retraction notice publication types
3. Expressions of concern
4. Corrections

Usage:
    python retraction-checker.py \
        --input references.bib \
        --output retraction_report.md

    python retraction-checker.py \
        --input dois.txt \
        --output retraction_report.md \
        --format txt

    python retraction-checker.py \
        --input references.bib \
        --output retraction_report.md \
        --email user@example.com
"""

import argparse
import json
import os
import re
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

CROSSREF_API = "https://api.crossref.org/works/"
PUBMED_ESEARCH = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
PUBMED_EFETCH = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"

# Rate limiting
CROSSREF_DELAY = 0.1   # seconds between CrossRef requests (polite pool)
PUBMED_DELAY = 0.34     # seconds between PubMed requests (3/sec without key)

USER_AGENT = "retraction-checker/1.0 (medical-paper-agents skill)"


@dataclass
class ReferenceRecord:
    """A reference to check."""
    ref_id: int
    doi: Optional[str] = None
    pmid: Optional[str] = None
    title: Optional[str] = None
    authors: Optional[str] = None
    year: Optional[str] = None
    status: str = "UNCHECKED"           # CLEAR, RETRACTED, EOC, CORRECTED, ERROR
    retraction_date: Optional[str] = None
    retraction_reason: Optional[str] = None
    retraction_doi: Optional[str] = None
    eoc_details: Optional[str] = None
    correction_details: Optional[str] = None
    check_source: Optional[str] = None  # crossref, pubmed, both


@dataclass
class CheckResults:
    """Overall check results."""
    total: int = 0
    clear: int = 0
    retracted: int = 0
    eoc: int = 0
    corrected: int = 0
    errors: int = 0
    unchecked: int = 0
    records: list = field(default_factory=list)


# ---------------------------------------------------------------------------
# Reference parsing
# ---------------------------------------------------------------------------

def parse_bib_file(filepath: str) -> list[ReferenceRecord]:
    """Parse a BibTeX file and extract DOIs, PMIDs, and metadata."""
    records = []
    ref_id = 0

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Split into entries
    entries = re.split(r'(@\w+\{)', content)

    current_entry = ""
    for part in entries:
        if part.startswith('@'):
            if current_entry:
                ref_id += 1
                record = parse_bib_entry(current_entry, ref_id)
                if record:
                    records.append(record)
            current_entry = part
        else:
            current_entry += part

    # Last entry
    if current_entry:
        ref_id += 1
        record = parse_bib_entry(current_entry, ref_id)
        if record:
            records.append(record)

    return records


def parse_bib_entry(entry: str, ref_id: int) -> Optional[ReferenceRecord]:
    """Parse a single BibTeX entry."""
    record = ReferenceRecord(ref_id=ref_id)

    # Extract DOI
    doi_match = re.search(r'doi\s*=\s*\{([^}]+)\}', entry, re.IGNORECASE)
    if doi_match:
        record.doi = doi_match.group(1).strip()
        # Clean DOI: remove URL prefix if present
        record.doi = re.sub(r'^https?://doi\.org/', '', record.doi)
        record.doi = re.sub(r'^https?://dx\.doi\.org/', '', record.doi)

    # Extract PMID
    pmid_match = re.search(r'pmid\s*=\s*\{(\d+)\}', entry, re.IGNORECASE)
    if pmid_match:
        record.pmid = pmid_match.group(1).strip()

    # Extract title
    title_match = re.search(r'title\s*=\s*\{([^}]+)\}', entry, re.IGNORECASE)
    if title_match:
        record.title = title_match.group(1).strip()

    # Extract author
    author_match = re.search(r'author\s*=\s*\{([^}]+)\}', entry, re.IGNORECASE)
    if author_match:
        record.authors = author_match.group(1).strip()

    # Extract year
    year_match = re.search(r'year\s*=\s*\{?(\d{4})\}?', entry, re.IGNORECASE)
    if year_match:
        record.year = year_match.group(1)

    # Only return if we have at least a DOI or PMID
    if record.doi or record.pmid or record.title:
        return record
    return None


def parse_doi_list(filepath: str) -> list[ReferenceRecord]:
    """Parse a plain text file of DOIs (one per line)."""
    records = []
    with open(filepath, 'r', encoding='utf-8') as f:
        for ref_id, line in enumerate(f, 1):
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            # Clean DOI
            doi = re.sub(r'^https?://doi\.org/', '', line)
            doi = re.sub(r'^https?://dx\.doi\.org/', '', doi)
            records.append(ReferenceRecord(ref_id=ref_id, doi=doi))
    return records


# ---------------------------------------------------------------------------
# CrossRef API
# ---------------------------------------------------------------------------

def check_crossref(record: ReferenceRecord, email: Optional[str] = None) -> None:
    """Check a DOI against CrossRef for retraction/correction/EOC updates."""
    if not record.doi:
        return

    url = f"{CROSSREF_API}{quote(record.doi, safe='')}"
    headers = {"User-Agent": USER_AGENT}
    if email:
        headers["mailto"] = email
        url += f"?mailto={quote(email)}"

    try:
        req = Request(url, headers=headers)
        with urlopen(req, timeout=15) as response:
            data = json.loads(response.read().decode('utf-8'))

        message = data.get('message', {})

        # Check for update-to records (retractions, corrections, EOCs)
        updates = message.get('update-to', [])
        for update in updates:
            update_type = update.get('type', '').lower()
            update_date = update.get('updated', {}).get('date-parts', [[None]])[0]
            update_doi = update.get('DOI', '')

            if update_type == 'retraction':
                record.status = 'RETRACTED'
                record.retraction_doi = update_doi
                if update_date and update_date[0]:
                    record.retraction_date = '-'.join(str(d) for d in update_date if d)
                record.check_source = 'crossref'
                return

            elif update_type == 'expression-of-concern':
                if record.status != 'RETRACTED':  # retraction takes priority
                    record.status = 'EOC'
                    record.eoc_details = f"DOI: {update_doi}"
                    record.check_source = 'crossref'

            elif update_type in ('correction', 'erratum'):
                if record.status not in ('RETRACTED', 'EOC'):
                    record.status = 'CORRECTED'
                    record.correction_details = f"Correction DOI: {update_doi}"
                    record.check_source = 'crossref'

        # Also check if THIS paper is itself a retraction notice
        # (rare but possible if someone cites the retraction notice itself)
        subtypes = message.get('subtype', '')
        if 'retraction' in str(subtypes).lower():
            # This DOI is a retraction notice, not a retracted paper
            pass  # Don't flag — it's the notice, not the retracted paper

        # If no updates found, mark as clear (from CrossRef perspective)
        if record.status == 'UNCHECKED':
            record.status = 'CLEAR'
            record.check_source = 'crossref'

    except HTTPError as e:
        if e.code == 404:
            # DOI not found in CrossRef — not necessarily an error for retraction check
            pass
        else:
            record.status = 'ERROR'
            record.check_source = f'crossref_error_{e.code}'
    except (URLError, TimeoutError, json.JSONDecodeError) as e:
        record.status = 'ERROR'
        record.check_source = f'crossref_error_{type(e).__name__}'


def check_pubmed_retraction(record: ReferenceRecord, email: Optional[str] = None) -> None:
    """Check PubMed for retraction notices linked to this paper."""
    # First, find PMID if we only have DOI
    pmid = record.pmid
    if not pmid and record.doi:
        pmid = doi_to_pmid(record.doi, email)
        if pmid:
            record.pmid = pmid

    if not pmid:
        return  # Cannot check PubMed without PMID

    # Search for retraction notices that reference this PMID
    params = {
        'db': 'pubmed',
        'term': f'{pmid}[uid] AND (retraction of publication[pt] OR retracted publication[pt] '
                f'OR expression of concern[pt])',
        'retmax': '5',
        'retmode': 'json',
    }
    if email:
        params['email'] = email

    query_string = '&'.join(f'{k}={quote(str(v))}' for k, v in params.items())
    url = f"{PUBMED_ESEARCH}?{query_string}"

    try:
        req = Request(url, headers={"User-Agent": USER_AGENT})
        with urlopen(req, timeout=15) as response:
            data = json.loads(response.read().decode('utf-8'))

        result = data.get('esearchresult', {})
        count = int(result.get('count', 0))

        if count > 0:
            # Found retraction-related records — need to determine type
            ids = result.get('idlist', [])
            # Fetch the records to check publication type
            for fetched_pmid in ids:
                pub_type = get_pubmed_publication_type(fetched_pmid, email)
                if 'Retracted Publication' in pub_type or 'Retraction of Publication' in pub_type:
                    record.status = 'RETRACTED'
                    record.check_source = (
                        f"{record.check_source}+pubmed" if record.check_source
                        else 'pubmed'
                    )
                    return
                elif 'Expression of Concern' in pub_type:
                    if record.status != 'RETRACTED':
                        record.status = 'EOC'
                        record.eoc_details = f"PubMed PMID: {fetched_pmid}"
                        record.check_source = (
                            f"{record.check_source}+pubmed" if record.check_source
                            else 'pubmed'
                        )

    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError):
        pass  # PubMed check is supplementary; do not override CrossRef result


def doi_to_pmid(doi: str, email: Optional[str] = None) -> Optional[str]:
    """Look up PMID from DOI via PubMed E-utilities."""
    params = {
        'db': 'pubmed',
        'term': f'{doi}[doi]',
        'retmax': '1',
        'retmode': 'json',
    }
    if email:
        params['email'] = email

    query_string = '&'.join(f'{k}={quote(str(v))}' for k, v in params.items())
    url = f"{PUBMED_ESEARCH}?{query_string}"

    try:
        req = Request(url, headers={"User-Agent": USER_AGENT})
        with urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))
        ids = data.get('esearchresult', {}).get('idlist', [])
        return ids[0] if ids else None
    except Exception:
        return None


def get_pubmed_publication_type(pmid: str, email: Optional[str] = None) -> list[str]:
    """Fetch publication types for a PubMed record."""
    params = {
        'db': 'pubmed',
        'id': pmid,
        'rettype': 'xml',
        'retmode': 'xml',
    }
    if email:
        params['email'] = email

    query_string = '&'.join(f'{k}={quote(str(v))}' for k, v in params.items())
    url = f"{PUBMED_EFETCH}?{query_string}"

    try:
        req = Request(url, headers={"User-Agent": USER_AGENT})
        with urlopen(req, timeout=10) as response:
            xml_data = response.read().decode('utf-8')

        # Simple XML parsing for PublicationType
        pub_types = re.findall(r'<PublicationType[^>]*>([^<]+)</PublicationType>', xml_data)
        return pub_types
    except Exception:
        return []


# ---------------------------------------------------------------------------
# Report generation
# ---------------------------------------------------------------------------

def generate_report(results: CheckResults, output_path: str) -> None:
    """Write the retraction check report."""
    lines = [
        "# Retraction Check Report",
        "",
        f"**Generated by:** retraction-checker.py",
        f"**Total references checked:** {results.total}",
        "",
        "## Summary",
        "",
        "| Status | Count |",
        "|---|---|",
        f"| Clear | {results.clear} |",
        f"| RETRACTED | {results.retracted} |",
        f"| Expression of Concern | {results.eoc} |",
        f"| Corrected | {results.corrected} |",
        f"| Check Error | {results.errors} |",
        f"| Unchecked (no DOI/PMID) | {results.unchecked} |",
        "",
    ]

    # Critical findings
    retracted = [r for r in results.records if r.status == 'RETRACTED']
    eocs = [r for r in results.records if r.status == 'EOC']
    corrected = [r for r in results.records if r.status == 'CORRECTED']

    if retracted:
        lines.extend([
            "---",
            "",
            "## RETRACTED REFERENCES (MUST REMOVE)",
            "",
        ])
        for r in retracted:
            lines.extend([
                f"### Reference {r.ref_id}",
                f"- **DOI:** {r.doi or 'N/A'}",
                f"- **PMID:** {r.pmid or 'N/A'}",
                f"- **Title:** {r.title or 'N/A'}",
                f"- **Retraction date:** {r.retraction_date or 'Unknown'}",
                f"- **Retraction DOI:** {r.retraction_doi or 'N/A'}",
                f"- **Reason:** {r.retraction_reason or 'Not available'}",
                f"- **Source:** {r.check_source}",
                "",
                "**ACTION REQUIRED:** Remove this reference and replace with a "
                "non-retracted alternative, or remove the dependent claim.",
                "",
            ])

    if eocs:
        lines.extend([
            "---",
            "",
            "## EXPRESSIONS OF CONCERN (review recommended)",
            "",
        ])
        for r in eocs:
            lines.extend([
                f"### Reference {r.ref_id}",
                f"- **DOI:** {r.doi or 'N/A'}",
                f"- **PMID:** {r.pmid or 'N/A'}",
                f"- **Title:** {r.title or 'N/A'}",
                f"- **Details:** {r.eoc_details or 'N/A'}",
                f"- **Source:** {r.check_source}",
                "",
                "**RECOMMENDED:** Review the expression of concern. Consider replacing "
                "this reference if the concern affects the claim being supported.",
                "",
            ])

    if corrected:
        lines.extend([
            "---",
            "",
            "## CORRECTED REFERENCES (note correction)",
            "",
        ])
        for r in corrected:
            lines.extend([
                f"### Reference {r.ref_id}",
                f"- **DOI:** {r.doi or 'N/A'}",
                f"- **Title:** {r.title or 'N/A'}",
                f"- **Correction:** {r.correction_details or 'N/A'}",
                "",
                "**INFO:** A correction has been issued. Verify that the claim "
                "supported by this reference is not affected by the correction.",
                "",
            ])

    # Full reference status table
    lines.extend([
        "---",
        "",
        "## Complete Reference Status",
        "",
        "| Ref # | DOI | Status | Source |",
        "|---|---|---|---|",
    ])
    for r in results.records:
        doi_display = r.doi[:50] + "..." if r.doi and len(r.doi) > 50 else (r.doi or "N/A")
        lines.append(f"| {r.ref_id} | {doi_display} | {r.status} | {r.check_source or '—'} |")
    lines.append("")

    os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

    print(f"Report written to: {output_path}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Check references against retraction databases"
    )
    parser.add_argument(
        "--input",
        required=True,
        help="Input file: BibTeX (.bib) or DOI list (.txt)",
    )
    parser.add_argument(
        "--output",
        default="retraction_report.md",
        help="Output report path (default: retraction_report.md)",
    )
    parser.add_argument(
        "--format",
        choices=["bib", "txt"],
        default=None,
        help="Input format (auto-detected from extension if not specified)",
    )
    parser.add_argument(
        "--email",
        default=None,
        help="Email for CrossRef polite pool (recommended for faster access)",
    )
    args = parser.parse_args()

    if not os.path.isfile(args.input):
        print(f"ERROR: Input file not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    # Determine format
    fmt = args.format
    if fmt is None:
        ext = Path(args.input).suffix.lower()
        if ext == '.bib':
            fmt = 'bib'
        else:
            fmt = 'txt'

    # Parse input
    print(f"Parsing {args.input} (format: {fmt})")
    if fmt == 'bib':
        records = parse_bib_file(args.input)
    else:
        records = parse_doi_list(args.input)

    print(f"Found {len(records)} references to check")

    if not records:
        print("No references found. Exiting.")
        sys.exit(0)

    # Check each reference
    results = CheckResults(total=len(records))

    for i, record in enumerate(records, 1):
        print(f"  Checking {i}/{len(records)}: {record.doi or record.pmid or record.title or 'unknown'}...")

        # CrossRef check (primary)
        if record.doi:
            check_crossref(record, email=args.email)
            time.sleep(CROSSREF_DELAY)

        # PubMed check (supplementary)
        if record.doi or record.pmid:
            check_pubmed_retraction(record, email=args.email)
            time.sleep(PUBMED_DELAY)

        # If no DOI or PMID, mark as unchecked
        if not record.doi and not record.pmid:
            record.status = 'UNCHECKED'
            record.check_source = 'no_identifier'

        # Count results
        if record.status == 'CLEAR':
            results.clear += 1
        elif record.status == 'RETRACTED':
            results.retracted += 1
        elif record.status == 'EOC':
            results.eoc += 1
        elif record.status == 'CORRECTED':
            results.corrected += 1
        elif record.status == 'ERROR':
            results.errors += 1
        else:
            results.unchecked += 1

    results.records = records

    # Generate report
    generate_report(results, args.output)

    # Summary
    print(f"\n--- Retraction Check Summary ---")
    print(f"  Clear:       {results.clear}")
    print(f"  RETRACTED:   {results.retracted}")
    print(f"  EOC:         {results.eoc}")
    print(f"  Corrected:   {results.corrected}")
    print(f"  Errors:      {results.errors}")
    print(f"  Unchecked:   {results.unchecked}")

    # Exit code: non-zero if any retracted references found
    if results.retracted > 0:
        print(f"\nCRITICAL: {results.retracted} retracted reference(s) found!")
        sys.exit(1)
    if results.eoc > 0:
        print(f"\nWARNING: {results.eoc} expression(s) of concern found.")
        sys.exit(0)  # Warning only, not a hard failure
    sys.exit(0)


if __name__ == "__main__":
    main()
