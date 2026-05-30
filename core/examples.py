"""
core/examples.py -- Few-shot examples of genuinely human LinkedIn posts.

These are the gold standard the AI should aim for. Each demonstrates a
different style and proves specificity, rhythm, and warmth can coexist
without a single banned phrase.

Usage:
    from core.examples import get_examples
    examples = get_examples(n=3)  # random subset for prompt injection
"""
from __future__ import annotations

import random
from typing import List


# ─────────────────────────────────────────────────────────────────────────────
# THE EXAMPLES
# ─────────────────────────────────────────────────────────────────────────────

_EXAMPLES: List[str] = [
    # ── 1. Nigerian professional storytelling ─────────────────────────────────
    """Three years ago we charged a client in Ikeja N450,000 for a compliance audit.

She balked. Said her previous lawyer charged N120,000. We showed her the 14-page gap analysis, the three regulatory filings she'd missed, and the N6.2 million penalty she was one inspection away from eating.

She paid that afternoon.

Last month she referred two other factory owners in Ogba to us. Both had the same gaps. Both had been paying "cheaper" firms that filed nothing.

We've done 23 of these audits now. Average client saves N4.1 million in avoided penalties within 8 months. The cheapest option and the least expensive outcome are almost never the same thing.

Our small team in Ikeja keeps learning that lesson. Every single quarter.""",

    # ── 2. Mid-scene opener ──────────────────────────────────────────────────
    """"Delete the entire campaign," my CD said. Wednesday. 6:47pm. Everyone else had gone home.

We'd spent three weeks on it. N1.8 million in production costs. The client presentation was Friday morning.

She wasn't being dramatic. She'd seen the focus group results an hour earlier. Four out of six participants confused our ad with a competitor's. The other two couldn't recall it at all.

So we started over. Thursday at 8am. Pulled two junior creatives off other projects. Ordered jollof rice at 11pm that night because nobody was leaving.

Friday at 9am we presented something rawer, less polished, built in 26 hours instead of three weeks.

The client ran it for 11 months. It outperformed the previous quarter's work by 340% on recall.

I still think about the version we killed. It was beautiful. It was also completely invisible.""",

    # ── 3. Withhold-the-lesson ────────────────────────────────────────────────
    """My first employee quit after four months. She gave two weeks notice on a Monday in March 2019.

I'd raised her salary twice already. Given her equity. Let her work from home every Friday. She was running the Lekki office basically alone while I chased new clients in Abuja.

During her notice period I asked what went wrong.

She said: "You never once asked me what I thought about the product. You asked me to execute. Every day. For four months."

She went to a 12-person startup in Yaba. Took a 30% pay cut. Last I checked she's their VP of Product.

I hired her replacement and gave them a title: "Operations Lead." Same job. Same salary.

It took me another year and a second resignation before I changed anything real about how I run the company.""",

    # ── 4. Communal/warm style ────────────────────────────────────────────────
    """We ran our first cohort of 8 founders through a 90-day revenue sprint in Port Harcourt last quarter.

Numbers first: 5 of 8 hit their revenue target. Average increase was 47% month-over-month by week 12. The other 3 didn't fail -- they pivoted mid-sprint and are tracking to hit target this month.

What we didn't expect: the WhatsApp group became more valuable than the curriculum. Founders were sharing supplier contacts, introducing each other to customers, negotiating group rates on logistics.

One founder -- runs a frozen food distribution network across Rivers State -- connected another founder to her cold chain supplier. Saved him N2.3 million on his first order. We didn't plan that. It just happened because we put the right 8 people in a room together.

We're running cohort 2 starting January. Same format. Still 8 people. We won't scale the cohort size because 8 is where trust forms fast enough to be useful.""",

    # ── 5. Data-driven but human ──────────────────────────────────────────────
    """Tracked every single proposal we sent in 2023. All 94 of them.

Win rate: 34%. Slightly above our industry average of 28%.

But here's what the breakdown showed:

Proposals sent within 48 hours of the first call: 52% win rate.
Proposals sent after 5+ days: 11% win rate.
Proposals where we included a one-page "here's what we heard" summary before the scope: 61% win rate.

That one-page summary takes about 40 minutes to write. It's not a proposal. It's proof that we were actually listening during the call and not just waiting to paste our standard deck.

We lost N14.2 million in potential revenue last year on proposals we sent too late. I know because I went back and counted.

This year the rule is simple: proposal goes out in 48 hours or we decline the opportunity. Sounds extreme. Our Q1 win rate is 49%.""",

    # ── 6. Ambiguous ending (no CTA) ─────────────────────────────────────────
    """Turned down a N7.5 million retainer last Tuesday.

The client wanted us to manage their entire social presence -- six platforms, daily posting, monthly reports, quarterly strategy reviews. Good scope. Fair price. 18-month contract.

During the briefing call their marketing director said something that stuck: "We just need someone to make us look consistent."

Consistent. Not interesting. Not useful to their audience. Not tied to any revenue outcome. Consistent.

I asked what success looked like at month 6. She said: "Posting every day without gaps."

We build campaigns that move revenue. We measure in leads, conversions, cost-per-acquisition. We've never once reported "days without a gap" to a client because it doesn't mean anything.

I sent a polite decline on Wednesday morning. Recommended two agencies who'd be a better fit.

My business partner thinks I'm stubborn. Maybe. Our pipeline is thinner this month than I'd like it to be.""",
]


