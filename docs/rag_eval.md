# RAG 检索评测说明

## 目标
评测三种检索策略：
- `hybrid_traditional`
- `graph_rag`
- `combined`

并区分：
- 闭式题（菜谱定位）
- 开放题（推荐）

## 口径
1. `GraphRAG` 原生 chunk 指标记 `N/A`。
2. 若后续实现 evidence grounding，单独在 `grounded_chunk_*` 字段汇报。
3. 闭式题默认不纳入 chunk 主指标，`minimal_support_chunk_ids` 仅用于附录分析。
4. 开放题使用 `preferred/acceptable` 双层标注，并计算 `Hit@K` 与 `nDCG@K`。

## 评测集构建
```bash
python -m eval.rag_eval.build_evalset \
  --nodes-csv data/cypher/nodes.csv \
  --relationships-csv data/cypher/relationships.csv \
  --output eval/rag_eval/evalset_v1_120.jsonl \
  --closed-count 60 \
  --open-count 60
```

输出 JSONL 字段：
- `qid`
- `question_type` (`closed|open`)
- `query`
- `gold_recipe_ids`（闭式）
- `preferred_recipe_ids`（开放）
- `acceptable_recipe_ids`（开放）
- `minimal_support_chunk_ids`（闭式可选）
- `source_note`

## 运行评测
确保已设置 `.env` 中数据库与 `OPENAI_API_KEY`（检索模块依赖 LLM 分析/关键词提取）。

```bash
python -m eval.rag_eval.run_retrieval_eval \
  --evalset eval/rag_eval/evalset_v1_120.jsonl \
  --output-dir eval/rag_eval/results \
  --strategies hybrid_traditional,graph_rag,combined \
  --top-k 5 \
  --ks 1,3,5
```

## 输出文件
- `eval/rag_eval/results/raw_runs.jsonl`
- `eval/rag_eval/results/metrics_by_strategy.csv`
- `eval/rag_eval/results/closed_chunk_appendix.csv`

## 说明
- `metrics_by_strategy.csv`：主榜单（闭式菜谱定位 + 开放 Hit/nDCG）。
- `closed_chunk_appendix.csv`：闭式 chunk 附录。
- `graph_rag` 的 chunk 指标列显示 `N/A`，不会按 0 计分。
