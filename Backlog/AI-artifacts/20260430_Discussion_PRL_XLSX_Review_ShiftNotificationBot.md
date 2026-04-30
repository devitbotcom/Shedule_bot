# Discussion — PRL & XLSX Source Review
**Date:** 2026-04-30  
**Role:** Architect  
**Status:** ⏳ Q10–Q17 answered. Q16 (header names) pending Owner confirmation.  
**Context:** Pre-S003 review. Before Telegram adapter sprint begins, Owner and Architect reviewed the original PRL and the actual `Apr.xlsx` file together. Six open questions emerged from reading primary sources rather than derived ARCH artifacts. All six must be answered before S003 scope is locked.

---

## What Was Reviewed

- `Backlog/2026-04-05_01-PRL` — original product requirements letter
- `Backlog/Apr.xlsx` — real schedule file (April 2026, the actual input data)
- `Backlog/shifts-Duty_Shift_Schema__24h__Night__Default_Day_.png` — shift type diagram
- `Backlog/shifts.puml` — shift sequence source

---

## Discussion

### Q10 — Shift type determination *(assigned to: Owner)*

The PRL text states:
- Monday–Friday → Night shift, 24h
- Saturday, Sunday → Day shift, 2h

The shift diagram (`shifts.puml`) shows **three** types:

| Type | Ukrainian | Hours |
|---|---|---|
| Денний | Day | 09:00–17:00 |
| Нічний | Night | 17:00–09:00 |
| Добовий | 24h | 09:00–09:00 |

These two sources contradict each other. The PRL implies only two types and "2h" matches none of the diagram times.

**Questions for Owner:**
- Which three types from the diagram are correct?
- How does the system know which type applies to a given date — purely day-of-week, or is there another rule?
- What does "2h" in the PRL refer to — is it a typo or a different concept?

**Answer:** 
- all 3 exist: Day, Night, 24h.
- Most crucial. We have holidays and normal days. So when it is normal day we have day+night. When it is normal Friday we have day + 24h begins. When it is Saturday or Sunday we have 24h. 
Maybe we need to add a column that indicates labour / holiday for simplicity in our current MVP.
- "2h"  is it a typo yes.





---

### Q11 — Are Ургенція staff notified? *(assigned to: Owner)*

The PRL lists the Ургенція block (column K, home call specialists) under **Inputs**, but never states whether the system sends them a notification message.

The main grid staff (cols A–J) clearly receive a message with duty, date, prev/next colleague.  
Ургенція staff have a different structure — they are assigned by specialty and day list, with no prev/next colleague concept.

**Questions for Owner:**
- Do Ургенція specialists receive a notification at all?
- If yes — what does their message contain? (They have no prev/next shift colleague.)
- If no — is the Ургенція block parsed only for reference, or ignored entirely?

**Answer:** *(Owner to complete)*
- It is for notification, but I want make it after all our notification system POC deployed and we have feedback. 

---

### Q12 — Ургенція entries with no days listed *(assigned to: Owner)*

Several entries in column K have a name but no day assignment:

```
Аносова М.В.        (under Ендокринологи)
Мельник В.П.        (under Ендокринологи)
Калініченко І.В.    (under Окуліст)
Андрющенко Н.О.     (under Інфекціоніст)
```

**Questions for Owner:**
- Are these specialists on duty for the **entire month** (permanent assignment)?
- Or is this a data entry issue in the XLSX?
- How should the parser treat them?

**Answer:**
- Now (POC) it is on hold. But see below. 
- All urgent doctors are 24h duty (for now). The format of each string is Name Initials Dates of duty e.g "Тищук І.О. 21,24" means Тищук І.О. has two 24h duties on April 21 and April 24
---

### Q13 — Employee registry location *(assigned to: Owner)*

The PRL states the employee registry (name, role, messenger, chat ID / phone) can be:
> "a separate sheet in the XLSX or a standalone file"

`Apr.xlsx` has only **one sheet** (Sheet1). There is no Sheet2 with messenger contact data.

The Sprint 002 ARCH was written assuming a Sheet2 would exist. This assumption is now unconfirmed.

**Questions for Owner:**
- Where does the messenger contact registry actually live?
- Will it be added as Sheet2 to the XLSX, or kept in a separate file?
- If a separate file — what format (CSV, JSON, another XLSX)?

