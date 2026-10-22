"""Inside the Models: three sections that teach linear regression, random forests and gradient boosting.

Run locally:  uv run --with streamlit,pandas,numpy streamlit run streamlit_app.py
Every number comes from outputs/*.json via m10.py; nothing is retrained here.
"""

import altair as alt
import pandas as pd
import streamlit as st

import m10
import music_player

LABELS = {"glucose": "Fasting glucose", "sbp": "Blood pressure", "fev1": "Lung function (FEV₁)"}
UP, DOWN, NEUTRAL, ACCENT = "#f28e2b", "#1b7bbf", "#8a8f98", "#d62728"


def signed(v: float, d: int = 1) -> str:
    return f"{v:+.{d}f}"


def pick_person() -> tuple[dict, dict]:
    key = st.sidebar.selectbox("Dataset", m10.DATASETS, format_func=LABELS.get, key="dataset")
    b = m10.load_bundle(key)
    labels = {p["id"]: f"{p['label']}: {p['description']}" for p in b["people"]}
    pid = st.sidebar.selectbox("Example person", list(labels), format_func=labels.get, key=f"person_{key}")
    person = next(p for p in b["people"] if p["id"] == pid)
    st.sidebar.markdown(
        f"**Predicting:** {b['target_label']} ({b['units']}) from {len(b['features'])} survey/body measurements. "
        f"The models learned from {b['n_train']:,} people; the example people are held out "
        f"(validation set, {b['n_validation']:,} people), so the models have not seen them.")
    st.sidebar.caption("Data: CDC/NCHS NHANES. Errors are in each dataset's own units, so don't compare them across datasets.")
    return b, person


def intro(b: dict, person: dict) -> None:
    st.markdown(f"**{person['label']}** — {person['description']}. "
                f"Measured {b['target_label'].lower()}: **{person['observed']:.1f} {b['units']}**.")


def label_of(b: dict, name: str) -> str:
    return next((f["label"] for f in b["features"] if f["name"] == name), name)


def units_of(b: dict, name: str) -> str:
    return next((f["units"] for f in b["features"] if f["name"] == name), "")


# ---- Push & Pull -------------------------------------------------------------
def waterfall(b: dict, ex: dict) -> alt.Chart:
    names = {g["name"]: g["label"] for g in b["categorical_groups"]}
    rows, run = [{"step": "Starting point", "start": 0.0, "end": ex["baseline"], "kind": "start", "value": ex["baseline"]}], ex["baseline"]
    for k, v in sorted(ex["grouped_pushes"].items(), key=lambda kv: -abs(kv[1])):
        rows.append({"step": names.get(k, label_of(b, k)), "start": run, "end": run + v,
                     "kind": "up" if v >= 0 else "down", "value": v})
        run += v
    rows.append({"step": "Prediction", "start": 0.0, "end": run, "kind": "total", "value": run})
    df = pd.DataFrame(rows)
    order = list(df["step"])
    color = alt.Color("kind:N", legend=None, scale=alt.Scale(
        domain=["start", "up", "down", "total"], range=[NEUTRAL, UP, DOWN, ACCENT]))
    lo = min(df["start"].where(df["kind"].isin(["up", "down"]), df["end"]).min(), df["end"].min())
    hi = max(df[["start", "end"]].max())
    pad = (hi - lo) * 0.25 or 1
    y = alt.Y("start:Q", title=f"{b['target_label']} ({b['units']})", scale=alt.Scale(domain=[lo - pad, hi + pad], clamp=True))
    bars = alt.Chart(df).mark_bar().encode(
        x=alt.X("step:N", sort=order, title=None, axis=alt.Axis(labelAngle=-35, labelLimit=160)),
        y=y, y2=alt.Y2("end:Q"), color=color,
        tooltip=["step", alt.Tooltip("value:Q", format="+.2f", title=f"Push ({b['units']})")])
    # white labels sit inside the bars: just under the top for the two tall bars, at the middle for pushes
    base = alt.Chart(df[df["kind"].isin(["start", "total"])]).mark_text(
        dy=14, fontSize=12, fontWeight="bold", color="white").encode(
        x=alt.X("step:N", sort=order), y="end:Q", text=alt.Text("value:Q", format=".1f"))
    df["mid"] = (df["start"] + df["end"]) / 2
    pushes = alt.Chart(df[df["kind"].isin(["up", "down"])]).mark_text(
        fontSize=12, fontWeight="bold", color="white").encode(
        x=alt.X("step:N", sort=order), y="mid:Q", text=alt.Text("value:Q", format="+.1f"))
    return (bars + base + pushes).properties(height=340)


