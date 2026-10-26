# OPEN_QUESTIONS — สิ่งที่ตรวจไม่ได้ และสิ่งที่ต้องให้ทีมตัดสินใจ

เรียงตามผลกระทบต่อการเลือกข้อมูล (มากไปน้อย)

## ✅ คำตอบจากทีม (2026-10-26)
| คำถาม | คำตอบ | ผลต่อแผน |
|---|---|---|
| ใช้เชิงพาณิชย์ไหม | **ไม่** | ใช้ชุด NC และชุดที่ไม่ระบุ license ได้สำหรับวิจัย/ใช้ภายใน (ชุดที่ไม่มี license ถือตามกฎหมายว่า "สงวนสิทธิ์" อยู่ดี จึงไม่ควรเผยแพร่ข้อมูลหรือโมเดลที่เทรนด้วยชุดเหล่านี้ต่อสาธารณะโดยไม่เช็คก่อน) |
| ข้อมูลที่มีส่วนใหญ่เป็นภาษาไทย | ใช่ | ต้องเติมข้อมูลทักษะภาษาอังกฤษ (โค้ด/tool/คณิต) ให้ไทยไม่เกินประมาณ 30–40% ของ token (BEST_PRACTICES §E) |
| GPU | เช่า 4090 24GB+ · เครื่องตัวเอง 2060 8GB | เทรนและรันครูบนเครื่องเช่า ใช้งานจริงบน 2060 (BEST_PRACTICES §H) |
| ส่วน SWE | ยังไม่แน่ใจเรื่องเครื่อง | **เลือกสร้าง trajectory ใหม่ที่สั้น** ไม่เทรนแบบ 32–64K · environment Docker ต้องรันบนเครื่องอื่นที่ไม่ใช่ pod ที่เช่า |
| runtime | llama.cpp | ข้อมูลเทรนต้องเรนเดอร์ด้วย template ที่ llama.cpp ใช้ (template ทางการที่ฝังใน GGUF + `--jinja`) |
| คิดเป็นภาษาไทย | ไม่จำเป็น | ปล่อยให้คิดตามธรรมชาติ ตอบเป็นภาษาของผู้ใช้ |
| ชุดวัดผล | ยังไม่รู้ | ผมเสนอชุดเริ่มต้นไว้ใน BEST_PRACTICES §H |
| รูปแบบข้อมูลภาพ | ต้องถาม agent ของทีม | ค้างไว้ |
| แปล prompt เป็นไทย | ยังไม่ชัดเจน ("ไม่เข้าใจคำถาม") | อธิบายใหม่ด้วยตัวอย่างในแชท (audit 2) รอคำตอบ ได้/ไม่ได้ · คำแนะนำ: **ได้** (แปลเฉพาะโจทย์, ครูตอบ, ตรวจด้วยเฉลยเดิม) |
| เทรนบน 4090 ได้ไหม | ได้ (2060 ใช้รันอย่างเดียว) | BEST_PRACTICES §G |
| สเปกเครื่องของทีมสำหรับรัน Docker | Windows 11 · RAM 32 GB · ดิสก์ว่างมาก · i5-9600K (6C/6T) | **พอสำหรับ pilot**: Docker Desktop + WSL2, `.wslconfig` memory=24GB processors=6, รันพร้อมกันเริ่มที่ 3 container, เก็บงานไว้ในไฟล์ระบบของ WSL (BEST_PRACTICES §G) |

## ✅ แก้แล้วในรอบ audit (2026-10-26)
- รูปแบบการเรนเดอร์: `tools/render_chat.py` ใช้ template ทางการ + แยกตาม user turn + `--require-think` (ทดสอบแล้วกับ 40 ชุด · audit 2 พบว่ายังมีปัญหาที่ test ชุดนี้จับไม่ได้ ดูหัวข้อถัดไป)
- ไฟล์ JSON array (xlam-irrelevance, DeepScaleR) และ parquet ใช้กับ converter ได้แล้ว
- TaskCraft `pure_qa.jsonl` ใช้ชื่อคอลัมน์ต่างจาก viewer แก้ converter แล้ว (ทดสอบกับไฟล์จริง 40,910 แถว)
- ปนจริงที่เจอเพิ่ม: DeepScaleR 93 แถวซ้ำ MMLU-Pro · xlam-irrelevance 6 แถว · When2Call train 4 แถว → มีคำสั่ง `filter` แล้ว