**Answer:** 
We will need to define it. I recommend to make it not in Git. Maybe for POC we can settings file that IT will manually update on hosting side? 

---

### Q14 — Name spacing errors in XLSX grid *(assigned to: Owner)*

Several names in the schedule grid (cols A–J) have no space before initials:

```
КуліковськаК.В.    (col F, multiple rows)
ЦиганокІ.І.        (col F, multiple rows)
ДесікевичІ.С.      (col F)
ГурженкоО.Ю        (col F, also missing trailing dot)
ШумейкоО.І.        (col K)
```

These are different from correctly spaced names like `Єрема В.Р.` or `Марченко А.С.`

**Questions for Owner:**
- Is this normal in the real XLSX files (parser must tolerate it), or should the Schedule Manager correct the file before use?
- Must the parser match `КуліковськаК.В.` to the same person as `Куліковська К.В.` in the registry?

**Answer:** 
We need to make reasonable error check, so IT can fix this before submission. In POC we do not read live google-sheet.

---

### Q15 — Row 48 footnote — parser skip rule *(assigned to: Owner / confirmation)*

The last row of `Apr.xlsx` (row 48) contains a footnote in column B:

> *"2. Про зміни в ургенстві та місці перебування спеціалістів — завчасно повідомляти чергового лікаря"*

This is administrative text, not data. Column K of the same row contains `Тищук І.О. 10,20,24,27,29` (a valid Ургенція entry).

**Confirmation needed from Owner:**
- The parser should skip column B of row 48 (treat it as a footnote, not a staff name). Correct?
- Are there other footnote rows in other months' files, or is this a one-off?

**Answer:**
True, it is an administrative tex, an example on how source file looks in live. System needs to handle this with nonblocking warning but not fail. Perform basic logic and skip unknown.

---

## Architect Synthesis — Post-Owner Answers

### Decisions confirmed
| Q   | Decision                                                                                                                                                                               |
|-----|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Q10 | All 3 shift types confirmed. Rule: Mon–Thu = Day+Night; Friday = Day+24h begins; Sat/Sun/Holiday = 24h. Owner proposes a labour/holiday column in the XLSX for MVP — Architect agrees. |
| Q11 | Ургенція notifications deferred to post-POC. Column K is **not parsed and not notified** in S003/S004.                                                                                 |
| Q12 | Ургенція entry format confirmed: `Name Initials Days`. Names with no days = on hold. Irrelevant for POC given Q11 deferral.                                                            |
| Q13 | Employee registry: separate file on server, not in Git, manually maintained by IT Owner. Format to be decided (see micro-decision B below).                                            |
| Q14 | Parser validates name format and reports mismatches clearly so IT can fix the XLSX. Does not crash. Does not silently skip.                                                            |
| Q15 | Unexpected/footnote rows: skip with non-blocking warning. Graceful degradation is the rule across the board.                                                                           |

### Architectural impact
- `schedule_parser.py` does **not** read a Sheet2. It reads the grid by **header name only** — never by column index. Employee contact data is loaded from a separate `contacts.json`.
- A new env variable (`CONTACTS_PATH`) points to the contacts file on the server.
- `shift_logic.py` receives the day type (`labor` / `holiday` / `other`) from the parsed `Day-type` column — no calendar API needed.
- Column K (Ургенція) is ignored entirely in POC. Parser emits a non-blocking log note that it was skipped.
- The `Shift` data model remains valid but `messenger` and `contact_id` come from `contacts.json`, not the XLSX.
- The `Shift` data model gains a `day_type` field: `'labor'` | `'holiday'` | `'other'`.

---

## Remaining Micro-Decisions (assigned to: Owner)

### Decision A — Holiday column format in XLSX ✅ RESOLVED

**Answer (Owner):** Column "Day-type" added as new column A (all other columns shifted right). Values: `labor`, `holiday`, `other`.

**Architect note:** Parser must locate this column by header name `Day-type`, not by letter position — see Q16.

---

### Decision B — Contacts file format ✅ RESOLVED

**Answer (Owner):** JSON array. Each entry:
```json
[
  {
    "name": "Mihai Ionescu",
    "channels": { "telegram": "222456789" },
    "primary_channel": "telegram"
  }
]
```

**Architect note:** `name` value must match the name as it appears in the XLSX exactly (IT is responsible for keeping these in sync).

---

### Q16 — Column identification strategy *(assigned to: Architect → Owner confirmation)*

