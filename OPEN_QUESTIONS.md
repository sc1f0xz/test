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
| แปล prompt เป็นไทย | ยังไม่ชัดเจน | อธิบายเพิ่มในแชทแล้ว รอคำตอบ |
| เทรนบน 4090 ได้ไหม | ได้ (2060 ใช้รันอย่างเดียว) | BEST_PRACTICES §G |
| **สเปกเครื่องของทีมสำหรับรัน Docker** | **รอคำตอบ:** OS, RAM, ดิสก์ว่าง, CPU | ใช้ตัดสินว่ารัน container ของ SWE บนเครื่องตัวเองได้ไหม หรือต้องเช่า VPS ที่ใช้ CPU |

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
6. **รูปแบบข้อมูลภาพ (VLM)**: รูปแบบ record ที่กำหนดไม่มีช่องรูปภาพ converter ของหมวด J จึงใส่ `<image>` ใน content และเก็บ id ไว้ใน `meta.images` ต้องยืนยันว่า pipeline เทรนจะอ่าน field นี้

## ข. ตรวจไม่ได้ในรอบนี้ (ข้อจำกัดของ sandbox)

7. **GitHub API ถูกบล็อก (403)** ทำให้ dataset ที่ปล่อยบน GitHub อย่างเดียว (release asset / Google Drive) ยังไม่ได้ตรวจ เช่น ข้อมูลของ paper adaptive-length บางตัวที่ไม่ได้ขึ้น HF (ดูหมวด F ส่วน "สูตรการสร้างข้อมูล")
8. **Gated (ไม่ได้ขอสิทธิ์ตามกติกา)**: GAIA (จึงไม่ได้ index ในการตรวจปน), Salesforce/xlam-function-calling-60k (gated auto), aisingapore/SEA-Instruct-2602, MiroVerse, hkust-nlp/WebExplorer-QA, II-Search-SFT, SynthLabsAI/Big-Math-RL-Verified, typhoon-ai rl-code-math-*, Nemotron-Post-Training-Dataset-v2, BIPIA variants, Thai OCR บางชุด
9. **ชุดที่ datasets-server อ่านไม่ได้ จึงไม่มีแถวตัวอย่าง**: lmarena-ai/search-arena-24k (scan limit), leapeto/tokenskip-math-qwen3-4b-thinking-n8 (error 500), FineEnvs/data-agent-harbor-train (เป็นไฟล์ task ไม่ใช่ตาราง)
10. **Nemotron-Post-Training-Dataset-v1 (chat)**: prompt ของ user **ถูกลบออก** (เป็นข้อความว่าง มีแค่ conversation_id ของ lmsys-chat-1m) ถ้าจะใช้ต้อง join กับ lmsys-chat-1m ซึ่งเป็น gated และมีใบอนุญาตแยก จึงตัด converter ออก
11. **typhoon-s AutoIF**: ไทยจริงประมาณ 39% (ประมาณจากแถวตัวอย่าง) และ **ไม่มี kwargs ของ constraint** ทำให้ `verifiers/constraints.py` ใช้ตรงไม่ได้ ต้อง parse constraint จากข้อความ หรือใช้ LLM-judge
12. **ตัวเลขผลวิจัยหลายข้อใน RESEARCH_NOTES วัดบน dense transformer** ยังไม่มีงานที่วัดการลืมของ LoRA บน Gated DeltaNet โดยตรง ข้อแนะนำเรื่อง target modules จึงเป็นการอนุมาน ควรทำ ablation เอง
13. **open-athena `*-131k-opencode-traces`**: ข้อความ user แรกว่าง (prompt อยู่ใน `instruction`) และ trace ยาวถึง 131k converter แก้ให้แล้ว แต่แนะนำให้ใช้รุ่น `*-32k-traces` แทน
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
