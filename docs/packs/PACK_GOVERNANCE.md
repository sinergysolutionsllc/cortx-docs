# Pack Governance & Approval Process

**Version:** 1.0.0
**Last Updated:** 2025-10-01
**Owner:** Compliance & Platform Governance Team
**Classification:** Internal

---

## Purpose

This document establishes the governance framework for RulePacks and WorkflowPacks in the CORTX Platform, including approval workflows, versioning policies, certification tiers, and quality standards.

---

## Governance Principles

### 1. Quality Over Speed
- Thoroughly tested packs prevent downstream issues
- Quality gates cannot be bypassed
- Technical debt is addressed proactively

### 2. Compliance First
- All packs must align with regulatory requirements
- Compliance officer review is mandatory for regulated industries
- Audit trails for all changes

### 3. Transparency
- All pack changes are publicly visible in Git
- Review feedback is documented
- Rejection reasons are clear and actionable

### 4. Community Collaboration
- Pack authors can be internal or external
- Community feedback drives improvements
- Knowledge sharing through documentation

---

## Pack Lifecycle

```
┌──────────┐
│  Draft   │  Author creates pack
└────┬─────┘
     │
     ▼
┌──────────┐
│  Review  │  Business analyst reviews
└────┬─────┘
     │
     ▼
┌──────────┐
│Compliance│  Compliance officer certifies
└────┬─────┘
     │
     ▼
┌──────────┐
│  Testing │  QA validates with test data
└────┬─────┘
     │
     ▼
┌──────────┐
│ Approval │  Admin approves for deployment
└────┬─────┘
     │
     ▼
┌──────────┐
│Deployment│  Pushed to production registry
└────┬─────┘
     │
     ▼
┌──────────┐
│ Active   │  Available for use
└──────────┘
```

---

## Approval Workflow

### Stage 1: Draft
**Owner:** Pack Author

**Activities:**
- Create pack (RulePack JSON or WorkflowPack YAML)
- Write documentation (README, USAGE, CHANGELOG)
- Create test cases
- Validate against schema

**Quality Gates:**
- [ ] Schema validation passes
- [ ] Basic test cases exist
- [ ] Documentation complete

**Transition:** Submit for review via Pull Request

---

### Stage 2: Business Review
**Owner:** Business Analyst / Functional Lead

**Activities:**
- Review functional correctness
- Validate business rules align with requirements
- Check error messages are clear and actionable
- Verify test coverage is adequate

**Quality Gates:**
- [ ] Business requirements met
- [ ] Rules/steps logically correct
- [ ] Error messages user-friendly
- [ ] Edge cases handled

**Duration:** 2-3 business days

**Outcomes:**
- **Approved:** Move to compliance review
- **Needs Changes:** Return to author with feedback
- **Rejected:** Close PR with explanation

---

### Stage 3: Compliance Review
**Owner:** Compliance Officer

**Activities:**
- Verify regulatory alignment
- Check compliance tags are accurate
- Validate control mappings (NIST, HIPAA, etc.)
- Ensure audit trail requirements met

**Quality Gates:**
- [ ] Compliance frameworks correctly tagged
- [ ] Control references accurate
- [ ] Regulatory requirements satisfied
- [ ] Audit logging adequate

**Duration:** 3-5 business days

**Outcomes:**
- **Certified:** Move to testing
- **Conditional Approval:** Minor changes required
- **Rejected:** Non-compliant, return to author

---

### Stage 4: Testing
**Owner:** QA Lead

**Activities:**
- Execute test cases
- Performance testing (RulePacks: 1M records <30s)
- Security scanning (no code injection, secrets)
- Integration testing with platform

**Quality Gates:**
- [ ] All test cases pass
- [ ] Performance benchmarks met
- [ ] No security vulnerabilities
- [ ] Integration tests successful

**Duration:** 3-5 business days

**Outcomes:**
- **Passed:** Move to final approval
- **Failed:** Return to author with test results

---

### Stage 5: Final Approval
**Owner:** Platform Admin

**Activities:**
- Review all prior approvals
- Verify pack metadata
- Check versioning is correct
- Approve deployment

**Quality Gates:**
- [ ] All prior stages approved
- [ ] Version number correct
- [ ] Deployment plan documented
- [ ] Rollback plan exists

**Duration:** 1-2 business days

**Outcomes:**
- **Approved:** Deploy to production
- **Rejected:** Rare; address final concerns

---

### Stage 6: Deployment
**Owner:** DevOps / Platform Team

**Activities:**
- Tag release in Git
- Deploy to production registry
- Update documentation
- Notify stakeholders

**Quality Gates:**
- [ ] Git tag created
- [ ] Production registry updated
- [ ] Documentation published
- [ ] Announcement sent

---

### Stage 7: Active
**Owner:** Pack Maintainers

**Ongoing Activities:**
- Monitor pack usage
- Address bug reports
- Plan future enhancements
- Deprecate when obsolete

---

## Versioning Policy

### Semantic Versioning

