# RESEARCH_NOTES: ความยาวการคิดแบบปรับตามโจทย์ (F) และการคงความสามารถเดิมระหว่าง LoRA (G)

เป้าหมาย: Qwen3.5-4B (hybrid Gated DeltaNet) · LoRA · คิดก่อนตอบเสมอ · EN+TH · agent/tool · context 16K · ครู Qwen3.8-27B
ป้ายกำกับ: **[ใกล้ 4B]** = วัดบนโมเดล 1.5–8B · **[ไม่ใช่ 4B]** = วัดบนโมเดลขนาดอื่น · **[ความเห็น]** = ข้อสรุปของผู้เขียนเอง ยังไม่มีงานวิจัยวัดตรงๆ
รายละเอียดและสถานะ VERIFIED ดูได้ที่ `hunt_sections/F.md` และ `hunt_sections/G.md`

---

## 1. ตั้งค่า LoRA สำหรับ Qwen3.5-4B

**target modules**
- Qwen3.5-4B มี 32 ชั้น แบ่งเป็น Gated DeltaNet 24 ชั้น และ full attention 8 ชั้น (ทุกชั้นที่ 4) · ชื่อโมดูลของชั้น DeltaNet คือ `in_proj_qkv, in_proj_z, in_proj_b, in_proj_a, out_proj` · `q/k/v/o_proj` มีเฉพาะ 8 ชั้น full attention · ถ้าตั้ง target เป็นแค่ q/k/v/o + MLP เหมือนตัวอย่างของ Unsloth ส่วน mixer ของ 24 ชั้นจะไม่ถูกแตะเลย — [config](https://huggingface.co/Qwen/Qwen3.5-4B/raw/main/config.json), [modeling](https://raw.githubusercontent.com/huggingface/transformers/main/src/transformers/models/qwen3_5/modeling_qwen3_5.py), [Unsloth](https://unsloth.ai/docs/models/qwen3.5/fine-tune) [ใกล้ 4B]
- **ให้ความสำคัญกับ MLP ก่อน** (`gate_proj, up_proj, down_proj` ทุกชั้น): attention-only แพ้ MLP-only อย่างชัดเจน และ MLP+attention ไม่ได้ดีกว่า MLP-only — [LoRA Without Regret](https://thinkingmachines.ai/blog/lora/) (8B, 30B-A3B), [LoRA Learns Less](https://arxiv.org/abs/2405.09673) (7B) [ใกล้ 4B]
- **ข้อเสนอเริ่มต้น:** MLP ทุกชั้น + `q_proj,k_proj,v_proj,o_proj` (8 ชั้น) + `in_proj_qkv,in_proj_z,out_proj` (24 ชั้น DeltaNet) · **อย่า** ใส่ LoRA ที่ `conv1d, A_log, dt_bias` · `in_proj_a/b` (output 32 มิติ) จะใส่หรือไม่ก็ได้ เพราะเงื่อนไขหลักคือ LoRA ใช้กับ linear projection ได้ แต่ "fails on SSM modules" — [PEFT-SSM](https://arxiv.org/abs/2410.09016) [ไม่ใช่ 4B] + [ความเห็น]
- **ระวัง `"all-linear"`** เพราะคลาสเป็น `Qwen3_5ForConditionalGeneration` (มี vision tower) all-linear อาจลาม LoRA ไปถึงชั้น vision ให้ระบุชื่อโมดูลเฉพาะ language model แทน [ความเห็น]
- **ทางเลือกเพื่อรักษา long-context:** ทำ ablation โดยตัด `q_proj,k_proj` ออกจาก target หรือทำ QK-Restore หลัง merge (คืน W_Q, W_K ของ 8 ชั้น full attention) เพราะ CoT-SFT ทำ NIAH ของ hybrid พัง — [Attention Amnesia](https://arxiv.org/abs/2606.11052) (HypeNet-5B: S3@256K 65.4 → 76.4 หลัง restore) [ใกล้ 4B]

**rank / alpha**
- **SFT: r=32, α=32** (scale α/r) เป็นค่าตั้งต้น ทำ ablation ที่ r=16 และ r=64 · บน Qwen3-4B, r=32 ให้คุณภาพงานดีที่สุด ส่วน rank เล็กเก็บความรู้ทั่วไปได้มากกว่า — [2605.17774](https://arxiv.org/abs/2605.17774) [ใกล้ 4B] · TM ใช้ α=32 คงที่และ LR แทบไม่ขึ้นกับ rank — [blog](https://thinkingmachines.ai/blog/lora/) [ใกล้ 4B]
- **RL / on-policy distillation: r=8–32 พอ** (RL ใช้แค่ rank 1 ก็เท่า FullFT) — [blog](https://thinkingmachines.ai/blog/lora/) [ใกล้ 4B (8B)]
- ใช้ **bf16 LoRA ไม่ใช่ QLoRA 4-bit** — [Unsloth](https://unsloth.ai/docs/models/qwen3.5/fine-tune) [ใกล้ 4B แต่เป็นคำแนะนำของผู้ทำเครื่องมือ]

**learning rate / epoch / batch**
- **LR ของ LoRA ≈ 10× LR ของ full FT** (ใช้ราว 15× ถ้า run สั้นไม่เกิน ~100 step) — [blog](https://thinkingmachines.ai/blog/lora/) [ใกล้ 4B] · full FT ของโมเดล <14B ใน Mix-Long ใช้ 1e-5 — [2502.12143](https://arxiv.org/abs/2502.12143) [ใกล้ 4B] → **LoRA SFT เริ่มที่ 1e-4 แล้ว sweep {5e-5, 1e-4, 2e-4}** ส่วน Biderman พบว่า best LR ของ LoRA คือ 2e-4 (math IFT) และ 5e-4 (code IFT) เทียบกับ full FT ที่ 1e-5 และ 5e-5 — [2405.09673](https://arxiv.org/abs/2405.09673) [ใกล้ 4B (7B)]
- **1–2 epoch:** SFT overfit เร็วและแทบไม่ได้ประโยชน์จาก epoch ที่ 2 — [SDFT](https://arxiv.org/abs/2601.19897) [ใกล้ 4B (7B)] · OOD สูงสุดตั้งแต่ช่วงต้นของ SFT แล้วตกลง จึงควรเซฟ checkpoint ถี่ๆ แล้วเลือกจาก forgetting suite — [2509.12235](https://arxiv.org/abs/2509.12235) [ไม่ใช่ 4B/ไม่ระบุ]
- **batch เล็กถึงปานกลาง** (effective batch ~32 sequence) เพราะ LoRA ทน batch ใหญ่ได้น้อยกว่า FullFT — [blog](https://thinkingmachines.ai/blog/lora/) [ใกล้ 4B]
- ถ้าเห็นว่าลืมมากใน batch ที่ loss สูง ให้ลอง **ลด LR ตาม loss** (FINCH: บน Qwen3-4B TruthfulQA degradation ลดลง 5×) — [2605.20005](https://arxiv.org/abs/2605.20005) [ใกล้ 4B]

## 2. การผสมข้อมูลกันลืม (replay)

- **ผสม general/chat replay อย่างน้อย 30%** ใน TM, เอกสาร:แชท = 70/30 ทำให้ IF-eval ลดจาก 85 เหลือ 79 (ถ้าไม่ผสมเหลือ 45) แปลว่า 30% ยังไม่พอจะกลับไปที่เดิม — [OPD blog](https://thinkingmachines.ai/blog/on-policy-distillation/) [ใกล้ 4B (8B)] → **ข้อเสนอ: replay 30–40% ของ token** [ความเห็น]
- **replay ควรเป็นคำตอบที่ Qwen3.5-4B ตัวเดิมสร้างเอง** (มี thinking และกรองด้วย verifier หรือ judge) ไม่ใช่ชุดแชทเก่าจากโมเดลอื่น · self-generated replay "nearly eliminating forgetting" — [2605.26097](https://arxiv.org/abs/2605.26097) [ไม่ระบุขนาด] · ข้อมูลที่ใกล้ on-policy คือเหตุผลที่ RL ลืมน้อย — [Retaining by Doing](https://arxiv.org/abs/2510.18874) [ใกล้ 4B]
- **สัดส่วน reasoning ไม่ควรต่ำกว่า ~75%** ถ้ามีตัวอย่างที่ไม่มีการคิด สำหรับเรา **ทุกตัวอย่างต้องมี `<think>` ที่ไม่ว่าง** เพราะเป้าหมายคือคิดเสมอ — [Unsloth](https://unsloth.ai/docs/models/qwen3.5/fine-tune) [ความเห็นของผู้ทำเครื่องมือ]
- **ข้อมูล answer-only อันตราย:** บน Olmo-3-7B-Think, SFT ด้วยคำตอบที่ไม่มี reasoning ทำให้ความแม่นลด 31.2 → 23.5 และ token ลด 4,612 → 3,273 — [SDFT](https://arxiv.org/abs/2601.19897) [ใกล้ 4B (7B)] · เทรนโหมด NoThink แล้วโมเดลไหลไปทาง Think (leakage 42–79%, มี Qwen3-4B) — [Thinking Leakage](https://arxiv.org/abs/2609.28682) [ใกล้ 4B] → ถ้าชุดไหนมีแต่คำตอบสุดท้าย (เช่น ToolACE หรือ glaive) ให้ครูเขียน think ใหม่ก่อนเสมอ [ความเห็น]
- **ให้ครูเขียนคำตอบใหม่ใน "สไตล์ของนักเรียน":** ข้อมูลที่โมเดลคุ้นเคย (perplexity ต่ำ) ช่วยคงความสามารถเดิม — [2402.11192](https://arxiv.org/abs/2402.11192) [ไม่ระบุขนาด] · KL จาก base ทำนายการลืม — [RL's Razor](https://arxiv.org/abs/2509.04259) [ใกล้ 4B (3B)] → วัด NLL ของคำตอบครูภายใต้ Qwen3.5-4B แล้วตัดหรือแก้ตัวอย่างที่ NLL ต่อ token สูงผิดปกติ (สูงกว่า percentile 90) [ความเห็น]
- **Iterative-SFT:** สร้างข้อมูลส่วน "ง่าย" ใหม่จากนักเรียนทุก epoch (เก็บเฉพาะข้อที่ถูก) จะลืมน้อยถึงไม่ลืม — [Retaining by Doing](https://arxiv.org/abs/2510.18874) [ใกล้ 4B]

## 3. ขั้นกู้คืนหลัง SFT (เลือกอย่างใดอย่างหนึ่ง เรียงจากถูกไปแพง)

1. **ย่อ update หรือ merge:** ลด scale ของ LoRA (เช่น ×0.8) หรือ merge แบบ linear กับ checkpoint ก่อนหน้า (SmolLM3 ใช้ 0.9/0.1 เพื่อกู้ RULER) — [SmolLM3](https://huggingface.co/blog/smollm3) [ใกล้ 4B (3B)], [grafting](https://arxiv.org/abs/2610.05872) [ไม่ระบุขนาด] · เลือก scale โดยดู forgetting suite [ความเห็น]
2. **QK-Restore** สำหรับ long-context ของ hybrid — [2606.11052](https://arxiv.org/abs/2606.11052) [ใกล้ 4B]
3. **On-policy distillation / SDFT:** นักเรียนสุ่มคำตอบเอง แล้วใช้ per-token reverse KL เทียบกับครู · TM กู้ IF-eval จาก 79 กลับมา 83 โดยไม่เสียความรู้ใหม่ · Qwen3-8B: OPD ได้ 74.4 AIME'24 ใช้ 1,800 GPU-h ขณะที่ RL ได้ 67.6 ใช้ 17,920 GPU-h — [OPD blog](https://thinkingmachines.ai/blog/on-policy-distillation/), [Qwen3](https://arxiv.org/abs/2505.09388) [ใกล้ 4B (8B)] · **ข้อควรระวัง:** OPD ต้องใช้ logit ของครูบน token ของนักเรียน **ตรวจแล้ว (2026-10-26): vocab และ merges ของ Qwen3.8-27B กับ Qwen3.5-4B ตรงกันทุกตัว** ครูมีแค่ special token เสียงเพิ่ม 7 ตัว (id 248070–248076) ให้ mask ออก ดังนั้นทำ OPD ได้ (ดู BEST_PRACTICES §F) · SDFT ที่ 3B ไม่ชนะ SFT — [SDFT](https://arxiv.org/abs/2601.19897) [ใกล้ 4B] · มีรายงานว่า OPSD ทำ reasoning collapse ได้ — [2610.05872](https://arxiv.org/abs/2610.05872) [ไม่ระบุขนาด]
4. **RL (GRPO) ด้วย LoRA rank เล็ก:** ลืมน้อยที่สุดเพราะเป็น on-policy (เช่น Qwen2.5-7B MMLU drop: SFT 14.6 vs GRPO 0.2) — [2510.18874](https://arxiv.org/abs/2510.18874) [ใกล้ 4B] · แต่ RLVR ที่ยาวมากก็ยังลืมได้ ควรผสม replay — [RECAP](https://arxiv.org/abs/2510.21978) [ใกล้ 4B (3B/7B VLM)]
- ถ้า tool-use กับ reasoning ฉุดกันเอง ลองแยก LoRA 2 ชุด — [2602.00994](https://arxiv.org/abs/2602.00994) [ไม่ระบุขนาด]

## 4. สร้างข้อมูล "คิดสั้นกับโจทย์ง่าย คิดยาวกับโจทย์ยาก" ด้วยครู Qwen3.8-27B + verifier

**ขั้นที่ 1: รวม prompt ที่มีตัวตรวจ (ไม่ใช้คำตอบเดิม)**
- คณิต: `nvidia/Nemotron-Math-v2` (มี pass rate low/med/high ใน metadata), DeepScaleR, ชุด RLVR ที่มีอยู่ · แชทง่าย: `HuggingFaceTB/smoltalk2` (`*_Qwen3_32B_think`) — **หมายเหตุ:** prompt ของ `Nemotron-Post-Training-Dataset-v1` chat ถูกลบเป็นข้อความว่าง (ตรวจจากแถวจริง ดู OPEN_QUESTIONS ข้อ 10) จึงใช้ไม่ได้ · agent/tool: ชุดที่มีอยู่แล้ว (มี exact-match) · ไทย: ชุดไทยที่มีอยู่ — ดู [F.md](hunt_sections/F.md)

**ขั้นที่ 2: วัดความยากด้วยตัวนักเรียน**
- ให้ Qwen3.5-4B (ก่อนเทรน, thinking) สุ่มคำตอบ **K=8 ครั้งต่อ prompt** (T≈0.6–0.7, max 16K) แล้วคิด pass rate p และความยาวของคำตอบที่ถูก (AdaptThink ใช้ K=16, tokenskip ใช้ N=8 บน Qwen3-4B) — [AdaptThink](https://arxiv.org/abs/2505.13417) [ไม่ใช่ 4B (1.5B/7B)], [tokenskip-qwen3-4b](https://huggingface.co/datasets/leapeto/tokenskip-math-qwen3-4b-thinking-n8) [ใกล้ 4B]
- แบ่งถัง: ง่าย (p ≥ 0.75), กลาง (0.25–0.75), ยาก (0 < p < 0.25), เกินความสามารถ (p = 0 ส่งให้ครู ถ้าครูก็ทำไม่ได้ให้ทิ้ง) [ความเห็น]

**ขั้นที่ 3: ให้ครูสร้างคำตอบตามงบ แล้วเลือกคำตอบที่ถูกและสั้นที่สุด**
- ครูสร้าง N=4–8 คำตอบต่อ prompt ในหลายระดับงบ โดยใช้กลไก thinking budget ของ Qwen (ครบงบแล้วแทรกประโยค stop-thinking ตามด้วย `</think>`) เช่นงบ 256/1K/4K/16K — [Qwen3](https://arxiv.org/abs/2505.09388) [ไม่ใช่ 4B]
- ตรวจด้วย verifier แล้วเลือก **คำตอบที่ถูกจากงบต่ำสุด** หรือ **คำตอบที่ถูกและสั้นที่สุด (SOL)** — [ShorterBetter](https://arxiv.org/abs/2504.21370) [ใกล้ 4B (1.5B/7B)] · สำหรับถังยาก ให้เก็บคำตอบที่ถูกและยาวพอ ไม่ต้องบังคับให้สั้น — [DAST](https://arxiv.org/abs/2503.04472) [ไม่ระบุขนาด]
- **สัดส่วนยาว:สั้น ราว 1:4** เพราะโมเดลเล็กเรียนจาก long CoT ล้วนได้แย่ (Qwen2.5-3B: Mix-Long 45.9 vs long 40.3) — [2502.12143](https://arxiv.org/abs/2502.12143) [ใกล้ 4B] · ระวังว่า 1:4 มาจากคณิตเท่านั้น ควรทำ ablation [ความเห็น]
- **"คิดสั้น" ต้องยังคิดอยู่:** ห้ามใช้ `<think></think>` ว่าง ตั้งขั้นต่ำไว้ราว 1–3 ประโยค [ความเห็น] (สอดคล้องกับ [Thinking Leakage](https://arxiv.org/abs/2609.28682) และ [SDFT/Olmo-Think](https://arxiv.org/abs/2601.19897) [ใกล้ 4B])
- **ใส่ trace ที่ตัดกลางทางราว 5%** (ตัด think ที่ 1–2K token แต่เก็บคำตอบที่ถูก) เพื่อให้ budget forcing ไม่ทำรูปแบบคำตอบพัง — [Nemotron Nano 2](https://arxiv.org/abs/2508.14444) [ไม่ใช่ 4B (9B hybrid)]
- สำหรับ agent/tool: ใช้ "จำนวน tool call และความยาวของ think ต่อ turn" เป็นงบ และเลือก trajectory ที่ถูกโดยใช้ tool call น้อยที่สุดและ think สั้นที่สุด [ความเห็น]
- context 16K: ตัดหรือทิ้งตัวอย่างที่ครูใช้ think เกิน ~12K token ในถังยาก (เช่น trace ของ s1K เฉลี่ย ~9.9K) [ความเห็น]

**ขั้นที่ 4 (ถ้ามีงบ): RL ด้วย length-aware reward บน LoRA rank เล็ก**
- เลือกหนึ่งแบบ: AdaptThink (constrained objective ที่ให้ความแม่นไม่ต่ำกว่า reference) · ShorterBetter (SOL reward) · L1/LCPO (ใส่งบใน prompt) · ThinkPrune (ลดเพดาน token ทีละรอบ) — [AdaptThink](https://arxiv.org/abs/2505.13417) (−53% ความยาว, +2.4% ความแม่น บน 1.5B), [L1](https://arxiv.org/abs/2503.04697), [ThinkPrune](https://arxiv.org/abs/2504.01296) (AIME24 ความยาวลดครึ่ง −2%) [ไม่ใช่ 4B (1.5B)] · ระวัง mode collapse ใน GRPO (Thinkless แก้ด้วย DeGRPO) — [Thinkless](https://arxiv.org/abs/2505.13379) [ไม่ใช่ 4B]

## 5. ตัวชี้วัดที่ต้องติดตามทุก checkpoint

**ประสิทธิภาพของความยาว (F)**
- accuracy ต่อถังความยาก และ **จำนวน thinking token เฉลี่ยต่อถัง** โดยถังง่ายควรสั้นลงชัดเจนและถังยากต้องไม่สั้นลงจนความแม่นตก [ความเห็น]
- **Spearman ρ ระหว่างความยาก (1−p) กับความยาวของ think** ควรเป็นบวกและเพิ่มขึ้นหลังเทรน [ความเห็น]
- **accuracy ต่อ 1K token** และเส้น Pareto accuracy–token ที่ budget 512/1K/2K/4K/8K/16K (รูปแบบเดียวกับตาราง Elastic Reasoning) — [Elastic](https://arxiv.org/abs/2505.05315) [ไม่ใช่ 4B]
- **flip rate:** สัดส่วนข้อที่ถูกที่ budget ต่ำแต่ผิดที่ budget สูง — [R2-Bench analysis](https://huggingface.co/datasets/thenaivekid/reasoning-models-cannot-budget-their-thinking) [ใกล้ 4B (Qwen3-4B-Thinking)]
- **well-formedness ภายใต้ budget forcing:** ปิด `</think>` ครั้งเดียว ไม่คิดต่อหลังปิด และมีคำตอบสุดท้าย — [Nemotron Nano 2](https://arxiv.org/abs/2508.14444) [ไม่ใช่ 4B]
- อัตราการเกิด think ว่างหรือสั้นเกินไป (ควรเป็น 0) และ "hybrid accuracy" (เลือกระดับความยาวได้ตรงกับระดับที่ดีที่สุด) — [LHRM](https://arxiv.org/abs/2505.14631) [ไม่ใช่ 4B]

**forgetting suite (G)** (ใช้ชุดที่ไม่ได้เทรน และรันกับ base เป็น baseline ก่อน)
- ความรู้และการทำตามคำสั่ง: IFEval, MMLU-Pro (เป็น eval ของเราอยู่แล้ว ห้ามเทรน) — [RL's Razor](https://arxiv.org/abs/2509.04259), [Retaining by Doing](https://arxiv.org/abs/2510.18874) ใช้ชุดแบบนี้ [ใกล้ 4B]
- reasoning: GSM8K test, AIME24/25, MATH500 วัดทั้งความแม่นและความยาว
- tool/agent: BFCL, Terminal-Bench subset · ภาษาไทย: ชุดข้อสอบไทยที่**ไม่ได้**อยู่ในข้อมูลเทรน
- **long-context:** NIAH หรือ RULER ที่ 8K/16K/32K เพราะ hybrid เสี่ยงลืมจาก CoT-SFT — [Attention Amnesia](https://arxiv.org/abs/2606.11052) [ใกล้ 4B]
- **KL(fine-tuned ‖ base)** บน prompt ทั่วไปชุดคงที่ ~500 prompt ใช้เป็นสัญญาณเตือนล่วงหน้าที่ถูก เพราะ R² กับการลืมเท่ากับ 0.71 ใน LLM — [RL's Razor](https://arxiv.org/abs/2509.04259) [ใกล้ 4B (3B)]
- safety/refusal และ calibration — [FINCH](https://arxiv.org/abs/2605.20005) [ใกล้ 4B]
- เลือก checkpoint จากผลรวม (target gain − forgetting drop) ไม่ใช่ checkpoint สุดท้าย — [2509.12235](https://arxiv.org/abs/2509.12235) [ไม่ระบุขนาด]

## 6. ความเสี่ยงและข้อจำกัดที่ต้องบอกตรงๆ
- ตัวเลขส่วนใหญ่วัดบน Qwen2.5, Llama หรือ R1-Distill ที่เป็น dense transformer **ยังไม่มีงานที่วัด LoRA-forgetting บน Gated DeltaNet โดยตรง** การตั้ง target ที่ชั้น DeltaNet จึงเป็น [ความเห็น] ควรทำ ablation 2 แบบ (มีและไม่มี DeltaNet proj) แล้วเทียบ forgetting suite
- งาน adaptive length เกือบทั้งหมดทำบนคณิตเท่านั้น การนำไปใช้กับ tool/agent และภาษาไทยยังไม่มีหลักฐาน [ความเห็น]
- Nemotron-Math-v2 ตัดโจทย์ง่ายทิ้ง จึงต้องหาโจทย์ "ง่าย" จากแหล่งอื่น (GSM8K train, แชทง่าย, tool call ง่าย) เพื่อให้มีถังสั้นมากพอ — [การ์ด](https://huggingface.co/datasets/nvidia/Nemotron-Math-v2)
