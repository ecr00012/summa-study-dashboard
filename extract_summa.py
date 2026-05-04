"""
Summa Theologica — Question Text Extractor
Produces pp_questions.json and ps_questions.json.

Strategy:
- Most questions are delimited by lines matching exactly: QUESTION N
- Two known anomalies are handled explicitly:
    Prima Pars Q116:     heading is "ON FATE" (no QUESTION 116 line)
    Prima Secundae Q1:   heading is "OF MAN'S LAST END" (no QUESTION 1 line)
"""

import zipfile, re, json, os

# ── Paths ──────────────────────────────────────────────────────────────────
PP_EPUB   = '/sessions/eager-nice-cori/mnt/Claude/Books/Summa Theologica/Prima Pars.epub'
PS_DIR    = '/sessions/eager-nice-cori/mnt/Claude/Books/Summa Theologica/Summa Theologica, Part I-II (Pars Prima Secundae) : From the Complete American Edition.epub/OEBPS/'
OUT_DIR   = '/sessions/eager-nice-cori/mnt/outputs/'

# ── Helpers ────────────────────────────────────────────────────────────────

def clean_html(raw):
    """Strip tags and unescape common HTML entities."""
    text = re.sub(r'<[^>]+>', '', raw)
    text = text.replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&')
    text = text.replace('&nbsp;', ' ').replace('&#160;', ' ')
    return text

def clean_text(text):
    """Remove Project Gutenberg boilerplate header that appears at the top of each xhtml file."""
    lines = text.split('\n')
    # PG header is always the first 1-2 lines: "The Project Gutenberg eBook of..."
    cleaned = []
    skip = True
    for line in lines:
        if skip and line.strip().startswith('The Project Gutenberg'):
            continue
        if skip and re.match(r'^From the Complete American Edition', line.strip()):
            continue
        skip = False
        cleaned.append(line)
    return '\n'.join(cleaned)

def sort_key_pp(filename):
    """Sort Prima Pars files: 17611-0-0, 17611-0-1, ... 17611-0-14"""
    m = re.search(r'-0-(\d+)\.txt', filename)
    return int(m.group(1)) if m else 0

def sort_key_ps(filename):
    """Sort Prima Secundae files: 17897-0, 17897-1, ... 17897-14"""
    m = re.search(r'-(\d+)\.txt', filename)
    return int(m.group(1)) if m else 0

def split_on_questions(full_text, total_expected, volume_label):
    """
    Core splitter. Finds all QUESTION N boundaries, slices text between them.
    Returns dict: {question_number: text_block}
    """
    pattern = re.compile(r'(?m)^QUESTION\s+(\d+)\s*$')
    matches = list(pattern.finditer(full_text))

    questions = {}
    for i, match in enumerate(matches):
        q_num = int(match.group(1))
        start = match.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(full_text)
        questions[q_num] = full_text[start:end].strip()

    print(f'{volume_label}: found {len(questions)} questions via standard pattern')
    return questions

# ── Extract Prima Pars ─────────────────────────────────────────────────────

print('=== Extracting Prima Pars ===')

with zipfile.ZipFile(PP_EPUB, 'r') as z:
    xhtml_files = sorted(
        [f for f in z.namelist() if 'txt.xhtml' in f],
        key=sort_key_pp
    )
    print(f'Reading {len(xhtml_files)} files in order:')
    for f in xhtml_files:
        print(f'  {f.split("/")[-1]}')

    all_text_pp = ''
    for fname in xhtml_files:
        raw = z.read(fname).decode('utf-8')
        cleaned = clean_text(clean_html(raw))
        all_text_pp += cleaned + '\n'

pp_questions = split_on_questions(all_text_pp, 119, 'Prima Pars')

# ── Handle PP anomaly: Q116 "On Fate" ─────────────────────────────────────
if 116 not in pp_questions:
    print('  Handling anomaly: Q116 (ON FATE) — no standard QUESTION 116 header')
    # Find "ON FATE" section header, which immediately precedes Q116 content
    fate_match = re.search(r'(?m)^ON FATE\s*$', all_text_pp)
    q117_match = re.search(r'(?m)^QUESTION\s+117\s*$', all_text_pp)
    if fate_match and q117_match:
        pp_questions[116] = all_text_pp[fate_match.start():q117_match.start()].strip()
        print(f'  Q116 extracted: {len(pp_questions[116])} chars')
    else:
        print('  ERROR: Could not locate ON FATE or QUESTION 117 boundary')

