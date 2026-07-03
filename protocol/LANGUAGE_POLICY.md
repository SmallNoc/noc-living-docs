# Language Policy

Default configuration:

```json
{
  "language": "zh-CN",
  "machine_keys": "en-US"
}
```

## Write In Chinese

Use Chinese for human-facing prose:

- background
- goals
- business explanations
- current behavior descriptions
- change reasons
- test notes
- open questions
- maintenance notes

## Keep In English

Keep these in English:

- file names
- directory names
- frontmatter keys
- JSON keys
- status values
- section headings used by the protocol
- IDs such as `BR-001`, `AC-001`, `G-001`, `TC-001`
- feature IDs and domain IDs
- code symbols
- commands
- Git commit types

## Example

```md
# Requirements: User Login

## Summary

用户登录功能支持邮箱和密码登录，并创建服务端会话。

## Business Rules

- BR-001: 登录失败时必须返回通用错误信息，不能暴露邮箱是否存在。
```

