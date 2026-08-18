# Day 0 launch email — Mailchimp

The announcement email: introduces the map, sets the one caveat the whole series
depends on, and previews the seven days. Assets are all built and pushed.

---

## Subject line

```
Every store that takes SNAP, mapped
```

34 characters, so it survives the mobile cut (~35–40). Concrete, no hype, and
"takes SNAP" is how people actually say it. The series name does the branding
inside the email; a cold subject line is the wrong place for it, because
"The Stores That Stayed" tells a first-time reader nothing about what they are
opening.

Alternates if you want to A/B:

```
The Stores That Stayed: every SNAP retailer, mapped
```
```
661,456 stores. Twenty years. One map.
```

The first pairs the series name with the concrete promise, which is the version
to use if you expect the name to become the brand. The second leads with the
number, which suits a data-native list.

## Preview text (preheader)

```
An interactive map of every SNAP retailer since 2006 — plus seven days of analysis, starting tomorrow.
```

101 characters. It does not repeat the subject: the subject says what the thing
is, the preheader says what else is coming. Set this in Mailchimp's preview-text
field, **not** as the first line of body copy.

---

## Layout, block by block

Mailchimp default 600px content width. Every image below is 1720px wide, so it
lands at ~2.9× on that column and stays sharp on retina.

### 1 — Header

Your standard masthead.

### 2 — Headline

```
The Stores That Stayed
```

Series title. Set it as the headline, and consider carrying it as a small kicker
above the headline in each of the seven daily sends — "The Stores That Stayed ·
Day 3" — so the run reads as one thing.

### 3 — Deck

```
Twenty years of SNAP retailers, mapped. Every store authorized to accept SNAP anywhere in the United States, 2006–2025 — 661,456 of them. An interactive map, and seven days of analysis built on it.
```

### 4 — Hero image, linked

| | |
|---|---|
| file | `reports/assets/snap-map-email.jpg` |
| size | 1200×771, 169 KB |
| link | your Prismic visualization page |

Alt text:

```
Dot map of 249,083 SNAP-authorized US stores in 2025, chains in blue and independents in orange.
```

### 5 — Key figures

Set these as **live text**, not the ledger PNG. Roughly a third of recipients
have images off by default, and these three numbers are the point of the email.

```
661,456 — stores authorized to accept SNAP at some point in the last twenty years
249,083 — still authorized at the end of 2025
20 — years you can move through, one at a time
```

### 6 — Body copy

```
SNAP is the largest food assistance program in the country. To use it you need a store that accepts it. USDA publishes a record of every store ever approved to do so, going back twenty years — 661,456 of them, each with a location, a store type, and the dates its approval started and ended.

We turned that file into a map you can explore, and then spent seven pieces working out what it says.
```

### 7 — What the map does

```
Filter by store type. All 18 of USDA's categories — supermarkets, superstores, convenience stores, dollar stores, farmers' markets and the rest.

Filter by retailer. 291 chains are named. Turn everything off, then switch on Kroger and Giant Eagle, and you are looking at two companies against an empty country.

Move through time. One year at a time, 2006 to 2025.
```

### 8 — Button

```
Open the map
```

Point it at the Prismic visualization page, not the raw GitHub Pages URL — the
Prismic page carries the methodology alongside it.

### 9 — The caveat

Keep this. It is the distinction the whole series rests on, and it is better to
set it before the first chapter than to defend it afterwards.

```
One thing before the first piece

This file records authorizations, not storefronts. A store leaving the data means its authorization ended. That usually means the store closed — but it can also mean the store is still open and simply stopped accepting SNAP.

They are not the same thing, and we do not treat them as the same thing. Where we use this data to say something about stores opening or closing, we check it against a source outside the file: a company's own reported store count, or the Census Bureau's count of business locations. Where we could not make that match work, we say so and make no claim.
```

### 10 — The seven days

Intro line:

```
Each piece stands alone, but the argument builds from one to the next. The first six are the story. The last is an epilogue about what it means for policy.
```

Then the seven cards, in order. All are in `reports/post0/images/`.

| block | file | alt text |
|---|---|---|
| Day 1 | `day-1.png` | Day 1 — One in four of the smallest grocery stores is gone. 25% fall in small grocery businesses by the Census Bureau's count. |
| Day 2 | `day-2.png` | Day 2 — Dollar stores cracked the code small grocers could not. Dollar store numbers up 307% since 2006. |
| Day 3 | `day-3.png` | Day 3 — Convenience stores thrived. Most of their owners did not. 14.2% of single-owner stores lasted thirteen years, against 78.7% of chains. |
| Day 4 | `day-4.png` | Day 4 — The bigger the store, the better it did, unless it belonged to a chain. 78% of chain super stores kept authorization against 46% of independents. |
| Day 5 | `day-5.png` | Day 5 — The one chain format that did not work. Chain pharmacies peaked at 20,341 and stand at 14,828. |
| Day 6 | `day-6.png` | Day 6 — Twenty years, one pattern. Chains went from 39% to 50% of every SNAP retailer in the country between 2006 and 2025. |
| Day 7 | `day-7.png` | Day 7 — In November, the rules change for the stores that are left. The small stores this rule hits hardest are 71% of SNAP retailers and 11% of SNAP spending. |

Do **not** link the cards. Days 1–7 are not published yet, and a dead link in a
launch email is worse than no link. Add links in the daily sends instead.

### 11 — What we are not claiming

```
This data has no prices, no floor space, and no sales. It has no idea what is on a shelf. A dollar store and a supermarket each count as one record. It also does not know whether anyone has a car — which is often what decides whether a store ten miles away is a quick errand or out of reach.

So this series is about where the stores are and what kind they are. That is a real and useful question. It is not the same as asking whether people are fed.
```

### 12 — Footer

```
Source: USDA FNS SNAP Retailer Locator Historical Data, 2005–2025. 661,456 stores, 703,441 authorization spells, of which 37,908 stores hold more than one. 656,868 have coordinates good enough to map.

The map, the pipeline that builds it, and every figure in this series:
github.com/Data4ThePeople/SNAP_Locations
```

---

## Notes

- **Total image payload is about 0.85 MB** — the hero at 169 KB plus 697 KB of
  cards. Fine, but it is most of the email's weight, so keep the HTML lean.
  Gmail's 102 KB clipping threshold counts HTML only, not linked images.
- **Seven cards makes a long email.** That is the right call for a launch that is
  promising seven days, but if you want it shorter, cut to Days 1–3 and finish
  with a line like "and four more through the week." The cards are the roadmap,
  so I would keep all seven.
- **Set a dark-friendly background.** The cards are drawn on `#181A1B` with
  `#BBBDC0` text. On a white email ground they will read as seven dark slabs.
  Either set the content background to `#181A1B` so they sit flush, or give them
  breathing room and accept the contrast.
- **Images off** is the failure mode worth designing against. With images
  suppressed, this email should still say: what the map is, the three numbers,
  the caveat, and the button. That is why the key figures are live text.
