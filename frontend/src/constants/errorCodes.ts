export const ERROR_HINTS: Record<string, string> = {
  'MTR-1003': 'DSL 语法不合法，请检查聚合表达式 / from / filter / grain 子句。',
  'MTR-1004': 'DSL 语义不合法，请检查聚合函数、grain 取值或 using 引用。',
  'MTR-1005': '指标 key 已被占用，换一个 key 或编辑已有指标。',
  'MTR-1008': '已有批次在执行，稍候再试。',
  'MTR-1010': '今日检查配额已用尽，明天再来或请管理员调整配额。',
  'MTR-1011': '请求过于频繁，稍候重试。',
  'MTR-1012': '当前角色或团队无权执行该操作。',
}
