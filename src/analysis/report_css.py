"""Shared report styling, used by every post so the series looks like a series."""

CSS = """
/* Subject is a federal authorization ledger, so the identity is serif prose
   against monospaced record-keeping: every figure, axis tick and label is mono
   and tabular. Neutrals are cooled toward the blue accent rather than left as
   default grey, and there is no sans-serif anywhere. */
:root {
  color-scheme: light;
  --paper:    #f5f7f9;
  --ink:      #16191c;
  --ink-mid:  #4d545c;
  --ink-soft: #878e96;
  --rule:     #dee4e9;
  --band:     #ecf0f3;
  --s1: #2a78d6; --s2: #eb6834; --s3: #1baf7a; --s4: #eda100;
  --s5: #e87ba4; --s6: #008300; --s7: #4a3aa7; --s8: #e34948;
  --muted: #b9c0c7;
  --grid: var(--rule); --surface: var(--paper);
  --ink-1: var(--ink); --ink-2: var(--ink-mid); --ink-3: var(--ink-soft);
  --serif: "Charter", "Iowan Old Style", "Palatino Linotype", Palatino, Georgia, serif;
  --mono: ui-monospace, "SF Mono", SFMono-Regular, "Cascadia Mono", "Roboto Mono", Menlo, monospace;
}
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    color-scheme: dark;
    --paper: #14171a; --ink: #eef1f4; --ink-mid: #b3bac1; --ink-soft: #7d858d;
    --rule: #262b30; --band: #1b1f23; --muted: #565e66;
    --s1: #3987e5; --s2: #d95926; --s3: #199e70; --s4: #c98500;
    --s5: #d55181; --s6: #008300; --s7: #9085e9; --s8: #e66767;
  }
}
:root[data-theme="dark"] {
  color-scheme: dark;
  --paper: #14171a; --ink: #eef1f4; --ink-mid: #b3bac1; --ink-soft: #7d858d;
  --rule: #262b30; --band: #1b1f23; --muted: #565e66;
  --s1: #3987e5; --s2: #d95926; --s3: #199e70; --s4: #c98500;
  --s5: #d55181; --s6: #008300; --s7: #9085e9; --s8: #e66767;
}
* { box-sizing: border-box; }
body {
  margin: 0;
  background: var(--paper);
  color: var(--ink);
  font: 17px/1.66 var(--serif);
  -webkit-font-smoothing: antialiased;
}
main {
  max-width: 880px; margin: 0 auto; padding: 64px 24px 110px;
  display: grid; gap: 0;
}
/* Prose keeps a readable measure; figures use the full field. */
h1, h2, p, table, .caveat, .sub, footer, .legend { max-width: 62ch; }

h1 {
  font: 400 clamp(30px, 4.4vw, 42px)/1.14 var(--serif);
  letter-spacing: -.015em; margin: 0 0 14px; text-wrap: balance;
}
.sub {
  font: 400 12px/1.6 var(--mono); color: var(--ink-soft);
  margin: 0 0 40px; letter-spacing: .01em;
}
h2 {
  font: 400 25px/1.25 var(--serif); letter-spacing: -.01em;
  margin: 60px 0 14px; padding-top: 22px; border-top: 1px solid var(--rule);
  text-wrap: balance;
}
p { margin: 0 0 20px; }
em { font-style: italic; }
strong { font-weight: 600; }

/* Ledger band: hairline rules and mono figures, in place of rounded cards. */
.ledger {
  display: grid; grid-template-columns: repeat(auto-fit, minmax(190px, 1fr));
  gap: 0 30px; margin: 34px 0 40px;
  border-top: 2px solid var(--ink); border-bottom: 1px solid var(--rule);
}
.ledger div { padding: 16px 0 15px; }
.ledger div + div { border-left: 1px solid var(--rule); padding-left: 24px; }
.ledger b {
  display: block; font: 400 34px/1.05 var(--mono);
  font-variant-numeric: tabular-nums; letter-spacing: -.03em; color: var(--s1);
}
.ledger span {
  display: block; margin-top: 7px;
  font: 400 11.5px/1.45 var(--mono); color: var(--ink-soft);
}

figure { margin: 30px 0 34px; }
figcaption {
  font: 400 11.5px/1.6 var(--mono); color: var(--ink-soft);
  margin-top: 12px; max-width: 74ch;
}
.chart { width: 100%; height: auto; display: block; overflow: visible; }
.tick, .note, .axis-title { font: 400 10.5px var(--mono); fill: var(--ink-soft); }
.dlabel, .bvalue { font: 400 11.5px var(--mono); fill: var(--ink-mid); }
.blabel { font: 400 11.5px var(--mono); fill: var(--ink-mid); }
.bvalue { font-variant-numeric: tabular-nums; }

.legend {
  display: flex; flex-wrap: wrap; gap: 6px 20px; margin: 12px 0 0;
  font: 400 11.5px var(--mono); color: var(--ink-mid);
}
.lg { display: inline-flex; align-items: center; gap: 7px; }
.lg i { width: 11px; height: 3px; flex: none; }

table {
  width: 100%; border-collapse: collapse; margin: 24px 0;
  font: 400 13px var(--mono); font-variant-numeric: tabular-nums;
}
th, td { text-align: right; padding: 9px 12px; border-bottom: 1px solid var(--rule); }
th:first-child, td:first-child { text-align: left; }
th {
  font-weight: 400; color: var(--ink-soft); font-size: 10.5px;
  text-transform: uppercase; letter-spacing: .08em;
  border-bottom: 1px solid var(--ink);
}

.caveat { margin: 42px 0 0; padding: 24px 0 0; border-top: 1px solid var(--rule); }
.caveat h3 {
  font: 400 10.5px var(--mono); text-transform: uppercase; letter-spacing: .1em;
  color: var(--ink-soft); margin: 0 0 12px;
}
.caveat p { font-size: 15.5px; color: var(--ink-mid); }
.caveat p:last-child { margin-bottom: 0; }

footer {
  margin-top: 52px; padding-top: 20px; border-top: 1px solid var(--rule);
  font: 400 11.5px/1.7 var(--mono); color: var(--ink-soft);
}
footer a { color: var(--s1); text-decoration: none; border-bottom: 1px solid var(--rule); }
footer a:hover { border-bottom-color: var(--s1); }
footer a:focus-visible { outline: 2px solid var(--s1); outline-offset: 2px; }
"""
