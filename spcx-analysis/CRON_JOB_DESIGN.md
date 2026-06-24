# SPCX Cron Job Design Documentation

## 原始设计 (Original Design)
```
一个 cron → 一个 prompt → 最终报告
```
- 单一Cron作业触发单一AI提示
- 提示包含所有11个分析section的完整要求
- AI一次性处理所有数据收集、分析和报告生成
- 存在超时风险（模型在处理过于复杂的单一提示时可能超时）

## 改进设计 (Improved Design)
```
数据层 → 验证层 → 建模层 → 研究层 → 最终报
```
- 将单一复杂的AI处理分解为5个明确的层次
- 每层有特定的职责和输出
- 中间结果保存为文件，便于调试和验证
- 提高故障隔离性和可维护性

## 实施细节 (Implementation Details)

### Layer 1: 数据层 (Data Layer)
**职责**: 获取原始数据
**操作**:
- 获取今日日期 (YYYY-MM-DD)
- 设置分析目录: `/home/node/.openclaw/workspace/spcx-analysis`
- 创建层目录: `layers/$TODAY`
- 定义文件路径:
  - `DATA_FILE`: 原始数据JSON
  - `VALIDATED_FILE`: 验证后数据JSON
  - `MODEL_FILE`: 建模结果JSON
  - `RESEARCH_FILE`: 研究叙事Markdown
  - `TODAY_FILE`: 最终报告Markdown
  - `YESTERDAY_FILE`: 昨日报告Markdown（用于变化检测）
- 获取数据:
  * 价格/成交量数据: 使用 web_fetch 从 Yahoo Finance (SPCX)
  * 最近新闻: 使用 web_search 搜索 "SpaceX SPCX news today" (限制5条)
  * 基本面数据: 有针对性的搜索收入、现金、负债等
- 保存原始获取数据为结构化JSON到 DATA_FILE

### Layer 2: 验证层 (Validation Layer)
**职责**: 清理和验证数据
**操作**:
- 读取 DATA_FILE
- 验证价格数据: 确保当前价格在52周范围内，成交量为正
- 验证新闻: 过滤相关性，检查时间戳，去重
- 验证基本面: 交叉检查数字的合理性
- 保存清理/验证后的数据为JSON到 VALIDATED_FILE
- 如果关键验证失败，记录问题但继续处理可用数据（标记限制）

### Layer 3: 建模层 (Modeling Layer)
**职责**: 执行定量计算和建模
**操作**:
- 读取 VALIDATED_FILE
- 计算估值指标:
  * 市销率 (TTM 和基于40-60%增长假设的前瞻值)
  * 市值、企业价值
  * 与可比公司对比: 特斯拉 (~8-10x P/S), 亚马逊 (~4x), 辉达 (~35x), Palantir (~20x)
- 计算技术指标（近似值）:
  * 20/50/200日移动平均线（从价格行为估算）
  * RSI (14) 基于最近价格变动
  * MACD 信号
  * 成交量趋势 vs 平均值
  * 识别支撑/阻力位
- 计算类别评分 (0-100分制):
  * 估值评分 (基于与可比公司的P/S比率和增长正当性)
  * 宏观评分 (美联储展望、流动性、情绪、美元)
  * 技术评分 (趋势、动量、成交量、振荡指标)
  * 机构评分 (分析师评级、持股变化、13F趋势)
  * 催化剂评分 (星舰、星链、政府合同、公司事件)
- 保存所有计算、指标和评分为JSON到 MODEL_FILE

### Layer 4: 研究层 (Research Layer)
**职责**: 生成定性分析和叙事
**操作**:
- 读取 MODEL_FILE 和 VALIDATED_FILE
- 读取 YESTERDAY_FILE（如果存在）
- 为每个section (1-11) 生成叙事分析:
  * SECTION 1 — 市场快照: 价格、表现、相对回报、情绪评估
  * SECTION 2 — 估值分析: 关键指标、可比公司表格、估值评估
  * SECTION 3 — 基本面催化剂监控: 星舰状态、星链指标、政府合同、公司事件、净催化剂评估
  * SECTION 4 — 宏观环境: 美联储利率展望、流动性、市场情绪(VIX、信用利差)、美元趋势、宏观评分
  * SECTION 5 — 技术分析: 移动平均线、RSI、MACD、成交量、支撑/阻力位、技术评分
  * SECTION 6 — 机构持仓: 分析师评级快照、持股评估、机构评分
  * SECTION 7 — 风险监控: 评估8种风险（估值、执行、星舰失败、星链增长、监管、地缘政治、利率、流动性）及等级（Low/Medium/High）
  * SECTION 8 — 情景分析: 牛/基/熊案例及概率(40/45/15%)、假设、价格目标、关键催化剂
  * SECTION 9 — 可操作投资者框架: 投资者画像、建议入场区域、风险控制
  * SECTION 10 — 日度投资决策: 建议（仅限一个：STRONG BUY/BUY/ACCUMULATE/HOLD/WAIT/REDUCE/SELL）及<200字理由和信心程度
  * SECTION 11 — 变化检测 & 趋势分析 (增强版):
    - 如果 YESTERDAY_FILE 存在: 执行比较分析，特别 addressing:
      a. 哪些指标最一致地预示上涨
         - 比较今日指标（成交量、价格变化、RSI、MACD等）与昨日
         - 识别模式: 例如,'成交量激增>50%以上平均值先于过去一周70%的上涨日'
         - 注意任何显示牛市分歧的领先指标
      b. 哪些新闻实际上没有影响价格
         - 列出昨日分析中的新闻条目
         - 检查SPCX价格是否在每条新闻后显著变动(>1%)
         - 标记媒体覆盖度高但价格关联度低(<0.5%变动)的新闻
      c. 哪些机构评级最具参考价值
         - 跟踪昨日/今日的任何分析师升级/降级或目标价变化
         - 比较预测与实际价格变动 following 每次评级变化
         - 按历史预测准确性对机构进行排名
      d. SPCX的长期趋势如何演变
         - 回顾spcx-analysis/目录中所有可用报告（最近7-14天）
         - 描述趋势: 上升、下降、横盘或反转
         - 注意关键转折点及对应的催化剂
         - 识别趋势强度是增加、减少还是稳定
    - 如果 YESTERDAY_FILE 不存在: 注明这是第一天并为未来比较建立基线
