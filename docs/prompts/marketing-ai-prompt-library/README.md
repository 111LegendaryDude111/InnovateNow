# Internal AI Prompt Library: marketing content

## Read Me

### Purpose

This library gives the marketing team reusable prompts for repeatable content work. Use it for first drafts, variants and structured creative exploration across core marketing channels.

### Recommended target tool

Use these prompts with a GPT-compatible chat model, including ChatGPT or an OpenRouter-hosted instruction-following model. Keep temperature moderate for creative variants and low for regulated or high-risk product claims.

### How to use

1. Choose the content area that matches the task.
2. Open the prompt file for that content area.
3. Copy the full prompt entry, including context and output requirements.
4. Replace every placeholder such as `[PRODUCT NAME]`, `[AUDIENCE]`, `[BRAND VOICE]` and `[TONE]`.
5. Add approved source facts before asking for product, legal, pricing or performance claims.
6. Review and edit the output before publishing.

### How to add or change prompts

- Add each new prompt as one markdown file inside the correct category directory.
- Keep the metadata fields exactly as shown below.
- Add a realistic example output for every new prompt.
- Use clear placeholders instead of hard-coded campaign details.
- Do not add claims, statistics or customer quotes unless they come from approved source material.
- Update the date and author when a prompt is materially changed.
- Update this index and coverage summary when files are added, moved or removed.

## Library structure

Each category has its own directory. Each prompt lives in its own markdown file.

```text
marketing-ai-prompt-library/
├── README.md
├── ad-copy/
├── blog-outlines/
├── email-subject-lines-and-preheaders/
├── product-descriptions/
└── social-media-posts/
```

Every prompt file uses these required fields:

- Prompt Name
- Category
- Persona/Role
- Goal
- Prompt Text
- Variables/Placeholders
- Example Output
- Best Practices/Tips
- Date Created
- Author

## Coverage summary

| Category | Directory | Required minimum | Included prompts | Status |
|---|---|---:|---:|---|
| Social media posts | `social-media-posts/` | 3 | 3 | Complete |
| Blog outlines | `blog-outlines/` | 3 | 3 | Complete |
| Email subject lines and preheaders | `email-subject-lines-and-preheaders/` | 3 | 4 | Complete |
| Product descriptions | `product-descriptions/` | 3 | 4 | Complete |
| Ad copy | `ad-copy/` | 3 | 4 | Complete |

Total prompt files in this version: 18.

## Prompt index

### Social media posts

- [Launch announcement post](social-media-posts/01-launch-announcement-post.md)
- [Educational carousel outline](social-media-posts/02-educational-carousel-outline.md)
- [Customer proof post](social-media-posts/03-customer-proof-post.md)

### Blog outlines

- [SEO blog outline](blog-outlines/01-seo-blog-outline.md)
- [Thought leadership outline](blog-outlines/02-thought-leadership-outline.md)
- [Comparison blog outline](blog-outlines/03-comparison-blog-outline.md)

### Email subject lines and preheaders

- [Newsletter subject line variants](email-subject-lines-and-preheaders/01-newsletter-subject-line-variants.md)
- [Product launch email subject lines](email-subject-lines-and-preheaders/02-product-launch-email-subject-lines.md)
- [Re-engagement subject lines](email-subject-lines-and-preheaders/03-re-engagement-subject-lines.md)
- [Event follow-up subject lines](email-subject-lines-and-preheaders/04-event-follow-up-subject-lines.md)

### Product descriptions

- [Website product description](product-descriptions/01-website-product-description.md)
- [Feature release description](product-descriptions/02-feature-release-description.md)
- [Marketplace listing description](product-descriptions/03-marketplace-listing-description.md)
- [Persona-specific product description](product-descriptions/04-persona-specific-product-description.md)

### Ad copy

- [Search ad copy](ad-copy/01-search-ad-copy.md)
- [Paid social ad copy](ad-copy/02-paid-social-ad-copy.md)
- [Retargeting ad copy](ad-copy/03-retargeting-ad-copy.md)
- [Landing page ad variant copy](ad-copy/04-landing-page-ad-variant-copy.md)
