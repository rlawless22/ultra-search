# Carrier Vetting Guide

Complete workflow for vetting moving companies and freight carriers using Ultra Search.

## Overview

Ultra Search now has three specialized domains for carrier due diligence:

1. **Regulatory Compliance** - FMCSA authority, safety ratings, business verification
2. **Reviews & Reputation** - Google, Yelp, multi-platform review aggregation
3. **Risk Screening** - Sanctions, watchlists, adverse media monitoring

---

## Complete Carrier Vetting Workflow

### Step 1: Verify Carrier Authority (FMCSA)

**Critical first step** - Verify the carrier has proper DOT authority and check safety record:

```python
# Lookup by DOT number (most reliable)
check_fmcsa_authority(
    dot_number="12345678",
    output_file="vetting/ABC_Moving/fmcsa_authority.json"
)

# Or by MC number
check_fmcsa_authority(
    mc_number="MC-123456",
    output_file="vetting/ABC_Moving/fmcsa_authority.json"
)

# Or by legal name (may return multiple matches)
check_fmcsa_authority(
    legal_name="ABC Moving Company",
    output_file="vetting/ABC_Moving/fmcsa_authority.json"
)
```

**What you get:**
- Operating status (active, out-of-service)
- Safety rating (Satisfactory, Conditional, Unsatisfactory, None)
- Safety percentages (crashes, unsafe driving, hours violations)
- Insurance status
- Cargo classifications
- Authority dates

**Red flags:**
- ❌ Out-of-service status
- ❌ No insurance on file
- ❌ High crash indicator
- ❌ Unsatisfactory safety rating
- ❌ Recent violations

---

### Step 2: Business Verification (KYB)

Verify the business entity is legitimate and check for risk signals:

```python
verify_business_kyb(
    business_name="ABC Moving Company LLC",
    address="123 Main St, City, ST 12345",
    dot_number="12345678",  # Links to FMCSA data
    output_file="vetting/ABC_Moving/kyb_verification.json"
)
```

**What you get:**
- Entity type and formation date
- Tax ID verification status
- Liens and judgments
- Bankruptcy filings
- Litigation history
- Watchlist screening
- FMCSA cross-verification
- Risk score (0-100)

**Red flags:**
- ❌ Active liens or judgments
- ❌ Recent bankruptcy
- ❌ Multiple lawsuits
- ❌ Watchlist hits
- ❌ Tax ID not verified

---

### Step 3: Review Analysis (Multi-Platform)

Aggregate reviews from Google and Yelp, detect fraud patterns:

```python
# Option A: Aggregate from all platforms
aggregate_reviews(
    business_name="ABC Moving Company",
    address="123 Main St, City, ST",
    phone="555-1234",
    platforms=["google", "yelp"],
    output_file="vetting/ABC_Moving/reviews_aggregate.json"
)

# Option B: Individual platforms for detailed analysis
search_google_reviews(
    business_name="ABC Moving Company",
    address="123 Main St, City, ST",
    max_reviews=50,
    output_file="vetting/ABC_Moving/google_reviews.json"
)

search_yelp_reviews(
    business_name="ABC Moving Company",
    location="City, ST",
    phone="555-1234",
    output_file="vetting/ABC_Moving/yelp_reviews.json"
)
```

**What you get:**
- Average rating across platforms
- Review text and timestamps
- Rating distribution
- Fraud pattern detection:
  - Time clustering (fake review campaigns)
  - Polarized ratings (lots of 5-star and 1-star)
  - Suspicious phrasing patterns

**Red flags to look for in review text:**
- ❌ "Held belongings hostage"
- ❌ "Price tripled on delivery"
- ❌ "Damaged/lost items"
- ❌ "Never showed up"
- ❌ "Demanded cash payment"
- ❌ "Threatened to auction belongings"

---

### Step 4: Risk Screening

Screen for sanctions and search for adverse media:

