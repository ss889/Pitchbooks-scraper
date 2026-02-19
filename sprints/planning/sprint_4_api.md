# Sprint 4: API Hardening & Dashboard

**Duration:** 1 week  
**Status:** Planning  
**Depends On:** Sprint 3 completion  

---

## Goal

Production-ready API and improved interactive dashboard

## Deliverables

- [ ] API key authentication
- [ ] Rate limiting middleware
- [ ] Request validation improvements
- [ ] Interactive dashboard (not static HTML)
- [ ] Real-time data refresh
- [ ] API integration tests

## Success Metrics

- API passes security checklist
- Dashboard loads in <2s
- 100% API endpoint coverage in tests

## Security Features

### API Key Authentication

```python
# Header-based authentication
Authorization: Bearer <api-key>

# Or query parameter (deprecated but supported)
?api_key=<api-key>
```

### Rate Limiting

```yaml
api:
  rate_limiting:
    enabled: true
    requests_per_minute: 60
    burst_limit: 10
    by: "api_key"  # or "ip"
```

### Security Checklist

- [ ] API key validation on all endpoints
- [ ] Rate limiting configured
- [ ] CORS origins restricted
- [ ] Input sanitization on search endpoints
- [ ] SQL injection prevention verified
- [ ] Error messages don't leak internals
- [ ] HTTPS enforced in production

## Dashboard Improvements

### Current: Static HTML
- Generated once, manual refresh
- No interactivity

### Target: Interactive SPA
- Real-time data from API
- Filter/search in browser
- Infinite scroll for articles
- Chart visualizations (Chart.js)

### Technology Options

| Option | Pros | Cons |
|--------|------|------|
| HTMX + Jinja | Simple, no build | Limited interactivity |
| Alpine.js | Lightweight | Learning curve |
| Vue 3 CDN | Full-featured, no build | Larger bundle |

**Recommended:** HTMX + Alpine.js combo

---

## Tasks Breakdown

*To be detailed when sprint becomes active*
