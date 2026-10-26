# VERIFIERS — ตัวตรวจอัตโนมัติ

ทุกตัวอยู่ใน `verifiers/` ใช้แค่ Python stdlib กับ `jsonschema` (ถ้ามี `sympy` + `antlr4` จะใช้เทียบนิพจน์คณิตเชิงสัญลักษณ์เพิ่มได้ แต่ไม่บังคับ)
ทดสอบหน่วย: `python3 -m unittest discover -s verifiers/tests -t .` → **26 tests ผ่านทั้งหมด** (รันใน sandbox วันที่ 2026-10-26)

ตัวตรวจทุกตัว**เขียนขึ้นจากข้อกำหนดที่เปิดสาธารณะ** (รูปแบบ tool call ของ OpenAI/Hermes/Qwen, JSON Schema, ประเภท constraint แบบ IFEval, วิธีวัด execution accuracy แบบ Spider) ไม่มีข้อมูลเทรนฝังอยู่ในโค้ด

| ไฟล์ | ใช้กับ | ฟังก์ชันหลัก | หมายเหตุ / ข้อจำกัด |
|---|---|---|---|
| `toolcall.py` | หมวด B (FC), หมวด A (ตรวจราย step) | `score_calls(pred, gold, ordered=False, gold_alternatives=False)` คืนค่า `exact`, `name_f1`, `arg_accuracy`, `no_call_correct` · `validate_against_schema(call, tools)` | รับ call ได้ทุกรูปแบบ (OpenAI `tool_calls`, `{name,arguments}`, xLAM/BFCL `{fn:{args}}`, arguments ที่เป็น JSON string) · parallel ไม่สนลำดับ (greedy matching) · `"5"` = `5` · float tolerance 1e-6 · gold ว่างใช้ตรวจเคส "ไม่ควรเรียก tool" · `gold_alternatives` รองรับรายการคำตอบที่ยอมรับได้แบบ BFCL (`""` แปลว่าพารามิเตอร์นั้นไม่บังคับ) · ยังไม่รองรับการเทียบความหมาย (เช่น "NYC" กับ "New York") |
| `json_schema.py` | structured output, JSON mode | `check(text, schema)`, `extract_json(text)` | ตัด `<think>` ออกก่อนตรวจ · ดึง JSON ได้จาก ```json fence, ข้อความที่มี JSON ปนอยู่ หรือวงเล็บปีกกาที่สมดุล · ใช้ validator ตาม `$schema` พร้อม FormatChecker · ยังไม่รองรับ YAML/TOML/XML (ถ้าต้องการ ใช้ `yaml.safe_load` / `tomllib` แล้วส่งต่อเข้า jsonschema) |
| `safe_exec.py` | โค้ด + unit test (หมวด E) | `run_function_tests(code, test_code, entry_point)` (แบบ assert / `check()` ของ HumanEval / `test_*` ของ pytest) · `run_stdio_tests(code, [(stdin, stdout)])` (แบบ Codeforces เทียบทีละ token และมี float tolerance) | แยก process + temp dir + `python -I` + rlimit (หน่วยความจำ/CPU/ขนาดไฟล์/จำนวน process) + timeout + kill ทั้ง process group + **ตัด network ด้วย `unshare -rn`** (ทดสอบแล้ว: เปิด URL ไม่ได้) · **ไม่ใช่ sandbox ด้านความปลอดภัยเต็มรูปแบบ** ถ้าจะรันโค้ดของโมเดลปริมาณมาก ควรครอบด้วย container หรือ VM อีกชั้น |
| `math_answer.py` | คณิตที่มีคำตอบสุดท้าย | `check(text, gold)`, `extract_answer`, `is_equivalent` | ใช้ `\boxed{}` ตัวสุดท้าย (นอก `<think>` ก่อน) แล้ว fallback ไปที่ `####` หรือ "answer is / คำตอบคือ" หรือตัวเลขตัวสุดท้าย · normalize `\dfrac`, องศา, %, จุลภาคหลักพัน, เศษส่วน↔ทศนิยม และ tuple ที่ไม่สนลำดับ · เทียบนิพจน์ได้เฉพาะเมื่อติดตั้ง sympy · **audit 2:** `\text{…}` ที่เป็นคำตอบทั้งก้อนถือเป็นคำตอบ (เดิมถูกลบทิ้งทั้งสองฝั่ง ทำให้คำตอบข้อความใดๆ "ตรงกัน") และคำตอบว่างไม่ตรงกับอะไรเลย |
| `constraints.py` | IF / AutoIF / constraint RL | `check_all(response, instruction_id_list, kwargs)` | รองรับ 22 ประเภทตามรูปแบบ id ของ IFEval (`keywords:existence`, `length_constraints:number_words`, …) + `language:response_language` ที่รองรับภาษาไทย + `number_chars` (ภาษาไทยไม่มีช่องว่างระหว่างคำ จึงควรนับตัวอักษรแทนการนับคำ) · id ที่ไม่รองรับจะถูกรายงานใน `unsupported` และนับเป็นไม่ผ่าน · **ห้ามใช้ prompt ของ IFEval มาเทรน** |
| `sql_exec.py` | text-to-SQL ที่ตรวจด้วยการรันจริง | `check(pred_sql, gold_sql, db_path)` | เปิด SQLite แบบ read-only · ปฏิเสธคำสั่งเขียนหรือ DDL · ใช้ progress handler จำกัดจำนวน step · เทียบผลแบบ multiset (ถ้า gold มี ORDER BY จะเทียบตามลำดับ) · **audit 2:** ถ้าผลของ gold ว่าง จะคืน `ok=False` (แยกถูกผิดไม่ได้ ให้ทิ้งข้อนั้น; ใช้ `allow_empty_gold=True` ถ้าต้องการแบบ BIRD) · gold ที่รันไม่ได้คืน error แทนการ crash |
| `regex_check.py` | โจทย์ regex | `check(pattern, positives, negatives)` | ต้อง fullmatch ทุกตัวอย่างบวกและต้องไม่ match ตัวอย่างลบ · รันใน subprocess ที่มี timeout เพื่อกัน ReDoS (ทดสอบกับ `(a+)+$` แล้ว) |
| `think_format.py` | gate รูปแบบ thinking-first ของทุกหมวด | `check(text)` | ต้องเริ่มด้วย `<think>…</think>` ที่ไม่ว่าง และมีแค่ block เดียว · หลังจากนั้นต้องเป็นคำตอบ หรือ `<tool_call>` แบบ JSON (Hermes/Qwen3) หรือแบบ XML `<function=..><parameter=..>` (Qwen3.5/Coder) · คืนค่าความยาวการคิดโดยประมาณสำหรับวัด accuracy ต่อ token · **audit 2:** tool call XML ที่ `<parameter>` ไม่ปิด หรือมีข้อความเกินใน `<function>` ถือว่าผิด (เดิมผ่านโดยได้ argument ว่าง) |