def linear_page() -> None:
    b, person = pick_person()
    u, lin = b["units"], b["linear"]
    groups = b["categorical_groups"]
    st.title("Push & Pull")
    st.subheader("A linear regression prediction is a starting point plus one signed push per feature.")
    intro(b, person)

    with st.expander("What is a linear regression, in one minute?", expanded=False):
        st.markdown(
            f"The model learned one number per feature, a **coefficient**: *how much the prediction changes when that "
            f"feature goes up by 1 unit, with every other feature held fixed*. To predict, it starts from the "
            f"prediction for an **average** person and adds a **push** for each way this person differs from average.\n\n"
            "**push = coefficient × (this person's value − training average)**\n\n"
            "**prediction = starting point + all the pushes**")

    # --- inputs
    values = dict(person["values"])
    grouped = {lv["column"] for g in groups for lv in g["levels"] if lv["column"]}
    numeric = [f for f in b["features"] if f["name"] not in grouped]
    with st.expander("Change this person's values and watch the pushes move", expanded=False):
        cols = st.columns(3)
        for i, f in enumerate(numeric):
            s = b["feature_stats"][f["name"]]
            values[f["name"]] = cols[i % 3].number_input(
                f"{f['label']} ({f['units']})", min_value=float(s["min"]), max_value=float(s["max"]),
                value=float(values[f["name"]]), key=f"{b['id']}_{person['id']}_{f['name']}")
        for j, g in enumerate(groups):
            levels = [lv["label"] for lv in g["levels"]]
            current = next((lv["label"] for lv in g["levels"] if lv["column"] and values[lv["column"]] == 1), g["reference"])
            choice = cols[(len(numeric) + j) % 3].selectbox(
                g["label"], levels, index=levels.index(current), key=f"{b['id']}_{person['id']}_{g['name']}")
            values.update({lv["column"]: float(lv["label"] == choice) for lv in g["levels"] if lv["column"]})
    ex = m10.linear_explain(b, values)
    edited = values != person["values"]

    # --- the build-up
    st.markdown("### 1. Build this person's prediction")
    st.altair_chart(waterfall(b, ex), width="stretch")
    st.markdown(
        f"Start at **{ex['baseline']:.1f} {u}** (the prediction for the training-average person). "
        "Orange bars push the prediction up, blue bars push it down. "
        f"Adding them all gives **{ex['prediction']:.1f} {u}**.")
    names = {g["name"]: g["label"] for g in groups}
    terms = " ".join(f"{signed(v)}" for v in ex["grouped_pushes"].values())
    st.code(f"{ex['baseline']:.1f} {terms} = {ex['prediction']:.1f} {u}", language=None)
    if edited:
        st.caption("These are edited values, so there is no measured value to compare with.")
    else:
        miss = ex["prediction"] - person["observed"]
        st.markdown(f"**Measured:** {person['observed']:.1f} {u} · **Model's miss:** {signed(miss)} {u}")
        if abs(miss) > lin["rmse"]["validation"]:
            st.warning(
                f"This miss is larger than the model's typical validation error ({lin['rmse']['validation']:.1f} {u}). "
                "A straight line can only push each feature the same way for everyone, so it can't follow patterns that bend "
                "(for example, lungs grow in childhood and shrink later in life). That is a limit of the model, not a bug.")
        else:
            st.caption(f"Typical validation error of this model: about {lin['rmse']['validation']:.1f} {u}.")

    # --- coefficient vs push
    st.markdown("### 2. A coefficient is not a push")
    st.markdown("A **coefficient** belongs to the model and is the same for everybody. A **push** belongs to one person: "
                "the coefficient times how far *that person* is from average.")
    options = {names.get(k, label_of(b, k)): k for k in ex["grouped_pushes"]}
    chosen = st.selectbox("Pick a feature", list(options), key=f"coef_{b['id']}")
    k = options[chosen]
    group = next((g for g in groups if g["name"] == k), None)
    if group is None:
        c, ref, val = lin["coefficients"][k], lin["reference"][k], values[k]
        un = units_of(b, k)
        st.markdown(
            f"- **Coefficient (everyone):** {signed(c, 3)} {u} per 1 {un}\n"
            f"- **This person:** {val:g} {un}; training average {ref:.1f} {un} → difference {val - ref:+.1f} {un}\n"
            f"- **Push (this person):** {signed(c, 3)} × {val - ref:+.1f} = **{signed(ex['grouped_pushes'][k], 2)} {u}**")
    else:
        sel = next((lv["label"] for lv in group["levels"] if lv["column"] and values[lv["column"]] == 1), group["reference"])
        rows = []
        for lv in group["levels"]:
            col = lv["column"]
            rows.append({"Group": lv["label"] + (" (reference group)" if not col else ""),
                         f"Coefficient vs {group['reference']} ({u})": 0.0 if not col else lin["coefficients"][col]})
        st.dataframe(pd.DataFrame(rows).set_index("Group").style.format("{:+.2f}"), width="stretch")
        st.markdown(
            f"The coefficients compare each group with **{group['reference']}** (just how the 0/1 columns are coded). "
            f"This person is **{sel}**. Their push is measured from the *training average mix* of groups, "
            f"so it is **{signed(ex['grouped_pushes'][k], 2)} {u}**, even for the reference group.")

    # --- general importance
    st.markdown("### 3. Which features matter most *in general*?")
    st.markdown("Raw coefficients can't be compared because the units differ (years vs. kg/m²). "
                "Instead, take each coefficient × one standard deviation (SD) of the feature — "
                "the effect of a typical difference between people. This is about the **model overall**, not this person.")
    imp = pd.DataFrame([{"Feature": label_of(b, k), "Effect": v, "Sign": "up" if v >= 0 else "down"}
                        for k, v in lin["typical_effect_per_sd"].items()])
    st.altair_chart(alt.Chart(imp).mark_bar().encode(
        y=alt.Y("Feature:N", sort=alt.EncodingSortField("Effect", op="sum", order="descending"), title=None),
        x=alt.X("Effect:Q", title=f"Change in prediction per 1 SD ({u})"),
        color=alt.Color("Sign:N", legend=None, scale=alt.Scale(domain=["up", "down"], range=[UP, DOWN])),
        tooltip=["Feature", alt.Tooltip("Effect:Q", format="+.2f")]).properties(height=60 + 34 * len(imp)),
        width="stretch")
    st.caption("Sex and ethnicity are single yes/no or category choices, so they have no SD-based effect here; see their coefficients above. "
               "These are associations in the data, not causes.")


