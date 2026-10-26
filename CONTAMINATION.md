# CONTAMINATION — การตรวจปน benchmark

## 1. วิธีตรวจ (8-gram shingle Jaccard)

เครื่องมือ: `tools/contamination.py` (ใช้แค่ stdlib)

```bash
python3 tools/contamination.py build  --cache ~/.cache/contam_bench          # โหลด benchmark (รวม ~8 MB) แล้วเก็บ cache นอก repo
python3 tools/contamination.py scan out.jsonl [more.jsonl] --cache ~/.cache/contam_bench [--jaccard 0.5] [--containment 0.8]
```

1. **Normalize**: NFKC → ตัวพิมพ์เล็ก → แยก token ด้วย `\w+` (รองรับทั้งไทยและละติน)
2. **Shingle**: ชุดของหน้าต่าง 8 token แล้วแฮชด้วย blake2b 48-bit (กำหนดได้แน่นอน ทำให้ cache ใช้ข้าม process ได้) ข้อความที่สั้นกว่า 8 token จะถูกข้าม
3. **หน่วยข้อความฝั่งเทรน**: ทุกข้อความ user / system / tool, ทุก string field ระดับบน (เปิด JSON-in-string ที่ซ้อนอยู่ด้วย) และทั้งแถวรวมกัน **ไม่สแกนข้อความ assistant** เพราะไม่ใช่ที่ที่ prompt ของ benchmark จะซ่อนอยู่
4. **ค้นคู่**: ใช้ inverted index (shingle → รายการ benchmark item) เพื่อหาข้อที่มี shingle ร่วมกันอย่างน้อย 1 ตัว จากนั้นคำนวณค่าจริง
   - `Jaccard = |A∩B| / |A∪B|` → **flag เมื่อ ≥ 0.5** (ตามข้อกำหนด)
   - `containment = |A∩B| / |B|` → รายงานเพิ่มเมื่อ ≥ 0.8 เพื่อจับกรณีที่โจทย์ benchmark ถูกฝังอยู่ใน prompt ที่ยาวกว่า (Jaccard จะต่ำเพราะตัวหารใหญ่)
5. **benchmark ที่ index** (จำนวนข้อจริงที่โหลดได้):

| benchmark | แหล่ง | ข้อ |
|---|---|---|
| GSM8K test | `openai/gsm8k` main/test | 1,319 |
| HumanEval | `openai/openai_humaneval` | 164 |
| MBPP+ | `evalplus/mbppplus` | 378 |
| IFEval | `google/IFEval` | 541 |
| BFCL v3 (ทุกหมวด รวม live / multi-turn) | `gorilla-llm/Berkeley-Function-Calling-Leaderboard` `BFCL_v3_*.json` | 5,251 |
| MMLU-Pro test | `TIGER-Lab/MMLU-Pro` | 12,032 |
| SWE-bench Verified / full test | `princeton-nlp/SWE-bench_Verified`, `princeton-nlp/SWE-bench` | 500 / 2,294 |
| Terminal-Bench 2.0 | `harborframework/terminal-bench-2.0` `*/instruction.md` | 89 |
| BrowseComp | `openaipublic…/browse_comp_test_set.csv` (ถอดรหัสด้วยวิธี canary ที่เปิดเผยใน openai/simple-evals) | 1,266 |
| GAIA | `gaia-benchmark/GAIA` เป็น **gated** | **ไม่ได้ index** (ต้องขอสิทธิ์เอง) |

> ข้อจำกัด
> - วิธีนี้จับได้เฉพาะการปนแบบ "ข้อความใกล้เคียง" จับการแปลภาษาหรือ paraphrase ไม่ได้ (เช่น GSM8K ที่แปลเป็นไทย ต้องใช้ embedding หรือแปลกลับก่อน)
> - BFCL ใช้ฟิลด์ `question` เท่านั้น ไม่ได้รวม function doc

## 2. Positive control (ยืนยันว่าเครื่องมือจับได้จริง)

| ชุดทดสอบ (300 แถวจาก 3 ช่วง offset) | flag ด้วย Jaccard ≥ 0.5 | flag ด้วย containment ≥ 0.8 | สรุป |
|---|---|---|---|
| `openai/gsm8k` test (ตัว benchmark เอง) | 300/300 | 300/300 | ✅ จับได้ครบทุกแถว |
| `nvidia/When2Call` **test/mcq** | **196/300 (65%)** ตรงกับ BFCL v3 | 98/300 | ✅ ยืนยันข้อค้นพบของหมวด B ว่า When2Call test สร้างจาก BFCL → **ห้ามใช้ split test ของ When2Call** |

## 3. ผลสแกนชุดที่จะใช้เทรน

