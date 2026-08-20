"""
Seed content for Critical Reasoning Review challenges (see
models.CriticalReasoningChallenge, routers/critical_reasoning.py): the
non-code sibling of Code Review, used as the required review step for
tracks whose review_kind is "reasoning" (see config.TRACKS) - currently
just system_design, which is being broadened into an interdisciplinary
design/tradeoff-thinking track rather than a software-architecture-only one.

A paragraph of prose reasoning (a business case, incident postmortem,
design rationale, economics-flavored argument) seeded with 1-3 real
reasoning flaws (correlation/causation mixups, survivorship bias, unstated
assumptions, base-rate neglect, Simpson's paradox, etc) instead of code
bugs. Same click-a-line/match-a-reason mechanic and marker-token authoring
convention as code_review_bank.py - _build()/_entry() are reused directly
from there since neither has any code-specific logic (they operate on
marker-tagged text and a list of {marker, reason, explanation} specs).
Passages are broken into one sentence (or short group of sentences) per
line, same as code_review_bank.py's snippets, so multi-issue entries can
put each flaw on a distinct flaggable line.

Two entries per difficulty tier (matches the weekday cadence - see
config.WEEKDAY_DIFFICULTY), mirroring the count code_review_bank.py used
for system_design before this track switched review_kind - expand over
time the same way the other content banks have.
"""
from .code_review_bank import _build, _entry


def _reasoning_entry(difficulty: str, topic: str, title: str, passage: str, issues: list[dict], distractor_reasons: list[str]) -> dict:
    """_entry()/_build() call the flawed text "snippet" (they're shared with
    code_review_bank.py) - rename that key to "passage" to match
    models.CriticalReasoningChallenge's field before this dict is seeded."""
    entry = _entry(difficulty, topic, title, passage, issues, distractor_reasons)
    entry["passage"] = entry.pop("snippet")
    return entry


