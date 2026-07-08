"""
NIRI Data Portal — Phase 3 Showcase Interface
Mirrors UK Biobank field-level pages with real participant counts & answer distribution charts.

Changes in v3:
  - BMC Latvia → NIRI throughout
  - English translations shown below each Latvian question
  - Visit logic: VISIT defaults to 1 for all participants;
    VISIT=2 shown where second visit records exist in production data
  - Loads enriched_catalogue_369_v3.json

Usage:
    1. Place this file and enriched_catalogue_369_v3.json in the same folder.
    2. pip install streamlit pandas plotly
    3. streamlit run master_data_dictionary_v3.py
"""

import json
from pathlib import Path
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(
    page_title="NIRI Data Portal",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
.portal-header {
    background: linear-gradient(135deg, #1a2744 0%, #2e4a7a 100%);
    color: white; padding: 18px 28px; border-radius: 12px;
    margin-bottom: 22px; display: flex; align-items: center;
    justify-content: space-between;
    box-shadow: 0 4px 16px rgba(26,39,68,0.18);
}
.portal-header .brand  { font-size: 1.35rem; font-weight: 800; letter-spacing: -0.3px; }
.portal-header .tagline { font-size: 0.75rem; opacity: 0.55; margin-top: 2px; }
.portal-header .subtitle { font-size: 0.9rem; opacity: 0.8; font-weight: 500; }

.stats-row { display: flex; gap: 10px; margin-bottom: 18px; flex-wrap: wrap; }
.stat-box {
    background: white; border: 1px solid #e2e8f0; border-radius: 10px;
    padding: 12px 22px; text-align: center; min-width: 110px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.05);
}
.stat-box .n { font-size: 1.5rem; font-weight: 800; color: #1a2744; line-height: 1.2; }
.stat-box .l { font-size: 0.68rem; color: #64748b; text-transform: uppercase; letter-spacing: 0.5px; }

.cls-path-wrapper { margin-bottom: 18px; }
.cls-path-label {
    font-size: 0.68rem; font-weight: 700; text-transform: uppercase;
    letter-spacing: 0.7px; color: #64748b; margin-bottom: 7px;
}
.cls-path {
    background: #1a2744; border-radius: 9px; padding: 12px 16px;
    display: flex; flex-wrap: wrap; align-items: center; gap: 4px;
}
.cls-path .crumb {
    background: rgba(255,255,255,0.1); border-radius: 5px;
    padding: 4px 12px; font-size: 0.83rem; font-weight: 600;
    color: rgba(255,255,255,0.65);
}
.cls-path .crumb.active { background: white; color: #1a2744; }
.cls-path .sep { color: rgba(255,255,255,0.3); font-size: 1.1rem; padding: 0 2px; }

/* Question text: Latvian + English */
.var-question-lv {
    font-size: 1.25rem; font-weight: 700; color: #1a2744;
    margin-bottom: 4px; line-height: 1.4;
}
.var-question-en {
    font-size: 0.97rem; font-weight: 400; color: #3d5a80;
    font-style: italic; margin-bottom: 10px; line-height: 1.4;
    padding-left: 3px; border-left: 3px solid #b8c8e8;
    padding-left: 10px;
}
.var-ids { font-size: 0.8rem; color: #64748b; margin-bottom: 16px; }

.badge { display: inline-block; border-radius: 20px; padding: 3px 11px;
         font-size: 0.71rem; font-weight: 600; margin-left: 6px; }
.badge-self   { background: #dbeafe; color: #1e40af; }
.badge-doctor { background: #dcfce7; color: #166534; }

.participant-banner {
    background: linear-gradient(90deg, #0d7377 0%, #14a085 100%);
    border-radius: 9px; padding: 14px 20px; margin-bottom: 16px;
    display: flex; align-items: center; gap: 18px; flex-wrap: wrap;
}
.participant-banner .big-n {
    font-size: 2.1rem; font-weight: 900; color: white; line-height: 1;
}
.participant-banner .p-label {
    font-size: 0.78rem; color: rgba(255,255,255,0.78); margin-top: 2px;
}
.participant-banner .divider {
    width: 1px; height: 40px; background: rgba(255,255,255,0.25);
}
.survey-pill {
    background: rgba(255,255,255,0.15); border-radius: 20px;
    padding: 4px 12px; font-size: 0.74rem; color: white; font-weight: 600;
}

.survey-coverage-grid {
    display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 16px;
}
.survey-box {
    border-radius: 8px; padding: 10px 16px; min-width: 120px; text-align: center;
    border: 1px solid #e2e8f0;
}
.survey-box.active { background: #f0fdf4; border-color: #86efac; }
.survey-box.inactive { background: #f8fafc; border-color: #e2e8f0; opacity: 0.5; }
.survey-box .sv-name { font-size: 0.75rem; font-weight: 700; color: #374151; }
.survey-box .sv-n { font-size: 1.1rem; font-weight: 800; color: #166534; }
.survey-box .sv-label { font-size: 0.65rem; color: #64748b; }

/* Visit boxes */
.visit-grid { display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 16px; }
.visit-box {
    border-radius: 8px; padding: 10px 18px; min-width: 110px; text-align: center;
    border: 1px solid #e2e8f0; background: #f0fdf4; border-color: #86efac;
}
.visit-box.inactive { background: #f8fafc; border-color: #e2e8f0; opacity: 0.45; }
.visit-box .vb-label { font-size: 0.72rem; font-weight: 700; color: #374151; }
.visit-box .vb-sub   { font-size: 0.62rem; color: #64748b; margin-top: 2px; }

.info-section {
    background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 9px;
    padding: 14px 18px; margin-bottom: 12px;
}
.info-section h5 {
    font-size: 0.68rem; font-weight: 700; text-transform: uppercase;
    letter-spacing: 0.6px; color: #94a3b8; margin: 0 0 10px 0;
}
.info-row { display: flex; gap: 6px; font-size: 0.83rem; margin-bottom: 5px; color: #374151; }
.info-label { color: #94a3b8; min-width: 118px; font-size: 0.78rem; flex-shrink: 0; }

.visit-notice {
    background: #fefce8; border: 1px solid #fde047; border-radius: 8px;
    padding: 10px 14px; font-size: 0.8rem; color: #713f12; margin-bottom: 14px;
}
.visit-2-notice {
    background: #eff6ff; border: 1px solid #93c5fd; border-radius: 8px;
    padding: 10px 14px; font-size: 0.8rem; color: #1e3a5f; margin-bottom: 14px;
}

.no-data-notice {
    background: #f0f9ff; border: 1px solid #bae6fd; border-radius: 8px;
    padding: 10px 14px; font-size: 0.8rem; color: #0c4a6e; margin-bottom: 14px;
}

.empty { text-align: center; padding: 60px 0; color: #94a3b8; font-size: 0.95rem; }
section[data-testid="stSidebar"] { background: #f8fafc; }
</style>
""", unsafe_allow_html=True)


# ── Data loading ───────────────────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def load_data():
    for path in [
        Path(__file__).parent / "enriched_catalogue_369_v3.json",
        Path("/mnt/user-data/outputs/enriched_catalogue_369_v3.json"),
        Path(__file__).parent / "enriched_catalogue_369_v2.json",
        Path("/mnt/user-data/outputs/enriched_catalogue_369_v2.json"),
    ]:
        if path.exists():
            with open(path, encoding="utf-8") as f:
                return json.load(f)
    return []


# ── Helpers ────────────────────────────────────────────────────────────────
def path_html(path_str: str) -> str:
    if not path_str:
        return ""
    crumbs = [c.strip() for c in path_str.split(">")]
    parts = []
    for i, c in enumerate(crumbs):
        css = "crumb active" if i == len(crumbs) - 1 else "crumb"
        if i > 0:
            parts.append('<span class="sep">›</span>')
        parts.append(f'<span class="{css}">{c}</span>')
    return f"""
    <div class="cls-path-wrapper">
      <div class="cls-path-label">Classification Path</div>
      <div class="cls-path">{"".join(parts)}</div>
    </div>"""


def provenance_badge(prov: str) -> str:
    css = "badge-doctor" if "doctor" in prov.lower() else "badge-self"
    return f'<span class="badge {css}">{prov}</span>'


def search_match(rec: dict, q: str) -> bool:
    if not q:
        return True
    q = q.lower()
    return any(q in str(rec.get(f, "")).lower() for f in [
        "harmonized_variable_name", "question_text", "question_text_en",
        "level_0", "level_1", "level_2", "level_3", "field_id",
    ])


# ── Bar chart ──────────────────────────────────────────────────────────────
def make_bar_chart(ans_dist: dict, question_text: str) -> go.Figure | None:
    if not ans_dist:
        return None
    clean = {k: v for k, v in ans_dist.items() if k.strip() != question_text.strip()}
    if not clean:
        clean = ans_dist
    items = sorted(clean.items(), key=lambda x: -x[1])[:10]
    if not items:
        return None
    labels = [str(k)[:50] + ("…" if len(str(k)) > 50 else "") for k, _ in items]
    counts = [v for _, v in items]
    total  = sum(counts)
    fig = go.Figure(go.Bar(
        x=counts, y=labels, orientation='h',
        marker_color='#0d7377', marker_line_color='#0a5e62', marker_line_width=0.5,
        text=[f"  {c:,}  ({c/total*100:.1f}%)" for c in counts],
        textposition='outside', cliponaxis=False,
    ))
    fig.update_layout(
        margin=dict(l=10, r=140, t=8, b=8),
        height=max(200, 44 * len(items)),
        xaxis=dict(title="Number of responses", showgrid=True, gridcolor='#f1f5f9',
                   tickformat=',', zeroline=False),
        yaxis=dict(autorange='reversed', tickfont=dict(size=11), tickcolor='#64748b'),
        plot_bgcolor='white', paper_bgcolor='white',
        font=dict(family='Inter, sans-serif', size=11, color='#374151'),
        showlegend=False,
    )
    return fig


# ── Survey coverage grid ───────────────────────────────────────────────────
ALL_SURVEYS = [
    ("VIGDB",       "VIGDB",       "Main questionnaire"),
    ("VIGDB_OM",    "VIGDB_OM",    "Extended form"),
    ("VIGDB_SHORT", "VIGDB_SHORT", "Short form"),
    ("MICROBIOM",   "MICROBIOM",   "Microbiome sub-study"),
]

def survey_coverage_html(survey_coverage: dict) -> str:
    boxes = []
    for sv_key, sv_label, sv_desc in ALL_SURVEYS:
        n = survey_coverage.get(sv_key)
        if n:
            boxes.append(
                f'<div class="survey-box active">'
                f'<div class="sv-name">{sv_label}</div>'
                f'<div class="sv-n">{n:,}</div>'
                f'<div class="sv-label">{sv_desc}</div>'
                f'</div>'
            )
        else:
            boxes.append(
                f'<div class="survey-box inactive">'
                f'<div class="sv-name">{sv_label}</div>'
                f'<div class="sv-n">—</div>'
                f'<div class="sv-label">{sv_desc}</div>'
                f'</div>'
            )
    return f'<div class="survey-coverage-grid">{"".join(boxes)}</div>'


def visit_coverage_html(has_visit_2: bool) -> str:
    """Render visit 1 / visit 2 boxes. Visit 1 is always active."""
    v1 = (
        '<div class="visit-box">'
        '<div class="vb-label">Visit 1</div>'
        '<div class="vb-sub">Baseline (all participants)</div>'
        '</div>'
    )
    if has_visit_2:
        v2 = (
            '<div class="visit-box">'
            '<div class="vb-label">Visit 2</div>'
            '<div class="vb-sub">Follow-up (subset)</div>'
            '</div>'
        )
    else:
        v2 = (
            '<div class="visit-box inactive">'
            '<div class="vb-label">Visit 2</div>'
            '<div class="vb-sub">No follow-up data</div>'
            '</div>'
        )
    return f'<div class="visit-grid">{v1}{v2}</div>'


# ══════════════════════════════════════════════════════════════════
# Main app
# ══════════════════════════════════════════════════════════════════

with st.spinner("Loading catalogue…"):
    records = load_data()

df = pd.DataFrame(records)

total_participants = 45651
total_responses    = 5995947
n_surveys          = 4

# ── Portal header ──────────────────────────────────────────────────────────
st.markdown(f"""
<div class="portal-header">
  <div>
    <div class="brand">🧬 NIRI DATA PORTAL</div>
    <div class="tagline">National Institute of Research Innovation</div>
  </div>
  <div class="subtitle">Research Data Showcase</div>
</div>
""", unsafe_allow_html=True)

st.markdown(f"""
<div class="stats-row">
  <div class="stat-box"><div class="n">{len(records):,}</div><div class="l">Data Fields</div></div>
  <div class="stat-box"><div class="n">{df['level_0'].nunique() if 'level_0' in df.columns else 8}</div><div class="l">Domains</div></div>
  <div class="stat-box"><div class="n">{df['level_1'].nunique() if 'level_1' in df.columns else 15}</div><div class="l">Subdomains</div></div>
  <div class="stat-box"><div class="n">{total_participants:,}</div><div class="l">Participants</div></div>
  <div class="stat-box"><div class="n">{total_responses:,}</div><div class="l">Total Responses</div></div>
  <div class="stat-box"><div class="n">{n_surveys}</div><div class="l">Surveys</div></div>
</div>
""", unsafe_allow_html=True)


# ── Sidebar filters ────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🔎 Search & Filter")

    search = st.text_input(
        "Search", placeholder="Keyword, variable name, field ID, question text…",
        label_visibility="collapsed"
    )

    st.markdown("**Data Provenance**")
    all_prov = sorted(df["data_provenance"].dropna().unique()) if "data_provenance" in df.columns else []
    sel_prov = st.multiselect("Provenance", all_prov, default=all_prov, label_visibility="collapsed")

    st.markdown("**Domain**")
    all_domains = sorted(df["level_0"].dropna().unique()) if "level_0" in df.columns else []
    sel_domains = st.multiselect("Domain", all_domains, default=all_domains, label_visibility="collapsed")

    st.markdown("**Subdomain**")
    avail_sub = sorted(
        df[df["level_0"].isin(sel_domains)]["level_1"].dropna().unique()
    ) if "level_1" in df.columns else []
    sel_sub = st.multiselect("Subdomain", avail_sub, default=avail_sub, label_visibility="collapsed")

    st.markdown("**Survey**")
    sv_options = ["VIGDB", "VIGDB_OM", "VIGDB_SHORT", "MICROBIOM", "(no named survey)"]
    sel_surveys = st.multiselect("Survey", sv_options, default=sv_options, label_visibility="collapsed")

    st.markdown("**Visit**")
    visit_filter = st.radio(
        "Visit", ["All visits", "Visit 1 only", "Has Visit 2"],
        label_visibility="collapsed"
    )

    st.markdown("**Source Form**")
    all_forms = sorted(df["source_form"].dropna().unique()) if "source_form" in df.columns else []
    sel_forms = st.multiselect("Form", all_forms, label_visibility="collapsed", placeholder="All forms")

    st.divider()
    st.caption(
        "NIRI · Data Portal v3.0 · Phase 3\n"
        "Participant count: 45,651 unique individuals (by TRC code)\n"
        "Visit 1 = baseline for all participants.\n"
        "Visit 2 = follow-up; 236 records across 5 fields."
    )


# ── Apply filters ──────────────────────────────────────────────────────────
def passes_survey_filter(rec, sel_surveys):
    named = rec.get('surveys_present', [])
    for sv in ["VIGDB", "VIGDB_OM", "VIGDB_SHORT", "MICROBIOM"]:
        if sv in sel_surveys and sv in named:
            return True
    cov = rec.get('survey_coverage', {})
    if "(no named survey)" in sel_surveys and '' in cov:
        return True
    return False

filtered = []
for r in records:
    if sel_prov and r.get("data_provenance") not in sel_prov:
        continue
    if sel_domains and r.get("level_0") not in sel_domains:
        continue
    if sel_sub and r.get("level_1") not in sel_sub:
        continue
    if sel_forms and r.get("source_form") not in sel_forms:
        continue
    if not passes_survey_filter(r, sel_surveys):
        continue
    if not search_match(r, search):
        continue
    # Visit filter
    if visit_filter == "Visit 1 only" and r.get('has_visit_2'):
        continue
    if visit_filter == "Has Visit 2" and not r.get('has_visit_2'):
        continue
    filtered.append(r)

filtered.sort(key=lambda r: (
    r.get("level_0",""), r.get("level_1",""),
    r.get("level_2",""), r.get("level_3",""),
    r.get("harmonized_variable_name","")
))


# ── Two-column layout ──────────────────────────────────────────────────────
left, right = st.columns([1, 2], gap="large")

with left:
    n = len(filtered)
    st.markdown(f"**{n:,}** field{'s' if n != 1 else ''} found")

    if n == 0:
        st.markdown('<div class="empty">No results — adjust your filters.</div>',
                    unsafe_allow_html=True)
        selected = None
    else:
        option_labels = []
        for r in filtered:
            named = r.get('surveys_present', [])
            en = r.get('question_text_en', '')
            display_text = en if en else r.get('question_text', '')
            label = (
                f"{r.get('field_id','?')}  ·  "
                f"{r.get('harmonized_variable_name','')}  —  "
                f"{display_text[:50]}"
                f"{'…' if len(display_text) > 50 else ''}"
            )
            option_labels.append(label)

        chosen_idx = st.selectbox(
            "Select a field →",
            range(len(option_labels)),
            format_func=lambda i: option_labels[i],
        )
        selected = filtered[chosen_idx]
        st.caption(f"All {n:,} fields have real participant data from the production database.")


# ── Detail panel ───────────────────────────────────────────────────────────
with right:
    if not filtered or selected is None:
        st.markdown(
            '<div class="empty" style="padding-top:80px">'
            '🧬<br><br>Select a field from the list to explore its data.</div>',
            unsafe_allow_html=True
        )
    else:
        r = selected
        prov          = r.get("data_provenance", "")
        total_p       = r.get("total_participants") or r.get("n_participants")
        n_resp        = r.get("n_responses")
        ans_dist      = r.get("answer_distribution", {})
        survey_cov    = r.get("survey_coverage", {})
        named_surveys = r.get("surveys_present", [])
        question_lv   = r.get("question_text", "—")
        question_en   = r.get("question_text_en", "")
        has_visit_2   = r.get("has_visit_2", False)

        # ── Field heading: Latvian + English ──
        en_block = (
            f'<div class="var-question-en">🇬🇧 {question_en}</div>'
            if question_en else ""
        )
        st.markdown(f"""
        <div class="var-question-lv">🇱🇻 {question_lv}</div>
        {en_block}
        <div class="var-ids">
          <strong>Field ID:</strong> {r.get('field_id','—')} &nbsp;·&nbsp;
          <strong>DB Question ID:</strong> {r.get('question_id_db','—')} &nbsp;·&nbsp;
          <strong>Variable:</strong> {r.get('harmonized_variable_name','—')}
          {provenance_badge(prov)}
        </div>
        """, unsafe_allow_html=True)

        # ── Participant banner ──
        if total_p:
            pct_of_cohort = total_p / total_participants * 100
            surveys_pills = "".join(
                f'<span class="survey-pill">{sv}</span>' for sv in named_surveys
            ) if named_surveys else '<span class="survey-pill" style="background:rgba(255,255,255,0.1)">no survey tag</span>'

            st.markdown(f"""
            <div class="participant-banner">
              <div>
                <div class="big-n">{total_p:,}</div>
                <div class="p-label">Participants with data</div>
              </div>
              <div class="divider"></div>
              <div>
                <div class="big-n" style="font-size:1.6rem">{pct_of_cohort:.1f}%</div>
                <div class="p-label">of total cohort</div>
              </div>
              <div class="divider"></div>
              <div>
                <div class="big-n" style="font-size:1.6rem">{n_resp:,}</div>
                <div class="p-label">Total responses</div>
              </div>
              <div class="divider"></div>
              <div style="display:flex;gap:6px;flex-wrap:wrap;align-items:center">
                {surveys_pills}
              </div>
            </div>
            """, unsafe_allow_html=True)

        # ── Visit coverage ──
        st.markdown("##### Visit Coverage")
        st.markdown(visit_coverage_html(has_visit_2), unsafe_allow_html=True)

        if has_visit_2:
            st.markdown(
                '<div class="visit-2-notice">ℹ️ This field has data from <strong>both visits</strong>. '
                'All participants have at least a <strong>Visit 1</strong> (baseline) record. '
                'A subset also has a <strong>Visit 2</strong> (follow-up) record in the production database.</div>',
                unsafe_allow_html=True)
        else:
            st.markdown(
                '<div class="no-data-notice">ℹ️ <strong>Visit 1 only.</strong> '
                'All records for this field are from the baseline assessment. '
                'No follow-up (Visit 2) records exist in the production data.</div>',
                unsafe_allow_html=True)

        # ── Survey coverage grid ──
        st.markdown("##### Survey Coverage")
        if r.get('survey_coverage_note'):
            st.caption(f"⚠ {r['survey_coverage_note']}")
        if named_surveys and "MICROBIOM" in named_surveys and len(named_surveys) == 1:
            st.markdown(
                '<div class="visit-notice">⚠ This field is exclusive to the <strong>MICROBIOM sub-study</strong> '
                '(~943 participants).</div>',
                unsafe_allow_html=True)
        st.markdown(survey_coverage_html(survey_cov), unsafe_allow_html=True)

        # ── Classification path ──
        st.markdown(path_html(r.get("improved_classification_path", "")), unsafe_allow_html=True)

        # ── Answer distribution chart ──
        if ans_dist:
            fig = make_bar_chart(ans_dist, question_lv)
            if fig:
                st.markdown("##### Answer Distribution")
                st.plotly_chart(fig, use_container_width=True,
                                config={'displayModeBar': False})

                with st.expander("View full coding table", expanded=False):
                    clean = {k: v for k, v in ans_dist.items()
                             if k.strip() != question_lv.strip()}
                    if not clean:
                        clean = ans_dist
                    total_ans = sum(clean.values())
                    dist_df = pd.DataFrame(
                        [(k, f"{v:,}", f"{v/total_ans*100:.1f}%")
                         for k, v in sorted(clean.items(), key=lambda x: -x[1])],
                        columns=["Answer", "Count", "Percent"]
                    )
                    st.dataframe(dist_df, use_container_width=True, hide_index=True)
            else:
                st.info("This is a continuous/numeric field — individual values are stored rather than coded answer options.")
        else:
            st.info("No answer distribution available for this field in the current export.")

        # ── Metadata cards ──
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"""
            <div class="info-section">
              <h5>🗂 Classification</h5>
              <div class="info-row"><span class="info-label">Domain</span>{r.get('level_0','—')}</div>
              <div class="info-row"><span class="info-label">Subdomain</span>{r.get('level_1','—')}</div>
              <div class="info-row"><span class="info-label">Group</span>{r.get('level_2','—')}</div>
              <div class="info-row"><span class="info-label">Variable class</span>{r.get('level_3','—')}</div>
              <div class="info-row"><span class="info-label">Category ID</span>{r.get('category_id','—')}</div>
            </div>
            """, unsafe_allow_html=True)
        with c2:
            visit_summary = "Visit 1 (baseline) + Visit 2 (follow-up)" if has_visit_2 else "Visit 1 (baseline)"
            st.markdown(f"""
            <div class="info-section">
              <h5>📋 Data Source</h5>
              <div class="info-row"><span class="info-label">Provenance</span>{prov}</div>
              <div class="info-row"><span class="info-label">Collection</span>{r.get('collection_method','—')}</div>
              <div class="info-row"><span class="info-label">Data source</span>{r.get('data_source','—')}</div>
              <div class="info-row"><span class="info-label">Source form</span>{r.get('source_form_label') or r.get('source_form','—')}</div>
              <div class="info-row"><span class="info-label">Visit(s)</span>{visit_summary}</div>
            </div>
            """, unsafe_allow_html=True)