## ✅ แก้แล้วในรอบ audit 2 (2026-10-26): ทดสอบทั้ง pipeline กับแถวจริงที่ไม่ถูกตัด (30 แถวต่อชุด × 38 ชุด)
ปัญหาที่เจอและแก้แล้ว (ทุกข้อเป็นแบบ "เทรนได้แต่ผิดเงียบๆ" ซึ่ง test ด้วย samples ที่ถูกตัดจับไม่ได้):
1. **DataMind**: ข้อมูลดิบใช้แท็กข้อความ `<code>` และผล execute มาเป็น user turn → ถ้าเทรนตรงๆ โมเดลจะพิมพ์ `<code>` แทนการเรียก tool และทุก step ก่อนหน้าจะถูกตัด `<think>` ทิ้ง → **แปลงเป็น tool call `execute_python` แบบ native แล้ว** (30/30 ผ่าน `--require-think`)
2. **open-athena `*-131k-opencode-traces`**: `instruction` **ไม่ใช่โจทย์** แต่เป็นข้อความสุดท้ายของโมเดลเอง ("Looking at this problem…", "Done. The solution:") converter เดิมเอามาใส่เป็น prompt → เท่ากับเทรนด้วย prompt ที่จริงๆ คือคำตอบ → แก้ให้ไม่ใช้ `instruction` เลย, ข้ามแถวที่ไม่มีโจทย์, บทบาทเปลี่ยนเป็น `exclude` (ชุด 32k ของ Terminus ไม่มีปัญหานี้: `instruction` = user turn แรก 30/30)
3. **ชุดภาพ (VLM)**: สตริง `<image>` ไม่ใช่ภาพสำหรับ Qwen3.5 (template ต้องการ content item `{"type":"image"}`) → ลบออก, เพิ่ม `multimodal_messages()` และตัวตรวจ record จะปฏิเสธ `<image>`
4. **Open-SWE**: ตัวกรองความยาวนับไม่ครบ (ไม่นับ argument ของ tool call) → แก้แล้ว แต่ผลจริงคือ **resolved 17 แถว ยาว 16.8K–120K token ใส่ 16K ได้ 0 แถว** (ดู TOP_DOWNLOAD_LIST #30)
5. **ledger KPI-QA**: รายงานยาว ~215K ตัวอักษรทุกแถว, qrels ไม่ครบ, เฉลยจาก yfinance → `exclude`
6. **tmax-sft**: 118/450 turn ไม่มี reasoning ทำให้ `--require-think` ทิ้ง 2/3 → เพิ่ม `--mask-nothink` (เก็บไว้แต่ไม่คิด loss กับ turn ที่ไม่คิด) ได้ 30 ตัวอย่าง 301 turn
7. **`huggingface-cli` ถูกถอดออกแล้ว** ใน huggingface_hub รุ่นใหม่ (2.3.0 มีแค่ `hf`) → เปลี่ยนคำสั่งทั้งหมดเป็น `hf download` และ**ทดสอบ `--dry-run` ผ่านทั้ง 31 คำสั่ง**
8. **mini-swe-agent 2.x**: `-c my.yaml` อย่างเดียวจะทำให้ config เริ่มต้น (prompt ของงาน SWE) ไม่ถูกโหลด → แก้ RUNBOOK เป็น `-c swebench.yaml -c my_model.yaml` · เขียนตัวแปลง trajectory แล้ว (`tools/convert_minisweagent.py`)
9. เพิ่ม `tools/pipeline_check.py` ให้ agent ของทีมรันซ้ำกับไฟล์จริงหลังดาวน์โหลด

ผล pipeline บนแถวจริง (converter → template ทางการ → tokenizer จริงของ Qwen3.5-4B, ตัดที่ 16,384 token):

| ชุด (บทบาท) | แถว→record | ตัวอย่างที่เทรนได้ | turn ไม่มีการคิด | ยาวเกิน 16K | token median/max |
|---|---|---|---|---|---|
| tmax-sft (sft, `--mask-nothink`) | 30→30 | 30 | 118 (mask) | 3 | 6,570 / 15,892 |
| zake7749 Tool-Calling (sft, `--mask-nothink`) | 30→30 | 118 | 7 (mask) | 0 | 2,423 / 7,360 |
| DataMind-12K (sft) | 30→30 | 30 | 0 | 0 | 4,057 / 6,745 |
| e2egit 32k traces (sft) | 30→26 | 116 | 0 | 0 | 2,825 / 7,006 |
| dr-tulu-sft (sft) | 30→26 | 22 | 0 | 4 | 5,937 / 15,951 |
| Open-SWE minisweagent (sft) | 30→1 | 0 | 0 | 1 | – |
| smoltalk2 think (style) | 30→30 | 30 | 0 | 0 | 929 / 1,878 |
| thai-magpie (style) | 30→30 | 30 | 0 | 0 | 1,014 / 2,502 |
| open-athena-131k, ledger (exclude) | 30→0 | – | – | – | – |
| ชุด `prompt_only` 27 ชุด + `dpo` 1 ชุด | แปลงได้ทั้งหมด 0 error | (ไม่เทรนตรง) | | | |

## ก. ต้องตัดสินใจ (ฉบับเดิม)

1. **ใช้ข้อมูลที่ไม่มีใบอนุญาตได้หรือไม่ (วิจัยเท่านั้น หรือเชิงพาณิชย์)**
   - ชุดอันดับต้นหลายชุดไม่มี license บนการ์ด: กลุ่ม open-athena `*-qwen3.5-122b-*` (~100 repo), zake7749/Qwen3.6-35B-A3B-Tool-Calling, zake7749/Qwen-3.6-plus…, PrimeIntellect/INTELLECT-3-RL, PrimeIntellect/SYNTHETIC-2-RL, Skywork/Skywork-OR1-RL-Data, ThaiLLM/med-tool-use (+med-iq), thavens/Qwen3-14B-secalign-tools, JWei05/swe_smith_*, FineEnvs Qwen3.8 rollouts, artillerywu/DeepResearch-9K (และสร้างจาก HotpotQA/2Wiki/MuSiQue 100% = wiki → ตัดออก), Tongyi-Zhiwen/DocQA-RL-1.6K, iapp/Thai-R1-Distill-SFT
   - ชุดที่เป็น **NC (ห้ามใช้เชิงพาณิชย์)**: KodCode (ทั้ง V1 และ Light-RL), Salesforce/APIGen-MT-5k, CohereLabs/tiny-aya-l2-thinker, miromind MiroVerse, Cognitive-Lab/NayanaOCR, OptimalThinkingBench (eval)
   - **GPL-3.0**: HuggingFaceM4/ChartQA
   - ถ้าคำตอบคือ "เชิงพาณิชย์" ต้องเปลี่ยนชุดเหล่านี้ใน TOP 30: #3 → nvidia/Nemotron-RL-math-OpenMathReasoning, #5 → When2Call + Synth-APIGen ให้ครูสร้างคำตอบใหม่, #15/#16 → allenai/tmax-sft + TMax-15K, #23 → Nemotron-RL competitive coding (ไฟล์ใหญ่)
2. **การแปลโจทย์ที่มีตัวตรวจอยู่แล้วเป็นภาษาไทย นับเป็น "สร้างข้อมูลเอง" หรือไม่**
   - หมวด D พบว่าไม่มี multi-turn agent / tool-use / โค้ดภาษาไทยที่มีตัวตรวจเลย นอกจาก ThaiLLM/med-tool-use (โดเมนการแพทย์ 7 tools)
   - ทางที่ใช้ได้จริงทางเดียวคือแปล prompt ของชุดที่มีตัวตรวจ (เช่น When2Call, xLAM-irrelevance, DeepMath, TMax) เป็นไทย แล้วให้ครูตอบเป็นไทย ตัวตรวจเดิมยังใช้ได้
3. **การฉีด tool error ลงใน environment ที่ execute ได้ (Synth-APIGen, dria) นับเป็นการสร้างข้อมูลหรือไม่**
   - หมวด B ไม่พบชุดที่สอน "กู้จาก tool error" ที่สะอาดเลย (HardGen/FunReason-MT สร้างจาก environment ของ BFCL และชุดของ rmems ห้ามนำไปเทรน)
4. **จะใช้อะไรเป็นชุดวัด held-out** (มีผลกับการเลือกข้อมูลเทรน)
   - ถ้าใช้ τ²-bench: ห้ามเทรนด้วย APIGen-MT, ToolScale, AReaL-tau2, zake7749 Qwen-3.6-plus (ToolScale)
   - ถ้าใช้ AgentDojo: ห้ามใช้ AI45Research/APP1
   - ถ้าใช้ IFEval: ห้ามใช้ IF_multi_constraints และส่วน IF ของ Cascade-2 และควรระวัง AutoIF
   - ถ้าใช้ ThaiExam: **ห้ามใช้ subset `onet`** เพราะซ้ำกับ thai-onet-m6-exam ที่เทรนอยู่แล้ว ให้ใช้ tgat/tpat1/a_level/ic
   - ถ้าใช้ OptimalThinkingBench: ครึ่งยากซ้ำกับ reasoning-gym
5. **มี Docker และพื้นที่ดิสก์บนเครื่องเช่าเท่าไร**
   - TMax-15K, SWE-smith, R2E-Gym, Harbor ต้องใช้ Docker และ image รวมหลายร้อย GB (หมวด L)
   - ถ้าไม่มี Docker ใช้ได้เฉพาะ reasoning-gym, tau2-bench (train), AppWorld และ verifier ใน `verifiers/`
6. **รูปแบบข้อมูลภาพ (VLM)**: record เก็บ id ของภาพไว้ใน `meta.images` (content เป็นข้อความล้วน) แล้ว `converters/common.py: multimodal_messages()` แปลงเป็นรูปแบบที่ Qwen3.5 ต้องการ (`{"type":"image"}` สำหรับ template/processor หรือ `image_url` สำหรับ API) **(แก้ใน audit 2: เดิมใส่ `<image>` ซึ่งผิด)** · ยังต้องยืนยันกับ agent ของทีมว่า pipeline เทรนภาพจะโหลดไฟล์ภาพจากช่อง `images` แบบไหน · **รอบเทรนข้อความล้วนต้องตัดชุดภาพออก**

## ข. ตรวจไม่ได้ในรอบนี้ (ข้อจำกัดของ sandbox)

7. **GitHub API ถูกบล็อก (403)** ทำให้ dataset ที่ปล่อยบน GitHub อย่างเดียว (release asset / Google Drive) ยังไม่ได้ตรวจ เช่น ข้อมูลของ paper adaptive-length บางตัวที่ไม่ได้ขึ้น HF (ดูหมวด F ส่วน "สูตรการสร้างข้อมูล")
8. **Gated (ไม่ได้ขอสิทธิ์ตามกติกา)**: GAIA (จึงไม่ได้ index ในการตรวจปน), Salesforce/xlam-function-calling-60k (gated auto), aisingapore/SEA-Instruct-2602, MiroVerse, hkust-nlp/WebExplorer-QA, II-Search-SFT, SynthLabsAI/Big-Math-RL-Verified, typhoon-ai rl-code-math-*, Nemotron-Post-Training-Dataset-v2, BIPIA variants, Thai OCR บางชุด
9. **ชุดที่ datasets-server อ่านไม่ได้ จึงไม่มีแถวตัวอย่าง**: lmarena-ai/search-arena-24k (scan limit), leapeto/tokenskip-math-qwen3-4b-thinking-n8 (error 500), FineEnvs/data-agent-harbor-train (เป็นไฟล์ task ไม่ใช่ตาราง)
10. **Nemotron-Post-Training-Dataset-v1 (chat)**: prompt ของ user **ถูกลบออก** (เป็นข้อความว่าง มีแค่ conversation_id ของ lmsys-chat-1m) ถ้าจะใช้ต้อง join กับ lmsys-chat-1m ซึ่งเป็น gated และมีใบอนุญาตแยก จึงตัด converter ออก
11. **typhoon-s AutoIF**: ไทยจริงประมาณ 39% (ประมาณจากแถวตัวอย่าง) และ **ไม่มี kwargs ของ constraint** ทำให้ `verifiers/constraints.py` ใช้ตรงไม่ได้ ต้อง parse constraint จากข้อความ หรือใช้ LLM-judge
12. **ตัวเลขผลวิจัยหลายข้อใน RESEARCH_NOTES วัดบน dense transformer** ยังไม่มีงานที่วัดการลืมของ LoRA บน Gated DeltaNet โดยตรง ข้อแนะนำเรื่อง target modules จึงเป็นการอนุมาน ควรทำ ablation เอง
13. **open-athena `*-131k-opencode-traces`**: ข้อความ user แรกว่างทุกแถว และ **`instruction` ไม่ใช่โจทย์ แต่เป็นข้อความสุดท้ายของโมเดล** (แก้ข้อความเดิมที่เขียนผิดว่า "prompt อยู่ใน instruction") → บทบาท `exclude` ใช้รุ่น `*-32k-traces` แทน หรือ join โจทย์จาก task-trove ด้วย `task` id แล้วส่งผ่าน `TASK_PROMPTS=` (ประมาณ 52% ของ turn ไม่มี `<think>` อยู่ดี)
14. **Nemotron-RL-Agentic-Indirect-Prompt-Injection**: ตัวตรวจในชุดดูแค่ว่า "ไม่ได้เรียก tool ที่ผู้โจมตีต้องการ" ทำให้ policy ได้รางวัลจากการไม่ทำอะไรเลย ต้องเพิ่มเงื่อนไข `required_tools` ถูกเรียก + ผลลัพธ์ถูกต้อง (converter ใส่ `required_tools` ไว้ใน gold แล้ว แต่ยังไม่ได้เขียนตัวตรวจ)
15. **DR Tulu SFT**: การ์ดไม่ระบุ teacher (หมวด C อ้างว่าเป็น GPT-5 จาก paper) และพบคำถามที่ระบุว่ามาจาก "Wikipedia article" ในซับเซ็ต taskcraft converter กรองคำถามที่มีคำว่า Wikipedia ออก แต่ยังไม่ได้วัดสัดส่วนทั้งชุด
16. **ชุด `samples/` ถูกตัดความยาว string** (ตามข้อกำหนด <30 KB) บางแถวจึงมี JSON-in-string ที่ขาดกลางทาง (เช่น open-athena 1 แถว) ซึ่งเป็นสาเหตุที่ converter ข้ามแถวนั้น ข้อมูลจริงไม่มีปัญหานี้

## ค. ข้อควรตัดสินใจเชิงเทคนิค (แนะนำแล้ว แต่ควรให้ทีมยืนยัน)

17. **LoRA target modules ของ Qwen3.5-4B** (ยืนยันจาก `config.json` และ `model.safetensors.index.json` จริง)
    - 32 ชั้น = linear_attn (Gated DeltaNet) 24 ชั้น + self_attn 8 ชั้น (`full_attention_interval=4`)
    - โมดูลของ DeltaNet: `in_proj_qkv, in_proj_z, in_proj_a, in_proj_b, out_proj` · MLP: `gate_proj, up_proj, down_proj`
    - ยังมี **`mtp.layers.*`** (multi-token prediction) และ **vision tower** ด้วย ควรตั้ง regex ให้ LoRA ครอบคลุมเฉพาะ `model.language_model.layers.*`
18. **การใช้ trajectory ที่ไม่มี thinking** (SWE-Hero, SWE-Lego, Qwen3-Coder) จะใช้เป็น RL env อย่างเดียว หรือผสมใน SFT ไม่เกิน ~20–30% (ความเห็นจากหลักฐานในหมวด G: ข้อมูลแบบ answer-only ทำให้โมเดล thinking ตอบสั้นลงและแม่นน้อยลง)
19. **ความยาว 16K**: trace ส่วนใหญ่ของ Open-SWE / CoderForge / OpenResearcher ยาวเกิน 16K จะตัด (ถ้าตัดจะเสียสัญญาณ "จบงาน") หรือทิ้ง (converter ใช้ `MAX_CHARS` ทิ้งให้)
