# Codecov Setup Instructions

## Quick Setup (5 minutes)

### Step 1: Get Your Codecov Token

1. **Visit Codecov:**
   - Go to <https://codecov.io/>
   - Click "Sign up" or "Log in with GitHub"

2. **Authorize GitHub:**
   - Allow Codecov to access your GitHub repositories
   - You'll be redirected to your Codecov dashboard

3. **Find Your Repository:**
   - Click "Add new repository" or search for `sinergysolutionsllc`
   - Click on the repository name

4. **Copy the Token:**
   - You'll see "Codecov upload token" on the setup page
   - Copy the token (format: `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`)

### Step 2: Add Token to GitHub

**Option A: Using GitHub Web UI** (Recommended)

1. Go to your repository: <https://github.com/sinergysolutionsllc/sinergysolutionsllc>
2. Click "Settings" → "Secrets and variables" → "Actions"
3. Click "New repository secret"
4. Name: `CODECOV_TOKEN`
5. Value: Paste your token
6. Click "Add secret"

**Option B: Using GitHub CLI**

```bash
cd /Users/michael/Development/sinergysolutionsllc

# Replace YOUR_TOKEN with the actual token from Codecov
gh secret set CODECOV_TOKEN --body "YOUR_TOKEN"
```

### Step 3: Verify Installation

```bash
# Check if secret was added
gh secret list

# Should show:
# CODECOV_TOKEN  Updated YYYY-MM-DD
```

---

## Testing the Setup

### Trigger a Test Workflow

```bash
# Option 1: Manual trigger via GitHub CLI
gh workflow run test-all-services.yml

# Option 2: Make a commit to trigger CI
git commit --allow-empty -m "test: trigger CI/CD with Codecov"
git push origin main

# Option 3: Create a test PR
git checkout -b test-codecov
git commit --allow-empty -m "test: codecov integration"
git push origin test-codecov
gh pr create --title "Test: Codecov Integration" --body "Testing CI/CD with Codecov"
```

### Check Workflow Execution

```bash
# Watch the workflow run
gh run watch

# Or view in browser
gh run list
gh run view --web
```

### Verify Coverage Upload

1. Go to <https://codecov.io/gh/sinergysolutionsllc/sinergysolutionsllc>
2. You should see:
   - Coverage percentage for each service
   - Coverage trends graph
   - File-by-file coverage breakdown
   - Pull request comments (if testing with PR)

---

## What Happens After Setup?

### Automatic Actions

**On Every Push/PR:**

1. All 9 service tests run in parallel
2. Coverage is collected for each service
3. Coverage reports are uploaded to Codecov
4. Codecov analyzes coverage changes
5. PR gets auto-commented with coverage diff
6. Status checks appear on the PR

**Expected PR Comment Format:**

```
# Codecov Report
> Merging #123 into main will increase coverage by 0.25%
> The diff coverage is 95.00%

## Coverage by Flag
- ai-broker: 85.2% (+0.3%)
- compliance: 82.1% (+0.1%)
- gateway: 87.5% (-0.2%)
...

## Coverage Diff
File | Before | After | Diff
services/rag/app/retrieval.py | 85% | 92% | +7%
```

### Quality Gates

**Automatic Checks:**

- ✅ Project coverage must be ≥80%
- ✅ Patch coverage (new code) must be ≥80%
- ✅ Each service must meet individual thresholds
- ❌ PR blocked if coverage drops below 80%

---

## Troubleshooting

### Issue: "CODECOV_TOKEN not found"

**Solution:**

```bash
# Verify secret exists
gh secret list | grep CODECOV_TOKEN

# If not found, add it again
gh secret set CODECOV_TOKEN
# Paste your token when prompted
```

### Issue: "codecov upload failed"

**Solution:**

1. Check Codecov token is correct
2. Verify repository is activated on Codecov
3. Check workflow logs: `gh run view --log`

### Issue: "Coverage reports not appearing"

**Solution:**

1. Wait 2-3 minutes after workflow completes
2. Check Codecov dashboard for processing status
3. Verify artifacts were uploaded in GitHub Actions
4. Re-run the workflow if needed: `gh run rerun <run-id>`

### Issue: "Quality gate failing"

**Solution:**

```bash
# Check which services are below threshold
# Run tests locally to see coverage
cd services/gateway
pytest --cov=app --cov-report=term-missing

# Add more tests to services below 80%
# See test plan for guidance
```

---

## Advanced Configuration

### Customize Coverage Requirements

Edit `/Users/michael/Development/sinergysolutionsllc/codecov.yml`:

```yaml
coverage:
  status:
    project:
      default:
        target: 85%  # Change from 80% to 85%
```

### Add Coverage Badges

Add to your README.md:

```markdown
[![codecov](https://codecov.io/gh/sinergysolutionsllc/sinergysolutionsllc/branch/main/graph/badge.svg)](https://codecov.io/gh/sinergysolutionsllc/sinergysolutionsllc)
```

### Service-Specific Badges

```markdown
[![Gateway Coverage](https://codecov.io/gh/sinergysolutionsllc/sinergysolutionsllc/branch/main/graph/badge.svg?flag=gateway)](https://codecov.io/gh/sinergysolutionsllc/sinergysolutionsllc)
```

---

## Next Steps After Codecov Setup

1. ✅ **Install Pre-commit Hooks** (Action Item 3)

   ```bash
   pip install pre-commit
   pre-commit install
   pre-commit run --all-files
   ```

2. **Run Initial Test Suite**

   ```bash
   # Test each service
   for service in gateway identity ai-broker validation workflow compliance rag ledger ocr; do
     echo "Testing $service..."
     cd services/$service
     pytest --cov=app --cov-report=html
     cd ../..
   done
   ```

3. **Review Coverage Reports**
   - Open `services/{service}/htmlcov/index.html` in browser
   - Identify files below 80% coverage
   - Add tests for uncovered code paths

4. **Set Up Branch Protection**
   - Require status checks to pass before merging
   - Require Codecov checks
   - Prevent force pushes to main

---

## Quick Reference

### Key URLs

- **Codecov Dashboard:** <https://codecov.io/gh/sinergysolutionsllc/sinergysolutionsllc>
- **GitHub Actions:** <https://github.com/sinergysolutionsllc/sinergysolutionsllc/actions>
- **Workflow Files:** `.github/workflows/test-*.yml`

### Key Commands

```bash
# Check secret
gh secret list | grep CODECOV_TOKEN

# Trigger workflow
gh workflow run test-all-services.yml

# Watch workflow
gh run watch

# View latest run
gh run view --web

# Check pre-commit
pre-commit run --all-files
```

### Support Resources

- **Codecov Docs:** <https://docs.codecov.io/>
- **GitHub Actions Docs:** <https://docs.github.com/en/actions>
- **Internal Docs:** `/docs/operations/CI_CD_SETUP.md`

---

**Status:** Ready for setup
**Estimated Time:** 5-10 minutes
**Required Access:** GitHub repository admin

Once complete, move to Action Item 3: Install Pre-commit Hooks
