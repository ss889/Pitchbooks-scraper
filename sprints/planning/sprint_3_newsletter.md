# Sprint 3: Newsletter Generation

**Duration:** 1 week  
**Status:** Planning  
**Depends On:** Sprint 2 completion  

---

## Goal

Automated newsletter content generation with templates

## Deliverables

- [ ] Newsletter template engine
- [ ] Content curation logic
- [ ] Markdown/HTML export
- [ ] Geographic distribution analysis
- [ ] Investor activity tracking
- [ ] CLI commands: `generate-newsletter`, `preview`

## Success Metrics

- Reproducible newsletter output
- Template customization working
- Export to HTML/Markdown/PDF

## Newsletter Content Structure

### Weekly AI Investment Digest

```
1. EXECUTIVE SUMMARY
   - Total deals this week: N
   - Total funding: $X.XB
   - Notable trend: [auto-generated]

2. TOP DEALS
   - Deal 1: Company raised $X (Round Type)
   - Deal 2: ...
   - Deal 3: ...

3. BY CATEGORY
   - Generative AI: N deals, $X funding
   - Enterprise AI: N deals, $X funding
   - Healthcare AI: N deals, $X funding
   ...

4. GEOGRAPHIC DISTRIBUTION
   - US: X%
   - Europe: X%
   - Asia: X%

5. INVESTOR SPOTLIGHT
   - Most active: Investor Name (N deals)
   - Largest check: Investor Name ($X)

6. NOTABLE NEWS
   - Article summaries without deals
```

## Template System

```python
# Jinja2-based templates
templates/
├── newsletter/
│   ├── base.html
│   ├── weekly_digest.html
│   ├── weekly_digest.md
│   └── components/
│       ├── deal_card.html
│       ├── category_chart.html
│       └── investor_table.html
```

## CLI Commands

```bash
# Generate weekly newsletter
pitchbook generate --format html --days 7

# Preview without saving
pitchbook generate --preview --days 7

# Generate for specific date range
pitchbook generate --from 2026-02-01 --to 2026-02-07

# Filter by category
pitchbook generate --category generative_ai
```

---

## Tasks Breakdown

*To be detailed when sprint becomes active*