**Format:** `MAJOR.MINOR.PATCH`

**MAJOR Version (X.0.0):**
- Breaking changes to pack structure
- Rule operator changes
- Workflow step type changes
- Requires re-certification

**MINOR Version (x.Y.0):**
- Backward-compatible additions
- New rules or workflow steps
- Optional field additions
- Standard review process

**PATCH Version (x.y.Z):**
- Bug fixes
- Error message improvements
- Documentation updates
- Fast-track approval

**Examples:**
```
1.0.0 → 1.0.1: Fixed typo in error message (PATCH)
1.0.1 → 1.1.0: Added 5 new rules (MINOR)
1.1.0 → 2.0.0: Changed rule operator from '==' to 'matches' (MAJOR)
```

### Version Compatibility

**Backward Compatibility:**
- MINOR and PATCH versions must be backward compatible
- Existing integrations must not break
- Default behavior unchanged

**Breaking Changes:**
- Require MAJOR version bump
- Documented in CHANGELOG
- Migration guide provided
- Deprecation notice (if replacing older pack)

### Deprecation Policy

**Deprecation Timeline:**
1. **Announce:** Deprecation notice 90 days before removal
2. **Mark:** Tag pack as deprecated in metadata
3. **Migrate:** Provide migration guide to newer version
4. **Remove:** After 90 days, remove from active registry

**Example:**
```json
{
  "metadata": {
    "pack_id": "legacy-gtas-v1",
    "version": "1.0.0",
    "deprecated": true,
    "deprecated_at": "2025-10-01",
    "replacement": "federal-gtas-v2",
    "deprecation_reason": "Replaced by v2 with enhanced validation"
  }
}
```

---

## Certification Tiers

### Tier 1: Official Packs
**Definition:** Created and maintained by regulatory authorities or Sinergy Solutions

**Criteria:**
- Source: Treasury, IRS, CMS, Sinergy platform team
- Funding: Government contracts or platform core
- Pricing: Free (publicly funded)
- Support: Official support SLA

**Examples:**
- `federal-gtas-v1`: Treasury-verified GTAS rules
- `hipaa-security-v1`: Official HIPAA compliance pack
- `nist-800-53-ac`: NIST access control mapping

**Badge:** ✅ Official

---

### Tier 2: Certified Packs
**Definition:** Community-created packs that passed rigorous certification

**Criteria:**
- Source: Third-party developers, consultancies
- Testing: Comprehensive test suite (>90% coverage)
- Review: Passed all governance stages
- Support: Author provides support
- Pricing: Author-defined (70/30 revenue split)

**Certification Requirements:**
- [ ] All test cases pass
- [ ] Documentation complete (README, USAGE, CHANGELOG)
- [ ] Compliance review passed
- [ ] Security scan clean
- [ ] Performance benchmarks met
- [ ] Author support commitment (email, SLA)

**Examples:**
- `healthcare-claims-verification-v1`: Third-party healthcare pack
- `realestate-title-search-v1`: Certified title verification

**Badge:** 🏆 Certified

---

### Tier 3: Community Packs
**Definition:** User-contributed packs, not certified

**Criteria:**
- Source: Any community member
- Testing: Basic schema validation
- Review: Automated checks only
- Support: Best-effort by author
- Pricing: Author-defined (70/30 split)

**Requirements:**
- [ ] Schema validation passes
- [ ] Basic test cases exist
- [ ] No critical security issues
- [ ] Documentation present

**Examples:**
- `custom-agency-workflow-v1`: Agency-specific workflow
- `experimental-ml-validation-v1`: Experimental features

**Badge:** 🧪 Community

---

### Tier 4: Private Packs
**Definition:** Enterprise or agency-specific packs (not in public marketplace)

**Criteria:**
- Source: Enterprise customer or agency
- Visibility: Private to tenant/agency
- Pricing: Enterprise license
- Support: Dedicated account team

**Use Cases:**
- Proprietary business logic
- Sensitive compliance rules
- Custom integrations
- Trade secrets

**Badge:** 🔒 Private

---

## Quality Standards

### RulePack Quality Standards

**Schema Compliance:**
- [ ] Valid JSON format
- [ ] Matches RulePack JSON Schema
- [ ] All required fields present

**Rule Quality:**
- [ ] Unique rule IDs
- [ ] Clear, actionable error messages
- [ ] Appropriate severity levels (FATAL/WARNING/INFO)
- [ ] Compliance references included
- [ ] Safe operators only (no code injection)

**Testing:**
- [ ] Minimum 10 test cases per pack
- [ ] Edge cases covered (null, empty, special chars)
- [ ] Performance tested (1M records <30s)
- [ ] All test cases pass

**Documentation:**
- [ ] README with overview and use cases
- [ ] USAGE guide with examples
- [ ] CHANGELOG with version history

---

### WorkflowPack Quality Standards

**Schema Compliance:**
- [ ] Valid YAML format
- [ ] Matches WorkflowPack schema
- [ ] All required fields present