### 3.1 แถวตัวอย่างใน `samples/` (40 ไฟล์ รวม 298 แถว)
**ไม่พบแถวที่ถึงเกณฑ์** ทั้ง Jaccard ≥ 0.5 และ containment ≥ 0.8 ในทุกไฟล์

### 3.2 ชุดเสี่ยงสูง สุ่มชุดละ 300 แถว (offset 0, n/3, 2n/3 ผ่าน datasets-server เก็บไว้นอก repo)

| ชุด | แถวที่สแกน | flag | รายละเอียด |
|---|---|---|---|
| allenai/IF_multi_constraints_upto5 | 300 | **1 (0.33%)** | แถวที่ 225 ตรงกับ IFEval #362 (Jaccard 0.556) และ #27 (0.536) ประโยค "First repeat the request word for word without change…" เป็นแม่แบบเดียวกับ IFEval นอกจากนี้หมวด E รายงานว่า constraint แบบ IFEval อยู่ใน 47% ของแถว (ปนในระดับ "ชนิดคำสั่ง" ซึ่งการเทียบ 8-gram จับไม่ได้) |
| KodCode/KodCode-V1 | 300 | 0 | การ์ดมีคอลัมน์ `benchmark_similarity` ให้เอง หมวด E วัดได้ว่า >0.79 ประมาณ 7.2% และ converter กรองออกให้แล้ว |
| MadeAgents/xlam-irrelevance-7.5k | 300 | 0 | |
| nvidia/When2Call train_sft | 300 | 0 | ส่วน train สะอาด (ต่างจากส่วน test) |
| PrimeIntellect/SYNTHETIC-2-RL | 300 | 0 | ชุดนี้มี `problem_id` แบบ `ifeval_*` ซึ่ง converter ตัดออกทั้งหมด (ไม่ได้วัดสัดส่วน) |
| zake7749/Qwen3.6-35B-A3B-Tool-Calling | 300 | 0 | |
| nvidia/Nemotron-RL-coding-competitive_coding | 300 | 0 | |
| Skywork/Skywork-OR1-RL-Data (math) | 300 | 0 | |
| zwhe99/DeepMath-103K | 300 | 0 | |
| PrimeIntellect/INTELLECT-3-RL (code) | 300 | 0 | |
| argilla/Synth-APIGen-v0.1 | 300 | 0 | |
| rl-research/dr-tulu-sft-data | 300 | 0 กับ BrowseComp | แต่ซับเซ็ต `browsecomp_*` (916 แถว) เป็นโจทย์สไตล์ BrowseComp จึงตัดออกเพื่อความปลอดภัย และพบคำถามที่ระบุว่ามาจาก "Wikipedia article" ในซับเซ็ต taskcraft |

### 3.3 ชุดที่ "ปนจริง" หรือ "เป็น benchmark" (จากการดูการ์ด/แถวจริงในหมวด A–L)

