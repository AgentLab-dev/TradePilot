#!/usr/bin/env python3
"""Read already-open Safari/Chrome tabs for WSJ / MarketWatch / Yahoo (headless tail).

Does not log in. Times out fast so macOS Automation prompts cannot hang FULL CHECK.
"""
from __future__ import annotations

import argparse
import subprocess
import sys

HOSTS = (
    "wsj.com",
    "marketwatch.com",
    "finance.yahoo.com",
    "cnbc.com",
    "reuters.com",
    "investors.com",
)

LIST_SAFARI = r'''
tell application "System Events"
  if not (exists process "Safari") then
    return "Safari not running"
  end if
end tell
tell application "Safari"
  if (count of windows) is 0 then
    return "Safari open, no windows"
  end if
  set out to ""
  repeat with w in windows
    try
      repeat with t in tabs of w
        try
          set u to URL of t
          set n to name of t
          set out to out & n & " | " & u & linefeed
        end try
      end repeat
    end try
  end repeat
  if out is "" then
    return "Safari: no readable tab URLs"
  end if
  return out
end tell
'''

LIST_CHROME = r'''
tell application "System Events"
  if not (exists process "Google Chrome") then
    return "Chrome not running"
  end if
end tell
tell application "Google Chrome"
  if (count of windows) is 0 then
    return "Chrome open, no windows"
  end if
  set out to ""
  repeat with w in windows
    try
      repeat with t in tabs of w
        try
          set u to URL of t
          set n to title of t
          set out to out & n & " | " & u & linefeed
        end try
      end repeat
    end try
  end repeat
  if out is "" then
    return "Chrome: no readable tab URLs"
  end if
  return out
end tell
'''

DUMP_SAFARI = r'''
tell application "Safari"
  set out to ""
  repeat with w in windows
    try
      repeat with t in tabs of w
        try
          set u to URL of t
          if u contains "wsj.com" or u contains "marketwatch.com" or u contains "finance.yahoo.com" or u contains "investors.com" then
            set n to name of t
            set body to ""
            try
              set body to do JavaScript "document.body.innerText.slice(0,4000)" in t
            end try
            if body is "" then
              try
                set body to text of t
              end try
            end if
            set out to out & "=== " & n & " ===" & linefeed & u & linefeed & body & linefeed
          end if
        end try
      end repeat
    end try
  end repeat
  if out is "" then
    return "no matching Safari tabs"
  end if
  return out
end tell
'''


def osa(script: str, timeout: float = 8.0) -> str:
    try:
        p = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True, text=True, timeout=timeout,
        )
        out = (p.stdout or "").strip()
        err = (p.stderr or "").strip()
        if p.returncode != 0 and err:
            return err.splitlines()[0]
        return out
    except subprocess.TimeoutExpired:
        return (
            "timed out waiting for Automation permission "
            "(System Settings → Privacy & Security → Automation)"
        )
    except FileNotFoundError:
        return "osascript not found (macOS only)"


def filter_lines(block: str) -> str:
    keep = []
    for line in block.splitlines():
        low = line.lower()
        if any(h in low for h in HOSTS) or line.startswith("===") or "not running" in low:
            keep.append(line)
        elif "timed out" in low or "not found" in low or "Safari:" in line or "Chrome:" in line:
            keep.append(line)
    return "\n".join(keep) if keep else block


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", action="store_true")
    args = ap.parse_args()
    chunks = ["# Safari", osa(LIST_SAFARI), "", "# Chrome", osa(LIST_CHROME)]
    if not args.list:
        chunks.extend(["", "# Safari dump", osa(DUMP_SAFARI, timeout=10.0)])
    text = "\n".join(chunks)
    if args.list:
        text = filter_lines("\n".join(chunks[:5]))
    sys.stdout.write(text.rstrip() + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
