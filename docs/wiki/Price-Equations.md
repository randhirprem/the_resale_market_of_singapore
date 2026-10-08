# Price equations and estate comparisons

[Wiki home](Home.md) · [Data and methodology](Data-and-Methodology.md)

## Purpose

Explain recorded HDB resale-price relationships using one consistent specification nationally and within each estate. These are descriptive hedonic regressions, not causal estimates, academic-school premiums, a valuation service or future-price forecasts. A national offset cannot be labelled a school, transport or amenity premium.

![Singapore and Jurong East equations in the current app](../screenshots/price-equations.jpg)

Captured 8 October 2026. Values reflect the imported snapshot.

## Equation

The Singapore equation is:

```
ln(P) = a + b ln(A/100) + c (L−70)/10 + d (S−8)/10 + e T + τflat + δestate + residual
```

- P: nominal resale price in SGD.
- A: floor area in square metres.
- L: supplied remaining lease in years.
- S: midpoint of the supplied storey range, not a known exact floor.
- T: years relative to the final training month (March 2026 in the initial build).
- τflat: categorical flat-type adjustment, with four-room as the zero reference.
- δestate: estate intercept in the national equation. Effects average to zero using training transaction weights.

Each eligible estate gets the same specification with its own coefficients and no additional estate term. Independent local equations require at least 200 training transactions, 20 distinct blocks and 30 comparable validation transactions. Bukit Timah falls below the training threshold in the current snapshot; it uses national slopes plus its national estate offset, clearly labelled pooled.

The formula is returned to SGD using `exp(fitted log price)`. This is a fitted geometric centre, not a bias-corrected arithmetic mean or guaranteed median. Intercepts describe an algebraic reference flat, which can lie outside an estate's observed range; for example, a 70-year lease is not observed in the Marine Parade training data.

## Estimation and validation

The most recent source month is always excluded as potentially incomplete. Of the preceding 36 months, the first 30 train the models; the last six test them. Initial window: October 2023–March 2026 training, April–September 2026 validation. No holdout outcomes are used to fit coefficients or define category coding. No final refit on the test set occurs.

Ordinary least squares is solved with NumPy's least-squares solver. Rank-deficient or severely ill-conditioned local designs are withheld. Two-, three-, four-, five-room and executive flats are included; rare one-room and multi-generation records are excluded, along with invalid required inputs. Sales within a block can occur in both time windows: this tests later sales in the market, not generalization to entirely unseen blocks.

Coefficient uncertainty uses block-clustered sandwich covariance with finite-sample correction and normal-approximation 95% intervals. These are coefficient intervals, not home-price prediction intervals. They do not account for all forms of spatial dependence. Separate national/local intervals do not constitute a formal test of their difference.

The main validation metric is mean absolute percentage error: `mean(abs(predicted/actual − 1))*100`. Median absolute percentage error is also retained in the artifact. Estate local-versus-national comparisons use exactly the same held-out sales, excluding flat types absent from local training; the minimum 30-sale threshold is reapplied after that exclusion.

## Reading associations

- A 10% area increase corresponds to `100*(exp(b*ln(1.1))−1)%`, holding included predictors fixed.
- Ten additional lease years correspond to `100*(exp(c)−1)%`.
- Ten storeys higher correspond to `100*(exp(d)−1)%`.
- Twelve months later correspond to `100*(exp(e)−1)%` within this historical specification; do not extrapolate this as a forecast.

Area and flat type are correlated, so the area coefficient is conditional on type and need not resemble raw size-price comparisons. Likewise, remaining lease may proxy for unrecorded project or location differences. Narrow within-estate variation and small category samples make some coefficients unstable. Marine Parade's lease range is under ten years, so a ten-year local comparison extrapolates beyond observed data and is flagged.

## What an “anchor” means here

Remove one group of predictors, refit on the same training rows and measure the change in held-out **mean** absolute percentage error. The groups are area plus flat type, remaining lease, storey, sale timing, and (nationally only) estate location. The greatest positive removal penalty identifies the most useful recorded factor group for this particular model/test window.

These values are error percentage points, not price premiums, causal contributions or additive shares of the house price. Negative penalties mean removing the factor helped on this holdout. Predictors can substitute for one another. Using this one holdout to inspect or choose models does not provide a second, untouched test of a resulting model-selection strategy.

## Why local relationships differ

Local housing mixes, lease ranges, flat-type supply, building heights and sample sizes differ. A town containing both new and old stock offers more age variation than an estate with similar-age flats. Area and type can account for much of a market with varied dwelling sizes. Storey may proxy for views and building characteristics. The app shows actual local interquartile ranges and validation comparisons rather than assigning unsupported neighbourhood stories.

The files do not supply verified coordinates for each transacted block, matched historical school/accessibility measures, renovation quality, views or facility opening dates. School, MRT, park and amenity explanations remain hypotheses until those variables are added with appropriate spatial and temporal controls.

## Maintenance

```sh
python3 -m pip install -r requirements-models.txt
npm run import
npm run model
npm test
npm run build
```

`backend/price_models.py` writes `data/price-models.json` atomically. File size and nanosecond modification time link the artifact to the imported SQLite database; generation also checks that the database did not change during fitting. The API rejects missing, outdated-version or stale artifacts. The JSON is generated local data and is ignored by Git. The standard-library HTTP server does not import NumPy when serving it.

## Asking-price comparison form

The separate [Asking-price assessment](Asking-Price.md) page documents the four-input form, comparison criteria, percentile range, outcome labels and limitations. It uses recent comparable sales directly, not this regression equation, and requires no model artifact. Its API contract is in [Architecture and API](Architecture-and-API.md#asking-price-api).
