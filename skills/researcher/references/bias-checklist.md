# Bias Checklist — Research Pipeline

Applied to every research inquiry and retroactively to the existing knowledge base.
All biases are **flagged and noted, not excluded** — unless the paper is from a
predatory journal or known fraudulent research.

---

## A. Funding / Conflict-of-Interest Detection

### Signals to scan for (in abstract and metadata)

```
funded by | received funding | grant from | honoraria | advisory board |
employee of | consultant to | stock holder | founder of | owns shares |
conflict of interest | industry funded | pharmaceutical | supplement company |
nutrition research | biotech |雀深 | funded by the author
```

### Confidence penalty table

| Source | Penalty |
|---|---|
| For-profit company funding own product | Downgrade 1 evidence level |
| Academic grant from company (no product stake) | Flag, no penalty |
| Government / public / academic funding (no corporate interest) | No penalty |
| Funding not declared | Flag, no penalty |
| Predatory journal / known fraudulent research | **Exclude** from corpus |

### Annotation format

```
[FUNDING CONFLICT] funded by {source} — confidence downgraded {old}→{new}
[BIAS NOTE] funding not declared — verify independently
[EXCLUDED] predatory journal — removed from corpus
```

---

## B. Publication Bias Detection

### Null-result search terms (always included in queries)

```
"no benefit" / "failed to improve" / "not significant" /
"null result" / "no difference" / "did not reduce" /
"placebo controlled" / "placebo-controlled" / "negative trial"
```

### Detection rule

- After corpus build: count papers with null-result signals vs. total with abstracts
- If null-result papers < 5% of corpus: **publication bias suspected**
- If industry-funded positive studies outnumber null results from independent sources:
  flag "industry-funded studies systematically more positive than independent trials"

### Annotation

```
[PUBLICATION BIAS SUSPECTED] null-result papers underrepresented
  (found {N}/{M} = {X}% null ratio; expected ≥5%)
[BIAS NOTE] null-result papers present in corpus
```

---

## C. Institutional / Training Bias Detection

### Concentration check

After corpus build, for each topic/inquiry:
- Count papers per institution (from author affiliations or common institutional names in author fields)
- Count papers per senior author / author group
- Flag if **>50% of corpus** comes from the same institution or author group

### Annotation

```
[BIAS NOTE] {institution} — {X}% of corpus on this topic
[BIAS NOTE] {author group} appears in {X}% of corpus — findings may reflect group interpretation
[CORPUS BALANCED] no single institution >50%
```

---

## D. Adversarial Bias Challenge

The Falsifier agent explicitly attacks:

1. **Funding conflicts** in cited papers — "this paper was funded by X, does that affect the finding?"
2. **Missing null results** — "has this hypothesis been tested in a null-result study or only in positive trials?"
3. **Institutional concentration** — "is the evidence base dominated by one institution's interpretation?"
4. **Selective outcome reporting** — "were all measured outcomes reported, or only the favorable ones?"

---

## E. Bias Disclosure in RESEARCH.md

Every final report includes:

```markdown
## Bias Disclosure

- Papers with funding conflicts: {count} — downgraded confidence
- Predatory/fraudulent papers excluded: {count}
- Institutional concentration: {institution} = {X}% of corpus
- Author group concentration: {group} = {X}% of corpus
- Publication bias: {"suspected" / "not suspected"} — null-result papers {"found" / "not found"}
- Funding not declared: {count} — flagged, not excluded
```

---

## F. Confidence Grade Adjustment Rules

When a paper has multiple bias flags, apply the **most severe penalty only**:

1. Predatory/fraudulent → exclude (do not cite)
2. Industry-funded (for-profit) + institutional concentration → downgrade 1 level
3. Industry-funded only → downgrade 1 level
4. Institutional concentration only → flag, note, no penalty
5. Funding not declared → flag, note, no penalty
6. Publication bias suspected → note, no automatic penalty but reduces confidence in positive direction

---

## G. Retroactive Application

For the existing knowledge base (5,947 papers):

1. Scan all papers with abstracts for funding/conflict signals → `bias-funding.json`
2. Scan author fields for institutional concentration → `bias-institutions.json`
3. Scan for null-result signals → `bias-publication-bias.json`
4. Write summary report → `BIA-Retroactive-Report.md`
5. Add `bias_check:` frontmatter field to each summary in `summaries/`
6. Add `## Bias Disclosure` section to each summary
7. Add bias disclosures to existing RESEARCH.md files in inquiry workspaces

