"""Check a batch of fictional laboratory samples and write a CSV report."""

import argparse
import csv
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path


# SECTION 1 — Input format and time handling
# Every sample needs an arrival time; unfinished tests leave completed_at empty.
FIELDS = ["sample_id", "received_at", "completed_at"]


def parse_time(value):
    timestamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if timestamp.tzinfo is None:
        raise ValueError("timestamps must include a timezone, such as Z or +00:00")
    return timestamp.astimezone(timezone.utc)


# SECTION 2 — Batch validation
# Validate the whole file before producing any results.
def read_samples(path, now):
    samples = []
    seen_ids = set()
    with open(path, newline="", encoding="utf-8-sig") as source:
        reader = csv.DictReader(source)
        if reader.fieldnames != FIELDS:
            raise ValueError("CSV header must be: " + ",".join(FIELDS))
        for line, row in enumerate(reader, start=2):
            try:
                if None in row or any(value is None for value in row.values()):
                    raise ValueError("incorrect number of columns")
                sample_id = row["sample_id"].strip()
                if not sample_id or sample_id in seen_ids:
                    raise ValueError("sample_id must be non-empty and unique")
                received = parse_time(row["received_at"].strip())
                completed_text = row["completed_at"].strip()
                completed = parse_time(completed_text) if completed_text else None
                if received > now or (completed and completed > now):
                    raise ValueError("sample timestamps cannot be in the future")
                if completed and completed < received:
                    raise ValueError("completion cannot precede receipt")
                seen_ids.add(sample_id)
                samples.append({"sample_id": sample_id, "received": received,
                                "completed": completed})
            except ValueError as error:
                raise ValueError(f"line {line}: {error}") from error
    return samples


# SECTION 3 — Turnaround checks
# Pending samples become overdue at the deadline; late completions stay visible.
def assess_samples(samples, now, deadline_minutes):
    if deadline_minutes <= 0:
        raise ValueError("deadline must be greater than zero")
    report = []
    for sample in samples:
        deadline = sample["received"] + timedelta(minutes=deadline_minutes)
        completed = sample["completed"]
        if completed:
            status = "COMPLETED_LATE" if completed > deadline else "COMPLETED"
        else:
            status = "OVERDUE" if now >= deadline else "PENDING"
        elapsed = ((completed or now) - sample["received"]).total_seconds() / 60
        report.append({"sample_id": sample["sample_id"], "status": status,
                       "elapsed_minutes": round(elapsed, 1),
                       "deadline_at": deadline.isoformat()})
    return report


# SECTION 4 — Report output
# Save one row per sample and print a compact summary for the batch.
def write_report(path, report):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as destination:
        writer = csv.DictWriter(destination, fieldnames=[
            "sample_id", "status", "elapsed_minutes", "deadline_at"])
        writer.writeheader()
        writer.writerows(report)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="CSV of synthetic sample records")
    parser.add_argument("--output", type=Path, default=Path("reports/report.csv"))
    parser.add_argument("--deadline", type=int, default=60, help="turnaround minutes")
    parser.add_argument("--now", help="timezone-aware timestamp for reproducible checks")
    args = parser.parse_args()
    try:
        if args.input.resolve() == args.output.resolve():
            raise ValueError("output must be different from input")
        now = parse_time(args.now) if args.now else datetime.now(timezone.utc)
        report = assess_samples(read_samples(args.input, now), now, args.deadline)
        write_report(args.output, report)
    except (ValueError, OverflowError, OSError, csv.Error) as error:
        print(f"Cannot process batch: {error}", file=sys.stderr)
        return 2
    print("SAMPLE BATCH REPORT")
    for status in ["COMPLETED", "COMPLETED_LATE", "PENDING", "OVERDUE"]:
        print(f"{status:18} {sum(row['status'] == status for row in report)}")
    print(f"Samples received:   {len(report)}")
    print(f"Tests completed:    {sum(row['status'].startswith('COMPLETED') for row in report)}")
    print(f"Report saved: {args.output}")
    return 1 if any(row["status"] in ["OVERDUE", "COMPLETED_LATE"] for row in report) else 0


# SECTION 5 — Command-line entry point
if __name__ == "__main__":
    sys.exit(main())