# ---- Wisdom of the Forest ----------------------------------------------------
def goes_text(g: str) -> str:
    return ">" if g.strip() == ">" else "≤"


def forest_page() -> None:
    b, person = pick_person()
    u, rf = b["units"], b["forest"]
    fp = rf["people"][person["id"]]
    trees = fp["tree_predictions"]
    n_trees = rf["n_trees"]
    st.title("Wisdom of the Forest")
    st.subheader(f"A random forest asks {n_trees} different decision trees and averages their answers.")
    intro(b, person)

    st.markdown("### 1. One tree = a chain of yes/no questions")
    st.markdown("A **decision tree** splits people with questions like \"is waist ≤ 90 cm?\" until it reaches a **leaf**, "
                "which predicts the average outcome of the training people who ended up there. "
                f"Here are the questions trees 1–5 ask about {person['label'].lower()}:")
    traced = fp["traced_trees"]
    tabs = st.tabs([f"Tree {i + 1}" for i in range(len(traced))])
    for i, (tab, t) in enumerate(zip(tabs, traced)):
        with tab:
            lines = []
            for s in t["steps"]:
                lab = label_of(b, s["feature"])
                un = units_of(b, s["feature"])
                thr = s["threshold"]
                if abs(thr - 0.5) < 1e-9 and any(f["name"] == s["feature"] and f["binary"] for f in b["features"]):
                    lines.append(f"{lab}: {'yes' if goes_text(s['goes']) == '>' else 'no'}")
                else:
                    lines.append(f"{lab} {goes_text(s['goes'])} {thr:g} {un}".rstrip())
            st.markdown("\n".join(f"{j + 1}. {l}" for j, l in enumerate(lines)))
            st.markdown(f"→ **Tree {i + 1} predicts {t['leaf_value']:.1f} {u}** "
                        f"(this person's path took {len(lines)} questions).")
    st.caption("Each list shows the path this person follows, the direction taken at every question, and the leaf reached.")

    st.markdown("### 2. Why are the trees different?")
    share = sum(rf["bootstrap_unique_training_rows"]) / len(rf["bootstrap_unique_training_rows"]) / rf["n_training_rows"]
    c1, c2 = st.columns(2)
    c1.markdown(f"**Different data.** Each tree trains on a *bootstrap sample*: people drawn at random **with repeats** "
                f"from the {rf['n_training_rows']:,} training people. A tree sees only about **{share:.0%}** of them "
                "(the rest are left out; some appear twice or more).")
    c2.markdown(f"**Different questions.** At every split a tree may only consider "
                f"**{rf['features_tried_per_split']} of the {rf['n_features']}** features, chosen at random. "
                "So trees can start with different questions:")
    roots = pd.Series([f"{label_of(b, r['feature'])} (≤ {r['threshold']:g})" if not any(
        f["name"] == r["feature"] and f["binary"] for f in b["features"]) else label_of(b, r["feature"])
        for r in rf["root_split"]]).value_counts().rename_axis("First question").reset_index(name="Trees")
    c2.dataframe(roots.head(6), hide_index=True, width="stretch")
    c2.caption("Each tree's *first* question; the top 6 of all trees.")

    st.markdown("### 3. Average them")
    n = st.slider("How many trees to average", 1, n_trees, 5, key=f"n_{b['id']}")
    partial = sum(trees[:n]) / n
    full = fp["prediction"]
    label = ("Whole forest" if n == n_trees else "Partial forest") + f" (average of {'all ' if n == n_trees else 'the first '}{n} trees)"
    df = pd.DataFrame({"tree": range(1, n_trees + 1), "guess": trees})
    df["used"] = df["tree"] <= n
    lo, hi = min(trees + [person["observed"]]), max(trees + [person["observed"]])
    pad = (hi - lo) * 0.05 or 1
    x = alt.X("guess:Q", bin=alt.Bin(maxbins=30), title=f"Tree's guess ({u})", scale=alt.Scale(domain=[lo - pad, hi + pad]))
    hist = alt.Chart(df).mark_bar().encode(
        x=x, y=alt.Y("count():Q", title="Number of trees"),
        color=alt.Color("used:N", legend=None, scale=alt.Scale(domain=[True, False], range=[ACCENT, "#cfd3d8"])),
        order=alt.Order("used:N"))
    marks = pd.DataFrame([{"v": partial, "what": label, "dash": 0}, {"v": person["observed"], "what": "Measured value", "dash": 1}])
    rules = alt.Chart(marks).mark_rule(size=3).encode(
        x=alt.X("v:Q"), color=alt.Color("what:N", scale=alt.Scale(range=[ACCENT, "#111111"]), legend=alt.Legend(orient="bottom", title=None)),
        strokeDash=alt.StrokeDash("dash:N", legend=None))
    st.altair_chart((hist + rules).properties(height=280), width="stretch")
    m1, m2 = st.columns(2)
    m1.metric(label, f"{partial:.1f} {u}")
    m2.metric(f"Forest prediction (all {n_trees} trees)", f"{full:.1f} {u}")
    st.markdown(f"Green bars are the {n} tree(s) being averaged; grey bars are the other trees. "
                f"Adding more trees moves the average toward the full forest's {full:.1f} {u}.")

    st.markdown("### 4. Disagreement is not uncertainty")
    st.markdown(
        f"These {n_trees} trees guessed anywhere from **{min(trees):.1f}** to **{max(trees):.1f} {u}** "
        f"(middle half: {pd.Series(trees).quantile(.25):.1f} to {pd.Series(trees).quantile(.75):.1f}). "
        "That spread is **disagreement between trees**: it shows how much the answer depends on which data and questions a tree got. "
        "It is **not** a confidence or prediction interval, because every tree has seen the same kind of data and may share the same blind spots.")
    st.markdown(f"A better sense of real error: on held-out validation people, the whole forest misses by about "
                f"**{rf['rmse']['validation']:.1f} {u}** (RMSE, a typical size of the miss). "
                f"For this person the forest missed by {signed(full - person['observed'])} {u}.")
    v = pd.DataFrame({"Trees averaged": range(1, n_trees + 1), "Validation RMSE": rf["validation_rmse_by_trees"]})
    st.altair_chart(alt.Chart(v).mark_line(color=ACCENT).encode(
        x=alt.X("Trees averaged:Q"), y=alt.Y("Validation RMSE:Q", title=f"Validation RMSE ({u})", scale=alt.Scale(zero=False)),
        tooltip=["Trees averaged", alt.Tooltip("Validation RMSE:Q", format=".2f")]).properties(height=220),
        width="stretch")
    st.caption("Averaging more trees lowers the validation error and then levels off: a single tree is noisy, the average is steadier. "
               f"A forest can only predict values within the range of the training outcomes ({rf['training_target_range'][0]:.1f} to "
               f"{rf['training_target_range'][1]:.1f} {u}).")


