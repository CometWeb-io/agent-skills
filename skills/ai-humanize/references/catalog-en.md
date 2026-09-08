# English rule catalog

Curated editing patterns for English prose, with stable IDs so examples and review notes can refer to the same rule over time. This bundle does not include a deterministic authorship scanner; use these entries as editorial heuristics, never as evidence that a model wrote the text.

Severity is editorial priority: `fatal` means remove unless an explicit exception applies, `high` and `medium` deserve review, and `low` is a preference. Allowances identify constructions that are ordinary language but become repetitive when overused.

Read [false-positives.md](false-positives.md) before treating any entry as absolute. Register, genre, and technical terminology can make a listed construction completely appropriate.

## Chat-assistant leakage (`collaborative_leakage`)

| id | severity | pattern name | fix |
|---|---|---|---|
| `AP-LEAK-001` | fatal | Chat-assistant leakage | Strip. This belongs in a chat window, not in published text. |

## Knowledge-cutoff or model disclaimers (`cutoff_disclaimer`)

| id | severity | pattern name | fix |
|---|---|---|---|
| `AP-CUT-001` | fatal | Knowledge-cutoff disclaimer | Delete. Give a dated fact or say the data is unavailable. |

## Negative parallelism (strongest single tell) (`negative_parallelism`)

| id | severity | pattern name | fix |
|---|---|---|---|
| `AP-NEG-001` | fatal | This isn't X, this is Y | Delete the negated clause. Keep only the positive statement. |
| `AP-NEG-002` | fatal | It's not about X, it's about Y | Say what it is about. Drop the contrast. |
| `AP-NEG-003` | fatal | Not only X, but rather Y | Delete the negated half. Keep the claim you are actually making. |
| `AP-NEG-004` | fatal | Forget X / Stop doing X, start doing Y | Drop the imperative setup. State the recommendation directly. |
| `AP-NEG-005` | fatal | Less X, more Y | Name the thing you want more of and stop there. |
| `AP-NEG-006` | fatal | You don't need X, you need Y | State the requirement once, positively. |
| `AP-NEG-007` | fatal | X is dead / overrated, Y is the future | Make the claim about the thing you are recommending, with evidence. |
| `AP-NEG-008` | fatal | The question isn't X, the question is Y | Ask the real question. Delete the false one. |
| `AP-NEG-009` | high | While X might seem right, Y actually | Delete the concession. Lead with what you actually think. |
| `AP-NEG-010` | high | X gets the attention, but Y is what actually matters | Write the claim about the thing that matters, without the foil. |
| `AP-NEG-011` | low (first 2 free) | Not only X, but also Y (conjunction) | Fine once or twice. By the third use in a document, write it as two plain statements. |

## Dead stock phrases (`dead_phrase`)

| id | severity | pattern name | fix |
|---|---|---|---|
| `AP-PHR-001` | high | In today's [anything] | Delete the opener. Start on the actual subject. |
| `AP-PHR-002` | high | It's important/worth noting that | Delete the frame. If it matters, just say it. |
| `AP-PHR-004` | high | Let's dive in / explore / unpack | Do the thing instead of announcing it. |
| `AP-PHR-008` | high | What nobody tells you / nobody is talking about | Delete. If the point is good it does not need a conspiracy frame. |
| `AP-PHR-003` | medium | In order to | Write 'to'. |
| `AP-PHR-005` | medium | At the end of the day / moving forward | Cut it. Neither phrase carries information. |
| `AP-PHR-006` | medium | What makes this interesting / the implications here | State the observation. Skip the drumroll. |
| `AP-PHR-007` | medium | In other words / it goes without saying | Say it once, correctly, and delete the restatement. |
| `AP-PHR-009` | medium | Despite its X, Y faces challenges | Name the specific constraint and who it hurts. |

## Mechanical discourse transitions (`dead_transition`)

| id | severity | pattern name | fix |
|---|---|---|---|
| `AP-TRN-001` | high (first 1 free) | Furthermore / Moreover / Additionally at sentence start | Open with the concrete thing instead: a number, a name, a place. |
| `AP-TRN-002` | high | In conclusion / to sum up | Delete. End on the last real point. |
| `AP-TRN-003` | medium (first 1 free) | That said / with that in mind / on top of that | Drop the hinge or replace it with the substantive contrast. |

