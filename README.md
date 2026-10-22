# Inside the Models

**App:** _paste your public Streamlit link here_ · **Created by Willie Robinson**

| Section | Direct link | My viewer should walk away knowing… |
|---|---|---|
| Push & Pull (linear regression) | _app link_`/linear` | A prediction is a starting point plus one signed push per feature, and a coefficient belongs to the model while a push belongs to one person. |
| Wisdom of the Forest (random forest) | _app link_`/forest` | A forest averages many different trees (each trained on different data and questions), and disagreement between trees is not the same as real uncertainty. |
| One Correction at a Time (gradient boosting) | _app link_`/boosting` | Boosting adds one small correction per round to fix what is still wrong, and validation error (not training error) tells you when to stop. |

**Inside the Models** is a Streamlit app that explains three regression models to a visitor who knows what machine learning and regression are, but not how these algorithms turn data into predictions. All three sections use the same three datasets from the CDC/NCHS NHANES survey (fasting glucose, systolic blood pressure and lung function / FEV₁) and the same five example people, so you can follow one person through every model.

## What each section teaches
- **Push & Pull:** waterfall chart from the training-average starting point to a person's prediction, editable inputs, coefficient vs. push, and which features matter most in general (effect per standard deviation).
- **Wisdom of the Forest:** the yes/no question path of individual trees, why trees differ (bootstrap samples and random feature choice), averaging with a "partial forest" slider, and why tree disagreement is not a confidence interval.
- **One Correction at a Time:** the boosting recipe, a round-by-round slider for one person, errors of 200 training people shrinking toward the diagonal, training vs. validation error with the validation-based stopping round, and a learning-rate 0.02 comparison.

A main menu page describes the site and links to all three sections.

## Where the numbers come from
Every number comes from the supplied, already-checked reference outputs in `outputs/` (read through `m10.py`). The app does not retrain or invent models or predictions. Results are associations in survey data, not causes, and errors are in each dataset's own units, so they should not be compared across datasets.

## Files
| File | What it is |
|---|---|
| `streamlit_app.py` | The app (main menu + three sections) |
| `m10.py` | Helpers that load the data and reference outputs and do the linear and boosting math |
| `requirements.txt` | Python packages for Streamlit Community Cloud |
| `.streamlit/config.toml` | Theme (red accent) |
| `outputs/` | Reference model outputs (field guide: `outputs/SCHEMA.md`) |
| `data/` | The three datasets and the data dictionary |
| `check.md` | Numbers the finished app must still show |
| `AGENT_BRIEF.md`, `SETUP.md` | Activity rules for the AI coding agent, and hosting steps |
| `index.html`, `app.js`, `m10.js` | Unused starter files for the GitHub Pages route (this app uses Streamlit) |

## Run locally
```bash
uv run --with streamlit,pandas,numpy streamlit run streamlit_app.py
```
Or with pip: `pip install -r requirements.txt` then `streamlit run streamlit_app.py`.

## Deploy
On [share.streamlit.io](https://share.streamlit.io), click **Create app**, choose this repository, branch `main` and main file `streamlit_app.py`, then deploy. Open the link in a private window to confirm it loads without signing in.

## Data and credits
Data: CDC/NCHS NHANES public-use files (see `data/README.md` for the data dictionary). Activity: <https://snsie.github.io/regression-activity/>. Built with Streamlit, pandas, NumPy and Altair.
