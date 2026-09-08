# Structured data library

## Contents

1. General rules and detection safeguards
2. Organization, LocalBusiness, Person
3. Article, Product/Offer, BreadcrumbList
4. FAQPage, HowTo, coherent entity graph


Structured data is explicit machine-readable description, not a general ranking boost. Validate
against current schema.org vocabulary and the target platform's current feature documentation.

Google currently says no special schema is required for generative AI Search. Feature support
changes over time, so refresh `live-source-registry.md` before promising a rich result.

Detection safeguard: a text-only/static fetch can strip JSON-LD or miss client-injected markup. Do
not issue a schema-absence finding until rendered DOM, a suitable validator, connected enhancement
data, or a JavaScript-rendered crawl supports it. Otherwise use `NOT_ASSESSED`.

## General rules

- Mark up facts that are visible or otherwise legitimately represented on the page/site.
- Do not fabricate ratings, prices, authors, credentials, locations, reviews, dates, or awards.
- Use stable absolute URLs and stable `@id` values for entities referenced across pages.
- Multiple valid JSON-LD blocks can work; a coherent `@graph` is useful when entities reference one
  another, but it is not mandatory.
- Do not duplicate contradictory Organization/Product/Person entities from multiple plugins.
- Validate syntax and semantic consistency after implementation.

## Organization

```json
{
  "@context": "https://schema.org",
  "@type": "Organization",
  "@id": "https://example.com/#organization",
  "name": "Example Brand",
  "url": "https://example.com/",
  "logo": "https://example.com/assets/logo.png",
  "sameAs": [
    "https://www.linkedin.com/company/example"
  ]
}
```

Use `sameAs` only for profiles that genuinely identify the same organization.

## LocalBusiness

Choose the most accurate subtype when one exists.

```json
{
  "@context": "https://schema.org",
  "@type": "ProfessionalService",
  "@id": "https://example.com/#localbusiness",
  "name": "Example Brand",
  "url": "https://example.com/",
  "telephone": "+48123456789",
  "address": {
    "@type": "PostalAddress",
    "streetAddress": "Example 1",
    "addressLocality": "Warsaw",
    "postalCode": "00-001",
    "addressCountry": "PL"
  }
}
```

Keep the underlying business facts consistent across visible site content and external profiles.
Formatting does not need to be character-for-character identical if the facts clearly match.

## Person

Useful for real author/expert/entity identity when appropriate; it is not proof of expertise.

```json
{
  "@context": "https://schema.org",
  "@type": "Person",
  "@id": "https://example.com/team/anna/#person",
  "name": "Anna Kowalska",
  "url": "https://example.com/team/anna/",
  "jobTitle": "Security Engineer",
  "worksFor": {"@id": "https://example.com/#organization"},
  "sameAs": ["https://www.linkedin.com/in/example"]
}
```

Only include credentials/affiliations that are real and useful to identify the person.

## Article / BlogPosting

```json
{
  "@context": "https://schema.org",
  "@type": "BlogPosting",
  "headline": "Exact visible article headline",
  "datePublished": "2026-08-01T09:00:00+02:00",
  "dateModified": "2026-08-20T12:00:00+02:00",
  "author": {"@id": "https://example.com/team/anna/#person"},
  "publisher": {"@id": "https://example.com/#organization"},
  "mainEntityOfPage": {"@type": "WebPage", "@id": "https://example.com/article/"}
}
```

Use `dateModified` only for a real substantive update.

## Product and Offer

```json
{
  "@context": "https://schema.org",
  "@type": "Product",
  "name": "Example Product",
  "url": "https://example.com/product/",
  "description": "Accurate product description.",
  "brand": {"@type": "Brand", "name": "Example Brand"},
  "offers": {
    "@type": "Offer",
    "priceCurrency": "PLN",
    "price": "199.00",
    "availability": "https://schema.org/InStock",
    "url": "https://example.com/product/"
  }
}
```

Only add `aggregateRating` or reviews when genuine qualifying reviews are visible and the current
target-platform rules are satisfied.

## BreadcrumbList

```json
{
  "@context": "https://schema.org",
  "@type": "BreadcrumbList",
  "itemListElement": [
    {"@type": "ListItem", "position": 1, "name": "Home", "item": "https://example.com/"},
    {"@type": "ListItem", "position": 2, "name": "Guides", "item": "https://example.com/guides/"},
    {"@type": "ListItem", "position": 3, "name": "Current guide"}
  ]
}
```

Keep the breadcrumb consistent with the page's real hierarchy.

## FAQPage - semantic use only unless current platform support says otherwise

As of the bundled registry's 2026-08-25 verification, Google Search no longer shows FAQ rich
results. Do not recommend FAQPage as a Google rich-result tactic.

If another consumer benefits from honest Q&A semantics, and the FAQ is visibly present:

```json
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "What is included?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "The plan includes A, B, and C."
      }
    }
  ]
}
```

The JSON-LD answer must accurately reflect the visible answer.

## HowTo - semantic use only unless current platform support says otherwise

Google HowTo rich results are deprecated. Do not pitch this as a current Google rich-result win.

```json
{
  "@context": "https://schema.org",
  "@type": "HowTo",
  "name": "How to complete the setup",
  "step": [
    {"@type": "HowToStep", "position": 1, "name": "Connect the account", "text": "Open settings and connect the account."},
    {"@type": "HowToStep", "position": 2, "name": "Verify access", "text": "Run the verification check and confirm success."}
  ]
}
```

## Coherent @graph example

```json
{
  "@context": "https://schema.org",
  "@graph": [
    {
      "@type": "Organization",
      "@id": "https://example.com/#organization",
      "name": "Example Brand",
      "url": "https://example.com/"
    },
    {
      "@type": "Person",
      "@id": "https://example.com/team/anna/#person",
      "name": "Anna Kowalska",
      "worksFor": {"@id": "https://example.com/#organization"}
    },
    {
      "@type": "BlogPosting",
      "headline": "Example article",
      "author": {"@id": "https://example.com/team/anna/#person"},
      "publisher": {"@id": "https://example.com/#organization"}
    }
  ]
}
```