## Dead AI vocabulary (`dead_vocabulary`)

| id | severity | pattern name | fix |
|---|---|---|---|
| `AP-LEX-001` | high | Signature LLM vocabulary | Replace with the plain word you would say out loud, or delete the adjective and name the specific thing. |
| `AP-LEX-002` | medium | Consultant filler adjectives | Swap for a concrete descriptor with a number, a name, or a measured effect. |
| `AP-LEX-003` | medium | Corporate verbs | Use the physical or specific verb: use, cut, ship, measure, rewrite, delete. |
| `AP-LEX-004` | low | Abstract 'landscape' / 'ecosystem' / 'journey' | If it is not a real place or a real ecosystem, name the market, the tool set, or the process instead. |

## Engagement bait (`engagement_bait`)

| id | severity | pattern name | fix |
|---|---|---|---|
| `AP-BAIT-001` | high | Let that sink in / read that again | Delete. Trust the reader. |
| `AP-BAIT-002` | medium | Full stop as drama | Delete the flourish and keep the sentence. |

## Hype and superpower promises (`hype`)

| id | severity | pattern name | fix |
|---|---|---|---|
| `AP-HYPE-001` | high | 10x / superpower promises | Replace with the measured outcome you can defend, or delete the claim. |

## Meta commentary about the text itself (`meta_commentary`)

| id | severity | pattern name | fix |
|---|---|---|---|
| `AP-META-001` | high | In this section we will | Do the thing. Delete the announcement. |

## Trailing participle summary clauses (`participle_tail`)

| id | severity | pattern name | fix |
|---|---|---|---|
| `AP-PART-001` | high | Trailing participle summary | Delete the clause. If the analysis matters, give it its own sentence. |

## Generic template headings (`template_header`)

| id | severity | pattern name | fix |
|---|---|---|---|
| `AP-TMPL-001` | high (first 2 free) | Generic template heading | Rename the heading after the actual decision, constraint, or number under it. |

## Ornate replacements for is/has (`copula_avoidance`)

| id | severity | pattern name | fix |
|---|---|---|---|
| `AP-COP-001` | medium | Ornate replacement for is/has | Write 'is' or 'has'. |

## Synonym churn instead of reusing the name (`elegant_variation`)

| id | severity | pattern name | fix |
|---|---|---|---|
| `AP-ALIAS-001` | medium | Synonym churn for an already-named subject | Use the name again. Repetition that keeps meaning clear is how people actually write. |

## False ranges that carry no information (`false_range`)

| id | severity | pattern name | fix |
|---|---|---|---|
| `AP-RANGE-001` | medium | From X to Y false range | Delete. Name the two or three things you actually mean. |

## Commitment-avoiding hedges (`hedge_vacillation`)

| id | severity | pattern name | fix |
|---|---|---|---|
| `AP-HEDGE-001` | medium | Commitment-avoiding hedge | Take a position, or state the uncertainty in the first person ('I think', 'I do not know yet'). |

## Inflated significance (`puffery`)

| id | severity | pattern name | fix |
|---|---|---|---|
| `AP-PUF-001` | medium | Inflated significance | State the fact. Let the reader judge importance. |




## Formulaic openers and frames (`formulaic_opener`)

| id | severity | pattern name | fix |
|---|---|---|---|
| `AP-OPEN-001` | high | In the realm of / In the world of | Delete the frame. Start with the concrete subject. |
| `AP-OPEN-002` | high | In a world where / In today's world | Delete. Lead with the claim or the evidence. |
| `AP-OPEN-003` | high | As we navigate / As we explore | Do the navigating. Drop the announcement. |
| `AP-OPEN-004` | medium | At its core / At the heart of | State the core claim without the drumroll. |
| `AP-OPEN-005` | medium | Whether you are a X or a Y | Address one reader or drop the menu of personas. |
| `AP-OPEN-006` | medium | In this post/article we will explore | Delete. Start the exploration. |

## Corporate and consultant verbs (`corporate_verb`)

| id | severity | pattern name | fix |
|---|---|---|---|
| `AP-VERB-001` | high | Leverage / utilize (when "use" works) | Write "use". |
| `AP-VERB-002` | high | Unlock the potential of | Name the specific outcome or capability. |
| `AP-VERB-003` | medium | Foster / cultivate (innovation, culture) | Say what was built, changed, or measured. |
| `AP-VERB-004` | medium | Streamline / optimize (as filler) | Name the step that got shorter or cheaper. |
| `AP-VERB-005` | medium | Empower (teams, users) | Say who can now do what that they could not. |
| `AP-VERB-006` | low | Drive (results, change) as empty verb | Prefer a verb that names the mechanism. |

