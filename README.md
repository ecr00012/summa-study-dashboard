# Summa Theologica — Study Dashboard

An interactive, offline-first study tool for St. Thomas Aquinas's *Summa Theologica*, covering the **Prima Pars** (Part I, 119 Questions) and the **Prima Secundae** (Part I-II, 114 Questions).

**No installation. No server. No API calls.** Open `index.html` and start reading.

![Dashboard preview showing question grid and reading panel](https://img.shields.io/badge/Questions-233%20total-7a2b2b?style=flat-square) ![Offline](https://img.shields.io/badge/Works-Offline-2d6a4f?style=flat-square) ![No dependencies](https://img.shields.io/badge/Dependencies-None-c9a84c?style=flat-square)

---

## What it does

- **Full text, instant access.** Click any of the 233 question chips to open the full text of that question in a full-page reading panel — no loading, no network call, no waiting.
- **Progress tracking.** Mark questions as explored. Two progress bars show how far you've come in each volume.
- **Notes & Quotes.** Save direct quotes (gold-bordered) or your own notes (red-bordered), tied to a specific question and volume.
- **Session log.** Log each study session with optional notes. Sessions auto-mark questions as explored.
- **Persistent.** Everything — progress, notes, sessions, current reading position — is stored locally in your browser and survives page reloads and app restarts.

---

## How to use it

**Just open `index.html` in any modern browser.**

On first load, the app silently populates a local IndexedDB database with the full text of all 233 questions (drawn from the embedded data). A status line in the header shows when it's ready. Every subsequent load reads directly from that database — fast, local, offline.

### Navigation

| Action | Result |
|---|---|
| Click a question chip | Opens full-page reading panel |
| ✕ button | Closes reading panel, returns to dashboard |
| **✓ Mark as Explored** (in panel) | Marks question green in the grid |
| **+ Add Note** (in panel) | Jumps to Notes tab pre-filled with this question |
| Session Log tab | Log a completed session |

---

## Structure

```
index.html          ← Everything. Self-contained, ~5.6MB with embedded text.
README.md           ← This file.
extract_summa.py    ← How the question texts were extracted from the source epubs.
build_dashboard.py  ← How index.html was generated from the extracted data.
```

The Python scripts are included for transparency and reproducibility — you don't need to run them. `index.html` is the complete, ready-to-use artifact.

---

## Source text

The full text of the *Summa Theologica* comes from [Project Gutenberg](https://www.gutenberg.org/), which makes it freely available in the public domain:

- **Prima Pars:** [gutenberg.org/ebooks/17611](https://www.gutenberg.org/ebooks/17611)
- **Prima Secundae:** [gutenberg.org/ebooks/17897](https://www.gutenberg.org/ebooks/17897)

Translation by the Fathers of the English Dominican Province (Benziger Brothers edition).

The text is in the public domain. This dashboard and all original code are released under the [MIT License](LICENSE).

---

## Two known parsing anomalies

The source text is consistent across 231 of 233 questions. Two questions use non-standard headings (likely because they open treatises) and are handled explicitly in the extraction script:

- **Prima Pars Q. 116** ("On Fate") — heading is `ON FATE` rather than `QUESTION 116`
- **Prima Secundae Q. 1** ("Of Man's Last End") — heading is `OF MAN'S LAST END` rather than `QUESTION 1`

Both are extracted correctly in the final dashboard.

---

## Rebuilding from source

If you want to regenerate `index.html` from the original epub files:

1. Download the two epubs from Project Gutenberg (links above)
2. Place them in the same directory as the scripts
3. Update the file paths at the top of `extract_summa.py`
4. Run:
   ```bash
   python3 extract_summa.py    # produces pp_questions.json and ps_questions.json
   python3 build_dashboard.py  # produces index.html
   ```

---

## License

Original code (dashboard, extraction scripts): **MIT License** — use, modify, share freely.

Source text: **Public domain** (Project Gutenberg).
