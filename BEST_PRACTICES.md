# BEST_PRACTICES — สิ่งที่มีหลักฐานว่าได้ผลจริง (และสิ่งที่ตัดออก)

> เป้าหมาย: Qwen3.5-4B (hybrid Gated-DeltaNet) + LoRA · คิดก่อนตอบเสมอ · EN+TH · agent/tool/search · เทรนที่ 16K · ครู Qwen3.8-27B
> ตรวจเมื่อ: 2026-10-26 · ทุกข้อเปิด abstract หรือเนื้อหาจริงแล้ว (arXiv API / arXiv HTML / การ์ดโมเดลทางการ / ซอร์สโค้ด transformers) ถ้าข้อไหนมาจากเอกสารที่ไม่ใช่ paper จะระบุไว้

## เกณฑ์การคัด
- **เก็บไว้** เฉพาะสิ่งที่มีการทดลองแล้วว่า**ดีขึ้นจริง** โดยระบุขนาดโมเดลที่ทดลอง: **[ใกล้ 4B]** = 1.5–9B · **[ไกล 4B]** = ≥14B หรือไม่ระบุ
- **ตัดออก** สิ่งที่มีคนลองแล้วไม่ดีขึ้น หรือทำให้แย่ลง (รายการอยู่ในส่วน B พร้อมหลักฐาน)
- **ไม่ใส่ในสูตรหลัก** สิ่งที่หลักฐานแย้งกันหรือยังไม่มีคนทดลอง (ส่วน C)
- ข้อที่เป็น **[ข้อเท็จจริงทางเทคนิค]** มาจากการ์ดโมเดลหรือโค้ด ไม่ใช่ผลทดลอง แต่ถ้าไม่ทำตามจะผิดพลาดแน่นอน

---

## สูตรสรุป 1 หน้า

1. **รูปแบบข้อมูล**: เรนเดอร์ด้วย `chat_template.jinja` ของ Qwen3.5-4B เท่านั้น · tool call เป็น XML `<function=…><parameter=…>` (parser `qwen3_coder`) · reasoning ของ turn ก่อน user ล่าสุดจะถูกตัดออก ส่วน turn ใน tool loop จะเก็บไว้ (template จัดการเอง)
2. **ทุกตัวอย่างต้องมี `<think>` ที่ไม่ว่าง** ห้ามใส่ข้อมูลแบบตอบตรง (answer-only) หรือโหมด non-thinking
3. **แหล่งคำตอบ**: ให้ Qwen3.5-4B สร้างคำตอบเองก่อน (rejection sampling ผ่าน `verifiers/`) แล้วใช้ครูเฉพาะข้อที่นักเรียนทำไม่ได้ · เลือก**คำตอบที่ถูกและสั้นที่สุด**ของแต่ละข้อ ข้อยากยอมให้ยาว
4. **SFT สั้นๆ เพื่อสอนรูปแบบ** (1–2 epoch, LoRA r≈32, LR ≈10× ของ full FT) **แล้วต่อด้วย RL ที่ใช้ตัวตรวจ** (LoRA rank เล็ก) สำหรับ tool, search, agent
5. **RL**: ใช้ reward แบบละเอียดราย tool call · ห้ามใช้ reward ที่ให้คะแนนตามความยาว · ใช้ clip-higher + overlong shaping + loss normalization แบบไม่ bias (Dr. GRPO) · mask token ที่มาจาก tool/search ออกจาก loss
6. **กันลืม**: replay ที่สร้างจากโมเดลตัวเองประมาณ 30% · เซฟ checkpoint ถี่ๆ แล้วเลือกจาก forgetting suite · ถ้ายังลืมให้ลด scale ของ LoRA หรือ merge กลับ
7. **ภาษาไทย**: มีข้อมูล SFT ภาษาไทยเสมอ · ไม่บังคับให้ "คิด" เป็นภาษาไทยทั้งหมด เพราะจะเสียความแม่น (ตอบเป็นไทยได้ ส่วนการคิดปล่อยตามธรรมชาติ)
8. **long-context**: ไม่ต้องใช้ synthetic long SFT · ใช้ข้อมูลสั้นคุณภาพดี แล้วเฝ้าดู RULER/NIAH เพราะ CoT-SFT ทำ recall ของโมเดล hybrid พังได้
9. **วัดผล**: วัด baseline ก่อน · ทุกครั้งที่ RL บน Qwen ได้ผลดีขึ้น ต้องมี control เพราะ Qwen ดีขึ้นได้แม้ใช้ reward สุ่ม

