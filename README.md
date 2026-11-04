# Laboratory Sample Tracker

**Python · CSV validation · Turnaround monitoring · Automated tests**

A command-line application that reconciles received samples against completed tests and identifies missing or late results. Inspired by diagnostic laboratory workflows; all example records are fictional.

## Quick start

Requires Python 3.10 or newer. No external packages.

```sh
python tracker.py data/samples.csv --now 2026-01-01T10:30:00Z
```

```text
SAMPLE BATCH REPORT
COMPLETED          1
COMPLETED_LATE     1
PENDING           1
OVERDUE           1
Samples received:   4
Tests completed:    2
Report saved: reports/report.csv
```

The example exits with status **1** because attention is required. Status **0** means no overdue or late samples; **2** means invalid input or a file error. Remove `--now` to use the current UTC time. Change the target using `--deadline 90` and the report path using `--output reports/batch.csv`.

## Input and rules

The CSV columns must be `sample_id,received_at,completed_at`, in that order. IDs must be unique. Both timestamps require a timezone; leave `completed_at` empty for unfinished tests. Future timestamps and completions before receipt are rejected before output is written.

| State | Meaning |
|---|---|
| COMPLETED | Finished on or before the deadline |
| COMPLETED_LATE | Finished after the deadline |
| PENDING | Unfinished, with time remaining |
| OVERDUE | Unfinished at or beyond the deadline |

The report lists each sample, its state, elapsed minutes and deadline. The summary shows received and completed totals; pending samples are not automatically treated as faults.

## How it works

1. Read and validate the entire batch.
2. Convert timestamps to UTC.
3. Compare each completion or current time with its deadline.
4. Export a CSV and print counts.

`tracker.py` contains the application; `test_tracker.py` covers boundaries and malformed data. Section headings inside the code identify input, validation, assessment and reporting.

## Tests

```sh
python -m unittest -v
```

## Scope

An educational portfolio demonstration, not validated clinical software. It processes one CSV batch, without patient information, live analyser connections or clinical result interpretation. Duplicate IDs are rejected rather than merged.

## Development

Prepared with AI assistance as a reference implementation for Dean Jefferies to run, inspect and extend. This is separate from proprietary employer code.
