# TOP_DOWNLOAD_LIST — 30 ชุดที่ควรโหลดก่อน

> เรียงตาม **คุณค่าต่อเป้าหมาย ÷ ต้นทุน** (ต้นทุน = ขนาดดาวน์โหลด + ปัญหาใบอนุญาต + งานแปลง/ต้องใช้ Docker)
> ขนาดทุกบรรทัด**ตรวจจริงด้วย HF tree API** โดยนับเฉพาะไฟล์ที่ match `allow_patterns` (2026-10-26)
> converter ของทุกชุดอยู่ที่ `converters/<ชื่อ>.py` และแถวตัวอย่างอยู่ที่ `samples/<ชื่อ>.jsonl` (รัน `python3 converters/test_converters.py` แล้วผ่าน 40/40)

**ความหมายของ "บทบาท"**
- **ใช้ตรง**: มีคำตอบที่มี reasoning และผ่านตัวตรวจแล้ว ใช้เทรน SFT ได้ทันที
- **prompt-only**: ใช้ prompt + ตัวตรวจ/เฉลย ให้ครู Qwen3.8-27B สร้างคำตอบใหม่ แล้วกรองผ่าน `verifiers/`
- **DPO**: มีคู่ chosen/rejected

**ใบอนุญาต**
- ⚠️ = ไม่ระบุ license บนการ์ด ต้องตัดสินใจก่อนใช้เชิงพาณิชย์ (ดู `OPEN_QUESTIONS.md`)
- NC = ห้ามใช้เชิงพาณิชย์