# ─────────────────────────────────────────────────────────────────────────────
# REGION-NEUTRAL EXAMPLES
# ─────────────────────────────────────────────────────────────────────────────
# Same gold standard as _EXAMPLES (specificity, rhythm, zero banned phrases) but
# without Nigeria-specific markers (naira, Lagos, CAC, etc). Used when Nigerian
# Voice Mode is OFF so a US/EU/global user doesn't get local context bleed.

_GLOBAL_EXAMPLES: List[str] = [
    # ── 1. Data-driven, generic currency ─────────────────────────────────────
    """Tracked every proposal we sent last year. All 88 of them.

Win rate: 31%. A little above our industry's 26%.

The breakdown is where it got interesting:

Proposals sent within 48 hours of the first call: 49% win rate.
Proposals sent after 5+ days: 9%.
Proposals that opened with a one-page "here's what we heard" summary: 58%.

That summary takes about 40 minutes. It isn't a pitch. It's proof we actually listened on the call instead of waiting to paste our deck.

We left roughly $90k on the table last year on proposals we sent too late. I went back and counted.

This year the rule is simple: it goes out in 48 hours or we pass. Q1 win rate so far is 46%.""",

    # ── 2. Mid-scene opener ──────────────────────────────────────────────────
    """"Kill the whole feature," my head of product said. 6:10pm on a Thursday. The release was Monday.

We'd spent five weeks on it. Two engineers, one designer, a stack of mockups everyone loved.

She'd watched six users try it that afternoon. Four couldn't find it. The two who did used it wrong and assumed they'd broken something.

So we cut it. Friday morning we shipped a smaller version built in a day instead of five weeks.

Support tickets for that flow dropped 40% the following month.

I still have the original mockups pinned above my desk. Beautiful screens. Nobody missed them.""",

    # ── 3. Withhold-the-lesson ────────────────────────────────────────────────
    """My first hire quit after five months. Gave notice on a Monday.

I'd raised her pay twice. Handed her the biggest account. Let her run the team while I chased new business.

During her notice I asked what went wrong.

She said: "You never once asked what I thought. You told me what to do. Every day. For five months."

She joined a ten-person team across town. Took a pay cut to do it. She runs their product org now.

I gave her replacement a better title and the same job. Same salary.

It took a second resignation, a year later, before I changed anything that actually mattered.""",

    # ── 4. Contrarian, calm ───────────────────────────────────────────────────
    """We stopped doing daily standups four months ago. Revenue is up. So is the team's mood.

Everyone said it would fall apart. It didn't.

Here's what we did instead. Each person posts three lines in a shared doc before noon: what shipped, what's stuck, what they need. No meeting. No 15 minutes of waiting for the laggard to join.

Blockers now get answered in writing, in minutes, by whoever knows the answer -- not at 9am the next morning by whoever happens to be in the room.

We got back about 45 minutes a day per person. Across eight people that's nearly five hours daily.

The standup was never the work. It was a status ritual we mistook for alignment.""",

    # ── 5. Communal/warm, no CTA ──────────────────────────────────────────────
    """Ran our first 8-person founder cohort through a 90-day revenue sprint last quarter.

Numbers first: 5 of 8 hit their target. Average lift was 44% month-over-month by week 12. The other three pivoted mid-sprint and are tracking to hit it this month.

The part we didn't plan for: the group chat became more useful than the curriculum. Founders traded supplier contacts, made customer intros, split logistics costs.

One founder connected another to her manufacturer and saved him about $14k on his first run. We didn't teach that. It happened because the right eight people were in one room.

Cohort two starts next month. Still eight people. We won't grow it -- eight is where trust forms fast enough to matter.""",
]


