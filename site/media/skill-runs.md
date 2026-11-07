# Skill runs shown on the landing page

Three requests sent to Claude Code 2.1.280 on 7 November 2026, run headless
with `claude -p`, the skills loaded from this repository with `--plugin-dir`
(commit `c40de2e`), from an empty working directory. The first two prompts do not
name a skill; Claude Code chose which one to load. The third names it (see
below). Tools allowed: Skill, Read, Glob,
Grep, WebFetch and WebSearch. The page shows a few sentences from each answer,
verbatim; the full answers are below. Local paths are replaced with `<repo>`
and `<scratch>`.

## 1. Homepage roast

Skill loaded: `cometweb-agent-skills:content-roaster`. Time: 39 s.

Prompt:

> Here is the hero section of our homepage. Roast it and tell me the three fixes that matter most.
> 
> Headline: "The AI-powered reliability platform for the modern enterprise"
> Subheadline: "Unlock next-generation insights with our cutting-edge, best-in-class solution."
> Button: "Book a demo today!"

Answer:

Verdict: the hero fails on all three lines, and the root cause is the same for each. Nothing in it is specific to your product, your buyer, or your proof. I inferred the contract since none was supplied: an enterprise buyer lands here and should know within five seconds what you fix and why to trust you.

**The roast**

- **Headline is a category label, not a promise.** "AI-powered reliability platform for the modern enterprise" tells me what shelf you sit on, not what changes for me. Every phrase is a 2026 default. Swap your logo for a competitor's and the headline still works, which is the test it fails.
- **Subheadline carries zero information.** Five adjectives, no noun a reader can picture. "Unlock", "next-generation", "cutting-edge" and "best-in-class" all do the same job, which is covering for the absence of proof. This is the one spot in the hero where evidence belongs, and it is empty.
- **The button asks for the most expensive action with no reason attached.** A demo is a 30-minute calendar commitment to a sales call. The hero gives nothing to justify it and offers no cheaper path for the 95 percent who are not ready. "Today!" with an exclamation mark reads as retail urgency, which enterprise buyers discount on sight.
- **"Modern enterprise" is nobody.** No role, no team, no situation. SRE lead at a bank and a VP Eng at a 200-person SaaS both bounce because neither sees themselves.

**The three fixes that matter, in order**

1. **Rewrite the headline around the outcome and the pain, not the category.** Name what breaks and what you change about it. Illustrative shape only, since I do not know your product: "Find the cause of an outage before your customers find it." Success condition: a reader can repeat what you do in one sentence after a glance. Failure signal: the line still fits a competitor's site unchanged.

2. **Replace the subheadline with one mechanism and one proof point.** One sentence on how it works in plain words, one sentence of evidence. Evidence means a named customer, a measured number, or what it plugs into, such as "Reads your Datadog, PagerDuty and Kubernetes data." If you have no proof point yet, that is a PROOF gap and no copy fixes it. Verification: delete the subheadline and reread. If the page lost nothing, the replacement was still filler.

3. **Lower the ask and pair it with a second path.** Drop "today!" and tell the reader what the demo is, for instance "See it on your incidents, 30 min." Add a low-commitment secondary next to it: a two-minute product video, interactive sandbox, or the docs. Verification: compare hero click-through before and after, and watch whether secondary clicks later convert to demos.

**What I could not check.** Whether "AI-powered" describes anything real in the product is a claim I could not verify from three lines. If the AI is a thin layer, drop it from the headline before a prospect asks what it does.

## 2. Release check

Skill loaded: `cometweb-agent-skills:release-readiness`. Time: 104 s.

Prompt:

> Is our release candidate v2.3.0 (build 1187) ready to ship to production today? What we know: all 412 unit tests pass; QA reproduced that checkout returns HTTP 500 for EUR payments (3 of 3 attempts); two minor UI typos on the settings page; a rollback plan exists and was rehearsed last week.

Answer:

**Verdict: NO_GO. Do not ship v2.3.0 build 1187 to production today.**

One caveat on process. The skill's gate engine could not be executed in this session because running a script outside the working directory needs an approval I cannot get non-interactively. I applied the engine's published precedence rules by hand, and the first rule settles it: a failed binding blocker check yields NO_GO before any score or coverage is considered. The manifest I built is saved in the scratchpad as `readiness-v2.3.0-b1187.json` if you want to run it yourself.

**Why it blocks**

