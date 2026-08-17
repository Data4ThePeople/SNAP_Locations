"""Measure reading level of the published markdown, so editing has a target.

The brief is an eighth-grade maximum. That is checkable rather than a matter of
taste, so this scores every piece and names the sentences that fail, instead of
leaving it to a subjective read.

Flesch-Kincaid grade level is the standard for this:

    0.39 * (words/sentence) + 11.8 * (syllables/word) - 15.59

Two things drive it, and only two: sentence length and syllables per word. So
the edit is always one of "split this sentence" or "use a shorter word". The
per-sentence report below sorts by the same formula, which makes the worst
offenders the obvious place to start.

Syllable counting is heuristic — vowel groups, minus a silent trailing 'e', with
a floor of one. It disagrees with a dictionary on maybe a few percent of words,
which is fine at the aggregate level and is why individual sentence grades are
treated as a ranking rather than a measurement.

What is deliberately NOT scored: headings, figure captions, image alt text,
table rows, blockquotes, the source footer, and anything inside a code span.
Those are labels rather than prose, they are dense with numbers and proper
nouns, and including them would swamp the signal from the body text.

Usage:
    python -m analysis.readability            # score every post
    python -m analysis.readability 2 --worst  # worst sentences in post 2
"""
import re
import sys

from config import ROOT

REPORTS = ROOT / "reports"
TARGET = 8.0

VOWELS = "aeiouy"


def syllables(word):
    """Vowel groups, less a silent trailing 'e'. Minimum of one."""
    w = re.sub(r"[^a-z]", "", word.lower())
    if not w:
        return 0
    n = len(re.findall(r"[aeiouy]+", w))
    if w.endswith("e") and not w.endswith(("le", "ee", "ye")) and n > 1:
        n -= 1
    return max(n, 1)


def prose(md):
    """Body prose only: drop headings, captions, tables, code, footers, lists' markers."""
    # The citation block sits after the final horizontal rule. It is a source
    # list, not prose the reader parses, and it is unavoidably dense with proper
    # nouns and statute names — scoring it would swamp the body-text signal.
    # Its opening line is caught by the "*Source" test below; this drops the
    # continuation lines with it.
    parts = md.rsplit("\n---\n", 1)
    if len(parts) == 2 and len(parts[1]) < 1200:
        md = parts[0]
    out = []
    for line in md.split("\n"):
        s = line.strip()
        if not s or s.startswith(("#", ">", "|", "![", "---", "*Source", "*SNAP")):
            continue
        if s.startswith("*") and s.endswith("*") and len(s) > 80:
            continue  # italic standfirst / source block
        # A stat line ("**5,000** — stores USDA expects to lose...") is a label
        # attached to a number, not a sentence. It has no verb and no full stop,
        # so the sentence splitter glues it to whatever follows and scores the
        # pair as one very long sentence.
        if re.match(r"^\*\*[^*]+\*\*\s+—", s):
            continue
        # Source-list items are strings of proper nouns and statute numbers with
        # no sentence structure at all.
        if s.startswith("- ") and not s.rstrip().endswith((".", "?", "!")):
            continue
        s = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", s)      # images
        s = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", s)  # links keep their text
        s = re.sub(r"`[^`]*`", "", s)                   # code spans
        s = re.sub(r"^[-*]\s+", "", s)                  # list markers
        s = s.replace("**", "").replace("*", "")
        out.append(s)
    return " ".join(out)


def sentences(text):
    # Protect decimals, currency and abbreviations from the sentence splitter.
    t = re.sub(r"(\d)\.(\d)", r"\1<DOT>\2", text)
    t = re.sub(r"\b(Mr|Mrs|Ms|Dr|St|No|vs|etc|Inc|Co|U\.S)\.", r"\1<DOT>", t)
    parts = re.split(r"(?<=[.!?])\s+", t)
    return [p.replace("<DOT>", ".").strip() for p in parts if len(p.strip()) > 1]


def grade(text):
    sents = sentences(text)
    words = re.findall(r"[A-Za-z][A-Za-z'’-]*", text)
    if not sents or not words:
        return None
    syl = sum(syllables(w) for w in words)
    wps, spw = len(words) / len(sents), syl / len(words)
    return {
        "grade": round(0.39 * wps + 11.8 * spw - 15.59, 2),
        "words": len(words), "sentences": len(sents),
        "words_per_sentence": round(wps, 1),
        "syllables_per_word": round(spw, 2),
        "long_words_pct": round(
            100 * sum(1 for w in words if syllables(w) >= 3) / len(words), 1),
    }


def worst(text, n=12):
    rows = []
    for s in sentences(text):
        g = grade(s)
        if g and g["words"] >= 8:
            rows.append((g["grade"], g["words"], s))
    rows.sort(reverse=True)
    return rows[:n]


def score_post(n):
    p = REPORTS / f"post{n}" / f"post{n}.md"
    if not p.exists():
        return None
    return grade(prose(p.read_text()))


def main():
    args = [a for a in sys.argv[1:]]
    if args and args[0].isdigit():
        n = int(args[0])
        text = prose((REPORTS / f"post{n}" / f"post{n}.md").read_text())
        g = grade(text)
        print(f"post{n}: grade {g['grade']}  "
              f"{g['words_per_sentence']} words/sentence  "
              f"{g['syllables_per_word']} syllables/word  "
              f"{g['long_words_pct']}% long words")
        if "--worst" in args:
            print(f"\nworst sentences (grade, words):")
            for gr, wc, s in worst(text):
                print(f"\n  [{gr:5.1f}] {wc:>3}w  {s}")
        return

    print(f"Flesch-Kincaid grade level, body prose only. Target: {TARGET} or below.\n")
    print(f"  {'post':>6} {'grade':>7} {'w/sent':>8} {'syl/w':>7} {'3+syl':>7} "
          f"{'words':>7}  status")
    print("  " + "-" * 62)
    fails = []
    for n in range(0, 8):
        g = score_post(n)
        if not g:
            continue
        ok = g["grade"] <= TARGET
        if not ok:
            fails.append((n, g["grade"]))
        print(f"  {'post'+str(n):>6} {g['grade']:>7.2f} {g['words_per_sentence']:>8.1f} "
              f"{g['syllables_per_word']:>7.2f} {g['long_words_pct']:>6.1f}% "
              f"{g['words']:>7,}  {'ok' if ok else 'OVER'}")
    if fails:
        print("\n  over target: " + ", ".join(f"post{n} ({g})" for n, g in fails))
        print("  run  python -m analysis.readability <n> --worst  to see the offenders")
    else:
        print("\n  every piece at or below target")


if __name__ == "__main__":
    main()
