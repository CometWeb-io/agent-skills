# Compliance and side-effect guardrails

## Public professional data only

Use company and public professional information relevant to a business relationship. Do not use leaked, breached, doxxed, or unprovenanced personal data.

Do not qualify, segment, or personalize from sensitive traits such as health, religion, political views, sexuality, financial hardship, or other protected/sensitive personal information.

## Platform access

- Do not bypass CAPTCHAs, login walls, robots restrictions, rate limits, or anti-bot controls.
- Do not bulk scrape LinkedIn, Google Maps, gated communities, or platforms whose terms prohibit the method.
- Use browser-assisted research on public pages or licensed data providers within their terms.
- Preserve source lineage for public contact information used downstream.

## Contact paths

Prefer:

- warm introduction,
- public business email,
- official contact form,
- public professional profile where business outreach is normal,
- role-based email published by the organization.

A public pain signal does not automatically authorize private personal outreach, especially in consumer or sensitive contexts.

## Side-effect authority

This skill may recommend actions and prepare context, but it must not automatically:

- send email/DM,
- submit forms,
- connect/follow/comment,
- create/update CRM records,
- schedule meetings,
- sign/accept agreements,
- promise pricing, discounts, roadmap work, exclusivity, security terms, or reference rights.

Require explicit user authorization for external writes/actions.

## Live pilot data

When the design partnership involves private customer data, production systems, employee/user data, credentials, or regulated/sensitive domains:

- minimize requested data/access,
- identify whether synthetic/sandbox data can answer the learning question first,
- surface security/privacy/data-processing implications,
- use current system-of-record policies and qualified review where material,
- never embed credentials or secrets in research artifacts.

## Legal posture

Do not encode static legal conclusions about cold outreach, privacy, contracts, IP, platform terms, or data processing. When jurisdiction or contract terms materially affect activation, verify current primary/official guidance and route unresolved legal issues for qualified review.