- **EUR checkout returns HTTP 500, reproduced 3 of 3 times.** That is a known P0 defect on the revenue path of a paid product. It fails two binding gates at once: release scope acceptance and billing entitlements. Nothing waives a binding blocker. Not accepted risk, not a compensating control, and not a rehearsed rollback.
- **A rollback plan reduces blast radius, it does not justify shipping a known-broken checkout.** You would be deploying a defect you already have proof of, then relying on rolling it back after EUR customers hit it.
- **412 green unit tests are not candidate verification.** The suite demonstrably did not cover the path that failed. Unit tests alone are "claimed" evidence under the policy, and there is no stated binding of that run to build 1187.

**What is not blocking**

- The two settings-page typos are minor and non-binding. On their own they would at most push a verdict to GO_WITH_CONTROLS.

**Even with the checkout fixed, you would be at DEFER, not GO.** The following are unknown and each one alone defers a release:

- Whether this release touches billing, auth, schema, or sensitive data. If billing code changed, the risk tier rises to R3 and requires deep mode plus billing state-transition evidence.
- Security, deploy pipeline, observability, operator docs, and support path have no evidence at all.
- The rollback rehearsal was last week, before this build, and no owner or trigger was named.

**Smallest closure path**

1. Fix the EUR checkout defect and produce a new build. Build 1187 cannot be rehabilitated; a changed candidate needs fresh evidence.
2. On the new build, run a checkout smoke test across every supported currency, including the failed and successful payment paths, with the result tied to the build number.
3. Resolve the risk flags above, link the CI run and deploy pipeline for the new build, and confirm that checkout 500s would page someone.
4. Re-run the gate on the new candidate.

## 3. Claim check

A first run with the plain prompt did not load a skill: Claude Code verified the
claim on its own. It was run again with the skill named as a slash command, and
that run is the one shown on the page. Time: 236 s.

Prompt:

> /cometweb-agent-skills:evidence-researcher Verify this claim against primary sources before we put it in a client report: "The European Accessibility Act applies from 28 June 2025."

Answer:

**Verdict: the claim is accurate and safe for the client report, with two wording precisions.** I verified it verbatim against the Official Journal text of Directive (EU) 2019/882, not a summary.

**Research status:** READY (STANDARD mode, as of 7 November 2026). The kernel audit did not run because the command needed an approval this session did not grant, so the status is my assessment, not a kernel result. The machine-readable pack is at `scratchpad/eaa-application-date-evidence-pack.json` if you want to run the audit yourself.

**What the primary source says** (Official Journal L 151, 7 June 2019):

- **Article 31(2), page L 151/97:** "They shall apply those measures from 28 June 2025." This is the controlling sentence behind the claim.
- **Article 2(1) and 2(2), page L 151/83:** the Directive applies to listed products placed on the market after 28 June 2025 and to listed services provided to consumers after 28 June 2025.
- **Article 31(1):** Member States had to adopt transposing law by 28 June 2022.
- **Article 34:** the Directive itself entered into force on 27 June 2019. This is a different date from the application date and the two are easy to confuse.

**Transitional measures the report should not omit** (Article 32, page L 151/98):

- Services may keep using products lawfully in use before 28 June 2025 until 28 June 2030.
- Service contracts agreed before 28 June 2025 may run until expiry, but no longer than five years from that date.
- Self-service terminals in use before 28 June 2025 may stay in use until the end of their economic life, but no longer than 20 years after entry into use.
- Member States may defer the 112 emergency-communication obligations in Article 4(8) to 28 June 2027 at the latest.

**Falsifier and version checks:**

- The EUR-Lex record shows the Directive as in force, with no adopted amendment. Corrigenda exist only for the German, Estonian, Finnish, French and Croatian versions.
- A pending Commission proposal from 9 September 2026, the Public Procurement Act (COM(2026) 590), lists this Directive among acts it would amend. It is a proposal, not law, so it changes nothing today. I could not reach the amending article in the truncated text, so I cannot say what it would change. Given its subject, it most likely replaces cross-references to the 2014 procurement directives, but that is an inference.
- A web search for any postponement of the EU-level date found none.

**Suggested wording for the report:** "The European Accessibility Act (Directive (EU) 2019/882) has applied since 28 June 2025. It covers in-scope products placed on the market and services provided to consumers after that date, subject to transitional periods running to 28 June 2030 for services using pre-existing products."

**One caveat outside this run's scope:** obligations reach companies through national transposing law, and some Member States transposed late. If the client operates in specific countries, check the national measures on the EUR-Lex transposition tab before stating a country-level date.