## Landscape / ecosystem / journey metaphors (`abstract_landscape`)

| id | severity | pattern name | fix |
|---|---|---|---|
| `AP-LAND-001` | medium | The landscape of X | Name the market, the tool set, or the constraint. |
| `AP-LAND-002` | medium | The X ecosystem | If it is not a real ecosystem, list the actual components. |
| `AP-LAND-003` | medium | The X journey | Describe the sequence of decisions or failures instead. |
| `AP-LAND-004` | low | Pivotal role / critical role | State the concrete contribution. |

## Rhetorical setup and false contrast (`rhetorical_setup`)

| id | severity | pattern name | fix |
|---|---|---|---|
| `AP-RHET-001` | high | It goes without saying / Needless to say | Delete. If it needed saying, just say it. |
| `AP-RHET-002` | medium | The reality is that / The truth is | Lead with the claim. |
| `AP-RHET-003` | medium | Make no mistake | Delete the warning. State the point. |
| `AP-RHET-004` | low (first 1 free) | On the one hand… on the other | Fine once. Prefer a direct comparison with numbers. |

## Uniform paragraph and list templates (`template_structure`)

| id | severity | pattern name | fix |
|---|---|---|---|
| `AP-STRUCT-001` | medium | Every section the same depth | Expand 1–3 focal points; cut symmetric filler sections. |
| `AP-STRUCT-002` | medium | Bullet list of three abstract nouns | Replace with the one concrete item that matters, or four if all are real. |


## Empty intensifiers and degree words (`empty_intensifier`)

| id | severity | pattern name | fix |
|---|---|---|---|
| `AP-INT-001` | medium | Truly / really / actually as filler intensifier | Delete or replace with a concrete measure. |
| `AP-INT-002` | medium | Highly / extremely / incredibly (before abstract adjectives) | Prefer a number, a comparison, or delete. |
| `AP-INT-003` | low | Very unique / quite unique | Unique is already absolute; drop the adverb or rephrase. |

## Question-as-opener and engagement bait (`question_bait`)

| id | severity | pattern name | fix |
|---|---|---|---|
| `AP-Q-001` | high | Rhetorical question as first sentence of a section | Start with the answer or the claim. |
| `AP-Q-002` | medium | "Ready to…?" / "Want to…?" as closer | State the next concrete action instead. |
| `AP-Q-003` | medium | "What if I told you…?" | Delete the setup. Deliver the fact. |

## Meta announcements about the text (`meta_announce`)

| id | severity | pattern name | fix |
|---|---|---|---|
| `AP-META-002` | high | "In this section we will discuss…" | Do the discussing. |
| `AP-META-003` | medium | "As mentioned earlier / as we have seen" | Repeat the point briefly or cut the reference. |
| `AP-META-004` | medium | "It is important to understand that" | State the thing that must be understood. |

## Symmetry and false balance (`false_balance`)

| id | severity | pattern name | fix |
|---|---|---|---|
| `AP-BAL-001` | medium | Equal space to minor and major points | Expand what matters; compress or cut the rest. |
| `AP-BAL-002` | medium | "Pros and cons" template when one side is weak | Lead with the decisive factor. |

## Over-hedging and double hedges (`over_hedge`)

| id | severity | pattern name | fix |
|---|---|---|---|
| `AP-HEDGE-002` | medium | "It could potentially possibly…" | One hedge is enough; prefer a clear claim + evidence. |
| `AP-HEDGE-003` | medium | "Some might argue that…" without naming who | Name the position or drop the straw man. |

## Stock closing formulas (`stock_close`)

| id | severity | pattern name | fix |
|---|---|---|---|
| `AP-CLOSE-001` | high | "In conclusion / To sum up / All in all" | End on the last real point. |
| `AP-CLOSE-002` | medium | "The future of X is bright / exciting" | State the next measurable step or risk instead. |
| `AP-CLOSE-003` | medium | "Only time will tell" | Prefer a concrete uncertainty or a next experiment. |

78 rules apply to en text.
