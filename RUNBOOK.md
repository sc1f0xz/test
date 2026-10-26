# RUNBOOK — ขั้นตอนลงมือจริง (สำหรับ agent ที่จะทำงานต่อ)

> เขียนเมื่อ 2026-10-26 · อ่านคู่กับ `BEST_PRACTICES.md` (เหตุผลของแต่ละขั้น) และ `TOP_DOWNLOAD_LIST.md` (ชุดข้อมูล)
> **ป้ายกำกับในเอกสารนี้**
> - **[ตรวจแล้ว]** = คำสั่ง/ตัวเลือกยืนยันจากเอกสารหรือซอร์สโค้ดจริงของเครื่องมือ (มีลิงก์)
> - **[ต้องปรับ]** = มีค่าที่ต้องใส่เอง (host, port, path)
> - **[ยังไม่ได้ทดสอบ]** = ยังไม่มีใครรันจริงบนเครื่องของทีม ให้ลองก่อนใช้จริง

## 0. ภาพรวมเครื่อง

| เครื่อง | หน้าที่ |
|---|---|
| **4090 24GB ที่เช่า** (RunPod/Vast) | (1) เปิด API ของโมเดล (vLLM) ให้ครูหรือนักเรียนสร้างข้อมูล (2) เทรน LoRA · **ห้ามวางแผนรัน Docker บนเครื่องนี้** เพราะผู้ให้บริการไม่อนุญาต Docker-in-Docker |
| **PC ของทีม** (Windows 11, RAM 32GB, i5-9600K 6C/6T, RTX 2060 8GB) | (1) รัน container ของโจทย์ SWE ผ่าน Docker Desktop + WSL2 (2) ใช้งานโมเดลที่เสร็จแล้วด้วย llama.cpp |

ลำดับงาน: **ขั้น 1–3 (pilot SWE) → ขั้น 4 (เตรียมข้อมูล) → ขั้น 5 (สร้างคำตอบ) → ขั้น 6 (เทรน) → ขั้น 7 (แปลงเป็น GGUF) → ขั้น 8 (วัดผล)** ขั้น 4–8 ทำได้โดยไม่ต้องรอ pilot SWE

---

## 1. ตั้งค่า PC ของทีม (Windows 11 + WSL2 + Docker)

1. เปิด virtualization (Intel VT-x) ใน BIOS
2. ติดตั้ง WSL2 + Ubuntu: เปิด PowerShell แบบ admin แล้วรัน `wsl --install -d Ubuntu`
3. สร้างไฟล์ `C:\Users\<ชื่อผู้ใช้>\.wslconfig` แล้วรัน `wsl --shutdown` หนึ่งครั้ง **[ต้องปรับ]**
   ```ini
   [wsl2]
   memory=24GB
   processors=6
   ```
4. ติดตั้ง Docker Desktop → Settings → General: เลือก "Use the WSL 2 based engine" → Resources → WSL integration: เปิดให้ Ubuntu → Resources → Advanced: ย้าย "Disk image location" ไปไดรฟ์ที่มีพื้นที่ว่างมาก
5. ใน Ubuntu (WSL) ให้ทำงานใน `~/work` (ไฟล์ระบบของ WSL) **ไม่ใช่ `/mnt/c/...`** เพราะการอ่านเขียนไฟล์ข้ามไปฝั่ง Windows ช้า
   ```bash
   docker run --rm hello-world          # ทดสอบ Docker
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

## 2. เปิด API โมเดลบน 4090 ที่เช่า แล้วต่อ SSH tunnel มาที่ PC

**ครู Qwen3.8-27B แบบ 4-bit (AWQ) บน 4090 ใบเดียว** **[ยังไม่ได้ทดสอบเรื่อง VRAM]**
```bash
pip install -U vllm
vllm serve cyankiwi/Qwen3.8-27B-AWQ-INT4 \
  --served-model-name teacher \
  --max-model-len 32768 --gpu-memory-utilization 0.92 \
  --reasoning-parser qwen3 --enable-auto-tool-choice --tool-call-parser qwen3_coder \
  --port 8000