## ใช้กับ pipeline ครู (Qwen3.8-27B)

1. ครูสร้างคำตอบ N ตัวอย่างต่อ prompt (เช่น N=4–8)
2. ส่งคำตอบผ่าน `think_format.check` ก่อน แล้วจึงผ่านตัวตรวจของหมวดนั้น
3. เก็บเฉพาะคำตอบที่ผ่าน (rejection sampling) หรือใช้ pass rate เป็น "ความยาก" ของโจทย์ แล้วนำไปตั้ง length budget ในหมวด F (ดู `RESEARCH_NOTES.md`)
4. คู่ผ่าน/ไม่ผ่านที่เป็นโจทย์เดียวกัน นำไปใช้เป็นคู่ DPO ได้

## สิ่งที่ยังไม่มี (ดู `OPEN_QUESTIONS.md`)
- ตัวตรวจแบบ LLM-judge/rubric (สำหรับ deep research แบบ long-form) ต้องใช้โมเดล judge ซึ่งไม่ได้เขียนไว้ในรอบนี้
- ตัวตรวจ trajectory ของ SWE/terminal ต้องใช้ Docker image ของแต่ละ task (SWE-smith, R2E-Gym, Harbor) ดูรายละเอียดในหมวด L ของ `DATASET_HUNT.md`