```python
# Comprehensive risk monitoring (runs both in parallel)
monitor_entity_risk(
    entity_name="ABC Moving Company",
    address="123 Main St, City, ST",
    entity_type="organization",
    check_sanctions=True,
    check_adverse_media=True,
    output_file="vetting/ABC_Moving/risk_screening.json"
)

# Or run individually:

# Sanctions screening
screen_sanctions(
    entity_name="ABC Moving Company",
    entity_type="organization",
    output_file="vetting/ABC_Moving/sanctions.json"
)

# Adverse media search
search_adverse_media(
    entity_name="ABC Moving Company",
    keywords=["fraud", "scam", "hostage", "lawsuit", "investigation", "complaint"],
    date_range="past_year",
    max_articles=100,
    output_file="vetting/ABC_Moving/adverse_media.json"
)
```

**What you get:**
- Sanctions/watchlist matches with confidence scores
- News articles mentioning fraud, scams, lawsuits
- Classification counts (fraud mentions, lawsuit mentions, etc.)
- Overall risk score
- Actionable recommendations

**Red flags:**
- ❌ Any watchlist matches (even low confidence - investigate!)
- ❌ Multiple fraud allegations in news
- ❌ Active investigations (DOJ, FTC, state AG)
- ❌ "Hostage load" or "moving scam" mentions
- ❌ BBB alerts or complaints

---

## Complete Parallel Workflow

Run ALL checks simultaneously for maximum efficiency:

```python
# All in one message to Claude Code - runs in parallel!

check_fmcsa_authority(
    dot_number="12345678",
    output_file="vetting/ABC_Moving/01_fmcsa.json"
)

verify_business_kyb(
    business_name="ABC Moving Company LLC",
    address="123 Main St, City, ST",
    dot_number="12345678",
    output_file="vetting/ABC_Moving/02_kyb.json"
)

aggregate_reviews(
    business_name="ABC Moving Company",
    address="123 Main St, City, ST",
    platforms=["google", "yelp"],
    output_file="vetting/ABC_Moving/03_reviews.md"
)

monitor_entity_risk(
    entity_name="ABC Moving Company",
    entity_type="organization",
    output_file="vetting/ABC_Moving/04_risk.json"
)
```

**All 4 checks run simultaneously! Results in seconds (for sync) or minutes (for async).**

---

## Interpreting Results

### Risk Scoring Matrix

| Category | Data Point | Weight | Red Flag Threshold |
|----------|-----------|--------|-------------------|
| **Authority** | Out-of-service | Critical | Any OOS status |
| **Authority** | Safety rating | High | Unsatisfactory |
| **Authority** | Crash indicator | High | >10% national average |
| **Authority** | No insurance | Critical | TRUE |
| **KYB** | Liens | Medium | Any active liens |
| **KYB** | Bankruptcy | High | Within 3 years |
| **KYB** | Litigation | Medium | >3 active cases |
| **KYB** | Watchlist hits | Critical | Any hits |
| **Reviews** | Avg rating | Medium | <3.0 stars |
| **Reviews** | Fraud patterns | High | Any detected |
| **Reviews** | Hostage mentions | Critical | >0 mentions |
| **Sanctions** | Match score | Critical | >0.7 confidence |
| **Adverse Media** | Fraud mentions | High | >3 articles |
| **Adverse Media** | Investigations | Critical | Any active |

### Decision Matrix

**GREEN LIGHT (Low Risk):**
- ✅ Active FMCSA authority with insurance
- ✅ Satisfactory or no safety rating
- ✅ No liens, bankruptcies, or watchlist hits
- ✅ Reviews >4.0 stars, no fraud patterns
- ✅ No sanctions matches
- ✅ No recent adverse media

**YELLOW LIGHT (Medium Risk - Investigate Further):**
- ⚠️ Conditional safety rating
- ⚠️ Some negative reviews but >3.5 stars
- ⚠️ Old liens or minor litigation
- ⚠️ 1-2 adverse media mentions (minor complaints)

**RED LIGHT (High Risk - Do Not Proceed):**
- ❌ Out-of-service or no authority
- ❌ No insurance
- ❌ Unsatisfactory safety rating
- ❌ Active liens or recent bankruptcy
- ❌ Watchlist matches
- ❌ Multiple "hostage load" mentions
- ❌ Active fraud investigations
- ❌ Polarized reviews with fraud patterns