```
- ตัวเลือก `--reasoning-parser qwen3 --tool-call-parser qwen3_coder` มาจากการ์ดของ Qwen3.5 **[ตรวจแล้ว]** ([Qwen3.5-4B card](https://huggingface.co/Qwen/Qwen3.5-4B)) · ของ 3.8 ให้เทียบกับ [vLLM recipe ของ Qwen3.8-27B](https://recipes.vllm.ai/Qwen/Qwen3.8-27B) อีกครั้ง
- ถ้า VRAM ไม่พอ (OOM) ให้ลด `--max-model-len` เหลือ 16384
- [cyankiwi/Qwen3.8-27B-AWQ-INT4](https://huggingface.co/cyankiwi/Qwen3.8-27B-AWQ-INT4) (Apache-2.0, การ์ดระบุว่ารองรับ vLLM) **[ตรวจแล้ว]**

**นักเรียน Qwen3.5-4B** (ใช้ตอนให้นักเรียนตอบเอง) **[ตรวจแล้ว จากการ์ด]**
```bash
vllm serve Qwen/Qwen3.5-4B --served-model-name student --max-model-len 32768 \
  --reasoning-parser qwen3 --enable-auto-tool-choice --tool-call-parser qwen3_coder --port 8001
```

**SSH tunnel จาก PC (ใน WSL)** **[ต้องปรับ]**
```bash
ssh -N -L 8000:localhost:8000 -p <SSH_PORT> root@<HOST_ของ_4090>
# เช็ค: curl http://localhost:8000/v1/models
```

## 3. Pilot SWE: mini-swe-agent + SWE-smith (20 โจทย์)

**ติดตั้ง** (ใน WSL) **[ตรวจแล้ว]** ([README](https://github.com/SWE-agent/mini-swe-agent), ระดับความยาก 1/5)
```bash
cd ~/work && uv tool install mini-swe-agent    # หรือ: pip install mini-swe-agent
export MSWEA_COST_TRACKING="ignore_errors"     # โมเดล local ไม่มีราคา [ตรวจแล้ว จาก docs/models/local_models.md]
```

**ไฟล์ config ของโมเดล** (คัดลอกจาก `src/minisweagent/config/benchmarks/swebench.yaml` แล้วแก้ส่วน `model:`) **[ตรวจแล้ว จาก docs/models/local_models.md]**
```yaml
model:
  model_name: "hosted_vllm/teacher"          # ต้องตรงกับ --served-model-name
  model_kwargs:
    api_base: "http://localhost:8000/v1"
  cost_tracking: "ignore_errors"
```

**รัน 20 โจทย์แรกจาก repo เดียว** **[ตรวจแล้ว: ตัวเลือก CLI จาก src/minisweagent/run/benchmarks/swebench.py]**
```bash
mini-extra swebench --subset smith --split train \
  --filter '^oauthlib__oauthlib' --slice 0:20 \
  -w 3 -c my_swebench.yaml -o runs/pilot1
