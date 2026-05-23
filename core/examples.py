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


def get_examples(n: int = 3) -> List[str]:
    """Return *n* randomly selected few-shot examples (without replacement).

    If n >= total available examples, returns all of them (shuffled).
    """
    count = min(n, len(_EXAMPLES))
    return random.sample(_EXAMPLES, count)