- 保存完整的研究叙事（所有11个section）为Markdown到 RESEARCH_FILE

### Layer 5: 最终报 (Final Report)
**职责**: 组装最终报告并输出
**操作**:
- 读取 RESEARCH_FILE
- 按照确切格式组装最终报告:

```
# SPCX Daily Analysis — [YYYY-MM-DD]
**Institutional-Grade Research Report | Space Exploration Technologies Corp.**
*Report Time: [YYYY-MM-DD] [HH:MM] UTC*

--- 

## SECTION 1 — MARKET SNAPSHOT
[来自研究层的内容]

## SECTION 2 — VALUATION ANALYSIS
[来自研究层的内容]

## SECTION 3 — FUNDAMENTAL CATALYST MONITOR
[来自研究层的内容]

## SECTION 4 — MACRO ENVIRONMENT
[来自研究层的内容]

## SECTION 5 — TECHNICAL ANALYSIS
[来自研究层的内容]

## SECTION 6 — INSTITUTIONAL POSITIONING
[来自研究层的内容]

## SECTION 7 — RISK MONITOR
[来自研究层的内容]

## SECTION 8 — SCENARIO ANALYSIS
[来自研究层的内容]

## SECTION 9 — ACTIONABLE INVESTOR FRAMEWORK
[来自研究层的内容]

## SECTION 10 — DAILY INVESTMENT DECISION
[来自研究层的内容]

## SECTION 11 — CHANGE DETECTION & TREND ANALYSIS
[来自研究层的内容]

--- 

## FINAL OUTPUT

**Overall Score: [X]/100**
([简要理由在括号中])

**Sub-Scores:**
| Category | Score |
|---|---|
| Valuation Score | [X]/100 |
| Macro Score | [X]/100 |
| Technical Score | [X]/100 |
| Institutional Score | [X]/100 |
| Catalyst Score | [X]/100 |

**Recommendation:** [STRONG BUY/BUY/ACCUMULATE/HOLD/WAIT/REDUCE/SELL]

**Confidence Level:** [Low / Medium / High]

---

### ⚠️ IMPORTANT DISCLAIMER

This report is for informational and research purposes only. It does not constitute financial advice, a solicitation, or a recommendation to buy, sell, or hold any security. The analysis is based on publicly available data and reasonable estimates. All investments carry risk, including the potential loss of principal. Past performance is not indicative of future results. Consult a licensed financial advisor before making investment decisions.

*Report generated: [YYYY-MM-DD] [HH:MM] UTC*
*Primary data source: Yahoo Finance (SPCX)*

**CRITICAL OUTPUT INSTRUCTION**: When delivering the final report to the user in this Telegram chat, you MUST output the ENTIRE report in CHINESE, exactly as shown in the previous successful run. All section headers, tables, and narrative must be translated to Chinese while preserving the structure and format.
```

## 关键改进点 (Key Improvements)

1. **故障隔离**: 每层通过文件解耦，一层失败不会完全影响其他层
2. **可调试性**: 中间文件便于检查每层的输出
3. **超时控制**: 每层处理更聚焦，降低单次模型调用超时风险
4. **可维护性**: 修改特定层的逻辑而不影响其他层
5. **可审计性**: 完整的数据 lineage 从原始获取到最终报告
6. **变化检测增强**: 第11层明确读取昨日文件进行比较分析
7. **角色明确**: 每次运行以高级高盛股票研究分析师身份执行
8. **语言一致性**: 最终报告完整输出为中文

## 参数和配置 (Parameters and Configuration)

- **Cron 调度**: 每天美国东部时间 20:30 (8:30 PM)
- **超时时间**: 600秒 (10分钟)
- **会话目标**: isolated (独立会话)
- **交付模式**: announce -> telegram:7681294076
- **数据目录**: `/home/node/.openclaw/workspace/spcx-analysis`
- **层目录结构**: `/spcx-analysis/layers/YYYY-MM-DD/`

## 使用说明 (Usage Instructions)

1. 要查看当前设计: `read /spcx-analysis/CRON_JOB_DESIGN.md`
2. 要修改设计: 编辑此文件并更新对应的cron job payload
3. 要查看中间输出: 检查 `/spcx-analysis/layers/YYYY-MM-DD/` 目录
4. 要查看最终报告: 检查 `/spcx-analysis/YYYY-MM-DD.md`

## 更新历史 (Update History)

- **2026-06-16**: 初始版本，基于方案A的增强现有方案实施
  - 从单一chunked section方法升级到明确的5层架构
  - 添加了详细的层职责和操作说明
  - 保留了所有原始功能包括Section 11增强变化检测
  - 确保了以高级高盛股票研究分析师身份执行
  - 确保了最终报告的完整中文输出

---
*此文件旨在作为参考，以便未来修改或更新分析逻辑。*