def _examples_pool_for(global_mode: bool) -> List[str]:
    """Expose the resolved pool (used by tests / debugging)."""
    return _GLOBAL_EXAMPLES if global_mode else _EXAMPLES


def get_examples(n: int = 3, seed: int | None = None, *, global_mode: bool = False) -> List[str]:
    """Return *n* randomly selected few-shot examples (without replacement).

    If n >= total available examples, returns all of them (shuffled).

    Parameters
    ----------
    seed : int or None
        When provided, creates a local Random instance seeded with this value
        so selection is deterministic without polluting the global random state.
    global_mode : bool, default False
        When True, draw from the region-neutral example pool (USD/generic) so
        non-Nigerian users don't get naira/Lagos context bleeding into their
        posts. When False (Nigerian Voice Mode), draw from the Nigerian pool.
        Falls back to the full combined pool if the chosen pool is too small.
    """
    pool = _GLOBAL_EXAMPLES if global_mode else _EXAMPLES
    if len(pool) < n:
        # Top up from the other pool so we always have enough calibration.
        other = _EXAMPLES if global_mode else _GLOBAL_EXAMPLES
        pool = pool + [e for e in other if e not in pool]

    count = min(n, len(pool))
    if seed is not None:
        rng = random.Random(seed)
        return rng.sample(pool, count)
    return random.sample(pool, count)


# ─────────────────────────────────────────────────────────────────────────────
# HOOK EXAMPLES (standalone first lines for hook-quality calibration)
# ─────────────────────────────────────────────────────────────────────────────

_HOOK_EXAMPLES: List[str] = [
    "Three years ago we charged a client in Ikeja N450,000 for a compliance audit.",
    "\"Delete the entire campaign,\" my CD said. Wednesday. 6:47pm.",
    "My first employee quit after four months.",
    "We ran our first cohort of 8 founders through a 90-day revenue sprint in Port Harcourt last quarter.",
    "Tracked every single proposal we sent in 2023. All 94 of them.",
    "Turned down a N7.5 million retainer last Tuesday.",
    "Is your SaaS contract actually enforceable under Nigerian law?",
    "94 proposals. 34% win rate. One variable changed everything.",
]


def get_hook_examples(n: int = 3, seed: int | None = None) -> List[str]:
    """Return *n* randomly selected hook examples (without replacement).

    If n >= total available hook examples, returns all of them (shuffled).

    Parameters
    ----------
    seed : int or None
        When provided, creates a local Random instance seeded with this value
        so selection is deterministic without polluting the global random state.
    """
    count = min(n, len(_HOOK_EXAMPLES))
    if seed is not None:
        rng = random.Random(seed)
        return rng.sample(_HOOK_EXAMPLES, count)
    return random.sample(_HOOK_EXAMPLES, count)


# ─────────────────────────────────────────────────────────────────────────────
# COMMENT EXAMPLES (strategic LinkedIn comments demonstrating quality)
# ─────────────────────────────────────────────────────────────────────────────

_COMMENT_EXAMPLES: List[str] = [
    "Your point about the 48-hour proposal window mirrors what we found tracking 62 pitches last year in Abuja. The number that shocked us: proposals sent within 24 hours had a 58% close rate vs 9% after day 5. Speed signals seriousness more than polish ever will.",
    "The arbitration clause point hits different when you've seen it go wrong. Had a client lose N12M because the seat was London but governing law was Nigerian -- nobody caught the conflict until enforcement stage. One line in the contract. Twelve million naira.",
    "That 47% month-over-month growth figure from the cohort -- was that measured from first revenue or from the sprint start date? Asking because we found a 3-week lag between intervention and measurable revenue shift in our accelerator. The real gains showed up in month 4, not month 3.",
    "This is the part most founders skip: the WhatsApp group becoming more valuable than the curriculum. We saw the same pattern running a 12-person cohort in Lekki. The peer referrals generated 3x more revenue than anything we taught directly.",
]


def get_comment_examples(n: int = 2, seed: int | None = None) -> List[str]:
    """Return *n* randomly selected comment examples (without replacement).

    If n >= total available comment examples, returns all of them (shuffled).

    Parameters
    ----------
    seed : int or None
        When provided, creates a local Random instance seeded with this value
        so selection is deterministic without polluting the global random state.
    """
    count = min(n, len(_COMMENT_EXAMPLES))
    if seed is not None:
        rng = random.Random(seed)
        return rng.sample(_COMMENT_EXAMPLES, count)
    return random.sample(_COMMENT_EXAMPLES, count)