| ชุด | ปนกับ | หลักฐาน / อัตรา | การจัดการ |
|---|---|---|---|
| nvidia/When2Call **test** | BFCL | 65% ของ 300 แถว (positive control ข้างบน) | ห้ามใช้ ใช้ได้เฉพาะ `train/` |
| allenai/IF_multi_constraints_upto5 | IFEval | 0.33% เกือบซ้ำทั้งข้อ + 47% ใช้ constraint แบบ IFEval | ถ้าจะใช้ IFEval เป็นชุดวัด ไม่ควรใช้ชุดนี้ หรือต้องตัดแถวที่ใช้ id ของ IFEval |
| PrimeIntellect/SYNTHETIC-2-RL `ifeval_*` | IFEval | ตาม problem_id | converter ตัดออกให้แล้ว |
| nvidia/Nemotron-Cascade-2-RL-data (ส่วน IF) | IFEval | ใช้ `instruction_id_list` แบบ IFEval (หมวด E) | ไม่ได้อยู่ใน TOP 30 |
| interstellarninja/hermes_reasoning_tool_use (มีอยู่แล้ว) | BFCL | การ์ดเขียนเองว่า "aligned with BFCL v3 scenarios" | แนะนำให้สแกนชุดเต็มด้วยเครื่องมือนี้ |
| HardGen / FunReason-MT | BFCL | สร้างใน environment ของ BFCL (หมวด B) | ตัดออก |
| agentica-org/DeepCoder-Preview-Dataset | LiveCodeBench / Codeforces | มี split `lcbv5/test`, `codeforces/test` | ใช้เฉพาะ train |
| agentica-org/DeepScaleR-Preview-Dataset | AIME/AMC ปีเก่า | มีโจทย์ AIME/AMC อยู่ในชุด | ห้ามใช้ AIME/AMC ปีเหล่านั้นเป็นชุดวัด |
| typhoon-ai/thai_exam, OpenThaiEval `onet_m6_*` | thai-onet-m6-exam (มีอยู่แล้ว) | ข้อสอบ O-NET ชุดเดียวกัน (หมวด D, K) | ห้ามใช้ ThaiExam-onet เป็นชุดวัด ใช้ tgat/tpat1/a_level/ic แทน |
| airesearch/WangchanX-Legal-ThaiCCL-RAG **test** | NitiBench | split test คือ NitiBench | ใช้เฉพาะ train |
| zjunlp/DataMind-12K **test** | BIRD / DAEval / TableBench | การ์ด | ใช้เฉพาะ train |
| AI45Research/APP1-Agentic-Safety-SFT-Data | AgentDojo | ใช้โดเมนเดียวกัน (banking/slack/travel/workspace) (หมวด I) | ห้ามใช้ถ้าจะวัดด้วย AgentDojo |
| Salesforce/APIGen-MT-5k, nvidia/ToolScale, AReaL-tau2 | τ-bench / τ²-bench | โดเมนเดียวกัน (หมวด B) | ถ้าจะใช้ τ² เป็นชุดวัด ไม่ควรเทรนด้วยชุดเหล่านี้ |
| OptimalThinkingBench (ครึ่งยาก) | reasoning-gym | ครึ่งยากสร้างจาก reasoning-gym (หมวด K) | ถ้าเทรนด้วย reasoning-gym ให้ใช้เฉพาะครึ่งง่ายเป็นชุดวัด |
| translated benchmark ภาษาไทย (`iapp/openai_humaneval-th`, `typhoon-ai/ifeval-th`, `iapp/math-500-th`, `aime_2024-th`, `livecodebench-th`) | HumanEval / IFEval / MATH / AIME / LCB | เป็นตัว benchmark เองที่แปลแล้ว | ห้ามใช้เทรน (8-gram จับข้ามภาษาไม่ได้) |

### 3.4 สแกนไฟล์จริงทั้งชุด (2026-10-26 รอบ audit) — **เจอปนจริงที่การสุ่ม 300 แถวพลาดไป**
ใช้ไฟล์ดิบจาก HF ทั้งไฟล์ → converter → `tools/contamination.py filter`

| ชุด | แถว | ตัดออก | ปนกับ | หมายเหตุ |
|---|---|---|---|---|
| agentica-org/DeepScaleR-Preview-Dataset | 40,315 | **93 (0.23%)** | **MMLU-Pro test** (Jaccard 1.0 ซ้ำทั้งข้อ) | ต้องรัน filter ก่อนใช้ทุกครั้ง |
| MadeAgents/xlam-irrelevance-7.5k | 7,500 | **6** | **BFCL v3** (มี Jaccard 1.0) | |
| nvidia/When2Call train_sft | 15,000 | **4** | BFCL v3 (containment 1.0) | ส่วน train แทบสะอาด ส่วน test ปน 65% |
| PersonalAILab/TaskCraft (pure_qa) | 40,444 | 0 | — | หลัง converter ตัด wiki 1.1% |
| callanwu/WebWalkerQA (silver) | 13,579 | 0 | — | |
| nvidia/Nemotron-RL-knowledge-web_search-mcqa | 2,929 | 0 | — | |

**บทเรียน:** การสุ่ม 300 แถวไม่พอ **ต้องรัน `filter` กับทุกไฟล์ทั้งชุดก่อนเทรนเสมอ**
```bash
python3 tools/contamination.py filter data/X.jsonl data/X.clean.jsonl
```

## 4. ขั้นตอนที่แนะนำก่อนเทรนจริง
1. แปลงทุกชุดด้วย `converters/` ก่อน แล้วรัน `scan` กับไฟล์ output **ทั้งชุด** (ใน sandbox สแกน 298 แถวตัวอย่างพร้อมสร้าง index ใช้เวลาประมาณ 9 วินาที สำหรับชุดใหญ่ควรแบ่งไฟล์แล้วรันขนานกัน)
2. ใช้คำสั่ง `filter` (ตัดแถวที่ Jaccard ≥ 0.5 **หรือ** containment ≥ 0.8 อัตโนมัติ และพิมพ์จำนวนที่ตัดแยกตาม benchmark)
3. ชุดภาษาไทยที่แปลมา ให้ตรวจเพิ่มด้วย embedding similarity (เช่น multilingual-e5) เทียบกับ benchmark ฉบับภาษาอังกฤษ
4. ถ้าต้องการวัดด้วย GAIA ให้ขอสิทธิ์ gated แล้วเพิ่ม loader ใน `BENCHMARKS`