| # | ชุด (repo) | หมวด | ไฟล์ที่โหลด (`allow_patterns`) | MB | ใบอนุญาต | บทบาท | converter / ตัวตรวจ | ทำไม |
|---|---|---|---|---|---|---|---|---|
| 1 | [allenai/tmax-sft](https://huggingface.co/datasets/allenai/tmax-sft) | A | `skill_tax_20260505_2.2k_combined_balanced_thinking_only_success/*` | 40.9 | ODC-BY | ใช้ตรง | `allenai__tmax-sft` | trajectory terminal ของ Qwen3.6-27B ที่มี `reasoning_content` และผ่าน verifier แล้ว สั้นพอสำหรับ 16K |
| 2 | [nvidia/When2Call](https://huggingface.co/datasets/nvidia/When2Call) | B | `train/*` | 41.2 | CC-BY-4.0 | prompt-only | `nvidia__When2Call` / toolcall | ป้ายกำกับ call / ถามกลับ / ทำไม่ได้ ชัดเจน (**ห้ามใช้ `test/`** เพราะสร้างจาก BFCL) |
| 3 | [PrimeIntellect/INTELLECT-3-RL](https://huggingface.co/datasets/PrimeIntellect/INTELLECT-3-RL) | E/F | `*/train-*.parquet` | 53.1 | ⚠️ | prompt-only | `…INTELLECT-3-RL__math` / `__code` / math_answer, safe_exec | มี avg@8 ของ **Qwen3-4B** ทุกแถว ใช้เป็นป้ายความยากสำหรับ budget การคิดได้ทันที |
| 4 | [Skywork/Skywork-OR1-RL-Data](https://huggingface.co/datasets/Skywork/Skywork-OR1-RL-Data) | E/F | `data/math-*.parquet` | 19.0 | ⚠️ | prompt-only | `Skywork__…__math` / math_answer | 105k ข้อ มี model_difficulty 0–16 และ decontam AIME แล้ว |
| 5 | [zake7749/Qwen3.6-35B-A3B-Tool-Calling](https://huggingface.co/datasets/zake7749/Qwen3.6-35B-A3B-Tool-Calling) | B/F | `data/train.parquet` | 196.5 | ⚠️ | ใช้ตรง + DPO | `zake7749__…` / toolcall | Qwen3.6 thinking ที่ผ่าน exact-match กับ gold และ reasoning ของคำตอบที่ถูกเลือกสั้นกว่าที่ถูกปฏิเสธ |
| 6 | [ThaiLLM/med-tool-use](https://huggingface.co/datasets/ThaiLLM/med-tool-use) | D/B | `data/train-*.parquet` | 36.1 | ⚠️ | prompt-only | `ThaiLLM__med-tool-use` | tool-use **ภาษาไทยแท้** มีเฉลยว่าควรเรียกหรือไม่ควรเรียก tool (ไม่เรียก 62%) |
| 7 | [nvidia/Nemotron-RL-Agentic-Indirect-Prompt-Injection-v1](https://huggingface.co/datasets/nvidia/Nemotron-RL-Agentic-Indirect-Prompt-Injection-v1) | I | `train.jsonl` | 11.7 | CC-BY-4.0 | prompt-only (RL env) | `nvidia__…Injection-v1` | ทำงานเดิมต่อโดยเพิกเฉย injection (ต้องเพิ่มเงื่อนไขว่างานเดิมต้องเสร็จด้วย ไม่งั้นการไม่ทำอะไรเลยก็ได้รางวัล) |
| 8 | [MadeAgents/xlam-irrelevance-7.5k](https://huggingface.co/datasets/MadeAgents/xlam-irrelevance-7.5k) | B | `xlam-7.5k-irrelevancek.json` | 7.8 | CC-BY-4.0 | prompt-only | `MadeAgents__…` / toolcall(no-call) | เคส "ไม่ควรเรียก tool" ราคาถูก |
| 9 | [driaforall/verifiable-pythonic-function-calling-lite](https://huggingface.co/datasets/driaforall/verifiable-pythonic-function-calling-lite) | B | `data/*.parquet`, `evaluate/*` | 26.3 | Apache-2.0 | prompt-only | `driaforall__…` | มี mock function ที่ execute ได้จริงเป็นตัวตรวจ (simple / parallel / multi-turn) |
| 10 | [rl-research/dr-tulu-rl-data](https://huggingface.co/datasets/rl-research/dr-tulu-rl-data) | C | `data/*.parquet` | 2.8 | ODC-BY | prompt-only (rubric RL) | `rl-research__dr-tulu-rl-data` | query งานวิจัยจริงพร้อม rubric การอ้างอิง |
| 11 | [callanwu/WebWalkerQA](https://huggingface.co/datasets/callanwu/WebWalkerQA) | C | `data/silver-*` | 7.6 | Apache-2.0 | prompt-only | `callanwu__WebWalkerQA__silver` | เดินเว็บไซต์จริง ไม่มี wiki (ใช้แค่ silver เพราะ main เป็น eval) |
| 12 | [nvidia/Nemotron-RL-knowledge-web_search-mcqa](https://huggingface.co/datasets/nvidia/Nemotron-RL-knowledge-web_search-mcqa) | C/F | `mcqa_search.jsonl` | 6.0 | CC-BY-4.0 | prompt-only | `nvidia__…web_search-mcqa` | มี schema ของ search tool + ความยากวัดด้วย Qwen3-32B ใช้สอน "ค้นหรือไม่ค้น" |
| 13 | [PersonalAILab/TaskCraft](https://huggingface.co/datasets/PersonalAILab/TaskCraft) | C | `pure_qa.jsonl` (ถ้าต้องการ trace ด้วย ให้เพิ่ม `multihop_subtask_trace.jsonl`) | 17.7 (+13.5) | MIT | prompt-only | `PersonalAILab__TaskCraft` | QA บนเว็บ/PDF ข้อละ 1–7 hop มี golden answer (wiki ประมาณ 1% converter กรองออกให้แล้ว) |
| 14 | [zjunlp/DataMind-12K](https://huggingface.co/datasets/zjunlp/DataMind-12K) | A | `train.parquet` | 75.9 | MIT | ใช้ตรง | `zjunlp__DataMind-12K` | agent วิเคราะห์ข้อมูล (Python+SQL) ที่มี `<think>` และ ground truth (**ห้ามใช้ test.parquet**) |
| 15 | [open-athena/e2egit-large-qwen3.5-122b-32k-traces](https://huggingface.co/datasets/open-athena/e2egit-large-qwen3.5-122b-32k-traces) | A | `data/train-*.parquet` | 86.9 | ⚠️ | ใช้ตรง (กรอง result=1) | `open-athena__e2egit-…` | Qwen3.5-122B มี `<think>` ทุก turn มี verifier |
| 16 | [open-athena/ghactions-v3-qwen3.5-122b-32k-traces](https://huggingface.co/datasets/open-athena/ghactions-v3-qwen3.5-122b-32k-traces) | A | `data/train-*.parquet` | 286.6 | ⚠️ | ใช้ตรง | ใช้ converter เดียวกับ #15 (schema เหมือนกัน) | งาน DevOps/CI ที่ผ่านประมาณ 9.9k แถว |
| 17 | [MiniMaxAI/SynLogic](https://huggingface.co/datasets/MiniMaxAI/SynLogic) | E | `synlogic_*/train.parquet` | 71.0 | MIT | prompt-only | `MiniMaxAI__SynLogic` (+ verifier ทางการบน GitHub) | ปริศนาตรรกะ 35 แบบที่มี solver ตรวจ |
| 18 | [thavens/Qwen3-14B-secalign-tools](https://huggingface.co/datasets/thavens/Qwen3-14B-secalign-tools) | I | `data/*.parquet` | 33.4 | ⚠️ | DPO | `thavens__…` (ตัดประโยคใบ้ออก) | คู่ "ทำงานเดิม vs ทำตาม injection" 19K คู่ |
| 19 | [MPX0222forHF/SynSQL-Complex-5K](https://huggingface.co/datasets/MPX0222forHF/SynSQL-Complex-5K) + [seeklhy/SynSQL-2.5M](https://huggingface.co/datasets/seeklhy/SynSQL-2.5M) | E | `train.parquet` + `databases.zip` | 19.2 + 54.5 | Apache-2.0 | prompt-only | `MPX0222forHF__…` / sql_exec | text-to-SQL ที่ตรวจด้วยการรันจริง ไม่ใช่ wiki |
| 20 | [casey-martin/Seal-Tools](https://huggingface.co/datasets/casey-martin/Seal-Tools) | B | `data/train-*` | 15.1 | MIT | prompt-only | `casey-martin__Seal-Tools` / toolcall | แหล่งเดียวที่มีเฉลย **nested call** |
| 21 | [argilla/Synth-APIGen-v0.1](https://huggingface.co/datasets/argilla/Synth-APIGen-v0.1) | B | `data/*.parquet` | 29.7 | Apache-2.0 | prompt-only | `argilla__Synth-APIGen-v0.1` | ฟังก์ชันที่ execute ได้ ใช้เป็นฐานสำหรับฉีด tool error |
| 22 | [airesearch/WangchanX-Legal-ThaiCCL-RAG](https://huggingface.co/datasets/airesearch/WangchanX-Legal-ThaiCCL-RAG) | D/H | `data/train-*` | 18.0 | MIT | ใช้ตรง / prompt-only | `airesearch__…` | ถาม-ตอบกฎหมายไทยที่ผู้เชี่ยวชาญตรวจแล้ว (**ห้ามใช้ test** เพราะเป็น NitiBench) |
| 23 | [KodCode/KodCode-Light-RL-10K](https://huggingface.co/datasets/KodCode/KodCode-Light-RL-10K) | E | `data/*.parquet` | 73.9 | **NC** | prompt-only | `KodCode__KodCode-V1` (schema เดียวกัน) / safe_exec | โค้ด + pytest แบบเลือกโจทย์มาแล้ว กรองด้วย `benchmark_similarity` ≤ 0.79 |
| 24 | [agentica-org/DeepScaleR-Preview-Dataset](https://huggingface.co/datasets/agentica-org/DeepScaleR-Preview-Dataset) | F/E | `deepscaler.json` | 21.5 | MIT | prompt-only | `agentica-org__…` / math_answer | ชุด prompt มาตรฐานของ L1 / AdaptThink / Thinkless ใช้เทียบผลกับ paper ได้ |
| 25 | [nvidia/Nemotron-RL-math-OpenMathReasoning](https://huggingface.co/datasets/nvidia/Nemotron-RL-math-OpenMathReasoning) | E | `train.jsonl` | ~70 (รวม validation 71.1) | CC-BY-4.0 | prompt-only | `nvidia__Nemotron-RL-math-OpenMathReasoning` | โจทย์ AoPS 113k ข้อ ใช้เชิงพาณิชย์ได้ |
| 26 | [HuggingFaceTB/smoltalk2](https://huggingface.co/datasets/HuggingFaceTB/smoltalk2) | F | `SFT/smoltalk_systemchats_Qwen3_32B_think-*`, `SFT/smoltalk_everyday_convs_reasoning_Qwen3_32B_think-*` | 71.2 | ไม่ระบุใน cardData | ใช้ตรง (ใช้แค่บางส่วน) | `HuggingFaceTB__smoltalk2__systemchats_think` | ตัวอย่างของ "โจทย์ง่าย → คิดสั้น" ที่ไม่ใช่คณิต |
| 27 | [Tongyi-Zhiwen/DocQA-RL-1.6K](https://huggingface.co/datasets/Tongyi-Zhiwen/DocQA-RL-1.6K) | H | `train.parquet` | 32.2 | ไม่ระบุ | prompt-only | `Tongyi-Zhiwen__DocQA-RL-1.6K` (ตัด musique ออก) | เอกสารยาวที่มี ground truth |
| 28 | [rl-research/dr-tulu-sft-data](https://huggingface.co/datasets/rl-research/dr-tulu-sft-data) | C | `train.jsonl` | 531.7 | ODC-BY | ใช้ตรง (หลังกรอง) | `rl-research__dr-tulu-sft-data` | trajectory ค้นเว็บพร้อม `<cite>` (ต้องตัด popqa_tydiqa, browsecomp_* และคำถามที่ระบุว่าเป็นบทความ Wikipedia) |
| 29 | [allenai/TMax-15K](https://huggingface.co/datasets/allenai/TMax-15K) | A/L | `data/*.parquet`, `tasks.zip` | 513.3 | ODC-BY | prompt-only (ต้องใช้ Docker) | `allenai__TMax-15K` | 14.6k task terminal ที่ตรวจด้วย pytest ใช้ให้ครูสร้าง trajectory ใหม่ |
| 30 | [nvidia/Open-SWE-Traces](https://huggingface.co/datasets/nvidia/Open-SWE-Traces) (v1.2 minisweagent, **qwen38_27b**) | A | `data/minisweagent/qwen38_27b/scale-swe/train-0000[0-3]-*`, `data/minisweagent/qwen38_27b/swe-rebench-v2/train-0000[0-3]-*` | 2017.4 (8 shard จาก 44) | CC-BY-4.0 | ใช้ตรง (resolved=1, ≤16K) | `nvidia__Open-SWE-Traces__v1.2-minisweagent` | ครูรุ่นเดียวกับเรา (Qwen3.8-27B) ส่วนนี้ไม่ซ้ำกับ opencode/flash_next ที่มีอยู่แล้ว |

**ขนาดรวมทั้ง 30 ชุด ≈ 4.5 GB** (ถ้าตัด #30 ออกจะเหลือ ≈ 2.5 GB)

### สำรอง (ไฟล์ใหญ่หรือคุณค่ารองลงมา; มี converter ให้แล้ว)
| ชุด | ไฟล์ | MB | หมายเหตุ |
|---|---|---|---|
| typhoon-ai/typhoon-s-instruct-post-training | `data/sft-*.parquet` | 837.8 | ภาษาไทยมีแค่ส่วน AutoIF (ไทยประมาณ 39%) + tool irrelevant ส่วนที่เหลือเป็น Tulu |
| wannaphong/thai-magpie-qwen3-think | `data/train-*.parquet` | 208.1 | trace การคิดเป็นภาษาไทย (Qwen3-32B) ไม่มีตัวตรวจ |
| DuckerMaster/Thai-Synth-Receipts | `train/metadata.jsonl`, `train/clean/json/*`, `train/clean/images/TH-*-0000[0-9]*` | 134.5 (ทั้งชุด 1,820) | VLM ภาษาไทยที่มี gold ทุกฟิลด์ |
| vinod-anbalagan/chart-reasoning-verified | `train.jsonl`, `images/*` | 95.3 | chart QA ที่ตรวจได้ CC-BY-4.0 |
| artefactory/ledger-long-context-KPI-QA | `no_eval/data-0000[0-3]-of-*.parquet` | 49.9 | long-context เฉลยเป็นตัวเลขจาก XBRL |
| leapeto/tokenskip-math-qwen3-4b-thinking-n8 | `original/math_raw_original_shard00of04.jsonl`, `scores/scores_ratio_0.5.jsonl` | 387.3 | ความยากที่วัดจาก Qwen3-4B-Thinking (ไม่มีแถวตัวอย่าง เพราะ viewer error 500) |
| PrimeIntellect/SYNTHETIC-2-RL | `data/*.parquet` | 1191.8 | ต้องตัด `ifeval_*` ออก ไม่มี license |
| nvidia/Nemotron-Math-v2 | `data/low.parquet` | 3119.8 | pass rate แยกตาม effort ไฟล์ใหญ่ ถ้าต้องการถูกลงให้ใช้ #3/#4 แทน |
| zwhe99/DeepMath-103K | `data/*.parquet` | 2136.1 | ไฟล์ใหญ่เพราะมีคำตอบของ R1 ×3 |
| nvidia/Nemotron-RL-coding-competitive_coding | `data/train-00000-of-00011.parquet` | 288.9 (ทั้งชุด 15,680) | stdio test ไฟล์ใหญ่มาก |
| lmarena-ai/search-arena-24k | `data/search-arena-chat-24k.parquet` | 400.7 | prompt ค้นเว็บจริง (viewer อ่านไม่ได้ จึงไม่มีแถวตัวอย่าง) |

## คำสั่งดาวน์โหลด

```bash
pip install -U "huggingface_hub>=0.25"
export HF_HUB_ENABLE_HF_TRANSFER=1   # ถ้าติดตั้ง hf_transfer ไว้
D=./data_raw

huggingface-cli download allenai/tmax-sft --repo-type dataset --local-dir $D/allenai__tmax-sft --include "skill_tax_20260505_2.2k_combined_balanced_thinking_only_success/*"
huggingface-cli download nvidia/When2Call --repo-type dataset --local-dir $D/nvidia__When2Call --include "train/*"
huggingface-cli download PrimeIntellect/INTELLECT-3-RL --repo-type dataset --local-dir $D/PrimeIntellect__INTELLECT-3-RL --include "*/train-*.parquet"
huggingface-cli download Skywork/Skywork-OR1-RL-Data --repo-type dataset --local-dir $D/Skywork__Skywork-OR1-RL-Data --include "data/math-*.parquet"
huggingface-cli download zake7749/Qwen3.6-35B-A3B-Tool-Calling --repo-type dataset --local-dir $D/zake7749__Qwen3.6-35B-A3B-Tool-Calling --include "data/train.parquet"
huggingface-cli download ThaiLLM/med-tool-use --repo-type dataset --local-dir $D/ThaiLLM__med-tool-use --include "data/train-*.parquet"
huggingface-cli download nvidia/Nemotron-RL-Agentic-Indirect-Prompt-Injection-v1 --repo-type dataset --local-dir $D/nvidia__ipi --include "train.jsonl"
huggingface-cli download MadeAgents/xlam-irrelevance-7.5k --repo-type dataset --local-dir $D/MadeAgents__xlam-irrelevance-7.5k --include "*.json"
huggingface-cli download driaforall/verifiable-pythonic-function-calling-lite --repo-type dataset --local-dir $D/driaforall__vpfc-lite --include "data/*.parquet" "evaluate/*"
huggingface-cli download rl-research/dr-tulu-rl-data --repo-type dataset --local-dir $D/rl-research__dr-tulu-rl-data --include "data/*.parquet"
huggingface-cli download callanwu/WebWalkerQA --repo-type dataset --local-dir $D/callanwu__WebWalkerQA --include "data/silver-*"
huggingface-cli download nvidia/Nemotron-RL-knowledge-web_search-mcqa --repo-type dataset --local-dir $D/nvidia__ws-mcqa --include "mcqa_search.jsonl"
huggingface-cli download PersonalAILab/TaskCraft --repo-type dataset --local-dir $D/PersonalAILab__TaskCraft --include "pure_qa.jsonl" "multihop_subtask_trace.jsonl"
huggingface-cli download zjunlp/DataMind-12K --repo-type dataset --local-dir $D/zjunlp__DataMind-12K --include "train.parquet"
huggingface-cli download open-athena/e2egit-large-qwen3.5-122b-32k-traces --repo-type dataset --local-dir $D/oa__e2egit --include "data/train-*.parquet"
huggingface-cli download open-athena/ghactions-v3-qwen3.5-122b-32k-traces --repo-type dataset --local-dir $D/oa__ghactions --include "data/train-*.parquet"
huggingface-cli download MiniMaxAI/SynLogic --repo-type dataset --local-dir $D/MiniMaxAI__SynLogic --include "synlogic_*/train.parquet"
huggingface-cli download thavens/Qwen3-14B-secalign-tools --repo-type dataset --local-dir $D/thavens__secalign --include "data/*.parquet"
huggingface-cli download MPX0222forHF/SynSQL-Complex-5K --repo-type dataset --local-dir $D/SynSQL-Complex-5K --include "train.parquet"
huggingface-cli download seeklhy/SynSQL-2.5M --repo-type dataset --local-dir $D/SynSQL-2.5M --include "databases.zip"
huggingface-cli download casey-martin/Seal-Tools --repo-type dataset --local-dir $D/casey-martin__Seal-Tools --include "data/train-*"
huggingface-cli download argilla/Synth-APIGen-v0.1 --repo-type dataset --local-dir $D/argilla__Synth-APIGen --include "data/*.parquet"
huggingface-cli download airesearch/WangchanX-Legal-ThaiCCL-RAG --repo-type dataset --local-dir $D/WangchanX-Legal --include "data/train-*"
huggingface-cli download KodCode/KodCode-Light-RL-10K --repo-type dataset --local-dir $D/KodCode-Light-RL-10K --include "data/*.parquet"
huggingface-cli download agentica-org/DeepScaleR-Preview-Dataset --repo-type dataset --local-dir $D/DeepScaleR --include "deepscaler.json"
huggingface-cli download nvidia/Nemotron-RL-math-OpenMathReasoning --repo-type dataset --local-dir $D/nemo-omr --include "train.jsonl"
huggingface-cli download HuggingFaceTB/smoltalk2 --repo-type dataset --local-dir $D/smoltalk2 --include "SFT/smoltalk_systemchats_Qwen3_32B_think-*" "SFT/smoltalk_everyday_convs_reasoning_Qwen3_32B_think-*"
huggingface-cli download Tongyi-Zhiwen/DocQA-RL-1.6K --repo-type dataset --local-dir $D/DocQA-RL --include "train.parquet"
huggingface-cli download rl-research/dr-tulu-sft-data --repo-type dataset --local-dir $D/dr-tulu-sft --include "train.jsonl"
huggingface-cli download allenai/TMax-15K --repo-type dataset --local-dir $D/TMax-15K --include "data/*.parquet" "tasks.zip"
huggingface-cli download nvidia/Open-SWE-Traces --repo-type dataset --local-dir $D/open-swe-qwen38 \
  --include "data/minisweagent/qwen38_27b/scale-swe/train-0000[0-3]-*" "data/minisweagent/qwen38_27b/swe-rebench-v2/train-0000[0-3]-*"
```

หรือใช้ Python:

```python
from huggingface_hub import snapshot_download
TOP = [
  ("allenai/tmax-sft", ["skill_tax_20260505_2.2k_combined_balanced_thinking_only_success/*"]),
  ("nvidia/When2Call", ["train/*"]),
  ("PrimeIntellect/INTELLECT-3-RL", ["*/train-*.parquet"]),
  ("Skywork/Skywork-OR1-RL-Data", ["data/math-*.parquet"]),
  # ... (ใช้รายการ allow_patterns จากตารางด้านบน)
]
for repo, pats in TOP:
    snapshot_download(repo, repo_type="dataset", allow_patterns=pats,
                      local_dir=f"data_raw/{repo.replace('/', '__')}")
```

## แปลงเป็นรูปแบบของเรา

```bash
# parquet -> jsonl -> converter
python3 -c "import pandas as pd,sys; pd.read_parquet(sys.argv[1]).to_json(sys.argv[2], orient='records', lines=True, force_ascii=False)" in.parquet in.jsonl
python3 converters/<ชื่อ>.py in.jsonl > out.jsonl     # สถิติ in/out/skipped จะพิมพ์ออกทาง stderr
python3 tools/contamination.py scan out.jsonl          # ตรวจปน benchmark ก่อนเทรน (ดู CONTAMINATION.md)
```