**Workflow Quality:**
- [ ] Unique step IDs
- [ ] Logical step ordering
- [ ] Error handling defined
- [ ] Compensation logic (for sagas)
- [ ] Environment variables for secrets

**Testing:**
- [ ] Simulation tests pass
- [ ] Integration tests pass (dev environment)
- [ ] Error scenarios tested
- [ ] Performance benchmarks met

**Documentation:**
- [ ] README with workflow description
- [ ] Step-by-step USAGE guide
- [ ] Architecture diagram (for complex workflows)
- [ ] CHANGELOG with version history

---

## Review Guidelines

### For Business Analysts

**Focus Areas:**
- Functional correctness
- Business rule accuracy
- User experience (error messages)
- Test coverage completeness

**Checklist:**
- [ ] Business requirements documented
- [ ] Rules/steps match specifications
- [ ] Error messages are clear
- [ ] Edge cases identified and handled
- [ ] Test cases validate requirements

**Approval Criteria:**
- All checklist items satisfied
- No critical functional issues
- Author responsive to feedback

---

### For Compliance Officers

**Focus Areas:**
- Regulatory alignment
- Compliance tagging accuracy
- Control mapping correctness
- Audit trail adequacy

**Checklist:**
- [ ] Compliance frameworks correctly identified
- [ ] Control references accurate (NIST, HIPAA, etc.)
- [ ] Regulatory requirements satisfied
- [ ] Audit logging implemented
- [ ] Data privacy considerations addressed

**Approval Criteria:**
- Compliance requirements met
- No regulatory risks
- Adequate documentation

---

### For QA Leads

**Focus Areas:**
- Test coverage
- Performance
- Security
- Integration

**Checklist:**
- [ ] All test cases pass
- [ ] Code coverage >80%
- [ ] Performance benchmarks met
- [ ] No security vulnerabilities
- [ ] Integration tests successful

**Approval Criteria:**
- All tests pass
- No critical issues
- Performance acceptable

---

## Marketplace Governance

### Submission Process

**1. Prepare Pack:**
- Complete all documentation
- Add examples and test cases
- Ensure quality standards met

**2. Submit for Review:**
```bash
cortx marketplace submit <pack-id> \
  --tier certified \
  --category compliance \
  --pricing free
```

**3. Automated Checks:**
- Schema validation
- Security scanning
- Test execution
- Documentation completeness

**4. Human Review:**
- Compliance certification (if applicable)
- Quality review
- Pricing review

**5. Approval/Rejection:**
- Approved: Published to marketplace
- Rejected: Feedback provided, resubmit allowed

---

### Revenue Model

**Certified Packs (Paid):**
- **Author:** 70% of revenue
- **Platform:** 30% of revenue

**Free Packs:**
- No revenue (official or free certified packs)

**Private Packs:**
- Enterprise licensing (custom pricing)

**Payment Schedule:**
- Monthly payouts for authors
- Minimum payout threshold: $100
- Payment via Stripe, PayPal, or ACH

---

## Monitoring & Metrics

### Pack Health Metrics

**Usage:**
- Downloads per month
- Active installations
- Execution count
- Error rate

**Quality:**
- User ratings (1-5 stars)
- Bug reports
- Support tickets
- Test pass rate

**Performance:**
- Average execution time
- p95/p99 latency
- Resource consumption

### Dashboards

**Pack Author Dashboard:**
- Usage analytics
- Revenue tracking (if paid)
- User feedback
- Issue tracker

**Platform Dashboard:**
- Total packs by tier
- Certification pipeline status
- Quality metrics across all packs
- Security vulnerability trends

---

## Incident Response

### Security Vulnerability

**Process:**
1. **Report:** User or security scan detects vulnerability
2. **Triage:** Security team assesses severity
3. **Notify:** Author notified within 24 hours
4. **Fix:** Author provides patch within SLA
5. **Redeploy:** Patched version deployed
6. **Communicate:** Users notified of update

**SLA:**
- **Critical:** 24-hour patch
- **High:** 3-day patch
- **Medium:** 7-day patch
- **Low:** 30-day patch

---

### Pack Failure

**Process:**
1. **Detect:** Monitoring alerts on high error rate
2. **Investigate:** Root cause analysis
3. **Mitigate:** Rollback or hotfix
4. **Communicate:** Users notified
5. **Postmortem:** Document lessons learned

---

## Appeals Process

**If Pack Rejected:**
1. Review rejection reason
2. Address feedback
3. Resubmit with changes documented
4. Escalate to governance committee (if disagreement)

**Governance Committee:**
- Platform architect
- Compliance officer
- QA lead
- Product manager

---

## Contact

**Pack Governance Team:**
- Email: pack-governance@sinergysolutions.ai
- Slack: #pack-governance
- Office Hours: Fridays 1-2 PM ET

---

**Document Control**
- **Version:** 1.0.0
- **Last Updated:** 2025-10-01
- **Review Cycle:** Quarterly
- **Next Review:** 2026-01-01
- **Approvers:** Compliance & Platform Governance Team
