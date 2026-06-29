# Crawling, Extraction, and Media Processing

## Crawl Governance Principle

No URL should be crawled without a policy decision.

## Crawl Policy Checks

```text
robots_txt_check()
domain_rate_limit_check()
private_ip_check()
content_type_check()
file_size_check()
mime_validation_check()
source_terms_check()
malware_risk_check()
download_safety_check()
user_agent_policy_check()
```

## Crawl Decision Contract

```json
{
  "url": "https://example.com/page",
  "robots_allowed": true,
  "rate_limit_ok": true,
  "private_ip_blocked": false,
  "content_type_allowed": true,
  "risk_score": 0.09,
  "decision": "allowed",
  "crawler_type": "scrapy"
}
```

## Crawler Selection

| Scenario | Crawler |
|---|---|
| Normal HTML | Scrapy |
| JavaScript-heavy page | Playwright fallback |
| Large domain crawl | Nutch, later iteration only |
| Archival WARC crawl | Heritrix, later iteration only |
| Historical copy | Common Crawl / Internet Archive |
| Media extraction | Media Worker |

## Default Strategy

```text
Try Common Crawl first when freshness is low
→ Try Scrapy for static pages
→ If extraction quality is low, detect JS requirement
→ Use Playwright only if high-value and budget allows
→ Extract and validate content
→ Index only trusted extraction
```

## Playwright Policy

Use Playwright only when:

- Static extraction failed.
- Important content appears hidden behind JavaScript.
- Page has high quality score.
- Job priority is high.
- Browser budget is available.

Do not use Playwright for:

- Low-quality pages.
- Duplicate pages.
- Blocked domains.
- Large low-priority batches.
- Known static websites.

## Extracted Fields

```text
title
main_text
canonical_url
description
author
publish_date
language
content_type
structured_data
headings
links
media_urls
entities
content_hash
readability_score
extraction_quality_score
```

## Extraction Corner Cases

| Case | Handling |
|---|---|
| Empty body | Mark extraction failed. |
| Boilerplate-heavy page | Use main-content extraction. |
| Infinite scroll | Playwright only if high priority. |
| Wrong language | Flag language mismatch. |
| PDF document | Route to PDF extractor. |
| Image-only page | OCR only if allowed. |
| Video page | Extract metadata only. |
| Thin content | Low extraction quality. |
| Multiple publish dates | Choose best source with confidence. |

## Media Processing

Supported media:

- Images.
- PDFs.
- Thumbnails.
- Video metadata.
- Audio metadata.
- Documents.
- Screenshots.

Media functions:

```text
validate_media_url()
check_file_size()
download_media()
validate_mime_type()
calculate_content_hash()
calculate_perceptual_hash()
extract_image_metadata()
extract_pdf_text()
generate_thumbnail()
store_media_object()
link_media_to_document()
```

## Crawl Kill Gates

Stop crawling when:

- robots.txt disallows path.
- Domain returns repeated 429.
- Redirect loop detected.
- CAPTCHA detected.
- Login required.
- Private IP redirect detected.
- Storage budget exceeded.
- Browser CPU budget exceeded.