# ── Verify Prima Pars ───��──────────────────────────────────────────────────
missing_pp = [q for q in range(1, 120) if q not in pp_questions]
print(f'\nVerification — Prima Pars:')
print(f'  Questions extracted: {len(pp_questions)}/119')
print(f'  Missing: {missing_pp if missing_pp else "None"}')
print(f'  Q1 chars: {len(pp_questions.get(1,""))}')
print(f'  Q116 chars: {len(pp_questions.get(116,""))}')
print(f'  Q119 chars: {len(pp_questions.get(119,""))}')

# ── Extract Prima Secundae ────────────────────���────────────────────────────

print('\n=== Extracting Prima Secundae ===')

ps_files = sorted(
    [f for f in os.listdir(PS_DIR) if 'txt.xhtml' in f],
    key=sort_key_ps
)
print(f'Reading {len(ps_files)} files in order:')
for f in ps_files:
    print(f'  {f}')

all_text_ps = ''
for fname in ps_files:
    with open(PS_DIR + fname, 'r') as f:
        raw = f.read()
    cleaned = clean_text(clean_html(raw))
    all_text_ps += cleaned + '\n'

ps_questions = split_on_questions(all_text_ps, 114, 'Prima Secundae')

# ── Handle PS anomaly: Q1 "Of Man's Last End" ─────────────────────────────
if 1 not in ps_questions:
    print("  Handling anomaly: Q1 (OF MAN'S LAST END) — no standard QUESTION 1 header")
    # Q1 starts at the Prologue section of Prima Secundae, just before "OF MAN'S LAST END"
    # We include the Prologue as part of Q1 since it introduces it
    prologue_match = re.search(r'(?m)^TREATISE ON THE LAST END', all_text_ps)
    q2_match = re.search(r'(?m)^QUESTION\s+2\s*$', all_text_ps)
    if prologue_match and q2_match:
        ps_questions[1] = all_text_ps[prologue_match.start():q2_match.start()].strip()
        print(f'  Q1 extracted: {len(ps_questions[1])} chars')
    else:
        print("  ERROR: Could not locate TREATISE ON THE LAST END or QUESTION 2 boundary")

# ── Verify Prima Secundae ──────────���───────────────────────────────────────
missing_ps = [q for q in range(1, 115) if q not in ps_questions]
print(f'\nVerification — Prima Secundae:')
print(f'  Questions extracted: {len(ps_questions)}/114')
print(f'  Missing: {missing_ps if missing_ps else "None"}')
print(f'  Q1 chars:  {len(ps_questions.get(1,""))}')
print(f'  Q2 chars:  {len(ps_questions.get(2,""))}')
print(f'  Q114 chars: {len(ps_questions.get(114,""))}')

# ── Spot-check: print first 300 chars of Q1 and Q116 ──────────────────────
print('\n--- PP Q1 preview ---')
print(pp_questions.get(1,'')[:300])
print('\n--- PP Q116 preview ---')
print(pp_questions.get(116,'')[:300])
print('\n--- PS Q1 preview ---')
print(ps_questions.get(1,'')[:300])

# ── Write JSON ─────────────────────────────────────────────────────────────
pp_path = OUT_DIR + 'pp_questions.json'
ps_path = OUT_DIR + 'ps_questions.json'

with open(pp_path, 'w') as f:
    json.dump({str(k): v for k, v in pp_questions.items()}, f, ensure_ascii=False, indent=2)

with open(ps_path, 'w') as f:
    json.dump({str(k): v for k, v in ps_questions.items()}, f, ensure_ascii=False, indent=2)

pp_size = os.path.getsize(pp_path) / 1024
ps_size = os.path.getsize(ps_path) / 1024
print(f'\n=== Output ===')
print(f'  pp_questions.json: {pp_size:.1f} KB')
print(f'  ps_questions.json: {ps_size:.1f} KB')
print(f'  Total: {pp_size + ps_size:.1f} KB')
print('\nDone.')