# ---- One Correction at a Time -----------------------------------------------
def boosting_page() -> None:
    b, person = pick_person()
    u, gb = b["units"], b["boosting"]
    p = gb["people"][person["id"]]
    n_rounds = len(p["corrections"])
    st.title("One Correction at a Time")
    st.subheader("Gradient boosting builds a prediction in small steps; each new tree corrects what is still wrong.")
    intro(b, person)

    st.markdown("### 1. The recipe")
    st.markdown(
        f"1. **Round 0:** predict the training average for everyone ({gb['init']:.1f} {u}).\n"
        "2. For each round: measure the **residuals** — measured value minus current prediction — for the *training* people. "
        "Fit a small tree to those residuals, so it learns where the model is still too low or too high.\n"
        "3. Add the tree's output to the prediction, scaled by a small **learning rate** "
        f"({gb['learning_rate']}) so no single tree can change much. The corrections shown below already include this scaling.\n"
        f"4. Repeat for {n_rounds} rounds.")

    st.markdown("### 2. Watch one person's prediction improve")
    r = st.slider("Round", 0, n_rounds, 1, key=f"round_{b['id']}")
    if r == 0:
        st.markdown(f"**Round 0:** everyone starts at the training average, **{gb['init']:.1f} {u}**.")
    else:
        c = p["corrections"][r - 1]
        st.markdown(f"Prediction after round {r - 1}: **{p['staged'][r - 1]:.1f}** &nbsp;+&nbsp; correction from tree {r}: "
                    f"**{signed(c, 2)}** &nbsp;=&nbsp; prediction after round {r}: **{p['staged'][r]:.1f} {u}**")
    stage = pd.DataFrame({"Round": range(n_rounds + 1), "Prediction": p["staged"]})
    line = alt.Chart(stage).mark_line(color=ACCENT).encode(
        x=alt.X("Round:Q", scale=alt.Scale(type="symlog", constant=5), title="Round (log-like scale)"),
        y=alt.Y("Prediction:Q", title=f"Prediction ({u})", scale=alt.Scale(zero=False)))
    now = alt.Chart(pd.DataFrame({"Round": [r], "Prediction": [p["staged"][r]]})).mark_point(
        size=120, filled=True, color=UP).encode(x="Round:Q", y="Prediction:Q")
    obs = alt.Chart(pd.DataFrame({"y": [person["observed"]], "what": ["Measured value"]})).mark_rule(
        strokeDash=[6, 4], color="#111111").encode(y="y:Q")
    st.altair_chart((line + now + obs).properties(height=260), width="stretch")
    st.caption(f"Dashed line = this person's measured value ({person['observed']:.1f} {u}). "
               "The prediction moves toward it in small steps but need not reach it, and it can drift past it.")

    st.markdown("### 3. How the errors of all training people shrink")
    snaps = gb["residual_snapshots"]
    snap_round = st.select_slider("Round shown", snaps["rounds"], value=snaps["rounds"][min(4, len(snaps["rounds"]) - 1)],
                                  key=f"snap_{b['id']}")
    sdf = pd.DataFrame({"Measured": snaps["observed"], "Predicted": snaps["predictions"][str(snap_round)]})
    lo, hi = min(sdf.min()), max(sdf.max())
    pts = alt.Chart(sdf).mark_circle(opacity=0.5, size=40, color=ACCENT).encode(
        x=alt.X("Measured:Q", title=f"Measured ({u})", scale=alt.Scale(domain=[lo, hi])),
        y=alt.Y("Predicted:Q", title=f"Predicted after round {snap_round} ({u})", scale=alt.Scale(domain=[lo, hi])))
    diag = alt.Chart(pd.DataFrame({"a": [lo, hi]})).mark_line(color="#111111", strokeDash=[4, 4]).encode(x="a:Q", y="a:Q")
    st.altair_chart((pts + diag).properties(height=300), width="stretch")
    st.caption("200 training people. Dots on the dashed diagonal are predicted perfectly. "
               "At round 0 everyone is predicted the same value (a flat row of dots); each round, dots move toward the diagonal.")

    st.markdown("### 4. When to stop? Use validation error")
    st.markdown(
        "**Training error** measures people the trees were fitted to, so it keeps falling with more rounds — eventually by "
        "memorizing noise. **Validation error** measures held-out people the trees never saw; it falls, then turns upward "
        "when extra rounds stop helping (overfitting). The best stopping point is where **validation** error is lowest.")
    rm = pd.DataFrame({"Round": range(n_rounds + 1), "Training": gb["rmse"]["train"], "Validation": gb["rmse"]["validation"]})
    long = rm.melt("Round", var_name="Error", value_name="RMSE")
    curves = alt.Chart(long).mark_line().encode(
        x=alt.X("Round:Q", scale=alt.Scale(type="symlog", constant=5), title="Round (log-like scale)"),
        y=alt.Y("RMSE:Q", title=f"RMSE ({u})", scale=alt.Scale(zero=False)),
        color=alt.Color("Error:N", scale=alt.Scale(domain=["Training", "Validation"], range=[DOWN, UP]),
                        legend=alt.Legend(orient="bottom", title=None)))
    best = alt.Chart(pd.DataFrame({"Round": [gb["best_validation_round"]]})).mark_rule(color=ACCENT, size=2).encode(x="Round:Q")
    chosen = alt.Chart(pd.DataFrame({"Round": [r]})).mark_rule(color="#111111", strokeDash=[4, 4]).encode(x="Round:Q")
    st.altair_chart((curves + best + chosen).properties(height=280), width="stretch")
    st.markdown(
        f"Green line: the validation-best round, **{gb['best_validation_round']}** "
        f"(validation RMSE **{gb['best_validation_rmse']:.1f} {u}**). Dashed line: round {r} from the slider, "
        f"where validation RMSE is **{gb['rmse']['validation'][r]:.1f} {u}** and training RMSE is "
        f"**{gb['rmse']['train'][r]:.1f} {u}**. RMSE is a typical size of the miss, in {u}.")
    st.caption("The stopping round is chosen using validation data, so it is a validation-based choice, not an independent test result.")

    st.markdown("### 5. Learning rate: small steps need more rounds")
    cmp = gb["comparison_learning_rate_0_02"]
    ls = pd.DataFrame({"Round": range(len(cmp["rmse"]["validation"])), "Learning rate 0.02": cmp["rmse"]["validation"]})
    ls["Learning rate 0.1 (main model)"] = gb["rmse"]["validation"][:len(ls)]
    ll = ls.melt("Round", var_name="Setting", value_name="Validation RMSE")
    st.altair_chart(alt.Chart(ll).mark_line().encode(
        x=alt.X("Round:Q", scale=alt.Scale(type="symlog", constant=5), title="Round (log-like scale)"),
        y=alt.Y("Validation RMSE:Q", title=f"Validation RMSE ({u})", scale=alt.Scale(zero=False)),
        color=alt.Color("Setting:N", scale=alt.Scale(range=[DOWN, UP]), legend=alt.Legend(orient="bottom", title=None))
    ).properties(height=240), width="stretch")
    st.markdown(f"With smaller steps (0.02), the best validation round moves from **{gb['best_validation_round']}** "
                f"to **{cmp['best_validation_round']}** (validation RMSE {cmp['best_validation_rmse']:.1f} {u}). "
                "This is a separately fitted model, not a rescaled copy of the main one.")


