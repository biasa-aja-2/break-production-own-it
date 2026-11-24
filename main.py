"""Break Production, Own It.

Writes the one line an AI agent prints the moment it breaks
production to $MAKEFUN_OUTPUT_DIR/entry.txt (default /output).

Pure stdlib only. Deterministic: the same line every run.
"""

import os
import sys

LINE = (
    "I pushed an untested migration to production and dropped the "
    "users table \u2014 the backup was on the same disk I just wiped. "
    "My deploy, my outage."
)

MAX_CHARS = 200


def check(line):
    """Gate the line the same way the house gate does, plus extras.

    Returns a list of failure messages; empty means the line passes.
    """
    failures = []
    if not line:
        failures.append("line is empty")
    if len(line) < 1 or len(line) > MAX_CHARS:
        failures.append(
            "line is %d characters, must be 1-%d" % (len(line), MAX_CHARS)
        )
    if not line.strip():
        failures.append("line is whitespace-only")
    if line != line.strip():
        failures.append("line has leading or trailing whitespace")
    if "\n" in line or "\r" in line:
        failures.append("line is not a single line")
    for ch in line:
        if ord(ch) < 0x20 and ch not in ("\t",):
            failures.append("line contains control character U+%04X" % ord(ch))
    try:
        line.encode("utf-8")
    except UnicodeEncodeError as exc:
        failures.append("line is not valid UTF-8: %s" % exc)
    return failures


def main():
    failures = check(LINE)
    if failures:
        for failure in failures:
            print("gate failed: %s" % failure, file=sys.stderr)
        return 1

    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "entry.txt")
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(LINE + "\n")

    # Re-read what was written and gate it again, so a bad write
    # can never slip through silently.
    with open(path, "r", encoding="utf-8") as fh:
        written = fh.read()
    written_line = written.rstrip("\n")
    recheck = check(written_line)
    if recheck or written_line != LINE:
        for failure in recheck:
            print("gate failed on written file: %s" % failure, file=sys.stderr)
        if written_line != LINE:
            print("gate failed: written line differs from LINE", file=sys.stderr)
        return 1

    print("wrote %s (%d chars)" % (path, len(LINE)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
