"""
Builds the updated Summa Theologica dashboard HTML.
Embeds question text data as a JS constant, wires up IndexedDB population
on first load, and adds a reading panel that renders question text on chip click.
"""

import json, re, os

OUT_DIR = '/sessions/eager-nice-cori/mnt/outputs/'
ARTIFACT_PATH = '/sessions/eager-nice-cori/mnt/Claude/Artifacts/summa-study-dashboard/index.html'

# Load and minify the JSON data
with open(OUT_DIR + 'pp_questions.json') as f:
    pp_data = json.load(f)
with open(OUT_DIR + 'ps_questions.json') as f:
    ps_data = json.load(f)

# Minify: compact JSON, no indent
pp_json = json.dumps(pp_data, ensure_ascii=False, separators=(',', ':'))
ps_json = json.dumps(ps_data, ensure_ascii=False, separators=(',', ':'))

print(f'PP JSON size: {len(pp_json)/1024:.1f} KB')
print(f'PS JSON size: {len(ps_json)/1024:.1f} KB')

# Build the HTML
html = r"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Summa Theologica — Study Dashboard</title>
  <style>
    :root {
      color-scheme: light;
      --bg: #faf8f3;
      --surface: #ffffff;
      --surface-alt: #f5f0e8;
      --border: #d4c9a8;
      --accent: #7a2b2b;
      --accent-light: #a34040;
      --gold: #c9a84c;
      --gold-light: #e8d49a;
      --text: #2c2416;
      --text-muted: #6b5d3f;
      --text-light: #9b8e6e;
      --explored: #2d6a4f;
      --explored-bg: #d8f3dc;
      --current-bg: #fde8e8;
      --treatise-bg: #f0ebe0;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: 'Georgia', serif; background: var(--bg); color: var(--text); min-height: 100vh; }

    /* ── Header ── */
    .header { background: var(--accent); color: white; padding: 18px 24px 14px; border-bottom: 3px solid var(--gold); }
    .header-top { display: flex; justify-content: space-between; align-items: flex-start; }
    .header h1 { font-size: 1.3rem; font-weight: normal; letter-spacing: 0.04em; line-height: 1.3; }
    .header h1 span { display: block; font-size: 0.82rem; color: var(--gold-light); font-style: italic; margin-top: 2px; }
    .header-date { font-size: 0.78rem; color: var(--gold-light); font-style: italic; text-align: right; }
    .db-status { font-size: 0.72rem; color: var(--gold-light); font-style: italic; margin-top: 3px; text-align: right; }

    /* ── Tabs ── */
    .tab-nav { display: flex; background: var(--surface-alt); border-bottom: 2px solid var(--border); padding: 0 18px; gap: 2px; }
    .tab-btn { background: none; border: none; border-bottom: 3px solid transparent; padding: 9px 14px; font-family: Georgia, serif; font-size: 0.82rem; color: var(--text-muted); cursor: pointer; margin-bottom: -2px; transition: all 0.15s; }
    .tab-btn:hover { color: var(--accent); }
    .tab-btn.active { color: var(--accent); border-bottom-color: var(--accent); font-weight: bold; }

    /* ── Layout ── */
    .main { padding: 18px; max-width: 860px; margin: 0 auto; }
    .tab-panel { display: none; }
    .tab-panel.active { display: block; }

    /* ── Progress ── */
    .progress-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; margin-bottom: 18px; }
    .progress-card { background: var(--surface); border: 1px solid var(--border); border-radius: 6px; padding: 14px 16px; }
    .progress-card h3 { font-size: 0.85rem; color: var(--accent); letter-spacing: 0.05em; text-transform: uppercase; margin-bottom: 4px; }
    .vol-subtitle { font-size: 0.72rem; color: var(--text-light); font-style: italic; margin-bottom: 10px; }
    .progress-bar-wrap { background: var(--border); border-radius: 20px; height: 7px; margin-bottom: 5px; overflow: hidden; }
    .progress-bar-fill { height: 100%; background: linear-gradient(90deg, var(--accent), var(--gold)); border-radius: 20px; transition: width 0.4s ease; }
    .progress-label { font-size: 0.75rem; color: var(--text-muted); }
    .progress-label strong { color: var(--accent); }

    /* ── Focus card ── */
    .focus-card { background: var(--surface); border: 1px solid var(--border); border-left: 4px solid var(--accent); border-radius: 6px; padding: 14px 18px; margin-bottom: 18px; }
    .focus-card h3 { font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.08em; color: var(--text-light); margin-bottom: 5px; }
    .focus-title { font-size: 1rem; color: var(--accent); margin-bottom: 3px; }
    .focus-meta { font-size: 0.78rem; color: var(--text-muted); font-style: italic; }

    /* ── Generic panel ── */
    .panel { background: var(--surface); border: 1px solid var(--border); border-radius: 6px; padding: 16px 18px; margin-bottom: 18px; }
    .panel h3 { font-size: 0.82rem; color: var(--accent); letter-spacing: 0.05em; text-transform: uppercase; margin-bottom: 12px; padding-bottom: 8px; border-bottom: 1px solid var(--border); }

    /* ── Question grid ── */
    .treatise-section { margin-bottom: 22px; }
    .treatise-header { font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.09em; color: var(--text-light); border-bottom: 1px solid var(--border); padding-bottom: 5px; margin-bottom: 9px; }
    .questions-grid { display: flex; flex-wrap: wrap; gap: 5px; }
    .q-chip { width: 36px; height: 36px; border-radius: 4px; display: flex; align-items: center; justify-content: center; font-size: 0.73rem; font-family: Georgia, serif; cursor: pointer; border: 1px solid var(--border); background: var(--surface); color: var(--text-muted); transition: all 0.15s; position: relative; }
    .q-chip:hover { border-color: var(--accent); color: var(--accent); transform: scale(1.1); z-index: 1; }
    .q-chip.explored { background: var(--explored-bg); border-color: var(--explored); color: var(--explored); font-weight: bold; }
    .q-chip.current { background: var(--current-bg); border-color: var(--accent); color: var(--accent); font-weight: bold; box-shadow: 0 0 0 2px var(--accent); }
    .q-chip.has-notes::after { content: '•'; position: absolute; top: 0px; right: 2px; font-size: 11px; color: var(--gold); }

    /* ── Legend ── */
    .legend { display: flex; gap: 14px; margin-bottom: 14px; flex-wrap: wrap; }
    .legend-item { display: flex; align-items: center; gap: 5px; font-size: 0.73rem; color: var(--text-muted); }
    .legend-dot { width: 13px; height: 13px; border-radius: 3px; border: 1px solid; }

    /* ── Notes ── */
    .note-entry { background: var(--surface-alt); border: 1px solid var(--border); border-radius: 4px; padding: 10px 12px; margin-bottom: 9px; }
    .note-entry .note-meta { font-size: 0.7rem; color: var(--text-light); margin-bottom: 5px; display: flex; justify-content: space-between; }
    .note-entry .note-text { font-size: 0.83rem; color: var(--text); line-height: 1.5; padding-left: 10px; }
    .note-type-quote { border-left: 3px solid var(--gold); }
    .note-type-note { border-left: 3px solid var(--accent); }
    .delete-btn { background: none; border: none; color: var(--text-light); cursor: pointer; font-size: 0.72rem; padding: 0 3px; }
    .delete-btn:hover { color: #c0392b; }

    /* ── Forms ── */
    .add-form { background: var(--treatise-bg); border: 1px solid var(--border); border-radius: 5px; padding: 14px; margin-top: 12px; }
    .add-form h4 { font-size: 0.76rem; color: var(--text-muted); margin-bottom: 9px; text-transform: uppercase; letter-spacing: 0.06em; }
    .form-row { display: flex; gap: 7px; margin-bottom: 7px; flex-wrap: wrap; }
    .form-row select, .form-row input { font-family: Georgia, serif; font-size: 0.8rem; padding: 5px 9px; border: 1px solid var(--border); border-radius: 4px; background: white; color: var(--text); }
    .form-row textarea { width: 100%; font-family: Georgia, serif; font-size: 0.82rem; padding: 7px 9px; border: 1px solid var(--border); border-radius: 4px; background: white; color: var(--text); resize: vertical; min-height: 65px; }
    .btn { background: var(--accent); color: white; border: none; padding: 6px 14px; border-radius: 4px; font-family: Georgia, serif; font-size: 0.8rem; cursor: pointer; transition: background 0.15s; }
    .btn:hover { background: var(--accent-light); }
    .btn-sm { padding: 4px 10px; font-size: 0.76rem; }

    /* ── Session log ── */
    .session-entry { border-bottom: 1px solid var(--border); padding: 10px 0; }
    .session-entry:last-child { border-bottom: none; }
    .session-date { font-size: 0.72rem; color: var(--text-light); font-style: italic; margin-bottom: 3px; }
    .session-q { font-size: 0.85rem; color: var(--accent); margin-bottom: 2px; }
    .session-note { font-size: 0.8rem; color: var(--text-muted); }

    /* ── Misc ── */
    .empty-state { text-align: center; padding: 24px; color: var(--text-light); font-style: italic; font-size: 0.82rem; }
    .section-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
    .section-title { font-size: 0.95rem; color: var(--accent); padding-bottom: 6px; border-bottom: 1px solid var(--border); flex: 1; }

    /* ── Reading Panel (slide-in from right) ── */
    .reading-overlay {
      position: fixed; top: 0; right: -100%; width: 50%; max-width: 600px; min-width: 340px;
      height: 100vh; background: var(--surface); border-left: 2px solid var(--border);
      box-shadow: -4px 0 20px rgba(0,0,0,0.12); z-index: 100;
      transition: right 0.3s ease; display: flex; flex-direction: column;
    }
    .reading-overlay.open { right: 0; }
    .reading-header {
      background: var(--accent); color: white; padding: 14px 18px;
      border-bottom: 2px solid var(--gold); flex-shrink: 0;
      display: flex; justify-content: space-between; align-items: flex-start;
    }
    .reading-header-text { flex: 1; }
    .reading-q-label { font-size: 0.72rem; color: var(--gold-light); letter-spacing: 0.08em; text-transform: uppercase; margin-bottom: 3px; }
    .reading-q-title { font-size: 1rem; font-weight: normal; line-height: 1.3; }
    .reading-close {
      background: none; border: none; color: var(--gold-light); cursor: pointer;
      font-size: 1.3rem; padding: 0 0 0 12px; line-height: 1; flex-shrink: 0;
    }
    .reading-close:hover { color: white; }
    .reading-toolbar {
      background: var(--surface-alt); border-bottom: 1px solid var(--border);
      padding: 8px 14px; display: flex; gap: 8px; align-items: center; flex-shrink: 0;
    }
    .reading-body {
      flex: 1; overflow-y: auto; padding: 20px 22px;
      font-size: 0.88rem; line-height: 1.8; color: var(--text);
    }
    .reading-body .q-section-title {
      font-size: 1.05rem; color: var(--accent); font-variant: small-caps;
      letter-spacing: 0.04em; margin-bottom: 6px; margin-top: 24px;
    }
    .reading-body .q-article-header {
      font-size: 0.78rem; color: var(--text-light); letter-spacing: 0.06em;
      margin-bottom: 4px; margin-top: 20px;
    }
    .reading-body .q-article-title {
      font-size: 0.95rem; color: var(--accent-light); font-style: italic;
      margin-bottom: 10px;
    }
    .reading-body .q-objection { color: var(--text-muted); margin-bottom: 8px; }
    .reading-body .q-answer { margin-bottom: 8px; }
    .reading-body .q-separator { border: none; border-top: 1px solid var(--border); margin: 16px 0; }
    .reading-body pre { white-space: pre-wrap; font-family: Georgia, serif; font-size: 0.88rem; line-height: 1.8; }
    .loading-text { color: var(--text-light); font-style: italic; text-align: center; padding: 40px; }
  </style>
</head>
<body>

<div class="header">
  <div class="header-top">
    <h1>Summa Theologica <span>Study Dashboard — St. Thomas Aquinas</span></h1>
    <div>
      <div class="header-date" id="headerDate"></div>
      <div class="db-status" id="dbStatus">Initializing...</div>
    </div>
  </div>
</div>

<div class="tab-nav">
  <button class="tab-btn active" onclick="switchTab('overview')">Overview</button>
  <button class="tab-btn" onclick="switchTab('prima-pars')">Prima Pars</button>
  <button class="tab-btn" onclick="switchTab('prima-secundae')">Prima Secundae</button>
  <button class="tab-btn" onclick="switchTab('notes')">Notes & Quotes</button>
  <button class="tab-btn" onclick="switchTab('log')">Session Log</button>
</div>

<div class="main">

  <!-- OVERVIEW -->
  <div class="tab-panel active" id="tab-overview">
    <div class="progress-grid">
      <div class="progress-card">
        <h3>Prima Pars · Part I</h3>
        <div class="vol-subtitle">God · Trinity · Creation · Angels · Man · Divine Government</div>
        <div class="progress-bar-wrap"><div class="progress-bar-fill" id="pp-bar" style="width:0%"></div></div>
        <div class="progress-label"><strong id="pp-count">0</strong> of 119 Questions explored</div>
      </div>
      <div class="progress-card">
        <h3>Prima Secundae · Part I-II</h3>
        <div class="vol-subtitle">Happiness · Will · Passions · Virtue · Sin · Law · Grace</div>
        <div class="progress-bar-wrap"><div class="progress-bar-fill" id="ps-bar" style="width:0%"></div></div>
        <div class="progress-label"><strong id="ps-count">0</strong> of 114 Questions explored</div>
      </div>
    </div>
    <div class="focus-card">
      <h3>Currently Exploring</h3>
      <div class="focus-title" id="focusTitle">No question selected</div>
      <div class="focus-meta" id="focusMeta">Select a question from the Prima Pars or Prima Secundae tab</div>
    </div>
    <div class="panel">
      <h3>Recent Notes & Quotes</h3>
      <div id="recentNotes"></div>
    </div>
  </div>

  <!-- PRIMA PARS -->
  <div class="tab-panel" id="tab-prima-pars">
    <div class="section-header">
      <div class="section-title">Prima Pars — 119 Questions</div>
      <button class="btn btn-sm" style="margin-left:12px;" onclick="markExplored('pp')">✓ Mark Current as Explored</button>
    </div>
    <div class="legend">
      <div class="legend-item"><div class="legend-dot" style="background:#fde8e8;border-color:#7a2b2b;"></div>Currently Reading</div>
      <div class="legend-item"><div class="legend-dot" style="background:#d8f3dc;border-color:#2d6a4f;"></div>Explored</div>
      <div class="legend-item"><div class="legend-dot" style="background:white;border-color:#d4c9a8;"></div>Not yet visited</div>
      <div class="legend-item"><span style="color:#c9a84c;font-size:1rem;line-height:1;">•</span>&nbsp;Has notes</div>
    </div>
    <div id="ppTreatises"></div>
  </div>

  <!-- PRIMA SECUNDAE -->
  <div class="tab-panel" id="tab-prima-secundae">
    <div class="section-header">
      <div class="section-title">Prima Secundae — 114 Questions</div>
      <button class="btn btn-sm" style="margin-left:12px;" onclick="markExplored('ps')">✓ Mark Current as Explored</button>
    </div>
    <div class="legend">
      <div class="legend-item"><div class="legend-dot" style="background:#fde8e8;border-color:#7a2b2b;"></div>Currently Reading</div>
      <div class="legend-item"><div class="legend-dot" style="background:#d8f3dc;border-color:#2d6a4f;"></div>Explored</div>
      <div class="legend-item"><div class="legend-dot" style="background:white;border-color:#d4c9a8;"></div>Not yet visited</div>
      <div class="legend-item"><span style="color:#c9a84c;font-size:1rem;line-height:1;">•</span>&nbsp;Has notes</div>
    </div>
    <div id="psTreatises"></div>
  </div>

  <!-- NOTES -->
  <div class="tab-panel" id="tab-notes">
    <div class="panel">
      <h3>All Notes & Quotes</h3>
      <div id="allNotes"></div>
      <div class="add-form">
        <h4>Add a Note or Quote</h4>
        <div class="form-row">
          <select id="noteVol"><option value="pp">Prima Pars</option><option value="ps" selected>Prima Secundae</option></select>
          <input type="number" id="noteQ" placeholder="Q. number" min="1" max="119" style="width:95px;">
          <select id="noteType"><option value="quote">Quote</option><option value="note">Note</option></select>
        </div>
        <div class="form-row"><textarea id="noteText" placeholder="Enter quote or note..."></textarea></div>
        <button class="btn" onclick="addNote()">Save</button>
      </div>
    </div>
  </div>

  <!-- SESSION LOG -->
  <div class="tab-panel" id="tab-log">
    <div class="panel">
      <h3>Session Log</h3>
      <div id="sessionLog"></div>
      <div class="add-form" style="margin-top:14px;">
        <h4>Log a Session</h4>
        <div class="form-row">
          <select id="logVol"><option value="pp">Prima Pars</option><option value="ps" selected>Prima Secundae</option></select>
          <input type="number" id="logQ" placeholder="Q. number" min="1" max="119" style="width:105px;">
        </div>
        <div class="form-row"><textarea id="logNote" placeholder="Session notes (optional)..."></textarea></div>
        <button class="btn" onclick="logSession()">Log Session</button>
      </div>
    </div>
  </div>

</div>

<!-- READING PANEL -->
<div class="reading-overlay" id="readingPanel">
  <div class="reading-header">
    <div class="reading-header-text">
      <div class="reading-q-label" id="readingLabel">Prima Secundae</div>
      <div class="reading-q-title" id="readingTitle">Question</div>
    </div>
    <button class="reading-close" onclick="closeReading()">✕</button>
  </div>
  <div class="reading-toolbar">
    <button class="btn btn-sm" onclick="markExploredFromPanel()">✓ Mark as Explored</button>
    <button class="btn btn-sm" onclick="openAddNoteFromPanel()" style="background:var(--gold);color:var(--text);">+ Add Note</button>
  </div>
  <div class="reading-body" id="readingBody">
    <div class="loading-text">Loading...</div>
  </div>
</div>

<script>
// ═══════════════════════════════════════════════════════════════════════════
// EMBEDDED TEXT DATA
// ═══════════════════════════════════════════════════════════════════════════
const SUMMA_DATA = {
  pp: PP_JSON_PLACEHOLDER,
  ps: PS_JSON_PLACEHOLDER
};

// ═══════════════════════════════════════════════════════════════════════════
// STRUCTURE DATA
// ═══════════════════════════════════════════════════════════════════════════
const PP_TREATISES = [
  { name:'Treatise on God', qs:[1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26] },
  { name:'Treatise on the Trinity', qs:[27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43] },
  { name:'Treatise on the Creation', qs:[44,45,46,47,48,49] },
  { name:'Treatise on the Angels', qs:[50,51,52,53,54,55,56,57,58,59,60,61,62,63,64] },
  { name:'Treatise on the Work of the Six Days', qs:[65,66,67,68,69,70,71,72,73,74] },
  { name:'Treatise on Man', qs:[75,76,77,78,79,80,81,82,83,84,85,86,87,88,89,90,91,92,93,94,95,96,97,98,99,100,101,102] },
  { name:'Treatise on the Divine Government', qs:[103,104,105,106,107,108,109,110,111,112,113,114,115,116,117,118,119] }
];
const PS_TREATISES = [
  { name:'Treatise on Happiness & Human Acts', qs:[1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21] },
  { name:'Treatise on the Passions', qs:[22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48] },
  { name:'Treatise on Habits', qs:[49,50,51,52,53,54,55,56,57,58,59,60,61,62,63,64,65,66,67,68,69,70] },
  { name:'Treatise on Vice and Sin', qs:[71,72,73,74,75,76,77,78,79,80,81,82,83,84,85,86,87,88,89] },
  { name:'Treatise on Law', qs:[90,91,92,93,94,95,96,97,98,99,100,101,102,103,104,105,106,107,108] },
  { name:'Treatise on Grace', qs:[109,110,111,112,113,114] }
];
const PP_TITLES = {1:'The Nature and Extent of Sacred Doctrine',2:'The Existence of God',3:'On the Simplicity of God',4:'The Perfection of God',5:'Of Goodness in General',6:'The Goodness of God',7:'The Infinity of God',8:'The Existence of God in Things',9:'The Immutability of God',10:'The Eternity of God',11:'The Unity of God',12:'How God Is Known by Us',13:'The Names of God',14:"Of God's Knowledge",15:'Of Ideas',16:'Of Truth',17:'Concerning Falsity',18:'The Life of God',19:'The Will of God',20:"God's Love",21:'The Justice and Mercy of God',22:'The Providence of God',23:'Of Predestination',24:'The Book of Life',25:'The Power of God',26:'Of the Divine Beatitude',27:'The Procession of the Divine Persons',28:'The Divine Relations',29:'The Divine Persons',30:'The Plurality of Persons in God',31:'Of What Belongs to the Unity or Plurality in God',32:'The Knowledge of the Divine Persons',33:'Of the Person of the Father',34:'Of the Person of the Son',35:'Of the Image',36:'Of the Person of the Holy Ghost',37:'Of the Name of the Holy Ghost—Love',38:'Of the Name of the Holy Ghost, as Gift',39:'Of the Persons in Relation to the Essence',40:'Of the Persons as Compared to the Relations or Properties',41:'Of the Persons in Reference to the Notional Acts',42:'Of Equality and Likeness Among the Divine Persons',43:'The Mission of the Divine Persons',44:'The Procession of Creatures from God',45:'The Mode of Emanation of Things from the First Principle',46:'Of the Beginning of the Duration of Creatures',47:'Of the Distinction of Things in General',48:'The Distinction of Things in Particular',49:'The Cause of Evil',50:'Of the Substance of the Angels Absolutely Considered',51:'Of the Angels in Comparison with Bodies',52:'Of the Angels in Relation to Place',53:'Of the Local Movement of the Angels',54:'Of the Knowledge of the Angels',55:'Of the Medium of the Angelic Knowledge',56:"Of the Angels' Knowledge of Immaterial Things",57:"Of the Angels' Knowledge of Material Things",58:'Of the Mode of the Angelic Knowledge',59:'The Will of the Angels',60:'Of the Love or Dilection of the Angels',61:'Of the Production of the Angels in the Order of Natural Being',62:'Of the Perfection of the Angels in the Order of Grace and of Glory',63:'The Malice of the Angels with Regard to Sin',64:'The Punishment of the Demons',65:'The Work of Creation of Corporeal Creatures',66:'On the Order of Creation Towards Distinction',67:'On the Work of Distinction in Itself',68:'On the Work of the Second Day',69:'On the Work of the Third Day',70:'On the Work of Adornment, as Regards the Fourth Day',71:'On the Work of the Fifth Day',72:'On the Work of the Sixth Day',73:'On the Things That Belong to the Seventh Day',74:'On All the Seven Days in Common',75:'Of Man Who Is Composed of a Spiritual and a Corporeal Substance',76:'Of the Union of Body and Soul',77:'Of Those Things Which Belong to the Powers of the Soul in General',78:'Of the Specific Powers of the Soul',79:'Of the Intellectual Powers',80:'Of the Appetitive Powers in General',81:'Of the Power of Sensuality',82:'Of the Will',83:'Of Free-Will',84:'How the Soul While United to the Body Understands Corporeal Things Beneath It',85:'Of the Mode and Order of Understanding',86:'What Our Intellect Knows in Material Things',87:'How the Intellectual Soul Knows Itself and All Within Itself',88:'How the Human Soul Knows What Is Above Itself',89:'Of the Knowledge of the Separated Soul',90:"Of the First Production of Man's Soul",91:"The Production of the First Man's Body",92:'The Production of the Woman',93:'The End or Term of the Production of Man',94:'Of the State and Condition of the First Man as Regards His Intellect',95:"Of Things Pertaining to the First Man's Will—Namely, Grace and Righteousness",96:'Of the Mastership Belonging to Man in the State of Innocence',97:'Of the Preservation of the Individual in the Primitive State',98:'Of the Preservation of the Species',99:'Of the Condition of the Offspring As to the Body',100:'Of the Condition of the Offspring As Regards Righteousness',101:'Of the Condition of the Offspring As Regards Knowledge',102:"Of Man's Abode, Which Is Paradise",103:'Of the Government of Things in General',104:'The Special Effects of the Divine Government',105:'Of the Change of Creatures by God',106:'How One Creature Moves Another',107:'The Speech of the Angels',108:'Of the Angelic Degrees of Hierarchies and Orders',109:'The Ordering of the Bad Angels',110:'How Angels Act on Bodies',111:'The Action of the Angels on Man',112:'The Mission of the Angels',113:'Of the Guardianship of the Good Angels',114:'Of the Assaults of the Demons',115:'Of the Action of the Corporeal Creature',116:'On Fate',117:'Of Things Pertaining to the Action of Man',118:'Of the Production of Man from Man As to the Soul',119:'Of the Propagation of Man As to the Body'};
const PS_TITLES = {1:"Of Man's Last End",2:"Of Those Things in Which Man's Happiness Consists",3:'What Is Happiness',4:'Of Those Things That Are Required for Happiness',5:'Of the Attainment of Happiness',6:'Of the Voluntary and the Involuntary',7:'Of the Circumstances of Human Acts',8:'Of the Will, in Regard to What It Wills',9:'Of That Which Moves the Will',10:'Of the Manner in Which the Will Is Moved',11:'Of Enjoyment, Which Is an Act of the Will',12:'Of Intention',13:'Of Choice, Which Is an Act of the Will with Regard to the Means',14:'Of Counsel, Which Precedes Choice',15:'Of Consent, Which Is an Act of the Will in Regard to the Means',16:'Of Use, Which Is an Act of the Will in Regard to the Means',17:'Of the Acts Commanded by the Will',18:'Of the Good and Evil of Human Acts, in General',19:'Of the Goodness and Malice of the Interior Act of the Will',20:'Of Goodness and Malice in External Human Actions',21:'Of the Consequences of Human Actions by Reason of Their Goodness and Malice',22:"Of the Subject of the Soul's Passions",23:'How the Passions Differ from One Another',24:'Of Good and Evil in the Passions of the Soul',25:'Of the Order of the Passions to One Another',26:'Of the Passions of the Soul in Particular: and First, of Love',27:'Of the Cause of Love',28:'Of the Effects of Love',29:'Of Hatred',30:'Of Concupiscence',31:'Of Delight Considered in Itself',32:'Of the Cause of Pleasure',33:'Of the Effects of Pleasure',34:'Of the Goodness and Malice of Pleasures',35:'Of Pain or Sorrow, in Itself',36:'Of the Causes of Sorrow or Pain',37:'Of the Effects of Pain or Sorrow',38:'Of the Remedies of Sorrow or Pain',39:'Of the Goodness and Malice of Sorrow or Pain',40:'Of the Irascible Passions, and First, of Hope and Despair',41:'Of Fear, in Itself',42:'Of the Object of Fear',43:'Of the Cause of Fear',44:'Of the Effects of Fear',45:'Of Daring',46:'Of Anger, in Itself',47:'Of the Cause That Provokes Anger, and of the Remedies of Anger',48:'Of the Effects of Anger',49:'Of Habits in General, As to Their Substance',50:'Of the Subject of Habits',51:'Of the Cause of Habits, As to Their Formation',52:'Of the Increase of Habits',53:'How Habits Are Corrupted or Diminished',54:'Of the Distinction of Habits',55:'Of the Virtues, As to Their Essence',56:'Of the Subject of Virtue',57:'Of the Intellectual Virtues',58:'Of the Difference Between Moral and Intellectual Virtues',59:'Of the Moral Virtues in Relation to the Passions',60:'How the Moral Virtues Differ from One Another',61:'Of the Cardinal Virtues',62:'Of the Theological Virtues',63:'Of the Cause of Virtues',64:'Of the Mean of Virtue',65:'Of the Connection of Virtues',66:'Of Equality Among the Virtues',67:'Of the Duration of Virtues After This Life',68:'Of the Gifts',69:'Of the Beatitudes',70:'Of the Fruits of the Holy Ghost',71:'Of Vice and Sin Considered in Themselves',72:'Of the Distinction of Sins',73:'Of the Comparison of One Sin with Another',74:'Of the Subject of Sin',75:'Of the Causes of Sin, in General',76:'Of the Causes of Sin, in Particular',77:'Of the Cause of Sin, on the Part of the Sensitive Appetite',78:'Of That Cause of Sin Which Is Malice',79:'Of the External Causes of Sin',80:'Of the Cause of Sin, As Regards the Devil',81:'Of the Cause of Sin, on the Part of Man',82:'Of Original Sin, As to Its Essence',83:'Of the Subject of Original Sin',84:'Of the Cause of Sin, in Respect of One Sin Being the Cause of Another',85:'Of the Effects of Sin, and First, of the Corruption of the Good of Nature',86:'Of the Stain of Sin',87:'Of the Debt of Punishment',88:'Of Venial and Mortal Sin',89:'Of Venial Sin in Itself',90:'Of the Essence of Law',91:'Of the Various Kinds of Law',92:'Of the Effects of Law',93:'Of the Eternal Law',94:'Of the Natural Law',95:'Of Human Law',96:'Of the Power of Human Law',97:'Of Change in Laws',98:'Of the Old Law',99:'Of the Precepts of the Old Law',100:'Of the Moral Precepts of the Old Law',101:'Of the Ceremonial Precepts in Themselves',102:'Of the Causes of the Ceremonial Precepts',103:'Of the Duration of the Ceremonial Precepts',104:'Of the Judicial Precepts',105:'Of the Reason for the Judicial Precepts',106:'Of the Law of the Gospel, Called the New Law, Considered in Itself',107:'Of the New Law As Compared with the Old',108:'Of Those Things That Are Contained in the New Law',109:'Of the Necessity of Grace',110:'Of the Grace of God as Regards Its Essence',111:'Of the Division of Grace',112:'Of the Cause of Grace',113:'Of the Effects of Grace',114:'Of Merit'};

// ═══════════════════════════════════════════════════════════════════════════
// INDEXEDDB
// ═══════════════════════════════════════════════════════════════════════════
const DB_NAME = 'summa_texts';
const DB_VERSION = 1;
let db = null;

function openDB() {
  return new Promise((resolve, reject) => {
    const req = indexedDB.open(DB_NAME, DB_VERSION);

    // Called when DB is first created or version changes
    req.onupgradeneeded = (e) => {
      const database = e.target.result;
      if (!database.objectStoreNames.contains('pp')) {
        database.createObjectStore('pp', { keyPath: 'q' });
      }
      if (!database.objectStoreNames.contains('ps')) {
        database.createObjectStore('ps', { keyPath: 'q' });
      }
    };

    req.onsuccess = (e) => { resolve(e.target.result); };
    req.onerror   = (e) => { reject(e.target.error); };
  });
}

function countRecords(database, storeName) {
  return new Promise((resolve, reject) => {
    const tx = database.transaction(storeName, 'readonly');
    const req = tx.objectStore(storeName).count();
    req.onsuccess = () => resolve(req.result);
    req.onerror   = () => reject(req.error);
  });
}

function populateStore(database, storeName, data) {
  return new Promise((resolve, reject) => {
    const tx = database.transaction(storeName, 'readwrite');
    const store = tx.objectStore(storeName);
    Object.entries(data).forEach(([k, v]) => {
      store.put({ q: parseInt(k), text: v });
    });
    tx.oncomplete = resolve;
    tx.onerror    = (e) => reject(e.target.error);
  });
}

async function initDB() {
  setStatus('Opening database...');
  db = await openDB();

  const ppCount = await countRecords(db, 'pp');
  const psCount = await countRecords(db, 'ps');

  // Only populate if stores are empty (first load)
  if (ppCount < 119) {
    setStatus('Populating Prima Pars texts (first load only)...');
    await populateStore(db, 'pp', SUMMA_DATA.pp);
  }
  if (psCount < 114) {
    setStatus('Populating Prima Secundae texts (first load only)...');
    await populateStore(db, 'ps', SUMMA_DATA.ps);
  }

  const finalPP = await countRecords(db, 'pp');
  const finalPS = await countRecords(db, 'ps');
  setStatus(`Text database ready (${finalPP} + ${finalPS} questions)`);
}

function getQuestion(vol, q) {
  return new Promise((resolve, reject) => {
    const tx = db.transaction(vol, 'readonly');
    const req = tx.objectStore(vol).get(q);
    req.onsuccess = () => resolve(req.result ? req.result.text : null);
    req.onerror   = () => reject(req.error);
  });
}

function setStatus(msg) {
  const el = document.getElementById('dbStatus');
  if (el) el.textContent = msg;
}

// ═══════════════════════════════════════════════════════════════════════════
// READING PANEL
// ═══════════════════════════════════════════════════════════════════════════
let readingVol = null, readingQ = null;

async function openReading(vol, q) {
  readingVol = vol; readingQ = q;
  const titles = vol === 'pp' ? PP_TITLES : PS_TITLES;
  const volLabel = vol === 'pp' ? 'Prima Pars' : 'Prima Secundae';

  document.getElementById('readingLabel').textContent = `${volLabel} · Question ${q}`;
  document.getElementById('readingTitle').textContent = titles[q] || '';
  document.getElementById('readingBody').innerHTML = '<div class="loading-text">Loading from database...</div>';
  document.getElementById('readingPanel').classList.add('open');

  try {
    const text = await getQuestion(vol, q);
    if (text) {
      document.getElementById('readingBody').innerHTML = formatQuestionText(text);
    } else {
      document.getElementById('readingBody').innerHTML = '<div class="loading-text">Text not found.</div>';
    }
  } catch(e) {
    document.getElementById('readingBody').innerHTML = `<div class="loading-text">Error: ${e.message}</div>`;
  }
}

function closeReading() {
  document.getElementById('readingPanel').classList.remove('open');
}

function formatQuestionText(raw) {
  // Render the plain text with basic structure highlighting
  const escaped = raw
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');

  const lines = escaped.split('\n');
  let html = '';

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i].trim();
    if (!line) { html += '<br>'; continue; }

    // Article citation header e.g. FIRST ARTICLE [I-II, Q. 1, Art. 1]
    if (/^(FIRST|SECOND|THIRD|FOURTH|FIFTH|SIXTH|SEVENTH|EIGHTH|NINTH|TENTH)\s+ARTICLE/.test(line)) {
      html += `<div class="q-article-header">${line}</div>`;
    }
    // Article question title (line after article header that starts with "Whether")
    else if (/^Whether\s/.test(line) && i > 0 && /ARTICLE/.test(lines[i-1]||'')) {
      html += `<div class="q-article-title">${line}</div>`;
    }
    // Separator lines
    else if (/^[_\-]{5,}$/.test(line)) {
      html += '<hr class="q-separator">';
    }
    // Objection lines
    else if (/^Obj\.\s+\d+:/.test(line) || /^Objection\s+\d+:/.test(line)) {
      html += `<div class="q-objection">${line}</div>`;
    }
    // Reply lines
    else if (/^Reply\s+Obj\./.test(line)) {
      html += `<div class="q-objection">${line}</div>`;
    }
    // "I answer that"
    else if (/^I answer that/.test(line)) {
      html += `<div class="q-answer"><strong>I answer that,</strong> ${line.replace(/^I answer that,\s*/,'')}</div>`;
    }
    // "On the contrary"
    else if (/^On the contrary/.test(line)) {
      html += `<div class="q-answer"><em>On the contrary,</em> ${line.replace(/^On the contrary,\s*/,'')}</div>`;
    }
    // ALL CAPS lines (titles, section headers)
    else if (line === line.toUpperCase() && line.length > 3 && !/^\(/.test(line) && !/^\[/.test(line)) {
      html += `<div class="q-section-title">${line}</div>`;
    }
    else {
      html += `<div>${line}</div>`;
    }
  }
  return html;
}

function markExploredFromPanel() {
  if (!readingVol || !readingQ) return;
  state.current = { vol: readingVol, q: readingQ };
  if (!state.explored[readingVol].includes(readingQ)) {
    state.explored[readingVol].push(readingQ);
  }
  saveState(state); render();
}

function openAddNoteFromPanel() {
  if (!readingVol || !readingQ) return;
  document.getElementById('noteVol').value = readingVol;
  document.getElementById('noteQ').value = readingQ;
  closeReading();
  switchTab('notes');
}

// ═══════════════════════════════════════════════════════════════════════════
// STUDY STATE (localStorage)
// ═══════════════════════════════════════════════════════════════════════════
function getState() {
  const def = { current:{vol:'ps',q:1}, explored:{pp:[],ps:[1]}, notes:[], sessions:[] };
  try { const s = localStorage.getItem('summa_v2'); return s ? {...def,...JSON.parse(s)} : def; }
  catch(e) { return def; }
}
function saveState(s) { try { localStorage.setItem('summa_v2', JSON.stringify(s)); } catch(e){} }
let state = getState();

// ═══════════════════════════════════════════════════════════════════════════
// RENDER
// ═══════════════════════════════════════════════════════════════════════════
function render() {
  document.getElementById('headerDate').textContent = new Date().toLocaleDateString('en-US',{weekday:'long',year:'numeric',month:'long',day:'numeric'});
  const ppc = state.explored.pp.length, psc = state.explored.ps.length;
  document.getElementById('pp-count').textContent = ppc;
  document.getElementById('ps-count').textContent = psc;
  document.getElementById('pp-bar').style.width = (ppc/119*100)+'%';
  document.getElementById('ps-bar').style.width = (psc/114*100)+'%';
  const {vol,q} = state.current;
  const T = vol==='pp'?PP_TITLES:PS_TITLES;
  const vl = vol==='pp'?'Prima Pars':'Prima Secundae';
  document.getElementById('focusTitle').textContent = `Q. ${q} — ${T[q]||''}`;
  document.getElementById('focusMeta').textContent = `${vl} · Click any question chip to open its text`;
  renderGrid('pp', PP_TREATISES, 'ppTreatises', PP_TITLES);
  renderGrid('ps', PS_TREATISES, 'psTreatises', PS_TITLES);
  renderNotesList('allNotes', [...state.notes].reverse(), true);
  renderNotesList('recentNotes', [...state.notes].slice(-3).reverse(), false);
  renderLog();
}

function renderGrid(vol, treatises, cid, titles) {
  const c = document.getElementById(cid); c.innerHTML='';
  treatises.forEach(t => {
    const sec = document.createElement('div'); sec.className='treatise-section';
    const hdr = document.createElement('div'); hdr.className='treatise-header';
    hdr.textContent = `${t.name} (QQ. ${t.qs[0]}–${t.qs[t.qs.length-1]})`;
    sec.appendChild(hdr);
    const grid = document.createElement('div'); grid.className='questions-grid';
    t.qs.forEach(q => {
      const chip = document.createElement('div'); chip.className='q-chip';
      chip.textContent = q; chip.title = `Q. ${q} — ${titles[q]||''} (click to read)`;
      if (state.current.vol===vol && state.current.q===q) chip.classList.add('current');
      else if (state.explored[vol].includes(q)) chip.classList.add('explored');
      if (state.notes.some(n=>n.vol===vol&&n.q===q)) chip.classList.add('has-notes');
      // Click now opens the reading panel
      chip.onclick = () => {
        state.current = {vol, q};
        saveState(state);
        render();
        openReading(vol, q);
      };
      grid.appendChild(chip);
    });
    sec.appendChild(grid); c.appendChild(sec);
  });
}

function renderNotesList(cid, notes, showDelete) {
  const c = document.getElementById(cid);
  if (!notes.length) { c.innerHTML='<div class="empty-state">No notes yet.</div>'; return; }
  c.innerHTML='';
  notes.forEach((n,ri) => {
    const realIdx = showDelete ? (state.notes.length-1-ri) : -1;
    const T = n.vol==='pp'?PP_TITLES:PS_TITLES;
    const vl = n.vol==='pp'?'Prima Pars':'Prima Secundae';
    const el = document.createElement('div'); el.className='note-entry';
    el.innerHTML=`<div class="note-meta"><span>${vl} · Q.${n.q} — ${(T[n.q]||'').substring(0,38)}… · <em>${n.type==='quote'?'Quote':'Note'}</em> · ${n.date}</span>${showDelete?`<button class="delete-btn" onclick="deleteNote(${realIdx})">✕</button>`:''}</div><div class="note-text note-type-${n.type}">${n.type==='quote'?'"'+n.text+'"':n.text}</div>`;
    c.appendChild(el);
  });
}

function renderLog() {
  const c = document.getElementById('sessionLog');
  if (!state.sessions.length) { c.innerHTML='<div class="empty-state">No sessions logged yet.</div>'; return; }
  c.innerHTML='';
  [...state.sessions].reverse().forEach(s => {
    const T = s.vol==='pp'?PP_TITLES:PS_TITLES;
    const vl = s.vol==='pp'?'Prima Pars':'Prima Secundae';
    const el = document.createElement('div'); el.className='session-entry';
    el.innerHTML=`<div class="session-date">${s.date}</div><div class="session-q">${vl} · Q. ${s.q} — ${T[s.q]||''}</div>${s.note?`<div class="session-note">${s.note}</div>`:''}`;
    c.appendChild(el);
  });
}

// ═══════════════════════════════════════════════════════════════════════════
// ACTIONS
// ═══════════════════════════════════════════════════════════════════════════
function switchTab(name) {
  const tabs=['overview','prima-pars','prima-secundae','notes','log'];
  document.querySelectorAll('.tab-btn').forEach((b,i)=>b.classList.toggle('active',tabs[i]===name));
  document.querySelectorAll('.tab-panel').forEach(p=>p.classList.remove('active'));
  document.getElementById('tab-'+name).classList.add('active');
}

function markExplored(vol) {
  if (state.current.vol!==vol) { alert(`Current focus is on ${state.current.vol==='pp'?'Prima Pars':'Prima Secundae'}, not this volume.`); return; }
  const q = state.current.q;
  if (!state.explored[vol].includes(q)) { state.explored[vol].push(q); saveState(state); render(); }
}

function addNote() {
  const vol=document.getElementById('noteVol').value;
  const q=parseInt(document.getElementById('noteQ').value);
  const type=document.getElementById('noteType').value;
  const text=document.getElementById('noteText').value.trim();
  if (!q||!text) { alert('Please fill in question number and text.'); return; }
  state.notes.push({vol,q,type,text,date:new Date().toLocaleDateString('en-US',{month:'short',day:'numeric',year:'numeric'})});
  saveState(state);
  document.getElementById('noteText').value='';
  document.getElementById('noteQ').value='';
  render();
}

function deleteNote(i) {
  if (confirm('Delete this note?')) { state.notes.splice(i,1); saveState(state); render(); }
}

function logSession() {
  const vol=document.getElementById('logVol').value;
  const q=parseInt(document.getElementById('logQ').value);
  const note=document.getElementById('logNote').value.trim();
  if (!q) { alert('Please enter a question number.'); return; }
  state.sessions.push({vol,q,note,date:new Date().toLocaleDateString('en-US',{weekday:'short',month:'short',day:'numeric',year:'numeric'})});
  state.current={vol,q};
  if (!state.explored[vol].includes(q)) state.explored[vol].push(q);
  saveState(state);
  document.getElementById('logNote').value='';
  document.getElementById('logQ').value='';
  render();
}

// ═══════════════════════════════════════════════════════════════════════════
// INIT
// ═══════════════════════════════════════════════════════════════════════════
render();
initDB().catch(e => setStatus('DB error: ' + e.message));
</script>
</body>
</html>"""

# Inject the actual data
html = html.replace('PP_JSON_PLACEHOLDER', pp_json)
html = html.replace('PS_JSON_PLACEHOLDER', ps_json)

# Write to artifact path
os.makedirs(os.path.dirname(ARTIFACT_PATH), exist_ok=True)
with open(ARTIFACT_PATH, 'w', encoding='utf-8') as f:
    f.write(html)

size_mb = os.path.getsize(ARTIFACT_PATH) / (1024*1024)
print(f'Dashboard written to: {ARTIFACT_PATH}')
print(f'File size: {size_mb:.2f} MB')
print('Done.')