---

## Output File Organization

Recommended structure for organized vetting:

```
vetting/
├── {Carrier_Name}/
│   ├── 01_fmcsa_authority.json       # DOT authority and safety
│   ├── 02_kyb_verification.json      # Business legitimacy
│   ├── 03_reviews_aggregate.md       # Multi-platform reviews
│   ├── 04_risk_screening.json        # Sanctions + adverse media
│   ├── google_reviews.json           # Detailed Google reviews
│   ├── yelp_reviews.json             # Detailed Yelp reviews
│   └── summary_report.md             # Final assessment
```

---

## Advanced: Batch Vetting Multiple Carriers

Use async research for comprehensive batch vetting:

```python
# Vet 10 carriers in parallel
carriers = [
    {"name": "ABC Moving", "dot": "12345678"},
    {"name": "XYZ Transport", "dot": "87654321"},
    # ... 8 more
]

for carrier in carriers:
    # Start comprehensive background check (runs in background)
    start_deep_research_async(
        query=f"Complete due diligence on {carrier['name']} DOT {carrier['dot']} including FMCSA safety record, reviews, sanctions screening, and adverse media",
        depth="comprehensive",
        output_file=f"vetting/{carrier['name']}/comprehensive_report.md"
    )

# All 10 research tasks run in parallel in background!
# Check back in 30 minutes for completed reports
```

---

## API Key Setup Priority

