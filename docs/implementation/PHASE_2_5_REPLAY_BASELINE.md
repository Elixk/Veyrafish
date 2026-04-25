# Phase 2.5 Replay Baseline

## 1. 目标

建立 Phase 2.5 的最小评估闭环，保证“固定样例可重放、可打分、可留痕”。

本基线对应执行计划 Wave 4 的 W4.1 / W4.2 / W4.3。

## 2. 固定样例集

- 样例文件：`docs/implementation/phase-2-5-replay-samples.json`
- 首批样例：3 个研究主题
1. `phase25-nev-price-war`
2. `phase25-llm-regulation`
3. `phase25-cultural-tourism`

## 3. 回放入口

- 脚本：`scripts/phase25_replay.py`
- 默认模式：`fixture`（离线夹具回放）
- 可选模式：`live`（真实三引擎执行）

### 3.1 离线回放（推荐作为 CI/本地基线）

```bash
python scripts/phase25_replay.py --mode fixture
```

### 3.2 真实回放（正式验收）

```bash
python scripts/phase25_replay.py --mode live --strict
```

说明：
- `live` 模式需要完整 API Key/网络环境。
- 建议在 Docker 与前端联调通过后执行，并把产物归档到日志。

## 4. 评分维度

`veyrafish_core/replay_eval.py` 定义以下 5 个维度：

1. `structure_integrity`：结构完整性（三引擎输出覆盖）
2. `coverage`：关键结论覆盖率（是否命中样例 keypoints）
3. `conflict_retention`：冲突保留与不确定性表达
4. `evidence_citation_stability`：证据引用稳定性（evidence 聚合与 top claims 命中）
5. `quality_gate_pass_rate`：质量门禁通过率（QualityGate）

默认总分阈值：
- `overall_score >= 0.70`
- 且每个维度达到其最小阈值（可在样例中覆盖）

## 5. 产物落盘

每次执行会写入：

- `outputs/phase25_replay/<timestamp>/replay_input.json`
- `outputs/phase25_replay/<timestamp>/evaluation.json`
- `outputs/phase25_replay/<timestamp>/report.md`

## 6. 当前限制

- `fixture` 模式仅验证评估闭环，不代表真实 LLM 质量。
- `live` 模式若失败，需在 Phase 2.5 日志中记录失败原因和残余风险，不得宣称正式验收通过。

