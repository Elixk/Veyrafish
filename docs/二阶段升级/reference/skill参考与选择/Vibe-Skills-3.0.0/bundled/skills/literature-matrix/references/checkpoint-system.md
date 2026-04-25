# 断点续传机制

## checkpoint.json 完整Schema

```json
{
  "version": "1.0",
  "created_at": "ISO8601 timestamp",
  "updated_at": "ISO8601 timestamp",
  "current_phase": 0-5,
  "config": {
    "domain": "研究领域",
    "keywords": ["关键词1", "关键词2"],
    "paper_count": 40,
    "timerange": "2024-2026",
    "source_mode": "auto|seed|list|hybrid",
    "weight_preset": "理论导向|工程导向|快速发表|均等|自定义",
    "weights": {
      "complementarity": 0.25,
      "data_compat": 0.20,
      "theory": 0.20,
      "innovation": 0.20,
      "feasibility": 0.15
    },
    "project_linked": false,
    "project_context": null
  },
  "phase_0": {"status": "completed|pending"},
  "phase_1": {
    "status": "completed|in_progress|pending",
    "papers_confirmed": 40,
    "papers_file": "./paper_matrix/analysis/paper_list.md"
  },
  "phase_2": {
    "status": "completed|in_progress|pending",
    "combinations_evaluated": 450,
    "total_combinations": 780,
    "matrix_file": "./paper_matrix/analysis/matrix_scores.csv",
    "top_candidates_count": 30
  },
  "phase_3": {
    "status": "completed|in_progress|pending",
    "papers_acquired": 12,
    "papers_needed": 20,
    "ideas_generated": 8,
    "selected_ideas": [1, 3, 7]
  },
  "phase_4": {
    "status": "completed|in_progress|pending",
    "frameworks_generated": 2
  },
  "phase_5": {
    "status": "completed|in_progress|pending",
    "code_files": []
  }
}
```

## 恢复流程

1. 检测 `./paper_matrix/checkpoint.json` 是否存在
2. 如果存在，读取并展示进度:
   "检测到上次分析进度。当前在Phase {X}，已完成{Y}%。是否继续？"
3. 用户选择:
   - 继续: 从中断点恢复，跳过已完成的步骤
   - 重新开始: 备份旧checkpoint为 `checkpoint_backup_{timestamp}.json`，创建新的
4. 恢复时，读取对应phase的输出文件验证完整性

## 错误恢复

| 错误场景 | 恢复策略 |
|----------|---------|
| checkpoint.json损坏 | 删除并从Phase 0重新开始 |
| Phase 2中断（部分评估） | 从已评估的位置继续 |
| 论文PDF缺失 | 重新触发获取流程 |
| 分析文件不完整 | 重新生成该phase的输出 |