**Context:** Adding "Day-type" as a new column A shifted all original columns one position to the right. If `schedule_parser.py` identifies columns by letter/index (e.g. col 0 = date, col 1 = Приймальне відділення), any future column addition will silently break the parser.

**Architect decision:** Parser must identify all columns **by header name only**, never by index or letter.

On startup, `schedule_parser.py` reads row 6 (the header row), builds a name→index map, and uses that map for all subsequent reads. If a required header is missing, it logs the missing name and exits with code 1.

**Required headers the parser must find by name:**

| Header (as in XLSX) | Maps to |
|---|---|
| `Дата` | shift date |
| `Day-type` | day type (`labor` / `holiday` / `other`) |
| `Приймальне відділення` | department 1 |
| `Анестезіологія` | department 2 |
| `реанімація` | department 3 |
| `хірургія` | department 4 |
| `акушерство` | department 5 |
| `травматологія` | department 6 |
| `неврологія` | department 7 |
| `УЗД` | department 8 |
| `Дитяче відділення` | department 9 |

Column K (Акушер-гінекологи / Ургенція block) — ignored in POC.

**Benefit:** Schedule Manager or IT Owner can reorder or add columns freely without touching code.

**Owner confirmation needed:** Are the header names above exactly as they appear in the updated XLSX (case, spelling)?

**Answer:** Headers are stable — defined by the export format, not changed at runtime. IT validates the export matches; no IT-editable config file needed.

**Architect resolution:** Required header names (`Дата`, `Day-type`, and each department column) are defined as **constants in `schedule_parser.py`**. On startup the parser reads XLSX row 6, builds a name→index map, and exits 1 if any required header is absent. `Ургенція спеціалістів на дому` is not in the required list — parser logs INFO and skips it. ✅ CLOSED

---

### Q17 — Message content: one handover or both? *(assigned to: Owner)*

**Context:** The Development Plan and PRL both state the message shows the previous AND next shift colleague. The Owner has clarified the intent was to show **either** prev or next depending on whether the recipient is arriving or leaving their shift.

**The ambiguity:** Every person both arrives at and departs from their shift. The system sends one notification per shift. So the question is:

- **Option A — Show both handovers (original plan):**
  > You are taking over from: *Єрема В.Р. (Анестезіологія)*
  > You hand over to: *Марченко А.С. (Анестезіологія)*

- **Option B — Show only the incoming handover (you arrive, here is who you relieve):**
  > You are taking over from: *Єрема В.Р. (Анестезіологія)*

- **Option C — Show only the outgoing handover (you leave, here is who relieves you):**
  > You hand over to: *Марченко А.С. (Анестезіологія)*

- **Option D — Context by shift type:**
  Different shift types have different handover moments. E.g. for a Night shift the critical handover is who you receive from (at 17:00) and who you hand to (at 09:00 next day). Both matter.

**Architect view:** Option A (both) is the safest for POC — it requires no extra logic and gives staff the most complete picture. Options B/C require the system to know which direction matters most per shift type, which adds complexity.

**Owner decision needed:** Which option?

**Answer:** ✅ Option A. Message template:

```
Зміна: {date}
{staff_name} заступає на зміну замість {previous_staff_name}.

Наступна зміна:
{next_date} о {next_time} — {next_staff_name}

```

**[RED FLAG] — Confirmation button conflicts with one-shot architecture:**  
Telegram inline button callbacks require the bot to receive events (webhook or polling — both are persistent processes). Namecheap kills persistent processes. This is architecturally incompatible with the cron-only design.

**Architect resolution for POC:**  
- POC sends plain text message only — no button.  
- Staff reply manually with a text message (e.g. "✅") if confirmation is wanted.  
- Confirmation button is scoped to **post-POC** when a persistent process or webhook relay is available.  
- PRL already marks confirmation as *Optional* — this is consistent.

**Owner confirmation needed:** Accept plain text for POC, confirmation button post-POC?

**Answer:** ✅ Button in a further sprint. POC = plain text only.

---

## Blocking Status

✅ **S003 scope is now locked.** Q16 closed — header names are export-format constants, no Owner confirmation of individual names required.

**Next steps for Architect:**
1. Revise the Sprint 002 ARCH (Sheet2 assumption corrected; column strategy updated; message template and date format added)
2. Update the Sprint Plan
3. Produce the S003 ARCH artifact
