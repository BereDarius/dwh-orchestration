# VS Code Quick Reference

## 🚀 Getting Started

```bash
code data-ingestion-framework.code-workspace
```

Install recommended extensions when prompted ✓

## ⌨️ Essential Shortcuts

| Action           | Mac                   | Windows/Linux          |
| ---------------- | --------------------- | ---------------------- |
| Command Palette  | `Cmd+Shift+P`         | `Ctrl+Shift+P`         |
| Run Task         | `Cmd+Shift+P` → Tasks | `Ctrl+Shift+P` → Tasks |
| Debug            | `F5`                  | `F5`                   |
| Format Document  | `Shift+Option+F`      | `Shift+Alt+F`          |
| Go to Definition | `F12`                 | `F12`                  |

## 📋 Common Tasks

```
Cmd+Shift+P → Tasks: Run Task

Testing:
  ✓ Run Tests with Coverage (default)
  ✓ Run Tests

Code Quality:
  ✓ Format Code
  ✓ Lint Code
  ✓ Type Check

Config:
  ✓ Validate Configs
  ✓ List All Configs
  ✓ Discover Configs (CLI)
```

## 🐛 Debug Configs

```
F5 → Select:

  ✓ Python: Current File
  ✓ Run Pipeline (Dev)
  ✓ List Pipelines
  ✓ Discover All Configs
  ✓ Run Tests with Coverage
  ✓ Run Current Test File
```

## ✨ Auto-Features

**On Save:**

- ✅ Black formatting (100 chars)
- ✅ Import sorting (isort)
- ✅ Ruff linting
- ✅ YAML formatting

**Real-time:**

- 🔍 Type checking (strict)
- 🎯 YAML validation
- 📊 Error highlighting
- 💡 Auto-complete

## 📝 YAML Editing

**Auto-completion** in config files:

```yaml
pipeline:
  name: | # ← Type and get suggestions
  environment: | # ← Shows: dev, stage, prod
  schedule:
    cron: | # ← Hover for format help
```

**Validation:**

- ❌ Invalid values highlighted
- 💡 Hover for field descriptions
- ✅ Real-time schema checking

## 🧪 Testing Workflow

1. Write test in `tests/`
2. Set breakpoint (click gutter)
3. `F5` → `Run Current Test File`
4. Debug with full context

**Coverage:**

1. Tasks → `Run Tests with Coverage`
2. Click `Watch` in status bar
3. See green/red gutters in editor

## 🎯 Tips

**Quick Config Check:**

- Open YAML → See errors instantly
- Hover fields → Read docs
- Ctrl+Space → Auto-complete

**Fast Debugging:**

- `F5` on any file → instant debug
- Breakpoints work everywhere
- Full variable inspection

**Git Integration:**

- Inline blame (GitLens)
- Visual diff
- Branch compare

## 📚 More Info

See: `docs/vscode-setup.md` for complete documentation