---

---

## H. Known Detection Failure — TM Organization Conflict

The automated bias scan (search_papers.py `scan_corpus_for_bias`) failed to flag the well-documented TM-organization affiliations of Orme-Johnson, Travis, Walton, and Rees in the meditation corpus. The corpus-level scan found 0 funding conflict signals in the meditation literature — this is implausibly low and indicates a detection gap, not absence of conflict.

**Manual flag for future inquiries:** When a corpus contains research from the Maharishi University of Management / TM organization (David Orme-Johnson, Frederick Travis, Kenneth Walton, Brian Rees), treat all their papers as carrying extreme funding conflict regardless of what the automated abstract scan reports. The conflict is structural and financial, not just declared in acknowledgments.

This is a documented limitation: the keyword-based abstract scan underestimates conflicts that are not explicitly declared in the abstract text. Manual checks for known institutional conflicts (TM organization, Maharishi University) are required in addition to automated scanning.

---

## I. Supplement-Specific Bias — Additional Flags

The supplement industry has **no pre-market efficacy or safety barrier** — this is the structural difference from pharmaceuticals. The manufacturer funds the study, the manufacturer sells the product. This creates a conflict-of-interest structure that is different from, and more severe than, most academic-industry partnerships.

### Supplement Industry Funding Signals

```
supplement company | nutrition research company | nutraceutical |
herbal supplement | funded by the manufacturer | product study |
self-funded by the company | trade association for the ingredient
```

### The Cochrane Fish Oil Problem (Illustrative)

The 2018 Cochrane fish oil review (86 RCTs, n=112,000) found no mortality or CVD benefit — the largest and least biased pool of evidence. Industry-funded fish oil studies (typically with 1–2g/day doses) had consistently positive results. When all industry-funded studies are pooled, the effect size looks positive. When the Cochrane team includes them as a sensitivity analysis and weighs by design quality, the effect disappears. This is the pattern to watch for in every supplement category.

### Key questions for any supplement claim

1. **Who funded the pivotal study?** If it's the brand selling the product, apply a1-level downgrade.
2. **Is there a third-party testing mark?** NSF Certified for Sport, USP Verified, ConsumerLab.com Verified — these are meaningful. Absence is a red flag.
3. **Is the dosage in the study the same as the recommended dose?** Under-dosing in the active arm is a common design flaw that makes the placebo look worse.
4. **Was the comparator appropriate?** Some studies compare their supplement to a placebo rather than to the active ingredient at therapeutic doses — making the active arm look better by default.
5. **Is the comparator a degraded form of the same ingredient?** (e.g., poorly absorbed form vs. the tested form) — a common tactic in magnesium and curcumin studies.
6. **Is there a null-result study in the same category?** If all studies are positive, publication bias is suspected regardless of P-values.

### Tainting/contamination categories

| Risk level | Categories | Notes |
|---|---|---|
| High | Protein powders, pre-workouts, libido supplements, "natural" testosterone boosters, bodybuilding supplements | Most frequently adulterated with pharmaceuticals (FDA 2018: ~700 products) |
| Moderate | Botanical extracts, herbal formulas | Heavy metal and fungal contamination documented; NSF/USP testing required for confidence |
| Lower | Single-ingredient vitamins, minerals, amino acids (creatine, glycine, NAC) | Creatine monohydrate is very stable and low contamination risk; single-ingredient vitamins are lower risk but not zero |

### Annotation format

```
[SUPPLMENT FUNDING CONFLICT] pivotal study funded by {brand} — confidence downgraded {A→B}
[THIRD-PARTY TESTING ABSENT] no NSF/USP/ConsumerLab mark — contamination risk unverified
[SUPPLEMENT DOSAGE NOTE] study used {X}mg but typical dose is {Y}mg — may not reflect real-world efficacy
[PUBLICATION BIAS SUSPECTED] all studies positive, no null results in corpus
[CONTAMINATION RISK] {category} is high-risk for tainting — NSF/USP testing required
```

*Last updated: 2026-06-09*