For immediate testing (no cost):
1. **OpenSanctions** - Free tier with business email (https://www.opensanctions.org/api/)
2. **FMCSA** - Free, register at https://ai.fmcsa.dot.gov/SMS/Tools/Downloads.aspx

For production use (paid but essential):
3. **Google Places** - Google Cloud Platform (pay-per-use)
4. **Yelp Fusion** - Free tier available (500 calls/day)
5. **NewsAPI** - Free tier (100 calls/day) or paid
6. **Middesk** - Paid, but comprehensive KYB

---

## Moving Scam Detection Keywords

When analyzing reviews and adverse media, watch for these patterns:

### Hostage Scams:
- "held hostage"
- "demanded more money"
- "wouldn't release belongings"
- "threatened to auction"
- "cash only"
- "price tripled"

### Damage/Loss:
- "damaged furniture"
- "lost items"
- "broken"
- "missing belongings"

### No-Show/Abandonment:
- "never showed up"
- "left items in storage"
- "disappeared"
- "won't respond"

### Fraud Indicators:
- "bait and switch"
- "different truck showed up"
- "unlicensed movers"
- "not the company I hired"

---

## Real-World Example

**Vetting "Swift Movers LLC":**

```python
# Step 1: FMCSA check
result1 = check_fmcsa_authority(dot_number="98765432")
# Result: Active, Satisfactory safety rating ✅

# Step 2: KYB verification
result2 = verify_business_kyb(
    business_name="Swift Movers LLC",
    address="456 Oak Ave, Houston, TX 77001",
    dot_number="98765432"
)
# Result: Verified entity, no liens, 1 old lawsuit (settled) ⚠️

# Step 3: Reviews
result3 = aggregate_reviews(
    business_name="Swift Movers",
    address="456 Oak Ave, Houston, TX",
    platforms=["google", "yelp"]
)
# Result: 4.2 stars Google, 3.8 stars Yelp, 2 fraud pattern flags ⚠️

# Step 4: Risk screening
result4 = monitor_entity_risk(
    entity_name="Swift Movers LLC",
    check_sanctions=True,
    check_adverse_media=True
)
# Result: No sanctions, 3 adverse media mentions (minor complaints) ⚠️

# Overall: YELLOW LIGHT - Proceed with caution, verify fraud patterns
```

---

## Best Practices

### 1. Always Start with FMCSA
No DOT number or out-of-service = immediate rejection

### 2. Cross-Reference Everything
- DOT number from FMCSA should match KYB records
- Business name should match across all platforms
- Address consistency is key

### 3. Look for Patterns, Not Single Reviews
One bad review = normal. Pattern of "hostage" mentions = red flag.

### 4. Time Matters
Recent adverse media (past 3 months) > old news (2+ years ago)

### 5. Save Everything
File output creates audit trail for compliance and decision justification

### 6. Use Async for Batch Processing
Vetting 50 carriers? Use async tools to run in parallel overnight.

---

## Tools Quick Reference

| Tool | Purpose | Output |
|------|---------|--------|
| `check_fmcsa_authority` | DOT/MC lookup, safety data | Authority status, safety ratings |
| `verify_business_kyb` | Entity verification, risk signals | Liens, bankruptcies, watchlist |
| `search_google_reviews` | Google reviews analysis | Ratings, review text, patterns |
| `search_yelp_reviews` | Yelp reviews analysis | Ratings, review text |
| `aggregate_reviews` | Multi-platform reviews | Combined ratings, fraud detection |
| `screen_sanctions` | Watchlist screening | Sanctions matches |
| `search_adverse_media` | Negative news search | Articles about fraud/lawsuits |
| `monitor_entity_risk` | Combined screening | Overall risk assessment |

---

## API Keys Needed

| Provider | Free Tier? | Where to Get | Priority |
|----------|-----------|--------------|----------|
| **FMCSA** | ✅ Yes | https://ai.fmcsa.dot.gov/SMS/Tools/Downloads.aspx | **HIGH** |
| **OpenSanctions** | ✅ Yes | https://www.opensanctions.org/api/ | **HIGH** |
| **Yelp Fusion** | ✅ Yes (500/day) | https://www.yelp.com/developers | **MEDIUM** |
| **NewsAPI** | ✅ Yes (100/day) | https://newsapi.org/ | **MEDIUM** |
| **Google Places** | 💰 Pay-per-use | https://console.cloud.google.com/ | **HIGH** |
| **Middesk** | 💰 Paid | https://www.middesk.com/ | **LOW** |

**Start with**: FMCSA + OpenSanctions (both have free tiers!)

---

## Compliance & Legal Notes

### Background Checks
You mentioned having legal standing for background checks. Ensure:
- Proper consent/disclosure if required by FCRA
- Minimal data retention
- Secure storage of results
- Clear business purpose

### Review Scraping
- Use official APIs only (Google Places, Yelp Fusion)
- Don't scrape review sites directly (violates ToS)
- Reviews are signals, not definitive truth

### Data Usage
- Purpose: Business due diligence for partnerships
- Retention: Only as long as needed for decision
- Access: Limited to authorized personnel
- Audit trail: File outputs provide this

---

## Next Steps

1. **Get API keys** (start with free ones: FMCSA, OpenSanctions)
2. **Test with known carrier** (use your company's DOT number to verify data)
3. **Create vetting template** (standardize checks for all carriers)
4. **Build workflow** (automate batch vetting with async tools)
5. **Monitor continuously** (set up periodic adverse media checks)

---

## Example: Full Carrier Report

```markdown
# Carrier Vetting Report: ABC Moving Company

**Generated:** 2026-02-04

## Summary
- **DOT Number:** 12345678
- **Overall Risk Level:** MEDIUM ⚠️
- **Recommendation:** Proceed with enhanced monitoring

## FMCSA Authority ✅
- Operating Status: ACTIVE
- Safety Rating: Satisfactory
- Insurance: ON FILE
- Last Update: 2026-01-15

## Business Verification ✅
- Entity: Verified LLC
- Liens: None
- Bankruptcies: None
- Watchlists: Clear

## Reviews ⚠️
- Google: 3.8 stars (127 reviews)
- Yelp: 3.5 stars (43 reviews)
- Patterns: Minor time clustering detected
- Red Flags: 2 mentions of "price increase" (within normal range)

## Risk Screening ⚠️
- Sanctions: Clear
- Adverse Media: 2 articles (minor complaints, resolved)
- Investigations: None
- Fraud Mentions: 0

## Recommendation
YELLOW LIGHT - Approve with conditions:
- Require detailed quote with price lock
- Request customer references
- Monitor reviews monthly
```

---

This guide provides everything you need to vet moving companies comprehensively and programmatically!