CRITICAL_REASONING_CHALLENGES = {
    "system_design": [
        _reasoning_entry(
            "easy", "Org Design", "Flattening the Reporting Structure",
            "Our team removed a layer of middle management last quarter, and shipping\n"
            "velocity is up 20% since then. The obvious conclusion is that management\n"
            "layers were slowing us down, so every team in the company should flatten\n"
            "its structure the same way. ‡bug1‡We should roll this out org-wide next\n"
            "quarter and expect the same 20% gain everywhere.",
            [{
                "marker": "‡bug1‡",
                "reason": "Correlation mistaken for causation",
                "explanation": (
                    "The same quarter also happened to ship a smaller, better-scoped backlog and lost two "
                    "new hires who were still ramping up - either of those could explain a velocity bump on "
                    "its own. Nothing here isolates the management-layer change as the cause, and a single "
                    "team's single quarter is far too small a sample to generalize into an org-wide policy."
                ),
            }],
            ["Appeal to popularity", "Sunk cost fallacy", "False dichotomy"],
        ),
        _reasoning_entry(
            "easy", "Incident Response", "Our Alerting Is Working Fine",
            "We haven't had a single missed page in six months, so our on-call alerting\n"
            "pipeline is clearly reliable and doesn't need the redundant paging provider\n"
            "we've been discussing. ‡bug1‡Every engineer we've asked says the current\n"
            "single-provider setup has never let them down.",
            [{
                "marker": "‡bug1‡",
                "reason": "Survivorship bias",
                "explanation": (
                    "Asking engineers who are still on the team, still get paged, and haven't quit over a missed "
                    "incident only samples the cases where the pipeline worked (or where a failure was never "
                    "noticed/escalated). It says nothing about the incidents that were missed entirely and never "
                    "generated a report, or near-misses that got caught by luck rather than the pipeline itself."
                ),
            }],
            ["Slippery slope", "Post hoc ergo propter hoc", "Bandwagon effect"],
        ),
        _reasoning_entry(
            "medium", "Trade-off Analysis", "The Microservices Pitch",
            "Our monolith is too slow for the team we've become, and everyone knows\n"
            "microservices scale better than monoliths. ‡bug1‡So the fastest way to fix\n"
            "our scaling problems is a full microservices migration - once each service\n"
            "is independently deployable, our throughput ceiling goes away.",
            [{
                "marker": "‡bug1‡",
                "reason": "Unstated assumption",
                "explanation": (
                    "\"Microservices scale better than monoliths\" is being treated as a universal law, but a "
                    "well-designed monolith can scale horizontally too (stateless instances behind a load "
                    "balancer, a properly indexed/sharded database) - the real bottleneck was never named or "
                    "diagnosed. Jumping straight to a full rewrite skips the step of confirming the monolith's "
                    "architecture, not its \"monolith-ness\", is actually what's capping throughput."
                ),
            }],
            ["Circular reasoning", "Straw man", "Red herring"],
        ),
        _reasoning_entry(
            "medium", "Hiring & Growth", "Why We Should Hire Only Senior Engineers",
            "Every senior engineer currently on the team says junior engineers slowed\n"
            "them down early in their career. ‡bug1‡Therefore, hiring only senior\n"
            "engineers going forward will make the whole team move faster, since we'll\n"
            "have eliminated the drag juniors cause.",
            [{
                "marker": "‡bug1‡",
                "reason": "Survivorship bias",
                "explanation": (
                    "The sample is every engineer who survived being a junior and became senior here - it can't "
                    "say anything about juniors who left, or about how much mentoring them contributed to the "
                    "seniors' own growth and the team's institutional knowledge. It also ignores the far higher "
                    "cost and hiring-pool constraints of an all-senior team, neither of which is a 'drag' juniors "
                    "specifically cause versus a cost every team structure pays somewhere."
                ),
            }],
            ["Appeal to authority", "False dichotomy", "Anchoring bias"],
        ),
        _reasoning_entry(
            "hard", "Metrics & Aggregation", "Region B Is Our Best-Performing Market",
            "Region B's overall conversion rate is higher than Region A's, so Region B's\n"
            "checkout flow is clearly the better design and we should roll it out\n"
            "everywhere. ‡bug1‡The numbers don't lie - a higher blended conversion rate\n"
            "settles the question.",
            [{
                "marker": "‡bug1‡",
                "reason": "Simpson's paradox",
                "explanation": (
                    "An aggregate rate can reverse once you split by segment: if Region B has a much larger share "
                    "of mobile-native, high-intent repeat customers than Region A, its checkout flow could "
                    "actually convert *worse* within every individual customer segment while still winning on the "
                    "blended number purely because of its more favorable traffic mix. The blended comparison "
                    "conflates 'better flow' with 'better audience' - they need to be compared segment by segment."
                ),
            }],
            ["Regression to the mean", "Base-rate neglect", "Selection bias"],
        ),
        _reasoning_entry(
            "hard", "Capacity Planning", "We Don't Need More On-Call Capacity",
            "Average time-to-acknowledge across all incidents this quarter was under two\n"
            "minutes, well within SLA, so the on-call rotation is adequately staffed as-is.\n"
            "‡bug1‡There's no need to add a second on-call engineer per shift.",
            [{
                "marker": "‡bug1‡",
                "reason": "Regression to the mean",
                "explanation": (
                    "An average dominated by many low-severity, fast-to-acknowledge pages hides the tail: a small "
                    "number of severe, multi-hour incidents where a single on-call engineer was overwhelmed and "
                    "acknowledgment (or resolution) actually blew past SLA. Staffing decisions driven by an "
                    "aggregate average rather than the distribution's tail miss exactly the scenario a second "
                    "responder exists to cover."
                ),
            }],
            ["Sunk cost fallacy", "Hasty generalization", "Confirmation bias"],
        ),
        _reasoning_entry(
            "expert", "Post-Incident Review", "Root-Causing the Checkout Outage",
            "During the outage, the only change deployed in the prior 24 hours was a\n"
            "caching config update, ‡bug1‡so that update is the root cause.\n"
            "Separately, the on-call engineer who responded had handled three prior\n"
            "outages successfully. ‡bug2‡Three clean prior responses is a strong track\n"
            "record, so their response process doesn't need scrutiny in this postmortem -\n"
            "the action items should focus solely on caching config review going forward.",
            [
                {
                    "marker": "‡bug1‡",
                    "reason": "Post hoc ergo propter hoc",
                    "explanation": (
                        "'The only recent change' being correlated with the outage's timing doesn't rule out a "
                        "latent bug exposed by ordinary traffic growth, a dependency's silent degradation, or an "
                        "interaction between the config change and something unrelated. Being the most recent "
                        "change is not the same as being demonstrated to be the cause - that still needs a "
                        "reproduction or a mechanism, not just timing."
                    ),
                },
                {
                    "marker": "‡bug2‡",
                    "reason": "Hasty generalization",
                    "explanation": (
                        "Three prior successful responses is a small sample, and 'successful' outcomes don't prove "
                        "the *process* used was sound - it could have gotten lucky, or those incidents may have "
                        "been simpler. Concluding the response process needs no scrutiny, and excluding it from "
                        "the postmortem on that basis, closes off a line of investigation without actually "
                        "checking it."
                    ),
                },
            ],
            ["Circular reasoning", "Slippery slope", "Appeal to authority", "False dichotomy"],
        ),
        _reasoning_entry(
            "expert", "Pricing Strategy", "Justifying the Annual-Only Plan",
            "Customers who switched from monthly to annual billing have a 40% lower churn\n"
            "rate than customers who stayed monthly. ‡bug1‡So forcing all customers onto\n"
            "annual billing will cut our overall churn by a similar margin.\n"
            "Our biggest competitor eliminated monthly billing two years ago and is still\n"
            "in business today, ‡bug2‡which confirms annual-only billing is a safe and\n"
            "proven strategy for us too.",
            [
                {
                    "marker": "‡bug1‡",
                    "reason": "Selection bias",
                    "explanation": (
                        "Customers who *chose* to switch to annual billing were already the ones confident enough "
                        "in the product to commit for a year - that confidence, not the billing cadence itself, is "
                        "plausibly what's driving their lower churn. Forcing the switch on customers who would "
                        "never have opted in themselves doesn't necessarily transplant that same lower churn rate "
                        "onto them; it may just make marginal customers not renew or not sign up at all."
                    ),
                },
                {
                    "marker": "‡bug2‡",
                    "reason": "Survivorship bias",
                    "explanation": (
                        "Pointing at the one competitor who made this change and is 'still in business' ignores "
                        "every company that made a similar switch and lost enough customers to fail or reverse "
                        "course - those failures are invisible in a story that only looks at survivors. 'Still in "
                        "business' also says nothing about whether that competitor's revenue or customer count "
                        "actually grew because of the change, versus despite it."
                    ),
                },
            ],
            ["Bandwagon effect", "Anchoring bias", "Straw man", "Sunk cost fallacy"],
        ),
    ],
}
