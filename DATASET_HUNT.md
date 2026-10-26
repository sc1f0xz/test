# DATASET_HUNT — dataset สาธารณะสำหรับเทรน Qwen3.5-4B (thinking เป็นค่าเริ่มต้น · tool/agent · ค้นเว็บ · ภาษาไทย)

> ตรวจเมื่อ: 2026-10-26 · ผู้ตรวจ: Claude Code (session ระยะไกล)
> ขอบเขต: Hugging Face (หลัก) + arXiv (เสริม) · **GitHub API ถูกบล็อกใน sandbox นี้ (HTTP 403)** ทำให้ dataset ที่อยู่บน GitHub อย่างเดียวยังไม่ได้ตรวจ

---

## 0. วิธีตรวจ และความหมายของคอลัมน์

**วิธีตรวจ (ไม่มีการดาวน์โหลดไฟล์ใหญ่):**
1. `huggingface.co/api/datasets/<id>` ใช้ดู license, tags, gated, วันแก้ไขล่าสุด
2. `datasets-server.huggingface.co/size` และ `/info` ใช้ดูจำนวนแถว ขนาด parquet และ schema จริง
3. `README.md` ของการ์ด ใช้ดูที่มาของข้อมูล โมเดลที่สร้าง และตัวตรวจ
4. `/first-rows` (ไม่เกิน 100 แถวที่ถูกตัดย่อ) ใช้ยืนยันว่ามี `<think>` หรือ `reasoning_content` และดูค่า reward/result จริง
5. ใช้ `/api/.../tree` (metadata) แทนเมื่อ dataset ไม่มี viewer

**สถานะ**
- **VERIFIED**: เปิดการ์ดจริงและอ่าน README/schema/แถวตัวอย่างแล้ว ข้อมูลในตารางมาจากการ์ดโดยตรง
- **VERIFIED\***: เปิดการ์ดได้ แต่ README ว่างหรือสั้นมาก ข้อมูลบางช่องอนุมานจากชื่อหรือ schema (บอกไว้ในหมายเหตุ)
- **UNVERIFIED**: การ์ดเป็น gated หรือไม่มี README ทำให้อ่านเนื้อหาไม่ได้ หรือข้อมูลที่ระบุมาจากความรู้เดิมโดยยังไม่ได้ยืนยัน

**ความเสี่ยงปน benchmark** (ชุดที่ตรวจ: GSM8K-test, HumanEval, MBPP, IFEval, BFCL, MMLU-Pro, SWE-bench, Terminal-Bench)
- 🟢 ต่ำ: การ์ดระบุว่า decontaminate แล้ว หรือที่มาไม่ทับกับ benchmark เลย
- 🟡 กลาง: ทับในเชิง "สไตล์/ประเภทงาน" หรือการ์ดไม่ได้บอกเรื่อง decontam
- 🔴 สูง: ใช้ข้อมูลหรือข้อกำหนดชุดเดียวกับ benchmark ต้องกรองก่อนใช้

> ⚠️ ทุกรายการยัง**ไม่ได้ทำ n-gram decontam จริง** (เพราะห้ามดาวน์โหลด) ระดับความเสี่ยงประเมินจากการ์ดและที่มาของข้อมูลเท่านั้น

**ชุดที่มีอยู่แล้ว ไม่รายงานซ้ำ:** Dolci-RL-Zero-Mix, RLVR-MATH, SchemaStress, toolcall-guard, tool-injection-answered-forget-set, RST-SFT-Qwen3.5-27B, swesmith-qwen3.6, Open-SWE-Traces, segym-r1, ToolACE, Nemotron-Agentic (v1), Toucan, glaive-fc-v2, hermes-function-calling, SWE-rebench-openhands, GSM8K, ARC, CSQA, OBQA, UltraChat, WangchanThaiInstruct, thai-local-instruction-v2, MCP-Atlas, JSONSchemaBench

---

## 1. Trajectory agent ที่มี reasoning/thinking ของโมเดลตระกูล Qwen และมีตัวตรวจความสำเร็จ (terminal, SWE, tool-use หลายรอบ)

**ข้อสรุป:** มีชุดที่ตรงครบทั้ง 3 เงื่อนไข (Qwen + thinking + มีตัวตรวจ) **น้อยมาก** ชุดที่ตรงที่สุดคือกลุ่ม open-athena (Qwen3.5-122B) ซึ่งข้อเสียหลักคือ**ไม่มี license** ส่วนชุด SWE ขนาดใหญ่ของ NVIDIA/Lego ใช้ **Qwen3-Coder-480B ที่ไม่มี thinking**

