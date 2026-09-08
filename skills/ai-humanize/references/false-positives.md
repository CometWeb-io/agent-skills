# False positives and register exceptions

This file is the brake on the rule catalogs. A writing guide that bans ordinary language produces stiff prose, so a catalog hit must always be interpreted in context.

Some examples below come from an earlier calibration pass over pre-LLM human writing (110 Polish articles from 2014–2018 and 50 English marketing articles from 2006–2008). The raw corpora and exact source manifest are **not bundled in this skill**, so treat the percentages as historical calibration notes rather than independently reproducible benchmark claims. They are useful for avoiding overreach, not for detecting authorship.

## Correlative conjunctions are ordinary grammar

**Polish: `nie tylko X, ale także Y`.** This is standard Polish grammar. In the historical calibration it appeared in 6.7% of the Polish human-writing sample.

**English: `not only X, but also Y`.** The same construction appeared in roughly 8% of the historical English marketing sample.

What is often worth editing is the rhetorical **crescendo** where the second half merely outbids the first:

- Edit candidate: `nie tylko proces, ale wręcz cały model` / `not only faster, but rather transformative`
- Ordinary: `nie tylko cena, ale także serwis` / `not only the price, but also the service`
- Ordinary: `nie tylko cena, ale przede wszystkim serwis`

The distinction is semantic. Addition is ordinary; ornamental substitution or escalation is the style problem.

## Domain terms are not corporate filler

In Polish SEO writing, `słowa kluczowe`, `kluczowe frazy`, and related inflections name the subject matter. Do not rewrite a technical/domain term simply because the same root can be corporate filler elsewhere.

General rule: before removing a catalog word, ask whether it is the correct name of the thing being discussed.

## One generic heading is architecture, not a template

`## Summary` / `## Podsumowanie` can be perfectly normal. The historical English calibration found a closing summary in 39 of 50 human articles.

The editing problem is usually the whole generic skeleton (`Introduction / Key Benefits / Challenges / Conclusion`) when the headings say nothing about the actual content. Prefer specific headings when they improve navigation, but do not ban a single generic section mechanically.

## Register matters more than a banned-word list

Marketing legitimately uses some language that also appears in generic model prose. Academic writing legitimately uses formal cohesion markers such as `furthermore` and `moreover`. Documentation legitimately repeats exact technical terms.

If a catalog rule conflicts with the destination register, preserve the register.

## The catalogs are not detectors

An earlier internal calibration reported AUC around 0.48 for separating a model sample from genre-matched human text using the rule hits. Because the full evaluation artifacts are not bundled here, do not present that number as a current benchmark or independently reproduced result.

The only operational conclusion is durable: **catalog hits are editing signals, not authorship evidence**. Never infer “many hits = AI-written.”

## Practical decision rule

When a rule fires, use this order:

1. Is the phrase technically or legally required? Keep it.
2. Is it ordinary grammar for this language? Keep it unless repetition hurts the prose.
3. Is it appropriate to the destination register? Keep it if it earns its place.
4. Does it merely add hype, meta-commentary, or template cadence? Rewrite or remove it.