# ---- Main menu ---------------------------------------------------------------
def home_page() -> None:
    st.title("Inside the Models")
    st.subheader("How do three regression models turn health data into a prediction?")
    st.caption("Created by Willie Robinson")
    st.markdown(
        "This site explains **three regression models**, one section each, for visitors who already know what "
        "machine learning and regression are but not how these algorithms produce a prediction. "
        "Every section uses the same three real datasets from the CDC/NCHS **NHANES** health survey and five "
        "example people, so you can follow one person through all three models.")
    st.markdown("#### Pick a dataset in the sidebar of any section")
    c = st.columns(3)
    for col, (name, text) in zip(c, [
            ("Fasting glucose (mg/dL)", "predicted from HbA1c (3-month average blood sugar), age, BMI, waist size and sex"),
            ("Blood pressure (mmHg)", "systolic pressure predicted from age, BMI, waist size, sex, family income and ethnicity"),
            ("Lung function (mL)", "FEV₁ (air blown out in one second) predicted from age, sex, BMI and family income")]):
        col.markdown(f"**{name}**  \n{text}")
    st.markdown("#### The three sections")
    for page, title, model, blurb in [
            (linear_pg, "Push & Pull", "Linear regression",
             "Start from the average person's prediction and add one signed push per feature. "
             "Learn the difference between a model's coefficient and one person's push."),
            (forest_pg, "Wisdom of the Forest", "Random forest",
             "See how 100 different decision trees each give a guess and how averaging them makes one prediction. "
             "Learn why tree disagreement is not the same as real uncertainty."),
            (boosting_pg, "One Correction at a Time", "Gradient boosting",
             "Watch each new small tree fix what is still wrong, round by round. "
             "Learn how validation error tells you when to stop.")]:
        with st.container(border=True):
            st.markdown(f"##### {title} · *{model}*")
            st.write(blurb)
            st.page_link(page, label=f"Open {title}", icon="➡️")
    st.info("All numbers come from models that were already trained and checked; nothing is retrained in the app. "
            "What you see are associations in survey data, not causes. Errors are in each dataset's own units, "
            "so don't compare them across datasets.")


st.set_page_config(page_title="Inside the Models", layout="wide")
music_player.render()
home_pg = st.Page(home_page, title="Main menu", url_path="home", default=True, icon="🏠")
linear_pg = st.Page(linear_page, title="Push & Pull", url_path="linear")
forest_pg = st.Page(forest_page, title="Wisdom of the Forest", url_path="forest")
boosting_pg = st.Page(boosting_page, title="One Correction at a Time", url_path="boosting")
st.navigation([home_pg, linear_pg, forest_pg, boosting_pg]).run()