---

## A. สิ่งที่ได้ผลจริง

### A1. รูปแบบข้อมูลและ template [ข้อเท็จจริงทางเทคนิค]

| ปฏิบัติ | หลักฐาน | ใช้กับเรา |
|---|---|---|
| **เรนเดอร์ด้วย chat template ทางการ** · tool call เป็น XML `<tool_call><function=NAME><parameter=K>V</parameter></function></tool_call>` และ `arguments` ต้องเป็น dict (template ใช้ `arguments\|items`) | [chat_template.jinja](https://huggingface.co/Qwen/Qwen3.5-4B/raw/main/chat_template.jinja) · การ์ดแนะนำ `--tool-call-parser qwen3_coder` · [model card](https://huggingface.co/Qwen/Qwen3.5-4B) | converter ของเราให้ `arguments` เป็น dict อยู่แล้ว ✔ |
| **"No thinking content in history"**: template ตัด reasoning ของ assistant turn ที่อยู่**ก่อน** user message ล่าสุด และ**เก็บไว้**ใน turn หลังจากนั้น (tool loop) | template บรรทัด `loop.index0 > ns.last_query_index` · Best Practices ข้อ 4 ใน model card | ห้ามตัด reasoning ใน tool loop เอง (แก้ default ของ converter `zake7749__…` แล้วใน commit นี้) |
| ค่า sampling ตอนสร้างข้อมูลและตอนวัดผลในโหมด thinking: `temperature=1.0, top_p=0.95, top_k=20, presence_penalty=1.5` (งานโค้ดใช้ `T=0.6, presence_penalty=0`) | Best Practices ข้อ 1 ใน model card | ใช้ค่าเดียวกันตอน rejection sampling ด้วยตัวนักเรียน · presence_penalty สูงอาจทำให้ภาษาปนกัน (การ์ดเตือนเอง) ควรระวังกับภาษาไทย |
| **ถ้าใช้ packing ต้องใช้ varlen path** (ส่ง `cu_seq_lens_q` ให้ kernel ของ gated-delta-rule) ไม่งั้น state ของ DeltaNet จะรั่วข้ามตัวอย่าง | [modeling_qwen3_5.py](https://raw.githubusercontent.com/huggingface/transformers/main/src/transformers/models/qwen3_5/modeling_qwen3_5.py) ส่ง `cu_seqlens` เข้า `chunk_gated_delta_rule` เฉพาะเมื่อมี kwarg นี้ | ทดสอบก่อน: loss ของ batch ที่ pack ต้องเท่ากับ loss ของ batch ที่ไม่ pack ถ้าไม่เท่าให้ปิด packing |
| ตั้ง LoRA target เฉพาะ `model.language_model.layers.*` (มี vision tower และ `mtp.layers.*` อยู่ด้วย) | `model.safetensors.index.json` จริง (ตรวจแล้วใน OPEN_QUESTIONS ข้อ 17) | อย่าใช้ `all-linear` แบบไม่กรอง |

### A2. แหล่งคำตอบและการคัดข้อมูล

| ปฏิบัติ | ผลที่รายงาน | ขนาด | แหล่ง |
|---|---|---|---|
| **Rejection-sampling FT ด้วยโมเดลตัวเอง** (เก็บเฉพาะคำตอบที่ถูก) ยิ่งได้หลายเส้นทางที่ต่างกันยิ่งดี และ**ช่วยโมเดลที่อ่อนกว่าได้มากกว่า** | LLaMA-7B GSM8K 35.9 → 49.3 | [ใกล้ 4B] (7B) | [2308.01825](https://arxiv.org/abs/2308.01825) |
| **ข้อมูลที่ใกล้ on-policy ลืมน้อยกว่า** (RL ลืมน้อยเพราะเรียนจากตัวอย่างของตัวเอง) · Iterative-SFT ที่สร้างส่วนง่ายใหม่จากนักเรียนทุก epoch ลืมน้อยมาก | Qwen2.5-7B MMLU drop: SFT 14.6 vs GRPO 0.2 | [ใกล้ 4B] | [2510.18874](https://arxiv.org/abs/2510.18874) · [RL's Razor 2509.04259](https://arxiv.org/abs/2509.04259) |
| **ผสม long CoT กับ short CoT สำหรับโมเดลเล็ก** ไม่ใช้ long CoT ล้วน | Qwen2.5-3B: Mix-Long 45.9 vs long-only 40.3 | [ใกล้ 4B] | [2502.12143](https://arxiv.org/abs/2502.12143) |
| **เลือกคำตอบที่ถูกและสั้นที่สุด** แล้วใช้ self-improve | เทียบเท่าครู QwQ บนคณิต · ยาวเกินไปทำให้แย่ลงในบางโดเมน | [ไกล 4B] (32B) | [2502.18080](https://arxiv.org/abs/2502.18080) · ShorterBetter [2504.21370](https://arxiv.org/abs/2504.21370) [ใกล้ 4B] |
| **ใช้ trajectory agent จริงแบบ end-to-end แทนการเย็บ trajectory สังเคราะห์** ข้อมูลที่หลากหลายและเหมาะกับโมเดลช่วย RL | "far stronger SFT initialization" · 4B ชนะ 32B บน AIME / GPQA / LCB | **[ใกล้ 4B]** (Qwen3-4B) | [2510.11701](https://arxiv.org/abs/2510.11701) |
| **distillation จากครู = วิธีเดียวที่เพิ่มความสามารถใหม่** (RL ไม่ขยายขอบเขตเกิน base เมื่อวัดด้วย pass@k ที่ k ใหญ่) | base ชนะ RL ที่ pass@k ใหญ่ ส่วน distill ขยายได้จริง | หลายขนาด | [2504.13837](https://arxiv.org/abs/2504.13837) → ทักษะใหม่ (เช่น agent ภาษาไทย) ต้องมาจากครู ส่วน RL ใช้ขัดเกลา |

### A3. LoRA และ hyperparameter (รายละเอียดอยู่ใน `RESEARCH_NOTES.md` §1)

| ปฏิบัติ | หลักฐาน | ขนาด |
|---|---|---|
| ใส่ LoRA ที่ MLP ทุกชั้นด้วย (attention-only แพ้ชัดเจน) | [LoRA Without Regret](https://thinkingmachines.ai/blog/lora/) (blog ที่มีผลทดลอง) · [2405.09673](https://arxiv.org/abs/2405.09673) | [ใกล้ 4B] (8B / 7B) |
| LR ของ LoRA ≈ 10× full FT · batch ไม่ใหญ่ · RL ใช้ rank เล็กได้ | LoRA Without Regret | [ใกล้ 4B] |
| SFT 1–2 epoch แล้วเลือก checkpoint จาก forgetting suite (OOD ดีที่สุดตั้งแต่ช่วงต้น) | [SDFT 2601.19897](https://arxiv.org/abs/2601.19897) · [2509.12235](https://arxiv.org/abs/2509.12235) | [ใกล้ 4B] / ไม่ระบุ |
| **ลดขนาด "intruder dimensions" หลังเทรน** (scale down LoRA) ลดการลืมโดยงานหลักเสียน้อย | ระบุสาเหตุการลืมของ LoRA ได้และกู้คืนได้ | หลายขนาด | [2410.21228](https://arxiv.org/abs/2410.21228) · SmolLM3 merge 0.9/0.1 [ใกล้ 4B] |

### A4. ลำดับการเทรน (SFT → RL)

| ปฏิบัติ | หลักฐาน | ขนาด |
|---|---|---|
| **SFT ยังจำเป็นเพื่อให้ format นิ่ง** แต่ RL generalize ได้ดีกว่า SFT | [2501.17161](https://arxiv.org/abs/2501.17161) | ไม่ใช่งาน LLM ข้อความล้วน (เกมการ์ด/VLM) |
| **tool-calling ด้วย RL ที่ใช้ reward แบบ binary (format + ความถูกของ call)** ชนะ SFT จาก trace ที่ distill มา | Tool-N1-7B/14B ชนะ GPT-4o (benchmark ในเปเปอร์รวม BFCL, API-Bank, ACEBench) | [ใกล้ 4B] (Qwen2.5-7B; 14B) | [2505.00024](https://arxiv.org/abs/2505.00024) |
| **reward แบบละเอียดสำหรับ tool** (แยกชื่อ / พารามิเตอร์ / ค่า) ด้วย GRPO | +17% จาก base, +15% จาก SFT | [ใกล้ 4B] (Qwen2.5-1.5B/3B/7B, Llama-3.2-3B) | [ToolRL 2504.13958](https://arxiv.org/abs/2504.13958) |
| **RL ของ agent**: clip-higher, overlong reward shaping, รักษา entropy · **คิดให้รอบคอบแล้วเรียก tool น้อยครั้ง** ชนะการเรียกถี่หรือคิดยืดยาว | ทั้งความแม่นและประสิทธิภาพของ tool | **[ใกล้ 4B]** | [2510.11701](https://arxiv.org/abs/2510.11701) |
| **Dr. GRPO** (ตัด bias ของการ normalize ความยาว) เพราะ GRPO เดิมทำให้คำตอบผิดยาวขึ้นเอง | token efficiency ดีขึ้นโดยความแม่นเท่าเดิม | [ใกล้ 4B] (7B) | [2503.20783](https://arxiv.org/abs/2503.20783) · กลไกเดียวกัน: [2504.05185](https://arxiv.org/abs/2504.05185) |
| **RL ขั้นที่ 2 สั้นๆ บนโจทย์ที่แก้ได้** ช่วยลดความยาวโดยไม่เสียความแม่น | ความยาวลดลงมาก ความแม่นเท่าเดิมหรือดีขึ้น | [ใกล้ 4B] (R1-Distill-Qwen-1.5B/7B) | [2504.05185](https://arxiv.org/abs/2504.05185) |

### A5. Adaptive reasoning length (รายละเอียดอยู่ใน `RESEARCH_NOTES.md` §4)
- **ใช้ความยากที่วัดจากตัวนักเรียนเอง** (pass rate จาก 8 ตัวอย่าง) แล้วแบ่งถัง ข้อง่ายใช้คำตอบที่ถูกและสั้นที่สุด ข้อยากยอมให้ยาว
  - AdaptThink: ความยาว −53% ความแม่น +2.4% [ใกล้ 4B (1.5B/7B)] [2505.13417](https://arxiv.org/abs/2505.13417)
  - ShorterBetter [ใกล้ 4B] [2504.21370](https://arxiv.org/abs/2504.21370)
- **RL ที่ใส่งบความยาวใน prompt** (L1/LCPO) หรือลดเพดาน token ทีละรอบ (ThinkPrune: AIME24 ความยาวลดครึ่ง ความแม่น −2%) [ใกล้ 4B (1.5B)] [2503.04697](https://arxiv.org/abs/2503.04697) · [2504.01296](https://arxiv.org/abs/2504.01296)
- **ใส่ trace ที่ตัดกลางทางราว 5%** เพื่อให้รูปแบบไม่พังเมื่อใช้ budget forcing [ไกล 4B (9B hybrid)] [Nemotron Nano 2](https://arxiv.org/abs/2508.14444)

### A6. Tool calling
- **ใส่ข้อมูล "irrelevance" (ไม่ควรเรียก tool) + function masking** (ซ่อนหรือสุ่มชื่อฟังก์ชันเพื่อไม่ให้โมเดลยึดชื่อ) ทำให้ผลข้าม benchmark นิ่งขึ้น [ใกล้ 4B (Qwen2-1.5B/7B, Qwen1.5-4B)] [Hammer 2410.04587](https://arxiv.org/abs/2410.04587)
- **ใส่ตัวอย่างลบ (negative samples)** ลด hallucination ของ agent · แยกการเรียนรู้ "รูปแบบ" ออกจาก "การคิด" [ใกล้ 4B (Llama2-7B)] [Agent-FLAN 2403.12881](https://arxiv.org/abs/2403.12881)
- **ผสมข้อมูล general** เพื่อไม่ให้เสียความสามารถทั่วไปเมื่อเทรน agent [Llama2 7–70B] [AgentTuning 2310.12823](https://arxiv.org/abs/2310.12823)

### A7. Search agent
- **mask token ของผลค้นหาออกจาก loss** ช่วยให้ RL นิ่ง และใช้ reward ตามผลลัพธ์แบบง่าย: Qwen2.5-3B +20%, 7B +41% เทียบกับ RAG [ใกล้ 4B] [Search-R1 2503.09516](https://arxiv.org/abs/2503.09516)
- **ใช้ reward แบบ EM + penalty ระดับ action** (F1 ล้วนทำให้โมเดลเลี่ยงการตอบจน training พัง) · prompt แบบ "Fast Thinking" นิ่งกว่า · REINFORCE ดีกว่า PPO และใช้การค้นน้อยกว่า: Search-R1++ 3B 0.289 → 0.331 [ใกล้ 4B] [2602.19526](https://arxiv.org/abs/2602.19526)

### A8. ภาษาไทย
- **สูตรของ Typhoon-S**: SFT ที่มีข้อมูลภาษาไทย + on-policy distillation + RFT ขนาดเล็กด้วย **InK-GRPO** (GRPO + next-word-prediction loss) ช่วยงานกฎหมายและความรู้ไทย**โดยไม่เสียความสามารถทั่วไป** ทดลองบน **Qwen3-4B / 8B** [ใกล้ 4B] [2601.18129](https://arxiv.org/abs/2601.18129)
- **ไม่บังคับให้คิดเป็นภาษาของผู้ใช้ด้วย prompt** เพราะเสียความแม่น ถ้าอยากให้คิดเป็นไทย ใช้ post-training ประมาณ 100 ตัวอย่างลดปัญหาได้ แต่ยังเสียความแม่นบางส่วน [2505.22888](https://arxiv.org/abs/2505.22888) → **สูตรของเรา:** คำตอบสุดท้ายเป็นไทย ส่วนการคิดปล่อยตามธรรมชาติ แล้ววัดทั้งสองแบบก่อนตัดสินใจ

### A9. Long context
- **SFT ด้วยข้อมูลสั้นคุณภาพดีอย่างเดียวก็ให้ผล long-context ดี** [ใกล้ 4B (8B)] [ProLong 2410.02660](https://arxiv.org/abs/2410.02660)
- **เฝ้าดู long-context recall ของโมเดล hybrid หลัง CoT-SFT** และกู้คืนด้วย QK-Restore ถ้าพัง: HypeNet-5B S3@256K 65.4 → 76.4 [ใกล้ 4B] [2606.11052](https://arxiv.org/abs/2606.11052) (ข้อนี้มาจาก `RESEARCH_NOTES` ที่ผู้ช่วยค้นอ่าน abstract แล้ว)
- การ์ดทางการแนะนำ context ตอน inference **≥128K เพื่อรักษาความสามารถในการคิด** [ข้อเท็จจริงทางเทคนิค จาก model card] เทรนที่ 16K ได้ แต่ตอนใช้งานไม่ควรตั้ง max length ต่ำเกินไป

---

## B. ตัดออก: มีคนลองแล้วไม่ดีขึ้นหรือแย่ลง

| สิ่งที่ตัดออก | ใครลอง / ผล | ขนาด | แหล่ง |
|---|---|---|---|
| **โมเดลเดียวที่มีทั้งโหมด think และ no-think (hybrid)** เพื่อประหยัด | ทีม Qwen เลิกใช้ hybrid ใน Qwen3-2507 แล้วแยกเป็นโมเดล Instruct และ Thinking "to maximize quality" | 4B–235B | [The Register](https://www.theregister.com/2025/07/31/alibaba_qwen3_hybrid_thinking/) (ข่าวที่อ้างคำแถลงของ Qwen) → **เรา: think เสมอ ห้ามผสมตัวอย่าง no-think** |
| **SFT ด้วยข้อมูลแบบตอบตรง (answer-only) บนโมเดล thinking** | Olmo-3-7B-Think: ความแม่น 31.2 → 23.5 · เทรนโหมด no-think แล้วรั่วไปโหมด think 42–79% (มี Qwen3-4B) | [ใกล้ 4B] | [SDFT 2601.19897](https://arxiv.org/abs/2601.19897) · [Thinking Leakage 2609.28682](https://arxiv.org/abs/2609.28682) |
| **ใช้ long CoT ของโมเดลใหญ่ล้วน** กับโมเดลเล็ก | Qwen2.5-3B แย่กว่าแบบผสม (40.3 vs 45.9) | [ใกล้ 4B] | [2502.12143](https://arxiv.org/abs/2502.12143) |
| **reward ที่ให้คะแนนตามความยาวการคิด** (ยิ่งยาวยิ่งดี) ในงาน tool | "Longer reasoning trace is not inherently better and length rewards can degrade performance" | [ใกล้ 4B] (1.5B–7B) | ToolRL §ผลของ length reward ([2504.13958](https://arxiv.org/abs/2504.13958)) |
| **ยืดการคิดให้ยาวขึ้นเรื่อยๆ** | CoT ที่ยาวเกินไปทำให้คณิตบางโดเมนแย่ลง | [ไกล 4B] (32B) | [2502.18080](https://arxiv.org/abs/2502.18080) |
| **ใช้ GRPO แบบเดิมไม่ดัดแปลง** (normalize ตามความยาว) | ทำให้คำตอบผิดยาวขึ้นเอง | [ใกล้ 4B] (7B) | [2503.20783](https://arxiv.org/abs/2503.20783) · [2504.05185](https://arxiv.org/abs/2504.05185) |
| **F1 reward ล้วนสำหรับ search agent** | training พังเพราะโมเดลเลี่ยงการตอบ | [ใกล้ 4B] | [2602.19526](https://arxiv.org/abs/2602.19526) |
| **GRPO สำหรับ search agent** (เมื่อมีทางเลือกอื่น) | เสถียรน้อยที่สุดเมื่อเทียบกับ REINFORCE / PPO | [ใกล้ 4B] | [2602.19526](https://arxiv.org/abs/2602.19526) (ผลนี้เฉพาะงาน search อย่าเหมารวม) |
| **บังคับด้วย prompt ให้ "คิดเป็นภาษาไทย"** | อ่านง่ายขึ้นแต่ความแม่นลดลง | หลายขนาด | [2505.22888](https://arxiv.org/abs/2505.22888) |
| **synthetic long-context instruction data** สำหรับ SFT | "adding synthetic data does not improve … as little as 1% synthetic data hurts" | [ใกล้ 4B] (8B) | ProLong §5 ([2410.02660](https://arxiv.org/abs/2410.02660)) → ลดลำดับความสำคัญของหมวด H เหลือ "ใช้เป็น eval / ใช้น้อยมาก" |
| **ถือว่า SFT แล้วตามด้วย RL ดีกว่าเสมอ** | สำหรับ tool-calling, SFT-then-RL "does not necessarily outperform pure RL" | [ใกล้ 4B] (7B) | [2505.00024](https://arxiv.org/abs/2505.00024) → ใช้ SFT แค่สั้นๆ เพื่อสอนรูปแบบ |
| **trajectory สังเคราะห์ที่เย็บต่อกัน** (stitched) | อ่อนกว่า trajectory จริงแบบ end-to-end อย่างชัดเจน | [ใกล้ 4B] | [2510.11701](https://arxiv.org/abs/2510.11701) |
| **เชื่อผล RL บน Qwen โดยไม่มี control** | Qwen2.5-Math-7B ได้ +21.4 จาก **reward สุ่ม** (reward จริงได้ +29.1) และผลนี้ไม่เกิดกับ Llama / OLMo | [ใกล้ 4B] (7B) | [Spurious Rewards 2506.10947](https://arxiv.org/abs/2506.10947) → ทุก RL run ต้องเทียบกับ baseline ที่ใช้ reward สุ่มหรือ format-only |
| **NEFTune** สำหรับงาน reasoning/tool | ผลที่รายงานเป็นคุณภาพแชท (AlpacaEval) ไม่มีหลักฐานกับ reasoning / tool / ความแม่นวัดได้ | 7B | [2310.05914](https://arxiv.org/abs/2310.05914) → ไม่ใส่ (ไม่ช่วยเป้าหมายเรา) |
| **QLoRA 4-bit** สำหรับ Qwen3.5 | Unsloth แนะนำ bf16 LoRA สำหรับ Qwen3.5 | — | [Unsloth Qwen3.5](https://unsloth.ai/docs/models/qwen3.5/fine-tune) (เอกสารของผู้ทำเครื่องมือ ไม่ใช่ paper) |
| ชุด **Nemotron-Post-Training-Dataset-v1 (chat)** เป็นแหล่ง prompt ง่าย | prompt ถูกลบเป็นข้อความว่าง (ตรวจจากแถวจริง) | — | `OPEN_QUESTIONS.md` ข้อ 10 · แก้ใน `RESEARCH_NOTES.md` แล้ว |

---

## C. ยังไม่ใส่ในสูตรหลัก (หลักฐานแย้งกันหรือยังไม่พอสำหรับ 4B)

| เรื่อง | ทำไมยังไม่ใส่ |
|---|---|
| **"Less is more"** (LIMO 817 ข้อ, s1 1K ข้อ, LIMI 78 ข้อ) | ทดลองบนโมเดล ≥32B ([2502.03387](https://arxiv.org/abs/2502.03387), [2501.19393](https://arxiv.org/abs/2501.19393), [2509.17567](https://arxiv.org/abs/2509.17567)) ส่วนงานบนโมเดลเล็กพบว่าเรียนจากตัวอย่างยากได้ไม่ดี ([2502.12143](https://arxiv.org/abs/2502.12143)) → ใช้ "คัดคุณภาพ" ได้ แต่อย่าลดข้อมูลเหลือหลักร้อย |
| **On-policy distillation / SDFT** | ได้ผลดีที่ 8B (TM blog, Qwen3) แต่ SDFT ที่ 3B ไม่ชนะ SFT และมีรายงานว่าทำ reasoning collapse ได้ (`RESEARCH_NOTES` §3) → ใช้เป็นขั้นกู้คืน ไม่ใช่ขั้นหลัก และต้องตรวจก่อนว่า tokenizer ของครูกับนักเรียนตรงกัน |
| **DoRA / LoRA+ / rsLoRA / PiSSA** | ไม่พบงานที่เทียบแล้วชนะ LoRA ธรรมดาที่ตั้ง LR ถูกต้องในงานแบบเรา (LoRA Without Regret พบว่า LoRA ธรรมดาเท่ากับ FullFT ในหลายกรณี) → ไม่จำเป็น |
| **ใส่ LoRA ที่ชั้น DeltaNet (`in_proj_*`, `out_proj`)** | ยังไม่มีงานที่วัดตรงๆ บน Gated DeltaNet → ต้องทำ ablation เอง (มี/ไม่มี) |
| **บังคับให้ think เป็นภาษาไทย 100%** | เสียความแม่น (B) แต่ผู้ใช้อาจต้องการอ่าน reasoning → รอทีมตัดสินใจ |

---

## D. รายการตรวจก่อนเริ่มเทรน (ทำได้ภายใน 1 วัน)
1. ☐ เรนเดอร์ converter output ผ่าน `chat_template.jinja` แล้วเทียบ token กับ output ของ vLLM (`--reasoning-parser qwen3 --tool-call-parser qwen3_coder`) ว่าตรงกัน
2. ☐ ทดสอบ packing: loss ของ batch ที่ pack = loss ของ batch ที่ไม่ pack (ไม่งั้นปิด packing)
3. ☐ วัด baseline ของ Qwen3.5-4B: ความแม่น, จำนวน thinking token ต่อถังความยาก, BFCL-style, When2Call (ส่วนที่ไม่ได้มาจาก BFCL), ThaiExam (ไม่รวม onet), RULER 16K
4. ☐ LoRA 100 step บน GPU จริง ที่ความยาว 16K และ target รวมชั้น DeltaNet แล้วดูว่า memory และ throughput ใช้ได้
5. ☐ ตั้ง control ของ RL: run ที่ใช้ reward สุ่มหรือ format-only คู่ไปกับ run จริงอย่างน้อย 1 ครั้ง