| # | ชื่อ + ลิงก์ | จำนวนแถว | ขนาด (parquet) | ใบอนุญาต | โมเดลที่สร้าง / thinking | ตัวตรวจ / เฉลย | เสี่ยงปน benchmark | Schema | สถานะ |
|---|---|---|---|---|---|---|---|---|---|
| 1 | **open-athena `*-qwen3.5-122b-*-traces`** (ตระกูลประมาณ 100 repo) เช่น [nemotron-code-oracle-filtered…131k-opencode](https://huggingface.co/datasets/open-athena/nemotron-code-oracle-filtered-qwen3.5-122b-131k-opencode-traces), [inferredbugs-sandboxes-verifier…131k](https://huggingface.co/datasets/open-athena/inferredbugs-sandboxes-verifier-qwen3.5-122b-131k-opencode-traces), [swesmith-oracle-filtered…32k](https://huggingface.co/datasets/open-athena/swesmith-oracle-filtered-qwen3.5-122b-32k-traces) | 5,688 / 5,827 / 864 (ต่อ repo; ทั้งตระกูลรวมหลักแสน) | 1.99 GB / 2.75 GB / 63 MB (ส่วนใหญ่เป็นคอลัมน์ token-ids + logprobs) | **ไม่ระบุ** ⚠️ | Qwen3.5-122B-A10B-FP8 · มี `<think>` (ยืนยันจากแถวจริง) · agent = OpenCode / Terminus | ✅ `result` (1.0/0.0) + `verifier_output` (เช่น log pytest) | 🟡 ไม่มี README เรื่อง decontam; ตัวที่เป็น swesmith/inferredbugs ไม่ใช่ repo ของ SWE-bench | `conversations[{role,content}]`, `agent`, `model`, `task`, `episode`, `result`, `instruction`, `verifier_output`, `prompt_token_ids`, `completion_token_ids`, `logprobs` | VERIFIED |
| 2 | [zake7749/Qwen-3.6-plus-agent-tool-calling-trajectory](https://huggingface.co/datasets/zake7749/Qwen-3.6-plus-agent-tool-calling-trajectory) | 3,950 (แตกตาม assistant turn) | 82 MB | **ไม่ระบุ** ⚠️ | Qwen3.6-Plus (ผ่าน OpenRouter) · `reasoning_content` ครบ 100% | ✅ `reward` 0/1 (ผ่าน 1,913 แถว = 48.4%) + `score` ต่อ step | 🟡 งานบน ToolScale ซึ่งมีโดเมนแบบ τ²-bench ไม่ทับกับรายการ benchmark ที่ให้มา | `id, domain, score, reward, num_turns, messages[{role,content,reasoning_content,tool_calls}]` | VERIFIED |
| 3 | [nvidia/Nemotron-Terminal-Corpus](https://huggingface.co/datasets/nvidia/Nemotron-Terminal-Corpus) | 366,154 | 8.2 GB | CC-BY-4.0 | **DeepSeek-V3.2** (ไม่ใช่ Qwen) · มี `<think>` และฟิลด์ `enable_thinking` · Terminus-2 | ⚠️ การ์ดบอกว่าเป็น "high-quality execution trajectories" แต่ไม่ได้บอกเกณฑ์ pass/fail ชัดเจน | 🟡 การ์ดใช้ Terminal-Bench 2.0 เป็นตัววัด แต่ไม่ได้พูดถึง decontam | `conversations, agent, model, task, episode, run_id, trial_name, enable_thinking` | VERIFIED |
| 4 | [nvidia/SWE-Hero-openhands-trajectories](https://huggingface.co/datasets/nvidia/SWE-Hero-openhands-trajectories) | 34,269 | 2.4 GB | CC-BY-4.0 | Qwen3-Coder-480B-A35B-Instruct · **ไม่มี thinking** (ยืนยันแล้วว่าไม่มี `<think>` และ `reasoning_content`) | ✅ "Execution-based" ตามการ์ด (ผ่านการรันจริง) | 🟢/🟡 task มาจาก SWE-Gym / R2E / SWE-rebench (คนละ repo กับ SWE-bench) | `instance_id, repo, license, trajectory_id, trajectory[{role,content,tool_calls}]` | VERIFIED |
| 5 | [Lego-X/SWE-Lego-Real-Data](https://huggingface.co/datasets/Lego-X/SWE-Lego-Real-Data) | 18,036 (resolved 5,009) | 1.4 GB | Apache-2.0 | Qwen3-Coder-480B · OpenHands 0.53 · ไม่มี thinking | ✅ `resolved` + `test_cmd`, `PASS_TO_PASS`, `test_patch` | 🟡 ใช้ประเมินด้วย SWE-bench Verified ควรเช็ค repo ซ้ำ | `instance_id, messages[{role,content,turn_mask}], resolved, test_cmd, PASS_TO_PASS, test_patch…` | VERIFIED |
| 6 | [togethercomputer/CoderForge-Preview](https://huggingface.co/datasets/togethercomputer/CoderForge-Preview) | 413,278 trajectory (ซับเซ็ต `filtered_reward1` = 155,144) + ชุด tokenized ซ้ำอีกชุด | 72.8 GB (รวมชุด tokenized) | ไม่ระบุใน tag (มีคอลัมน์ `license` แยกรายแถว) | **การ์ดไม่ได้ระบุ teacher** (ระบุแค่ว่ามีชุด tokenized สำหรับ qwencoder) · ไม่มี `<think>` | ✅ `reward` (test-verified) | 🟡 มาจาก SWE-rebench / SWE-smith / R2E | `trajectory_id, finish_reason, image, messages(str), reward, tools(str), license` | VERIFIED\* |
| 7 | [JWei05/swe_smith_py_qwen3.5_35b_trajs_1952](https://huggingface.co/datasets/JWei05/swe_smith_py_qwen3.5_35b_trajs_1952) (+ ชุดพี่น้อง js/java/go/rs) | 2,000 (py) | 469 MB | **ไม่ระบุ** | Qwen3.5-35B-A3B (ตามชื่อและคอลัมน์ `model`) · ยังไม่ยืนยันว่ามี thinking | ✅ `success_rate` จากการรันหลายรอบ + FAIL_TO_PASS | 🟢 SWE-smith | `instance_id, patch, FAIL_TO_PASS, PASS_TO_PASS, success_rate, trajectories, model…` | VERIFIED\* (README ว่าง) |
| 8 | [open-thoughts/AgentTrove](https://huggingface.co/datasets/open-thoughts/AgentTrove) | 1,696,847 | 19.6 GB | Apache-2.0 | ผสม 219 แหล่ง: GLM-4.6/4.7, GPT-5.x-nano, Kimi-K2-Thinking, MiniMax-M2, **Qwen3-8B** (กรองได้ด้วย `original_teacher`) | ✅ `reward` 1/0 (มีเกือบทุกแหล่ง แต่ไม่ครบ) | 🟡 ต้องกรอง `original_source` ทิ้ง task ที่มีหน้าตาแบบ tbench | `messages, original_source, original_teacher, reward, …` | VERIFIED |

**ใช้ไม่ได้ตามกติกา "ต้องผ่านการตรวจ" หรือมีความเสี่ยงสูง**
- [ukisai/Qwen3.8-27B-multi-turn-agent-sft](https://huggingface.co/datasets/ukisai/Qwen3.8-27B-multi-turn-agent-sft): 15,209 แถว, Apache-2.0, Qwen3.8-27B, Terminus-2 → ❌ **ไม่มีคอลัมน์ result/reward** (สร้าง trace ใหม่บนชุด task ของ OpenThoughts-Agent-v1 โดยไม่ได้กรอง) · VERIFIED
- [nvidia/SWE-Zero-openhands-trajectories](https://huggingface.co/datasets/nvidia/SWE-Zero-openhands-trajectories): 318,115 แถว / 12.2 GB, CC-BY-4.0 → ❌ การ์ดระบุว่าเป็น "execution-free" คือไม่ได้รันตรวจ · VERIFIED
- [open-thoughts/OpenThoughts-Agent-SFT-100K](https://huggingface.co/datasets/open-thoughts/OpenThoughts-Agent-SFT-100K): teacher เป็น GLM แถวตัวอย่างมี `result` = None / AgentTimeoutError → ❌ ไม่ใช่ Qwen และไม่ได้กรองตามผลลัพธ์
- trace ที่ได้จากการรัน benchmark (เช่น `kaitchup/DeepSWE1.1-trajectories-Qwen3.8-27B`, `Lottolabs/terminal-bench-2.1-qwen3.8-27b-traces`, `Stage-jh-monitor/appworld-qwen35-4b-*`) → 🔴 **ห้ามใช้เทรน** เพราะเป็นผลบน test set โดยตรง

---

## 2. Function/tool calling ที่มีเฉลย call ที่ถูก (ชื่อฟังก์ชัน + อาร์กิวเมนต์) รวมเคสไม่ควรเรียก tool, parallel และ multi-turn

| # | ชื่อ + ลิงก์ | จำนวนแถว | ขนาด | ใบอนุญาต | โมเดลที่สร้าง / thinking | ตัวตรวจ / เฉลย | เสี่ยงปน benchmark | Schema | สถานะ |
|---|---|---|---|---|---|---|---|---|---|
| 1 | [zake7749/Qwen3.6-35B-A3B-Tool-Calling](https://huggingface.co/datasets/zake7749/Qwen3.6-35B-A3B-Tool-Calling) | 35,850 SFT (no-multistep 14,545) + preference pair 18,822 แถว | 197 MB | **ไม่ระบุ** ⚠️ | Qwen3.6-35B-A3B-FP8 · `enable_thinking=true` · มีฟิลด์ `reasoning` | ✅ **exact-match ชื่อฟังก์ชัน + อาร์กิวเมนต์ที่ parse แล้ว** เทียบกับ ground truth (สุ่ม 4 คำตอบต่อโจทย์) | 🟡 prompt มาจาก Nemotron-RL agentic corpora (ต้องเช็คซ้ำกับ Nemotron-Agentic ที่มีอยู่) | `tools(str), messages[{role,content,reasoning,tool_calls[{id,type,function{name,arguments}}]}]` | VERIFIED |
| 2 | [nvidia/Nemotron-RL-Agentic-Function-Calling-Pivot-v1](https://huggingface.co/datasets/nvidia/Nemotron-RL-Agentic-Function-Calling-Pivot-v1) | 9,620 | 268 MB | CC-BY-4.0 | expert: DeepSeek-V3.2, GLM-4.6, gpt-oss-120b, Kimi-K2 | ✅ `expected_action` ต่อ step (behavior cloning reward) · มี `parallel_tool_calls` | 🟡 การ์ดไม่ได้บอกเรื่อง decontam กับ BFCL | `trajectory_id, info{turn,step,depth}, responses_create_params{input,tools}, expected_action, agent_ref` | VERIFIED |
| 3 | [nvidia/Nemotron-RL-Agentic-Conversational-Tool-Use-Pivot-v1](https://huggingface.co/datasets/nvidia/Nemotron-RL-Agentic-Conversational-Tool-Use-Pivot-v1) | 96,968 | 1.56 GB | CC-BY-4.0 | expert trajectories ครอบคลุม 838 โดเมน | ✅ `expected_action` ต่อ step (multi-turn) | 🟡 | เหมือนข้อ 2 + `parallel_tool_calls` | VERIFIED |
| 4 | [nvidia/When2Call](https://huggingface.co/datasets/nvidia/When2Call) | train_sft 15,000 + train_pref 9,000 (ส่วน test 3,952 **ห้ามใช้**) | 12.5 MB | CC-BY-4.0 | — | ✅ ป้ายกำกับว่าควร call / ถามกลับ / ตอบว่าไม่สามารถ / ตอบตรง พร้อม chosen/rejected | 🟢 (ใช้เฉพาะ split train) | `tools, messages, chosen_response, rejected_response` | VERIFIED |
| 5 | [MadeAgents/xlam-irrelevance-7.5k](https://huggingface.co/datasets/MadeAgents/xlam-irrelevance-7.5k) | 7,500 | 2.6 MB | CC-BY-4.0 | ดึงมาจาก xLAM-60k แล้วลบฟังก์ชันที่ถูกออก | ✅ `answers=[]` (ไม่ควรเรียก tool) | 🟡 สไตล์เดียวกับหมวด irrelevance ของ BFCL | `query, tools, answers` | VERIFIED |
| 6 | [Salesforce/xlam-function-calling-60k](https://huggingface.co/datasets/Salesforce/xlam-function-calling-60k) | 60,000 | 98 MB (json) | CC-BY-4.0 (gated-auto) | ผ่าน pipeline APIGen | ✅ ตรวจ 3 ขั้น (format, execution, semantic) · มี parallel call | 🟡 ตัวโมเดล xLAM ถูกวัดด้วย BFCL แต่ข้อมูลไม่ได้มาจาก BFCL | `query, tools, answers(json)` | VERIFIED |
| 7 | [Nanbeige/ToolMind](https://huggingface.co/datasets/Nanbeige/ToolMind) | 368,611 (graph_syn 163,180 + open 205,431) | 3.9 GB | Apache-2.0 | multi-agent simulation · มี reasoning trace | ✅ กรองทั้งระดับ trajectory และระดับ turn | 🟡 ส่วน open รวม xLAM / When2Call / **glaive** ไว้ (ซ้ำกับชุดที่มีอยู่) | `conversations(json), tools(json)` | VERIFIED |
| 8 | [nvidia/Nemotron-SFT-Agentic-v4](https://huggingface.co/datasets/nvidia/Nemotron-SFT-Agentic-v4) | 634,664 (tool_calling 549,707 + knowledge_agent 84,957) | 18.9 GB (jsonl) | OpenMDW-1.1 | **Qwen3.5-397B-A17B + GLM-5.2** · มี `reasoning_content` | ⚠️ การ์ดไม่ได้ระบุ judge/verifier ของ v4 | 🟡 | messages + tools + `reasoning_content` (ไม่มี viewer) | VERIFIED\* |
| 9 | [interstellarninja/hermes_reasoning_tool_use](https://huggingface.co/datasets/interstellarninja/hermes_reasoning_tool_use) | 51,004 | 131 MB | Apache-2.0 | rollout ใน Atropos (DeepHermes-3-8B) · มี `<think>` + `<tool_call>` | ✅ validator ตรวจ schema + เก็บเฉพาะ call ที่ถูก หรือการปฏิเสธที่ถูกต้อง (relevance) | 🔴/🟡 การ์ดบอกเองว่า "aligned with BFCL v3 scenarios" | `conversations(sharegpt), tools, task, category, scenario_category` | VERIFIED |
| 10 | [Salesforce/APIGen-MT-5k](https://huggingface.co/datasets/Salesforce/APIGen-MT-5k) | 5,000 | 10 MB | **CC-BY-NC-4.0** | APIGen-MT | ✅ verifiable multi-turn | 🔴 โดเมนเดียวกับ τ-bench (retail/airline) ไม่อยู่ในรายการ benchmark ที่ให้มา แต่ควรระวัง | `conversations, tools, system` | VERIFIED |
| 11 | [nvidia/Nemotron-SFT-Agentic-v2](https://huggingface.co/datasets/nvidia/Nemotron-SFT-Agentic-v2) | 991,900 | 21.9 GB | CC-BY-4.0 / Apache / MIT | DeepSeek-V3.2 + GLM-4.6 | ✅ LLM-judge กรอง | 🟡 มี glaive และ Toucan บางส่วนปนอยู่ (ซ้ำกับชุดที่มีอยู่) · **ซับเซ็ต search ต้องตัดทิ้งเพราะสร้างจาก Wikidata** | jsonl | VERIFIED |

**ตัดออก:** `allenai/Dolci-Instruct-SFT-Tool-Use` (227,579 แถว, ODC-BY) เพราะการ์ดไม่ได้บอกเรื่องตัวตรวจ (❌ ตามกติกา) · `emrecanacikgoz/ToolRL` เพราะไม่มี README และ license อยู่ในการ์ดเปล่า (UNVERIFIED)

---

## 3. ค้นเว็บด้วย search tool หลายรอบแล้วสรุปพร้อมอ้างอิง (ไม่ใช่ wiki)

**ข้อสรุป:** ชุดส่วนใหญ่ในหมวดนี้มี **ซับเซ็ตที่สร้างจาก Wikipedia ปนอยู่** (HotpotQA, 2Wiki, MuSiQue, PopQA, TyDiQA, Wikidata) ต้องกรองตามคอลัมน์ source ก่อนใช้ ไม่สามารถใช้ทั้งชุดได้

| # | ชื่อ + ลิงก์ | จำนวนแถว | ขนาด | ใบอนุญาต | โมเดลที่สร้าง / thinking | ตัวตรวจ / เฉลย | เสี่ยงปน benchmark / wiki | Schema | สถานะ |
|---|---|---|---|---|---|---|---|---|---|
| 1 | [rl-research/dr-tulu-sft-data](https://huggingface.co/datasets/rl-research/dr-tulu-sft-data) | 13,062 (long_form 6,525 / exact 3,811 / short 2,726) | 234 MB | ODC-BY | การ์ด**ไม่ระบุ teacher** · มี reasoning + tool call · ใช้ Serper (Google) และ Semantic Scholar | ✅ คำตอบมี `<cite id=…>` · ซับเซ็ต exact/short มี gold answer | ⚠️ **ต้องตัด `popqa_tydiqa_en` (874 แถว) เพราะเป็น wiki** · ซับเซ็ต `browsecomp_*` (916 แถว) เสี่ยงปนกับ BrowseComp | `id, source, question, type, num_tool_calls, conversations` | VERIFIED |
| 2 | [rl-research/dr-tulu-rl-data](https://huggingface.co/datasets/rl-research/dr-tulu-rl-data) | 4,881 | 2.8 MB | ODC-BY | rubric สร้างด้วย GPT-4.1 | ✅ `ground_truth` / rubric (มีลักษณะเป็น LLM-judge) | 🟢 OpenScholar + SearchArena (ไม่ใช่ wiki) | `source, question_type, messages, ground_truth, dataset` | VERIFIED |
| 3 | [ScienceOne-AI/S1-DeepResearch-15k](https://huggingface.co/datasets/ScienceOne-AI/S1-DeepResearch-15k) | 15,000 | 1.37 GB | Apache-2.0 | การ์ดไม่ระบุ teacher · มี `<think>` + tool call (ยืนยันจากแถวจริง) · EN/ZH | ✅ มี `answer` เฉพาะซับเซ็ตปลายปิด (Closed-ended Multi-hop) | 🟡 ไม่ได้บอกแหล่งของคำถาม (ตัวอย่างที่เห็นเป็นแนว BrowseComp) | `meta{id,question,answer,language,type}, messages[{role,content}]` | VERIFIED |
| 4 | [OpenResearcher/OpenResearcher-Dataset](https://huggingface.co/datasets/OpenResearcher/OpenResearcher-Dataset) | 97,630 (16 seed × 6,102 คำถาม) | 7.45 GB | MIT | GPT-OSS-120B · 100+ turn · native browser tool | ✅ `answer` | 🔴 **คำถามมาจาก MiroVerse ซึ่งมี 2Wiki/HotpotQA/MuSiQue ปน** ต้อง join กลับไปหาที่มาก่อนกรอง | `qid, question, answer, messages(harmony channels)` | VERIFIED |
| 5 | [artillerywu/DeepResearch-9K](https://huggingface.co/datasets/artillerywu/DeepResearch-9K) | 12,974 (teacher ตอบถูก 5,026) | 163 MB | **ไม่ระบุ** | teacher ไม่ระบุ | ✅ ระบุว่า teacher ตอบถูกหรือผิด + `difficulty` | 🟡 ไม่บอกแหล่งของคำถาม | `question, difficulty, search trajectory, final answer` | VERIFIED |
| 6 | [open-athena/nemotron-gym-knowledge-web-search-mcqa-qwen3.5-122b-131k-opencode-traces](https://huggingface.co/datasets/open-athena/nemotron-gym-knowledge-web-search-mcqa-qwen3.5-122b-131k-opencode-traces) | 2,913 | 399 MB | **ไม่ระบุ** | Qwen3.5-122B · มี `<think>` | ✅ `result` 0/1 (แถวตัวอย่างผ่าน 4 จาก 10) | 🟡 เป็นปรนัย (ไม่มีการอ้างอิง) และไม่บอกแหล่งของคำถาม | เหมือนกลุ่ม open-athena ในหมวด 1 | VERIFIED |
| 7 | [callanwu/WebWalkerQA](https://huggingface.co/datasets/callanwu/WebWalkerQA) (silver) | 13,579 silver (ส่วน main 680 เป็น eval) | 2.7 MB | Apache-2.0 | — (เป็นแค่ prompt สำหรับ RL ไม่มี trajectory) | ✅ `answer` + `root_url` + golden_path | 🟢 เดินบนเว็บไซต์ทางการ ไม่ใช่ wiki | `question, answer, root_url, info{domain,source_website,golden_path,type}` | VERIFIED |
| 8 | [PersonalAILab/AFM-WebAgent-SFT-Dataset](https://huggingface.co/datasets/PersonalAILab/AFM-WebAgent-SFT-Dataset) | 7,607 | 78 MB | Apache-2.0 | distill มาจากระบบ multi-agent (Chain-of-Agents) | ⚠️ ไม่บอกเกณฑ์ตรวจของ SFT | 🟡 ไม่บอกแหล่งของคำถาม | `domain, DEFAULT_MODEL, STRONG_MODEL, instruction, input, output` | VERIFIED |

**ตัดออก (wiki หรือไม่มีการค้นจริง):**
- `nvidia/Nemotron-SFT-Agentic-v2` ซับเซ็ต search: การ์ดบอกเองว่าสร้างจาก **Wikidata**
- `Nanbeige/ToolMind-Web-QA`: การ์ดบอกว่า "synthesized from **Wikipedia** entities"
- `inclusionAI/ASearcher-*` และ `Search-R1` data: ใช้ NQ/HotpotQA/2Wiki (wiki)
- `zai-org/DeepDive` (4,108 แถว, Apache-2.0): สร้างจาก knowledge graph ซึ่ง**น่าจะเป็น KILT (Wikipedia)** แต่การ์ดไม่ได้ระบุ จัดเป็น UNVERIFIED แบบเสี่ยง ไม่แนะนำให้ใช้จนกว่าจะเช็คจาก paper
- `miromind-ai/MiroVerse-v0.1`: gated, CC-BY-NC, ไม่มี README · มีไฟล์ `2WikiMultihopQA / HotpotQA / MuSiQue / WikiTables` ใช้ได้เฉพาะซับเซ็ต MegaScience, TaskCraft, WebDancer, WebWalkerQA, Voyager · UNVERIFIED
- `yatin-superintelligence/Edge-Agent-Reasoning-WebSearch-260K`: เป็นแค่ reasoning สำหรับวางแผน **ไม่มีการเรียก search จริง** และไม่มีตัวตรวจ

---

## 4. ภาษาไทย: โจทย์คณิต/โค้ด/ความรู้ที่มีเฉลย, instruction, tool-use ภาษาไทย

**ข้อสรุปตรงๆ:** ไม่พบ tool-use ภาษาไทยที่เป็น**ข้อมูลไทยดั้งเดิม (native) และมีตัวตรวจ** มีแต่ชุดแปล และ**ไม่พบโจทย์โค้ดภาษาไทยที่มี unit test สำหรับเทรน** (ชุดที่มีอยู่เป็น benchmark ที่แปลมา ห้ามใช้เทรน)

| # | ชื่อ + ลิงก์ | จำนวนแถว | ขนาด | ใบอนุญาต | โมเดลที่สร้าง / thinking | ตัวตรวจ / เฉลย | เสี่ยงปน benchmark | Schema | สถานะ |
|---|---|---|---|---|---|---|---|---|---|
| 1 | [typhoon-ai/typhoon-s-instruct-post-training](https://huggingface.co/datasets/typhoon-ai/typhoon-s-instruct-post-training) | 515,813 (sft 357,072 + distill 158,741) · **Thai AutoIF 38,753** · tool-use: irrelevant 40,000 / multi-turn 34,508 / single-turn 43,836 | 1.14 GB | ODC-BY | ผสม Tulu-3 + Thai AutoIF + Toucan subset | ✅ AutoIF = constraint ที่ตรวจด้วยโค้ดได้ · tool-use มี `target_tools` · มีเคส **irrelevant (ไม่ควรเรียก tool)** | 🟡 AutoIF มีสไตล์ใกล้ IFEval · ส่วน Tulu ใช้ซับเซ็ต `*_decontaminated` · ส่วน tool ซ้ำกับ Toucan ที่มีอยู่ | `messages(str), tools(str), question, target_tools, subset_name, source, id, uuid` | VERIFIED |
| 2 | [typhoon-ai/typhoon-s-sovereign-capability-dataset](https://huggingface.co/datasets/typhoon-ai/typhoon-s-sovereign-capability-dataset) | 30,053 (train 29,437) · NitiBench-RL 8,211 | 43 MB | ODC-BY | — | ✅ ชุด RL มีคำตอบอ้างอิง (กฎหมายไทย) | 🟡 NitiBench เป็น benchmark เอง (ห้ามใช้ split test) | `messages, extra_info{doc_id,title}` | VERIFIED |
| 3 | [CohereLabs/tiny-aya-l2-thinker-multilingual-reasoning](https://huggingface.co/datasets/CohereLabs/tiny-aya-l2-thinker-multilingual-reasoning) (config `th`) | th: 4,085 train + 451 test | ทั้งชุด 1.24 GB (ส่วนไทยเล็กมาก) | **CC-BY-NC-4.0** | แปล reasoning trace (prompt มาจาก AM-DeepSeek-R1-0528-Distilled) · มี thinking เป็นภาษาไทย | ⚠️ มี `output` แต่ไม่มีตัวตรวจอัตโนมัติ | 🟡 ไม่บอกเรื่อง decontam | `id, language, domain, question, thinking, output, original_question…` | VERIFIED |
| 4 | [iapp/Thai-R1-Distill-SFT](https://huggingface.co/datasets/iapp/Thai-R1-Distill-SFT) | 10,000 | 33 MB | **ไม่ระบุ** | แปลไทยแบบมี `<think>` · แหล่ง: orca_math, cn_k12, synthetic_math/amc, gsm8k (NuminaMath) | ✅ คอลัมน์ `solution` เป็นคำตอบอ้างอิง (`verified` = null) | 🟡 มีแถวที่มาจาก gsm8k (ส่วน train ของ Numina) และส่วนใหญ่ง่ายระดับ GSM8K | `problem, solution, reannotated_assistant_content, source` | VERIFIED |
| 5 | [wannaphong/verifiable-pythonic-function-calling-lite-thai](https://huggingface.co/datasets/wannaphong/verifiable-pythonic-function-calling-lite-thai) | 12,571 | 8.8 MB | CC-BY-3.0 (ชุดต้นทาง Apache-2.0) | แปลจาก Dria (ไม่ระบุวิธีแปล) | ⚠️ **ชุดไทยเก็บไว้แค่ `messages`** คอลัมน์ mock_functions/checklist ของต้นทางหายไป ทำให้ตรวจโดยตรงไม่ได้ ต้อง join กลับไปหาต้นทาง | 🟢 | `messages[{role,content}]` | VERIFIED |
| 6 | [wannaphong/thai-glaive_2-tool](https://huggingface.co/datasets/wannaphong/thai-glaive_2-tool) | 65,440 | 27 MB | CC-BY-3.0 | แปลจาก glaive-v2 | ⚠️ เฉลยมาจากต้นทาง (glaive ไม่ได้ตรวจด้วยการ execute) | 🟢 · **เป็นตัวแปลของชุดที่มีอยู่แล้ว** | `conversations(str), tools(str)` | VERIFIED |
| 7 | [wannaphong/ToolACE-Qwen-cleaned-thai](https://huggingface.co/datasets/wannaphong/ToolACE-Qwen-cleaned-thai) | 6,850 | 4.8 MB | CC-BY-3.0 | แปลจาก ToolACE | ⚠️ เฉลยมาจากต้นทาง | 🟢 · **เป็นตัวแปลของชุดที่มีอยู่แล้ว** | `conversations(str), tools(str)` | VERIFIED |
| 8 | [pythainlp/han-instruct-dataset-v4.0](https://huggingface.co/datasets/pythainlp/han-instruct-dataset-v4.0) | 4,377 | 2.4 MB | CC-BY-SA-4.0 | เขียนโดยคน + โมเดลรุ่นเก่า | ⚠️ ไม่มีตัวตรวจอัตโนมัติ (ข้อมูลส่วนที่คนเขียนถือว่าผ่านการคัดโดยคน) | 🟢 | `messages` | VERIFIED |
| 9 | [ThaiLLM/med-tool-use](https://huggingface.co/datasets/ThaiLLM/med-tool-use) | 51,239 (train 46,117) | 40 MB | **ไม่ระบุ** | ไม่ระบุ | ⚠️ มี `answer` ที่มี tool call แต่ไม่มี README | 🟢 | `prompt[{role,content}], answer` | UNVERIFIED (README ว่าง) |
| 10 | [aisingapore/SEA-Instruct-2602](https://huggingface.co/datasets/aisingapore/SEA-Instruct-2602) (config `Thai`) | ไม่ทราบ (Thai 21 ไฟล์) | ≈3.8 GB (ส่วนไทย) | ODC-BY (gated) | ไม่ทราบ | ไม่ทราบ | ไม่ทราบ | ไม่ทราบ | UNVERIFIED (gated และไม่มี README) |

**🔴 ห้ามใช้เทรน (เป็น benchmark ที่แปลไทย หรือเป็นข้อสอบ):** `iapp/openai_humaneval-th` (HumanEval), `typhoon-ai/ifeval-th` (IFEval), `iapp/math-500-th`, `iapp/aime_2024-th`, `typhoon-ai/livecodebench-th`, `typhoon-ai/thai_exam`, `matichon/thai-onet-m6-exam` และ `openthaigpt/thai-onet-m6-exam` (เป็นส่วนหนึ่งของ ThaiExam), `wannaphong/gsm8k-thai` (ต้องเช็คก่อนว่ามี split test หรือไม่)
**ตัดออกเพราะสร้างจาก wiki:** `airesearch/wangchanx-seed-free-synthetic-instruct-thai-120k` (การ์ดระบุ "derived from Wikipedia"), `pythainlp/thai-wiki-*`, `iapp/iapp_wiki_qa_squad`, `pythainlp/thai-wiktionary-prompt`
**ไม่แนะนำ:** `Jnx03/kanitakorn-*` เพราะการ์ดบอกเองว่า "Thai-benchmark-targeted" และผสม HotpotQA (wiki) เสี่ยงปน ThaiExam สูง

---

## 5. โจทย์ที่ตรวจคำตอบได้อัตโนมัติ (คณิต, โค้ดพร้อม unit test, JSON schema, constraint) ยากกว่า GSM8K

| # | ชื่อ + ลิงก์ | จำนวนแถว | ขนาด | ใบอนุญาต | โมเดลที่สร้าง / thinking | ตัวตรวจ / เฉลย | เสี่ยงปน benchmark | Schema | สถานะ |
|---|---|---|---|---|---|---|---|---|---|
| 1 | [PrimeIntellect/INTELLECT-3-RL](https://huggingface.co/datasets/PrimeIntellect/INTELLECT-3-RL) | 70,694 (math 21,161 / science 29,307 / logic 11,647 / code 8,579) | 53 MB | **ไม่ระบุใน tag** | — · **มีคอลัมน์ `avg@k_qwen3_4b_instruct_2507`** (pass rate ของโมเดลขนาด 4B) | ✅ อยู่ใน `info` (คำตอบ / test) | 🟡 README ว่าง | `question, info(str), avg@8/16_qwen3_4b…` | VERIFIED\* |
| 2 | [nvidia/Nemotron-RL-Instruction-Following-Structured-Outputs-v2](https://huggingface.co/datasets/nvidia/Nemotron-RL-Instruction-Following-Structured-Outputs-v2) | 62,696 | 763 MB | CC-BY-4.0 | — | ✅ `schema_str` → validator ของ JSON/YAML/XML/TOML/CSV | 🟢 | `responses_create_params, schema_str, schema_type, schema_fields_count, agent_ref` | VERIFIED |
| 3 | [zwhe99/DeepMath-103K](https://huggingface.co/datasets/zwhe99/DeepMath-103K) | 103,022 | 2.1 GB | MIT | มีคำตอบเฉลยจาก R1 ข้อละ 3 แบบ | ✅ `final_answer` + `difficulty` (ระดับ 5–9) | 🟢 การ์ดระบุว่า decontam ด้วย semantic matching | `question, final_answer, difficulty, topic, r1_solution_1..3` | VERIFIED |
| 4 | [nvidia/Nemotron-RL-coding-competitive_coding](https://huggingface.co/datasets/nvidia/Nemotron-RL-coding-competitive_coding) | 16,083 | 2.9 GB | CC-BY-SA-4.0 | — | ✅ `verifier_metadata.unit_tests{inputs,outputs}` | 🟢 มาจาก CodeContests และแหล่งอื่น (ไม่ใช่ HumanEval/MBPP) | `responses_create_params, verifier_metadata, hash_id, dataset, source` | VERIFIED |
| 5 | [KodCode/KodCode-V1](https://huggingface.co/datasets/KodCode/KodCode-V1) | 487,432 | 2.6 GB | **CC-BY-NC-4.0** | GPT-4o สร้างคำตอบและ test | ✅ unit test (pytest) + `gpt_difficulty` | 🟡 → 🟢 **มีคอลัมน์ `benchmark_similarity`** (เทียบกับ HumanEval/MBPP/BCB/LCB) ใช้ตั้ง threshold กรองได้ | `question, solution, test, test_info, gpt_difficulty, benchmark_similarity…` | VERIFIED |
| 6 | [MiniMaxAI/SynLogic](https://huggingface.co/datasets/MiniMaxAI/SynLogic) | 49,297 (easy 15,837 / hard 32,840) | 72 MB | MIT | — | ✅ verifier รายงาน 35 แบบ + `reward_model.answer` | 🟢 | `data_source, prompt, ability, reward_model{answer,solution,style}, extra_info` | VERIFIED |
| 7 | [nvidia/Nemotron-RL-ReasoningGym-v1](https://huggingface.co/datasets/nvidia/Nemotron-RL-ReasoningGym-v1) | 15,000 | 31 MB (jsonl) | CC-BY-4.0 | — | ✅ verifier ของ reasoning-gym | 🟢 | jsonl | VERIFIED |
| 8 | [nvidia/Nemotron-RL-Math-v2](https://huggingface.co/datasets/nvidia/Nemotron-RL-Math-v2) | 7,732 | 2.2 MB | CC-BY-4.0 | — | ✅ `expected_answer` + `verifier_type` | 🟡 ไม่บอกเรื่อง decontam | `question, expected_answer, verifier_type, responses_create_params` | VERIFIED |
| 9 | [nvidia/Nemotron-Cascade-2-RL-data](https://huggingface.co/datasets/nvidia/Nemotron-Cascade-2-RL-data) | 27,930 (IF/MOPD 6,171 · multi-domain 18,147 · SWE-RL 3,612) | 720 MB | ODC-BY | — | ✅ `instruction_id_list+kwargs` (IF) / `expected_answer` / `test_patch` | 🔴 ส่วน IF ใช้ instruction id แบบ IFEval · 🟡 ส่วน SWE-RL ต้องเช็คซ้ำกับ repo ของ SWE-bench | หลาย config | VERIFIED |
| 10 | [agentica-org/DeepCoder-Preview-Dataset](https://huggingface.co/datasets/agentica-org/DeepCoder-Preview-Dataset) | train: primeintellect 16,252 + taco 7,436 + lcbv5 599 | 7.8 GB | MIT | — | ✅ `tests` | 🟡 ใช้เฉพาะ train · **ห้ามใช้ split `codeforces/test` และ `lcbv5/test`** | `problem, tests, starter_code, metadata` | VERIFIED |
| 11 | [allenai/IF_multi_constraints_upto5](https://huggingface.co/datasets/allenai/IF_multi_constraints_upto5) | 95,373 | 72 MB | ODC-BY | — | ✅ `ground_truth` ตรวจ constraint ด้วยโค้ด | 🔴 **constraint 25 แบบเป็นแบบเดียวกับ IFEval** (prompt ไม่ซ้ำ แต่จะทำให้คะแนน IFEval สูงเกินจริง) | `messages, ground_truth, constraint_type, constraint` | VERIFIED |

---

## 6. ข้อมูลสอนให้ "คิดสั้นกับโจทย์ง่าย คิดยาวกับโจทย์ยาก" (adaptive reasoning length)

**ข้อสรุปตรงๆ:** แทบ**ไม่มี dataset สาธารณะที่ติดป้าย "ง่าย → สั้น / ยาก → ยาว" ไว้พร้อมใช้** งานวิจัยส่วนใหญ่ (AdaptThink, Thinkless, DART, LCPO) ปล่อยแค่ prompt แล้วสร้างพฤติกรรมด้วย **RL ที่มี length reward** สิ่งที่หาได้จึงเป็น (ก) ข้อมูลที่มีคู่สั้น/ยาว (ข) ข้อมูลที่มีสัญญาณความยาก สำหรับเอาไปทำ curriculum หรือ reward

| # | ชื่อ + ลิงก์ | จำนวนแถว | ขนาด | ใบอนุญาต | โมเดลที่สร้าง / thinking | ตัวตรวจ / เฉลย | เสี่ยงปน benchmark | Schema | สถานะ |
|---|---|---|---|---|---|---|---|---|---|
| 1 | [zake7749/Qwen3.6-35B-A3B-Tool-Calling](https://huggingface.co/datasets/zake7749/Qwen3.6-35B-A3B-Tool-Calling) (ซ้ำกับหมวด 2) | preference pair 18,822 แถว | 197 MB | **ไม่ระบุ** | Qwen3.6 thinking | ✅ exact-match · การ์ดวัดไว้ว่า reasoning ของคำตอบที่ถูกเลือกสั้นกว่าที่ถูกปฏิเสธ (median 236 vs 417 token) | 🟡 | ดูหมวด 2 | VERIFIED |
| 2 | [Vinnnf/Hybrid-OpenThoughts2-1M-1.5B](https://huggingface.co/datasets/Vinnnf/Hybrid-OpenThoughts2-1M-1.5B) (Thinkless warm-up) | 2,280,390 (โจทย์ละ 2 แบบ: ยาว + สั้น) | 9.0 GB | Apache-2.0 | ยาว = OpenThoughts2 (R1) · สั้น = Qwen2.5-Math-1.5B-Instruct · ใช้ control token สลับโหมด | ⚠️ ไม่มีตัวตรวจในชุด warm-up (ส่วน RL ใช้ DeepScaleR) | 🟡 OpenThoughts2 มีโจทย์จำนวนมาก | `instruction, output` | VERIFIED |
| 3 | [nvidia/Llama-Nemotron-Post-Training-Dataset](https://huggingface.co/datasets/nvidia/Llama-Nemotron-Post-Training-Dataset) | 1,073,011 (SFT) | 6.8 GB | CC-BY-4.0 | หลายโมเดล · **บาง prompt มีคำตอบทั้งโหมด reasoning on และ off** | ⚠️ ขึ้นกับซับเซ็ต (math/code มีการกรองตามการ์ดหลัก) | 🟡 | `input, output, reasoning, generator, category, license` | VERIFIED |
| 4 | [zwhe99/DeepMath-103K](https://huggingface.co/datasets/zwhe99/DeepMath-103K) + [PrimeIntellect/INTELLECT-3-RL](https://huggingface.co/datasets/PrimeIntellect/INTELLECT-3-RL) (ซ้ำกับหมวด 5) | ดูหมวด 5 | — | MIT / ไม่ระบุ | — | ✅ `difficulty` และ `avg@k` ของ Qwen3-4B → ใช้แบ่งช่วง length budget | 🟢/🟡 | ดูหมวด 5 | VERIFIED |
| 5 | [UWNSL/Mix-Long_long_0.2_short_0.8](https://huggingface.co/datasets/UWNSL/Mix-Long_long_0.2_short_0.8) | 5,383 | 4.7 MB | **ไม่ระบุ** | ยาว 20% จาก QwQ-32B-Preview + สั้น 80% (MATH train) | ⚠️ ใช้เฉลยของ MATH | 🟢 (MATH train) | `problem, solution` | VERIFIED |
| 6 | [artillerywu/DeepResearch-9K](https://huggingface.co/datasets/artillerywu/DeepResearch-9K) (ซ้ำกับหมวด 3) | 12,974 | 163 MB | **ไม่ระบุ** | — | ✅ `difficulty` + ตอบถูกหรือผิด | 🟡 | ดูหมวด 3 | VERIFIED |
| 7 | [Xin-Rui/Dataset-BudgetThinker](https://huggingface.co/datasets/Xin-Rui/Dataset-BudgetThinker) | 14,470 | 1.8 MB | **ไม่ระบุ** | — (prompt สำหรับ RL ที่ควบคุม budget) | ✅ `answer` | 🟡 | `problem, answer` | VERIFIED\* (README ว่าง) |

**ตัดออก หรือเข้าใจผิดง่าย:** `allenai/Dolci-Think-SFT-Olmo-Hybrid` ชื่อมีคำว่า Hybrid แต่หมายถึงสถาปัตยกรรม Olmo Hybrid ไม่ใช่ hybrid thinking (README มีแค่ license) · `dungnv/qwen36-27b-length-traces` เป็นงานทำนายความยาวสำหรับ scheduling ไม่ใช่ข้อมูลเทรน · `THU-KEG/DeepPrune` (gated) เป็นเรื่อง pruning reasoning แบบขนาน · `YangXiao-nlp/LIMOPro-*` ไม่มี README (UNVERIFIED)

---

## 7. ข้อวิเคราะห์เชิงกลยุทธ์ (ข้อดี / ข้อเสีย / ความเสี่ยง / ข้อจำกัด)

### 7.1 Top-pick ต่อหัวข้อ
| หัวข้อ | เลือก | เหตุผล | ความเสี่ยงหลัก |
|---|---|---|---|
| Agent + Qwen thinking + ตัวตรวจ | open-athena Qwen3.5-122B (กรอง `result==1.0`) | เป็นชุดเดียวที่ครบทั้ง Qwen3.5, `<think>` และ verifier | **ไม่มี license** · trace ยาวถึง 131k token เกิน context ที่เหมาะกับการเทรน 4B |
| Function calling | Qwen3.6-35B-A3B-Tool-Calling + When2Call + Nemotron-RL Pivot | มี thinking จริง, exact-match และเคสไม่ควรเรียก tool | ชุดแรกไม่มี license · prompt อาจซ้ำกับ Nemotron-Agentic ที่มีอยู่ |
| ค้นเว็บพร้อมอ้างอิง | DR Tulu SFT + RL (ตัดซับเซ็ต popqa_tydiqa) | มี citation จริงและใช้ search API จริง | teacher ไม่ใช่ Qwen ทำให้รูปแบบ thinking ต่างกัน · ซับเซ็ต browsecomp อาจปน eval |
| ภาษาไทย | Typhoon-S (Thai AutoIF + tool/irrelevant) | ใหญ่ที่สุด, ODC-BY, มีส่วนที่ตรวจด้วยโค้ดได้ | tool-use ส่วนใหญ่เป็นภาษาอังกฤษ (จาก Toucan) |
| ตรวจคำตอบอัตโนมัติ | INTELLECT-3-RL + DeepMath + Structured-Outputs-v2 | INTELLECT-3 มี pass rate ของ Qwen3-4B ให้เลือกโจทย์ที่ยากพอดีกับโมเดล | INTELLECT-3 ไม่มี license tag และ README ว่าง |
| Adaptive length | Qwen3.6-TC (pair สั้น/ยาว) + ใช้ difficulty สร้าง reward | ไม่มีชุดพร้อมใช้ที่ดีกว่านี้ | ต้องพึ่ง RL มากกว่า SFT |

### 7.2 จุดอ่อนและสมมติฐานที่ควรตั้งคำถาม
1. **trajectory ที่ไม่มี thinking (Qwen3-Coder-480B, GLM, GPT-OSS) อาจกดโหมด thinking ของ Qwen3.5-4B ลง**
   - ข้อดี: SWE trajectory คุณภาพสูงที่มีขนาดใหญ่ส่วนใหญ่เป็นชุดประเภทนี้
   - ความเสี่ยง: ถ้าใส่ `<think></think>` ว่างลงไปจำนวนมาก โมเดลอาจเรียนรู้ว่าไม่ต้องคิดกับงาน agent
   - ทางเลือก: (ก) ใช้ชุดเหล่านี้เป็น RL environment (ใช้ task + test) แทน SFT หรือ (ข) จำกัดสัดส่วนไม่เกิน ~20–30% ของ agent SFT และทดสอบ A/B
2. **ความยาวของ trace:** open-athena 131k, OpenResearcher 100+ turn, CoderForge ยาวมาก
   - ข้อจำกัด: ต้องตั้ง max length ใน SFT ของ 4B (เช่น 32k) แล้วตัดหรือทิ้ง trace ที่เกิน ถ้าตัดกลางทางจะเสียสัญญาณการ "จบงานสำเร็จ"
3. **License:** ชุดที่ดีที่สุดหลายชุดในหมวด 1, 2, 3 และ 6 **ไม่มี license** (open-athena, zake7749, INTELLECT-3-RL, DeepResearch-9K) และมีอีกหลายชุดเป็น **NC** (KodCode, APIGen-MT, tiny-aya, MiroVerse)
   - หากจะใช้เชิงพาณิชย์ ต้องตัดออกหรือติดต่อเจ้าของก่อน
4. **การปนกับ benchmark ยังเป็นแค่การประเมินจากการ์ด** ก่อนเทรนจริงต้องรัน n-gram (13-gram) หรือ embedding decontam เทียบกับ BFCL, IFEval, SWE-bench Verified, Terminal-Bench 2.x, HumanEval/MBPP และ GSM8K-test
   - ระวังเป็นพิเศษ: hermes_reasoning_tool_use (ตั้งใจให้ตรงกับ BFCL), IF_multi_constraints และ Cascade-2 IF (constraint แบบ IFEval), DeepCoder (มี split test ปนมาใน repo)
5. **ภาษาไทยเป็นจุดอ่อนใหญ่ที่สุด:** ไม่มีข้อมูล tool-use หรือโค้ดภาษาไทยที่เป็น native และตรวจได้
   - ทางเลือก (ไม่ได้สร้างข้อมูลเองจากศูนย์): แปลโจทย์ที่**มีตัวตรวจอยู่แล้ว** (เช่น DeepMath, xLAM, When2Call) แล้วใช้ verifier เดิมตรวจคำตอบ ซึ่งต้องให้คุณตัดสินว่าขัดกับกติกา "ห้ามสร้างข้อมูลเอง" หรือไม่

### 7.3 ข้อจำกัดของการค้นครั้งนี้
- การค้นของ HF ทำงานแบบ substring บนชื่อ repo ชุดที่ตั้งชื่อไม่ตรงคีย์เวิร์ดอาจหลุดไป
- **GitHub API ถูกบล็อก (403)** จึงไม่ได้ตรวจ dataset ที่ปล่อยบน GitHub อย่างเดียว (เช่น release ของ paper ที่ไม่ได้ขึ้น HF)
- เรื่องจำนวนแถว ใช้ตัวเลขจาก datasets-server หรือการ์ด ชุดที่ไม่มี viewer ใช้ขนาดไฟล์จาก tree API

### 7.4 คำถามกลับ (มีผลต่อการจัดอันดับ)
1. ต้องการใช้**เชิงพาณิชย์**หรือไม่ ถ้าใช่ ชุดที่ไม่มี license หรือเป็น NC ต้องตัดออก และ top-pick ในหมวด 1 จะเปลี่ยน
2. งบ context ของ SFT/RL สำหรับ 4B คือเท่าไร (16k / 32k / 64k) ตัวเลขนี้จะกำหนดว่าใช้ชุด 131k-trace ได้จริงหรือไม่
3. การ "แปลโจทย์ที่มีตัวตรวจอยู่แล้วเป็นภาษาไทย" นับเป็น "สร้างข้อมูลเอง" ตามกติกาหรือไม่
4. รูปแบบ tool-call ของ pipeline ที่ใช้คือแบบไหน (Qwen3.5 XML / Hermes `<tool_call>` JSON / OpenAI `tool_calls`) เพราะจะกำหนดต้นทุนการแปลง schema ของแต่ละชุด