```
- `--subset smith` = HF `SWE-bench/SWE-smith` (ในโค้ดมี `"smith": "SWE-bench/SWE-smith"`) · ในชุดมีคอลัมน์ `image_name` อยู่แล้ว เช่น `jyangballin/swesmith.x86_64.oauthlib_1776_oauthlib.1fd52536` (1 image ต่อ repo จึงประหยัดดิสก์)
- `-w 3` = รันพร้อมกัน 3 งาน (เหมาะกับ CPU 6 core) ถ้าเครื่องยังลื่นค่อยเพิ่มเป็น 4
- ผลอยู่ใน `runs/pilot1/` (trajectory + `preds.json`)

**ตรวจว่าแก้สำเร็จจริง** **[ตรวจแล้ว: README ของ SWE-smith]**
```bash
pip install swesmith
python -m swesmith.harness.eval --dataset_path <ไฟล์ task ของ repo>.json --predictions_path runs/pilot1/preds.json --run_id pilot1
```
ตัวเลือกที่เหลือดูจาก [swesmith.com/guides/harnesses](https://swesmith.com/guides/harnesses/)

**สิ่งที่ต้องจดจาก pilot** (ใช้ตัดสินขั้นต่อไป)
- อัตราแก้สำเร็จ (ของครู และของนักเรียน 4B ถ้าลองรันด้วย)
- เวลาต่อโจทย์, จำนวน turn เฉลี่ย, จำนวน token
- RAM/CPU ของ PC ตอนรัน 3 งานพร้อมกัน และดิสก์ที่ image ใช้
- หลังเสร็จรัน `docker image prune -a` เพื่อคืนพื้นที่

**แปลงผลเป็นข้อมูลเทรน**: ใช้ `tools/filter_swe_trajectories.py` เป็นต้นแบบ (ตอนนี้รองรับ schema ของ OpenHands/nebius) สำหรับ trajectory ของ mini-swe-agent ต้องเขียนตัวแปลงเพิ่ม **[ยังไม่มี]** · เกณฑ์เหมือนเดิม: ผ่าน test, ทำบั๊กให้เกิดซ้ำก่อนแก้, เลือกเส้นที่สั้นที่สุด, ยาวไม่เกิน 16K

## 4. เตรียมข้อมูล (ทำบนเครื่องไหนก็ได้ที่มีพื้นที่ดิสก์)

1. ดาวน์โหลดตาม `TOP_DOWNLOAD_LIST.md` (มีคำสั่ง `huggingface-cli download … --include` ครบ ประมาณ 4.5 GB)
2. แปลง parquet → jsonl แล้วรัน converter:
   ```bash
   python3 converters/<ชื่อชุด>.py in.jsonl > data/<ชื่อชุด>.jsonl
   python3 converters/test_converters.py     # ต้องผ่าน 40/40
   ```
3. ตรวจปน benchmark:
   ```bash
   python3 tools/contamination.py build
   python3 tools/contamination.py scan data/*.jsonl > contamination_report.json
   ```
   ตัดแถวที่ Jaccard ≥ 0.5 หรือ containment ≥ 0.8 ออก (`CONTAMINATION.md`)
4. **ห้ามใช้:** split test ของ When2Call / WangchanX-Legal / DataMind · ThaiExam-onet · ชุด benchmark ที่แปลเป็นไทย (ดูรายชื่อใน `CONTAMINATION.md` §3.3)

## 5. สร้างคำตอบ (นักเรียนก่อน ครูทีหลัง) **[ยังไม่มีสคริปต์ → งานถัดไป]**

ตามสูตรใน `BEST_PRACTICES.md` §A2, §F
1. ใช้ prompt จากชุดที่บทบาทเป็น `prompt-only` ส่งให้ **student** (port 8001) ตอบข้อละ 8 ครั้ง (`temperature=1.0, top_p=0.95, top_k=20, presence_penalty=1.5`)
2. ตรวจทุกคำตอบด้วย `verifiers/think_format.py` แล้วตามด้วยตัวตรวจของหมวดนั้น (`toolcall`, `math_answer`, `safe_exec`, `json_schema`, `constraints`, `sql_exec`)
3. เก็บ pass rate ไว้เป็น "ความยาก" · ข้อง่ายให้เก็บคำตอบที่ถูกและสั้นที่สุด
4. ข้อที่นักเรียนผ่าน 0/8 ให้ส่ง **teacher** (port 8000) ตอบ โดยตั้ง:
   - `reasoning_effort`: `low` สำหรับข้อง่าย / `medium` / `xhigh` สำหรับข้อยาก (ใช้ `xhigh` กับงาน agent)
   - **`preserve_thinking: false`** สำหรับบทสนทนาหลายรอบ
   - sampling ของครู: `T=1.0, top_p=0.95, top_k=20, presence_penalty=0.0`
5. **ตรวจว่าไม่มีข้อความ "Reasoning effort is set to" หลุดเข้าไปในข้อมูลที่จะเทรน** (เก็บแค่ messages แล้วเรนเดอร์ใหม่ด้วย template ของนักเรียน)
6. สุ่มอ่านคำตอบภาษาไทยของครูด้วยมือ 50–100 ตัวอย่างก่อนสร้างจำนวนมาก

## 6. เทรน LoRA บน 4090 (Unsloth, bf16)

ต้นแบบจาก [Unsloth Qwen3.5 fine-tune](https://unsloth.ai/docs/models/qwen3.5/fine-tune.md) **[ตรวจแล้ว: ตัวเลือก API]** แล้วปรับตาม `BEST_PRACTICES.md` / `RESEARCH_NOTES.md`
```python
from unsloth import FastLanguageModel
from trl import SFTTrainer, SFTConfig

max_seq_length = 2048   # ทดสอบก่อน แล้วค่อยเพิ่มเป็น 16384
model, tokenizer = FastLanguageModel.from_pretrained(
    model_name="Qwen/Qwen3.5-4B", max_seq_length=max_seq_length,
    load_in_4bit=False, load_in_16bit=True, full_finetuning=False)   # Unsloth ไม่แนะนำ QLoRA กับ Qwen3.5

model = FastLanguageModel.get_peft_model(
    model, r=32, lora_alpha=32, lora_dropout=0, bias="none",
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj",          # 8 ชั้น full attention
                    "gate_proj", "up_proj", "down_proj",             # MLP ทุกชั้น (สำคัญที่สุด)
                    "in_proj_qkv", "in_proj_z", "out_proj"],          # 24 ชั้น DeltaNet → ทำ ablation มี/ไม่มี
    use_gradient_checkpointing="unsloth", random_state=3407, max_seq_length=max_seq_length)
```
- ตัวอย่างของ Unsloth ใส่แค่ q/k/v/o + MLP ซึ่ง**ไม่ได้แตะ 24 ชั้น DeltaNet** (ชื่อโมดูลตรวจจาก `model.safetensors.index.json` จริงแล้ว) ให้ทำ ablation ทั้งสองแบบ
- ตรวจด้วยว่า LoRA ไม่ลามไปที่ vision tower หรือ `mtp.*` (พิมพ์ `model.print_trainable_parameters()` แล้วดูรายชื่อโมดูล)
- `SFTConfig`: `per_device_train_batch_size=1`, `gradient_accumulation_steps` ให้ได้ effective batch ประมาณ 32, `learning_rate=1e-4` (sweep 5e-5 / 1e-4 / 2e-4), `num_train_epochs=1–2`, `optim="adamw_8bit"`
- **เรนเดอร์ข้อมูลด้วย `tokenizer.apply_chat_template(messages, tools=json.loads(rec["tools"]))` ของ Qwen3.5-4B เท่านั้น** (template จะจัดการ reasoning ของ turn เก่าเอง)
- **packing:** ถ้าเปิด ต้องทดสอบก่อนว่า loss ของ batch ที่ pack เท่ากับ batch ที่ไม่ pack (`BEST_PRACTICES.md` §A1)
- ก่อนเทรนจริง: รัน 100 step ที่ 16K เพื่อดูว่า VRAM พอ **[ยังไม่ได้ทดสอบ]**
- เซฟ checkpoint ถี่ๆ แล้วเลือกจากผลวัดใน §8 ไม่ใช่เลือก checkpoint สุดท้ายเสมอ

## 7. แปลงเป็น GGUF แล้วรันบน 2060 ด้วย llama.cpp

```bash
# 1) merge LoRA เข้า base (Unsloth)
model.save_pretrained_merged("merged", tokenizer, save_method="merged_16bit")
# 2) แปลงเป็น GGUF และ quantize (ใน repo llama.cpp)
python convert_hf_to_gguf.py merged --outfile model-bf16.gguf --outtype bf16
./llama-quantize model-bf16.gguf model-Q5_K_M.gguf Q5_K_M      # 4B: Q5_K_M ≈ 3.1 GB, Q6_K ≈ 3.5 GB
# 3) รัน (บน PC ที่มี 2060)
./llama-server -m model-Q5_K_M.gguf --jinja -c 32768 -ngl 99 \
  --temp 1.0 --top-p 0.95 --top-k 20 --presence-penalty 1.5
```
- llama.cpp รองรับ arch `qwen35` และ parse tool call แบบ XML ของ Qwen3.5 ได้ **[ตรวจแล้ว: llama-arch.cpp / chat.cpp]**
- **ต้องใช้ `--jinja`** · ตรวจว่าการคิดเปิดอยู่ (GGUF ขนาดเล็กของ Unsloth ปิดการคิดไว้เป็นค่าเริ่มต้น ถ้าจำเป็นให้เพิ่ม `--chat-template-kwargs '{"enable_thinking":true}'`)
- **วัดผลซ้ำบนไฟล์ GGUF** ด้วย (§8) เพราะ quantize อาจทำให้ผลลดลง

## 8. วัดผล (รันกับ base ก่อนเทรน ทุก checkpoint และบน GGUF สุดท้าย)

ใช้ชุดใน `BEST_PRACTICES.md` §H:
- **ไม่ต้องใช้ Docker:** BFCL v4, ToolHop, tau2-bench, S1-Bench, OptimalThinkingBench, ThaiExam (เฉพาะ tgat/tpat1/a_level/ic), IFEval-TH, MT-Bench-Thai, RULER (8K/16K/32K), MMLU-Pro, GSM8K test
- **ต้องใช้ Docker (รันบน PC):** Terminal-Bench 2.0, SWE-bench Verified (ใช้ `mini-extra swebench --subset verified --split test` แล้วประเมินด้วย harness ของ SWE-bench)

นอกจากความแม่น ให้วัดจำนวน thinking token แยกตามระดับความยากด้วย และถ้าทำ RL ต้องมี run เปรียบเทียบที่ใช้ reward สุ่มคู่กันเสมอ (`BEST_PRACTICES.md` §B)

## 9. งานที่ยังไม่ได้ทำ (ให้ agent ทำต่อ)
1. สคริปต์ขั้น 5 (นักเรียนตอบก่อน → ตัวตรวจ → ครูตอบเฉพาะข้อที่ไม่ผ่าน)
2. ตัวแปลง trajectory ของ mini-swe-agent ให้เป็นรูปแบบ record ของเรา
3. สคริปต์เรนเดอร์ด้วย chat template แล้วเทียบ token กับ llama.cpp / vLLM
4. ตัวตรวจ prompt injection ที่เช็คว่างานเดิมทำเสร็จด้วย
5. ค้างจากทีม: แปลโจทย์เป็นไทยได้ไหม · รูปแบบข้อมูลภาพของ pipeline เทรน (`OPEN_QUESTIONS.md`)
