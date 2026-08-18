"""Render reports/post7.html from reports/data/post7.json."""
import json

from analysis import charts, palette
from analysis.report_css import CSS, HEAD
from config import ROOT

LADDER = ["Small Grocery Store", "Convenience Store", "Combination Grocery/Other",
          "Medium Grocery Store", "Supermarket", "Large Grocery Store"]

DATA = ROOT / "reports" / "data" / "post7.json"
OUT = ROOT / "reports" / "post7.html"


def main():
    d = json.loads(DATA.read_text())
    palette.validate(3, "light", verbose=False)
    palette.validate(3, "dark", verbose=False)

    P = d["policy"]
    tfp, o, n, im = P["tfp"], P["old_standard"], P["new_standard"], P["impact"]
    nfa, dg = P["need_for_access"], P["dollar_general"]
    pre, tm = d["precedent"], d["thin_markets"]
    surv = {r["segment"]: r for r in d["survival"]}
    den, tl = tm["density"], tm["total_loss"]

    s_pre = [{"name": "new authorizations", "values": pre["new"], "slot": 1},
             {"name": "departures", "values": pre["departed"], "slot": 2}]
    c_pre = charts.line_chart(pre["years"], s_pre,
                             y_label="small grocery stores per year",
                             annotate=[{"year": 2018, "text": "2018 standard"}],
        title="Last time the rules tightened, new sign-ups fell",
        subtitle="small grocery stores per year")

    # The size ladder, not the survival gradient: a stocking rule asks for stock,
    # so the prediction it supports is about how much stock a format carries.
    eu = {r["store_type"]: r for r in d["entry_change_usda"]}
    ladder_rows = "".join(
        f"<tr><td>{typ}</td><td>{eu[typ]['pct']:+.0f}%</td></tr>"
        for typ in LADDER if typ in eu)

    std_tbl = "".join(f"<tr><td>{lbl}</td><td>{a}</td><td>{b}</td></tr>" for lbl, a, b in [
        ("Varieties required in each of four categories",
         o["varieties_per_category"], n["varieties_per_category"]),
        ("Categories that must include a perishable food",
         o["perishable_categories"], n["perishable_categories"]),
    ])

    pos_tbl = "".join(
        f"<tr><td>{p['who']}</td><td>{p['represents']}</td><td>{p['stance']}</td></tr>"
        for p in P["positions"])

    html = f"""{HEAD}<title>In November, the rules change for the stores that are left</title>
<style>{CSS}</style>
<main>
<h1>In November, the rules change for the stores that are left</h1>
<p class="sub">An epilogue · the Thrifty Food Plan, the new SNAP stocking standard, and a prediction
made before the deadline</p>

<div class="ledger">
  <div><b>{im['small_share_of_retailers_pct']}% of stores, {im['small_share_of_redemptions_pct']}% of
    spending</b><span>the small stores this rule hits hardest are most of the SNAP retailers in the
    country and almost none of the SNAP money</span></div>
  <div><b>${im['cost_year_one_small']}</b><span>what USDA estimates it costs a small store to comply in the first
    year</span></div>
  <div><b>{n['compliance']}</b><span>the day every SNAP retailer has to meet it</span></div>
</div>

<p>The six chapters before this one are measurement. This piece is not. It is about a policy that rests on an assumption the measurement has quietly undercut. And about a rule that takes effect in a few months.</p>

<p>Two things here cannot be settled with this data, and both are labelled where they appear.</p>

<h2>The benefit is a shopping list</h2>

<p>The size of a SNAP benefit is not chosen. It is calculated. USDA builds a shopping list called the
<strong>Thrifty Food Plan</strong>, prices it, and that price becomes the maximum monthly allotment. The
plan was re-evaluated in {tfp['reevaluated']} for the first time since {tfp['previous']}, as Congress
directed in the {tfp['directive']}.</p>

<p>It is a real list, built to be cheap. It is priced for a family of four: {tfp['reference_family']}. Seafood is the most expensive category on it, at about <strong>${tfp['seafood_weekly_cost']:.2f} a week</strong>. The plan keeps that cost down by assuming cheap choices. It names <strong>tilapia or canned tuna</strong> as its examples. Someone worked out that a
family on the lowest food budget the government models could buy frozen tilapia.</p>

<p>Now notice what the plan does not model. It prices the basket at national average prices. It assumes
a working kitchen, time to cook, storage space, and a way to get to a store. It does not ask whether any
store within reach of a household actually carries the items on the list.</p>

<h2>SNAP's bar for a store is far lower than its own basket</h2>

<p>Until this year the bar was low. A store needed three kinds of food in each of four staple categories, three units of each. That is <strong>{o['total_items']} items</strong> in total, of which {o['perishable_items']} had to be perishable, spread across at least {o['perishable_categories']} categories. That is the floor. A store
can be fully SNAP-authorized and carry a small fraction of the basket the benefit was priced from.</p>

<p>Put that beside what this series found. In {tl['no_grocery']} of the ZIP codes that lost their last
chain pharmacy, the only SNAP-authorized food retail left is a dollar store or a convenience store. Both
are formats built around a narrow, shelf-stable assortment.</p>

<p>So the question is simple, and <strong>we cannot answer it</strong>: how much of the Thrifty Food Plan
can actually be bought in these places? There are no shelves in this data. We know where the stores are
and what type they are; we have no idea what is inside them. Anyone offering a number here is guessing,
and we are not going to.</p>

<p>But the question did not use to matter as much, and now it does. The benefit is calculated as though a
household shops somewhere that stocks a full-line basket. In a growing number of places, the store that
stocks a full-line basket is the one that left.</p>

<h2>What changes in November</h2>

<p>The floor is about to move. Congress ordered a seven-variety standard back in the {n['directive']}. Then it blocked the same standard in 2017. Now USDA has finalized it. It takes effect <strong>{n['effective']}</strong>, and every authorized store must comply by <strong>{n['compliance']}</strong>.</p>

<table><thead><tr><th>Requirement</th><th>Until now</th><th>From November</th></tr></thead>
<tbody>{std_tbl}</tbody></table>

<p>The four categories are {n['category_names']}. The variety requirement more than doubles.</p>

<p>USDA has published its own forecast, in an impact analysis filed with the rule.
<strong>{im['stores_needing_varieties']:,} stores</strong> have to add varieties to keep selling to SNAP
households. Of those, the agency expects about <strong>{im['stores_denied']:,} to be denied</strong> — a
denial rate of {im['new_denial_rate_pct']}%, up from the {im['baseline_denial_rate_pct']}% and roughly
{im['baseline_annual_denials']:,} denials a normal year produces.</p>

<p>That is not the same as {im['stores_denied']:,} stores gone, and it is worth being precise about it.
USDA expects most of those stores to buy the stock and apply again: it budgets for
{im['reauthorizations_expected']:,} reauthorizations. Its own projected net loss is about
<strong>{im['net_permanent_loss']:,} stores</strong>. Around
<strong>{im['small_share_of_retailers_pct']}%</strong> of all SNAP
retailers are the small formats most exposed: convenience stores, small grocers, and the combination
stores that include dollar stores.</p>

<h2>Why USDA thinks that is acceptable</h2>

<p>The same analysis says why the agency is not worried, and it is worth quoting, because it is the
argument this whole series has been circling.</p>

<p>Only about <strong>{im['small_share_of_redemptions_pct']}% of SNAP spending</strong> happens at the
small store types this rule hits hardest — the ones that make up about
<strong>{im['small_share_of_retailers_pct']}% of all SNAP-authorized retailers</strong>. Meanwhile
{im['large_share_of_redemptions_pct']}% of SNAP spending happens at superstores and supermarkets, which
are {im['large_share_of_retailers_pct']}% of retailers. From that, USDA concludes: "If participants are
not redeeming a significant amount of SNAP benefits at these smaller stores, then it is not likely that
their removal from the program will pose hardship to many SNAP participants."</p>

<p>Read one way, that is simply true. Most SNAP money is spent at big stores, and it always has been.</p>

<p>Read another way, it is the argument for every change in this series. A store that holds 11% of
spending still holds all of the spending for the household that walks to it. The six days before this
one were about which stores are near people and which are not, and averages do not answer that question.
The 7.7% of ZIP codes with a dollar store and no grocery are not visible in a national redemption
share.</p>

<h2>Two problems with that forecast</h2>

<p><strong>The first is the cost.</strong> USDA put compliance at about
<strong>${im['cost_year_one_small']} in the first year</strong> and ${im['cost_five_years_small']} over five years
for a store that needs to add varieties. That figure is what let the agency conclude the rule has
"{im['rfa_finding']}".</p>

<p>But the requirement that actually bites is not the seven varieties. A small store can stock seven
shelf-stable varieties in each category without much trouble. It is that perishable foods must now appear
in <strong>{n['perishable_categories']}</strong> of the four categories rather than
{o['perishable_categories']}. Perishable means refrigeration. A commercial cooler does not cost
${im['cost_year_one_small']}. If that is the binding constraint, the agency has priced the easy half of its own
rule.</p>

<p><strong>The second is that a store can be spared.</strong> A third authorization pathway,
<strong>"need for access"</strong> ({nfa['citation']}), lets USDA keep a store in the program if it sits
where food access is significantly limited. The agency weighs several things: {nfa['factors']}. It can also weigh, in the regulation's own words, "{nfa['catchall']}".</p>

<p>That provision could protect exactly the stores this series has been describing. But it is
discretionary, and <strong>USDA has not published the scoring methodology it uses</strong>. So whether
those stores survive is an administrative decision that currently cannot be audited from outside.</p>

<h2>A prediction, before the deadline</h2>

<p>We are writing this before {n['compliance']}, which means we can say what we expect and then be
checked against it. That seems fairer than explaining it afterwards.</p>

<p><strong>First: it will look like an entry collapse, not a wave of closures.</strong> This is the
clearest prediction, because it already happened. When stocking standards last tightened in 2018, new
small-grocery authorizations fell <strong>{abs(pre['entry_pct']):.0f}%</strong> while departures fell
{abs(pre['exit_pct']):.0f}% — that is, exits did not rise at all. A rule that raises the bar mostly stops
the next store from starting.</p>

<figure>{c_pre}{charts.legend(s_pre)}
<figcaption>New authorizations and departures for small grocery stores. The last time stocking standards
tightened, the entry line moved and the exit line did not.</figcaption></figure>

<p><strong>Second: the losses will fall on the stores that carry the least stock.</strong> A stocking rule asks for a fixed amount of inventory. That is a large demand on a small store and no demand at all on a big one. When the standard last tightened, the fall sorted by exactly that, in USDA's own categories:</p>

<table><thead><tr><th>USDA store type</th><th>Change in new sign-ups per year</th></tr></thead>
<tbody>{ladder_rows}</tbody></table>

<p>It is tempting to shorten this to "chains will be fine, independents will not." The record does not support that cleanly. Inside the one USDA category that holds both, the non-dollar chains fell as far as the independents did — and those chains are Walgreens, CVS, Rite Aid, Big Lots and Fred's, so their fall is tangled up with a bankruptcy and a liquidation. Scale helps a store stay in the program once it is in. It did not decide who stopped signing up.</p>

<p><strong>Third: the access consequences will concentrate in the places in this series.</strong> Losing
one authorized store matters little in a city. It matters a great deal in a ZIP code of
{den['lost_no_grocery']['median_pop']:,} people with no grocery store left.</p>

<p><strong>Fourth, and this is the one that matters: it will push in the direction things were already
going.</strong></p>

<p>Day 4 found two rules running through this whole series. Bigger stores kept their authorization —
among independent stores, survival ran straight down the size order, from 46% for a super store to 4%
for a small grocery. And a chain did not need to be big: a dollar store held its authorization as
reliably as a super store did.</p>

<p>Now read the new standard against those two rules. It asks for a fixed quantity of stock — seven
varieties in each of four categories, a perishable in three of them. A fixed demand is close to nothing
for a large store and a great deal for a small one. It is also far easier for a chain, which has
distribution, buying power and refrigeration it already owns, than for an independent buying at retail
and finding somewhere to put a cooler.</p>

<p>That is the same axis. The rule does not create the trend this series has been describing. It leans
on it.</p>

<p>And USDA's own analysis amounts to a decision to accept that. The small stores are
{im['small_share_of_retailers_pct']}% of SNAP retailers and {im['small_share_of_redemptions_pct']}% of
SNAP spending, and from that the agency reasons that losing some of them will not cause hardship. As a
reading of an average, that is defensible. It is also a judgment that twenty years of consolidation is
not a thing worth slowing down.</p>

<h2>Who argued about this, and who did not</h2>

<table><thead><tr><th>Organization</th><th>Represents</th><th>Position</th></tr></thead>
<tbody>{pos_tbl}</tbody></table>

<p>That line-up is worth sitting with. The formats that already meet the standard are for it. The formats that do not are against it. Whatever the rule does for nutrition, it also hands an advantage to stores that already carry a full range.</p>

<p>The dollar store chains said nothing in public at all. Their actions point both ways. The largest of them has put SNAP payment on delivery apps for more than {dg['ebt_delivery_stores']:,} of its stores. Yet it sells fresh produce in fewer than one in three of them, and it is slowing that rollout down.</p>

<p>There is precedent for what happens next. A version of this rule was proposed in 2019. It drew more than {P['precedent_2019']['opposing_comments']:,} comments against it. Most were about the same worry: {P['precedent_2019']['theme']}.</p>

<h2>What we will do about it</h2>

<p>Every figure in this series comes from a file USDA updates. When it updates, the same code that made these charts will show which stores lost authorization. By format, by ZIP code, and by how many people live there. It will also show whether {im['net_permanent_loss']:,} was close.</p>

<p>We will publish that either way.</p>

<p>None of this argues for a particular policy. It argues something narrower. A benefit priced from a basket is only as good as the nearest store's willingness to stock that basket. And the economics under that assumption have moved a long way in twenty years. If the formats that survive in thin
markets are the ones never designed to sell a week of groceries, then the question is not only how much
money a household gets. It is how food reaches people who have the fewest ways to go and get it.</p>

<div class="caveat">
<h3>Limits</h3>
<p><strong>The Thrifty Food Plan question is a question, not a finding.</strong> This data cannot see
inside a store, so no estimate is made of how much of the plan's basket is stocked anywhere. Measuring
that needs shelf-level audit data — the kind collected by in-store surveys such as NEMS-S, not by an
authorization file. The stocking standards and the plan's assumptions are cited so the gap between them
can be checked, not to imply it has been measured.</p>
<p><strong>We describe effects, not motives.</strong> USDA's stated purpose for the rule is nutrition.
Nothing here claims it is intended to reduce program spending, and this data could not establish intent
if it were. Note also that fewer authorized stores does not by itself reduce SNAP benefits, which are set
by household size and income against the Thrifty Food Plan price. Any spending effect would run
indirectly, through households finding the program harder to use — which this data cannot observe
either.</p>
<p><strong>The predictions are predictions.</strong> They follow from patterns measured in earlier
chapters, not from any knowledge of how USDA will administer the rule. The "need for access" pathway
gives the agency wide discretion, and a determined effort to protect rural stores could make all three
wrong. That would be a good outcome and we would report it as one.</p>
<p>The compliance-cost and store-loss figures are USDA's own. We have not independently estimated
either.</p>
</div>

<footer>
Sources: {tfp['source']} · {o['source']} · {n['source']} (docket {n['docket']}, effective
{n['effective']}, compliance {n['compliance']}) · {im['source']} · need-for-access pathway at
{nfa['citation']} · trade association positions from published statements by FMI and the National
Grocers Association and the joint comments of NACS, NATSO and SIGMA filed 24 November 2025 ·
{dg['source']}. Store-count and survival figures from USDA FNS SNAP Retailer Locator Historical Data,
2005–2025, using 656,868 stores with usable coordinates. Code, pipeline and verification:
<a href="https://github.com/Data4ThePeople/SNAP_Locations">Data4ThePeople/SNAP_Locations</a>.
</footer>
</main>"""

    OUT.write_text(html)
    print(f"wrote {OUT} ({len(html)//1000} KB)")
    print(f"  entry {pre['entry_pct']:+.0f}% vs exit {pre['exit_pct']:+.0f}%")
    print(f"  {im['stores_denied']:,} denials, {im['reauthorizations_expected']:,} reapplications, "
          f"net ~{im['net_permanent_loss']:,}")


if __name__ == "__main__":
    main()
