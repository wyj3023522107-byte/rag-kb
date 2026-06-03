# K12智能学习助手前端视觉重设计实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将K12智能学习助手前端升级为科技感毛玻璃风格，支持亮色/暗色双主题。

**Architecture:** 采用CSS变量系统实现主题切换，通过backdrop-filter实现毛玻璃效果，使用Flexbox/Grid布局，原生JavaScript处理交互逻辑。

**Tech Stack:** HTML5, CSS3 (Variables, Flexbox, Grid, backdrop-filter), Vanilla JavaScript, KaTeX, Marked.js

---

## 文件结构

```
web/static/
├── css/
│   ├── variables.css      # 新建 - CSS变量定义（颜色、间距、圆角、阴影）
│   ├── base.css           # 新建 - 基础重置样式
│   ├── layout.css         # 新建 - 布局结构（导航栏、侧边栏、主内容）
│   ├── components.css     # 新建 - 组件样式（按钮、卡片、输入框、标签）
│   ├── chat.css           # 修改 - 对话页面特定样式
│   └── knowledge.css      # 修改 - 知识库页面特定样式
├── js/
│   ├── theme.js           # 新建 - 主题切换逻辑
│   ├── sidebar.js         # 新建 - 侧边栏拖拽交互
│   ├── app.js             # 修改 - 主应用逻辑适配
│   ├── api.js             # 保留 - API请求
│   ├── knowledge.js       # 修改 - 知识库页面适配
│   └── markdown.js        # 保留 - Markdown渲染
├── index.html             # 修改 - 对话页面HTML结构
└── knowledge.html         # 修改 - 知识库页面HTML结构
```

---

### Task 1: 创建CSS变量文件

**Files:**
- Create: `web/static/css/variables.css`

- [ ] **Step 1: 创建CSS变量文件**

```css
/* web/static/css/variables.css */

/* ===== 共用强调色 ===== */
:root {
  --accent-cyan: #4ECDC4;
  --accent-blue: #45B7D1;
  --accent-purple: #5C7AEA;
  --accent-deep-purple: #764ba2;

  /* 渐变 */
  --gradient-primary: linear-gradient(135deg, var(--accent-cyan), var(--accent-purple));
  --gradient-accent: linear-gradient(135deg, var(--accent-cyan), var(--accent-blue), var(--accent-purple));

  /* 功能色 */
  --color-success: #22c55e;
  --color-error: #f87171;
  --color-warning: #fbbf24;

  /* 圆角 */
  --radius-sm: 6px;
  --radius: 10px;
  --radius-lg: 12px;
  --radius-xl: 16px;
  --radius-full: 999px;

  /* 过渡 */
  --transition-fast: 0.15s ease;
  --transition: 0.2s ease;
  --transition-slow: 0.3s ease;

  /* 布局 */
  --nav-height: 56px;
  --sidebar-width: 220px;
  --sidebar-min-width: 160px;
  --sidebar-max-width: 320px;
}

/* ===== 亮色模式 ===== */
:root,
[data-theme="light"] {
  /* 背景 */
  --bg-primary: #f8fafc;
  --bg-secondary: #f1f5f9;
  --bg-card: #ffffff;
  --bg-nav: rgba(255, 255, 255, 0.85);
  --bg-sidebar: rgba(248, 250, 252, 0.9);

  /* 文字 */
  --text-primary: #1e293b;
  --text-secondary: #64748b;
  --text-muted: #94a3b8;

  /* 边框 */
  --border-color: #e2e8f0;
  --border-light: rgba(0, 0, 0, 0.06);

  /* 阴影 */
  --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.05);
  --shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  --shadow-lg: 0 4px 12px rgba(0, 0, 0, 0.1);
  --shadow-glow: 0 4px 20px rgba(92, 122, 234, 0.25);

  /* 毛玻璃 */
  --glass-bg: rgba(255, 255, 255, 0.85);
  --glass-border: rgba(0, 0, 0, 0.06);
}

/* ===== 暗色模式 ===== */
[data-theme="dark"] {
  /* 背景 */
  --bg-primary: #0f0f1a;
  --bg-secondary: #12121e;
  --bg-card: rgba(30, 30, 50, 0.5);
  --bg-nav: rgba(18, 18, 30, 0.8);
  --bg-sidebar: rgba(20, 20, 35, 0.6);

  /* 文字 */
  --text-primary: #ffffff;
  --text-secondary: rgba(255, 255, 255, 0.6);
  --text-muted: rgba(255, 255, 255, 0.35);

  /* 边框 */
  --border-color: rgba(255, 255, 255, 0.08);
  --border-light: rgba(255, 255, 255, 0.06);

  /* 阴影 */
  --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.2);
  --shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
  --shadow-lg: 0 8px 24px rgba(0, 0, 0, 0.4);
  --shadow-glow: 0 4px 20px rgba(92, 122, 234, 0.35);

  /* 毛玻璃 */
  --glass-bg: rgba(30, 30, 50, 0.5);
  --glass-border: rgba(255, 255, 255, 0.08);
}

/* ===== 消息气泡特定变量 ===== */
:root,
[data-theme="light"] {
  --user-bubble-bg: var(--gradient-primary);
  --user-bubble-text: #ffffff;
  --assistant-bubble-bg: #ffffff;
  --assistant-bubble-border: var(--border-color);
}

[data-theme="dark"] {
  --user-bubble-bg: var(--gradient-primary);
  --user-bubble-text: #ffffff;
  --assistant-bubble-bg: rgba(30, 30, 50, 0.5);
  --assistant-bubble-border: rgba(255, 255, 255, 0.08);
}
```

- [ ] **Step 2: 验证文件创建**

```bash
ls -la web/static/css/variables.css
```

Expected: 文件存在且内容正确

---

### Task 2: 创建基础样式文件

**Files:**
- Create: `web/static/css/base.css`

- [ ] **Step 1: 创建基础重置样式**

```css
/* web/static/css/base.css */

/* ===== 重置样式 ===== */
*,
*::before,
*::after {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html {
  font-size: 16px;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  font-size: 14px;
  line-height: 1.6;
  color: var(--text-primary);
  background-color: var(--bg-primary);
  transition: background-color var(--transition-slow), color var(--transition-slow);
}

/* ===== 滚动条 ===== */
::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

::-webkit-scrollbar-track {
  background: transparent;
}

::-webkit-scrollbar-thumb {
  background-color: var(--border-color);
  border-radius: 3px;
}

::-webkit-scrollbar-thumb:hover {
  background-color: var(--text-muted);
}

/* ===== 选择文本 ===== */
::selection {
  background-color: rgba(78, 205, 196, 0.2);
  color: var(--text-primary);
}

/* ===== 链接 ===== */
a {
  color: var(--accent-cyan);
  text-decoration: none;
  transition: color var(--transition-fast);
}

a:hover {
  color: var(--accent-purple);
}

/* ===== 代码 ===== */
code {
  font-family: 'SF Mono', Monaco, 'Cascadia Code', 'Courier New', monospace;
  font-size: 0.9em;
  padding: 2px 6px;
  background-color: rgba(78, 205, 196, 0.1);
  border-radius: var(--radius-sm);
}

pre {
  font-family: 'SF Mono', Monaco, 'Cascadia Code', 'Courier New', monospace;
  font-size: 0.875em;
  padding: 16px;
  background-color: #1e1e2e;
  border-radius: var(--radius);
  overflow-x: auto;
  color: #cdd6f4;
}

pre code {
  background: none;
  padding: 0;
  color: inherit;
}

/* ===== 毛玻璃工具类 ===== */
.glass {
  background: var(--glass-bg);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border: 1px solid var(--glass-border);
}

.glass-strong {
  background: var(--glass-bg);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid var(--glass-border);
}

/* ===== 渐变文字 ===== */
.gradient-text {
  background: var(--gradient-primary);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

/* ===== 动画 ===== */
@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes messageIn {
  from {
    opacity: 0;
    transform: translateY(8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes pulse {
  0%, 100% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.05);
  }
}

@keyframes glow {
  0%, 100% {
    box-shadow: 0 0 10px rgba(78, 205, 196, 0.3);
  }
  50% {
    box-shadow: 0 0 20px rgba(78, 205, 196, 0.5);
  }
}

/* ===== 响应式 ===== */
@media (max-width: 768px) {
  html {
    font-size: 14px;
  }
}
```

- [ ] **Step 2: 验证文件创建**

```bash
ls -la web/static/css/base.css
```

---

### Task 3: 创建布局样式文件

**Files:**
- Create: `web/static/css/layout.css`

- [ ] **Step 1: 创建布局样式**

```css
/* web/static/css/layout.css */

/* ===== 应用容器 ===== */
.app-container {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}

/* ===== 顶部导航栏 ===== */
.top-nav {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  height: var(--nav-height);
  background: var(--bg-nav);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border-bottom: 1px solid var(--border-light);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  z-index: 100;
  transition: background var(--transition-slow), border-color var(--transition-slow);
}

.nav-left {
  display: flex;
  align-items: center;
  gap: 24px;
}

.nav-right {
  display: flex;
  align-items: center;
  gap: 10px;
}

/* Logo */
.logo {
  display: flex;
  align-items: center;
  gap: 10px;
  font-weight: 700;
  font-size: 16px;
}

.logo-icon {
  width: 34px;
  height: 34px;
  background: var(--gradient-primary);
  border-radius: var(--radius);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-weight: 700;
  font-size: 15px;
}

.logo-text {
  background: var(--gradient-primary);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  font-size: 17px;
}

/* 导航菜单 */
.nav-menu {
  display: flex;
  align-items: center;
  gap: 6px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 9px 14px;
  border-radius: var(--radius);
  font-size: 13px;
  font-weight: 500;
  color: var(--text-secondary);
  cursor: pointer;
  transition: all var(--transition-fast);
  text-decoration: none;
}

.nav-item:hover {
  color: var(--text-primary);
  background: var(--bg-secondary);
}

.nav-item.active {
  color: var(--accent-cyan);
  background: rgba(78, 205, 196, 0.1);
  border: 1px solid rgba(78, 205, 196, 0.25);
}

.nav-item svg {
  width: 16px;
  height: 16px;
}

/* ===== 主内容区域 ===== */
.main-wrapper {
  display: flex;
  margin-top: var(--nav-height);
  min-height: calc(100vh - var(--nav-height));
}

/* ===== 侧边栏 ===== */
.sidebar {
  width: var(--sidebar-width);
  min-width: var(--sidebar-min-width);
  max-width: var(--sidebar-max-width);
  background: var(--bg-sidebar);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border-right: 1px solid var(--border-light);
  display: flex;
  flex-direction: column;
  transition: width var(--transition), background var(--transition-slow), border-color var(--transition-slow);
  position: relative;
  flex-shrink: 0;
}

.sidebar-header {
  padding: 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid var(--border-light);
}

.sidebar-title {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.sidebar-content {
  flex: 1;
  overflow-y: auto;
  padding: 12px;
}

/* 拖拽手柄 */
.resize-handle {
  position: absolute;
  right: 0;
  top: 0;
  bottom: 0;
  width: 4px;
  cursor: col-resize;
  background: transparent;
  transition: background var(--transition-fast);
}

.resize-handle:hover,
.resize-handle.active {
  background: var(--accent-cyan);
}

/* 侧边栏折叠状态 */
.sidebar.collapsed {
  width: 60px;
  min-width: 60px;
}

.sidebar.collapsed .sidebar-title,
.sidebar.collapsed .history-item-title,
.sidebar.collapsed .history-item-time {
  display: none;
}

/* ===== 主内容 ===== */
.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
  background: var(--bg-primary);
  transition: background var(--transition-slow);
}

/* ===== 响应式 ===== */
@media (max-width: 1024px) {
  .sidebar {
    width: 60px;
    min-width: 60px;
  }

  .sidebar .sidebar-title,
  .sidebar .history-item-title,
  .sidebar .history-item-time {
    display: none;
  }
}

@media (max-width: 768px) {
  .top-nav {
    padding: 0 16px;
  }

  .nav-left {
    gap: 12px;
  }

  .logo-text {
    display: none;
  }

  .sidebar {
    position: fixed;
    left: -280px;
    top: var(--nav-height);
    bottom: 0;
    width: 280px;
    z-index: 90;
    transition: left var(--transition);
  }

  .sidebar.open {
    left: 0;
  }

  .sidebar-overlay {
    display: none;
    position: fixed;
    inset: 0;
    top: var(--nav-height);
    background: rgba(0, 0, 0, 0.5);
    z-index: 80;
  }

  .sidebar.open + .sidebar-overlay {
    display: block;
  }
}
```

- [ ] **Step 2: 验证文件创建**

```bash
ls -la web/static/css/layout.css
```

---

### Task 4: 创建组件样式文件

**Files:**
- Create: `web/static/css/components.css`

- [ ] **Step 1: 创建组件样式**

```css
/* web/static/css/components.css */

/* ===== 按钮 ===== */
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 10px 18px;
  border-radius: var(--radius);
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all var(--transition-fast);
  border: none;
  text-decoration: none;
}

.btn-primary {
  background: var(--gradient-primary);
  color: white;
  box-shadow: var(--shadow-sm);
}

.btn-primary:hover {
  transform: translateY(-1px);
  box-shadow: var(--shadow-glow);
}

.btn-primary:active {
  transform: translateY(0);
}

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

.btn-secondary {
  background: var(--bg-secondary);
  color: var(--text-primary);
  border: 1px solid var(--border-color);
}

.btn-secondary:hover {
  border-color: var(--accent-cyan);
  color: var(--accent-cyan);
}

.btn-ghost {
  background: transparent;
  color: var(--text-secondary);
}

.btn-ghost:hover {
  background: var(--bg-secondary);
  color: var(--text-primary);
}

.btn-icon {
  width: 36px;
  height: 36px;
  padding: 0;
  border-radius: var(--radius);
}

/* 新建对话按钮 */
.new-chat-btn {
  width: 100%;
  padding: 12px 16px;
  background: var(--gradient-primary);
  color: white;
  border: none;
  border-radius: var(--radius);
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  transition: all var(--transition-fast);
  box-shadow: var(--shadow-sm);
}

.new-chat-btn:hover {
  transform: translateY(-1px);
  box-shadow: var(--shadow-glow);
}

.new-chat-btn svg {
  width: 16px;
  height: 16px;
}

/* ===== 卡片 ===== */
.card {
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-color);
  padding: 20px;
  transition: all var(--transition-fast);
}

.card:hover {
  border-color: var(--accent-cyan);
  box-shadow: var(--shadow);
}

.card-glass {
  background: var(--glass-bg);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border: 1px solid var(--glass-border);
}

/* ===== 输入框 ===== */
.input {
  width: 100%;
  padding: 12px 16px;
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius);
  font-size: 14px;
  color: var(--text-primary);
  transition: all var(--transition-fast);
  outline: none;
}

.input:focus {
  border-color: var(--accent-cyan);
  box-shadow: 0 0 0 3px rgba(78, 205, 196, 0.1);
}

.input::placeholder {
  color: var(--text-muted);
}

/* 文本域 */
.textarea {
  resize: none;
  min-height: 44px;
  max-height: 150px;
}

/* 选择框 */
.select {
  padding: 10px 14px;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius);
  font-size: 13px;
  color: var(--text-primary);
  cursor: pointer;
  transition: all var(--transition-fast);
  outline: none;
}

.select:focus {
  border-color: var(--accent-cyan);
}

/* ===== 标签 ===== */
.tag {
  display: inline-flex;
  align-items: center;
  padding: 4px 10px;
  border-radius: var(--radius-sm);
  font-size: 11px;
  font-weight: 500;
}

.tag-cyan {
  background: rgba(78, 205, 196, 0.1);
  border: 1px solid rgba(78, 205, 196, 0.25);
  color: var(--accent-cyan);
}

.tag-purple {
  background: rgba(92, 122, 234, 0.1);
  border: 1px solid rgba(92, 122, 234, 0.25);
  color: var(--accent-purple);
}

.tag-blue {
  background: rgba(69, 183, 209, 0.1);
  border: 1px solid rgba(69, 183, 209, 0.25);
  color: var(--accent-blue);
}

/* ===== 快捷按钮 ===== */
.quick-btn {
  padding: 12px 18px;
  background: linear-gradient(135deg, rgba(78, 205, 196, 0.08), rgba(92, 122, 234, 0.08));
  border: 1px solid rgba(78, 205, 196, 0.2);
  border-radius: var(--radius-lg);
  font-size: 13px;
  font-weight: 500;
  color: var(--accent-cyan);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.quick-btn:hover {
  transform: translateY(-2px);
  border-color: var(--accent-cyan);
  box-shadow: var(--shadow);
}

/* ===== 统计卡片 ===== */
.stat-card {
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-color);
  padding: 20px;
  text-align: center;
  transition: all var(--transition-fast);
}

.stat-card:hover {
  border-color: var(--accent-cyan);
  transform: translateY(-2px);
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  background: var(--gradient-primary);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.stat-label {
  font-size: 12px;
  color: var(--text-secondary);
  margin-top: 4px;
}

/* ===== 历史记录项 ===== */
.history-item {
  padding: 12px 14px;
  border-radius: var(--radius);
  cursor: pointer;
  transition: all var(--transition-fast);
  margin-bottom: 4px;
}

.history-item:hover {
  background: var(--bg-secondary);
}

.history-item.active {
  background: rgba(78, 205, 196, 0.1);
  border: 1px solid rgba(78, 205, 196, 0.2);
}

.history-item-title {
  font-size: 13px;
  color: var(--text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.history-item-time {
  font-size: 11px;
  color: var(--text-muted);
  margin-top: 4px;
}

.history-item-delete {
  opacity: 0;
  padding: 4px;
  border-radius: var(--radius-sm);
  transition: all var(--transition-fast);
}

.history-item:hover .history-item-delete {
  opacity: 0.6;
}

.history-item-delete:hover {
  opacity: 1;
  background: rgba(248, 113, 113, 0.2);
  color: var(--color-error);
}

/* ===== 主题切换按钮 ===== */
.theme-toggle {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius);
  font-size: 12px;
  color: var(--text-secondary);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.theme-toggle:hover {
  border-color: var(--accent-cyan);
  color: var(--text-primary);
}

/* ===== 上传区域 ===== */
.upload-area {
  border: 2px dashed var(--border-color);
  border-radius: var(--radius-lg);
  padding: 32px;
  text-align: center;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.upload-area:hover {
  border-color: var(--accent-cyan);
  background: rgba(78, 205, 196, 0.05);
}

.upload-icon {
  font-size: 32px;
  margin-bottom: 8px;
}

.upload-text {
  font-size: 14px;
  color: var(--text-secondary);
}

.upload-hint {
  font-size: 12px;
  color: var(--text-muted);
  margin-top: 4px;
}

/* ===== 删除按钮 ===== */
.delete-btn {
  padding: 6px 12px;
  background: transparent;
  border: 1px solid var(--color-error);
  border-radius: var(--radius-sm);
  color: var(--color-error);
  font-size: 11px;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.delete-btn:hover {
  background: var(--color-error);
  color: white;
}
```

- [ ] **Step 2: 验证文件创建**

```bash
ls -la web/static/css/components.css
```

---

### Task 5: 更新聊天页面CSS

**Files:**
- Modify: `web/static/css/chat.css` (完全重写)

- [ ] **Step 1: 重写聊天页面样式**

```css
/* web/static/css/chat.css */

/* ===== 聊天主区域 ===== */
.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: var(--bg-primary);
  transition: background var(--transition-slow);
}

/* ===== 消息容器 ===== */
.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 28px;
  scroll-behavior: smooth;
}

/* ===== 欢迎消息 ===== */
.welcome-message {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  animation: fadeIn 0.4s ease;
  min-height: calc(100vh - var(--nav-height) - 120px);
}

.welcome-icon {
  width: 80px;
  height: 80px;
  background: var(--gradient-primary);
  border-radius: 22px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 38px;
  color: white;
  box-shadow: var(--shadow-glow);
  margin-bottom: 20px;
}

.welcome-message h2 {
  font-size: 24px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 8px;
}

.welcome-message p {
  font-size: 15px;
  color: var(--text-secondary);
  margin-bottom: 28px;
}

.quick-actions {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  justify-content: center;
  max-width: 600px;
}

/* ===== 消息气泡 ===== */
.message {
  display: flex;
  margin-bottom: 20px;
  gap: 12px;
  animation: messageIn 0.25s ease;
}

.message.user {
  flex-direction: row-reverse;
}

.message-avatar {
  width: 36px;
  height: 36px;
  border-radius: var(--radius);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  font-weight: 600;
  flex-shrink: 0;
}

.message.user .message-avatar {
  background: var(--gradient-primary);
  color: white;
}

.message.assistant .message-avatar {
  background: var(--gradient-primary);
  color: white;
}

.message-content {
  max-width: 65%;
  padding: 14px 18px;
  border-radius: var(--radius-xl);
  line-height: 1.65;
  font-size: 14px;
}

.message.user .message-content {
  background: var(--gradient-primary);
  color: white;
  border-bottom-right-radius: 6px;
}

.message.assistant .message-content {
  background: var(--assistant-bubble-bg);
  border: 1px solid var(--assistant-bubble-border);
  color: var(--text-primary);
  border-bottom-left-radius: 6px;
}

/* Markdown 内容样式 */
.message-content h3 {
  margin: 16px 0 10px;
  font-size: 1.05rem;
}

.message-content h3:first-child {
  margin-top: 0;
}

.message-content p {
  margin: 0 0 10px;
}

.message-content p:last-child {
  margin-bottom: 0;
}

.message-content code {
  background-color: rgba(0, 0, 0, 0.08);
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 0.88em;
}

.message.user .message-content code {
  background-color: rgba(255, 255, 255, 0.2);
}

.message-content pre {
  background-color: #1e1e2e;
  color: #cdd6f4;
  padding: 14px 16px;
  border-radius: var(--radius);
  overflow-x: auto;
  margin: 14px 0;
}

.message-content pre code {
  background: none;
  padding: 0;
  color: inherit;
}

.message-content ul,
.message-content ol {
  margin: 10px 0;
  padding-left: 24px;
}

.message-content li {
  margin: 6px 0;
  line-height: 1.6;
}

.message-content blockquote {
  margin: 14px 0;
  padding: 10px 16px;
  border-left: 4px solid var(--accent-cyan);
  background: rgba(78, 205, 196, 0.05);
  color: var(--text-secondary);
  border-radius: 0 var(--radius) var(--radius) 0;
}

.message-content table {
  width: 100%;
  border-collapse: collapse;
  margin: 14px 0;
  font-size: 0.9em;
}

.message-content th,
.message-content td {
  padding: 10px 14px;
  text-align: left;
  border: 1px solid var(--border-color);
}

.message-content th {
  background: rgba(78, 205, 196, 0.1);
  font-weight: 600;
}

/* ===== 输入区域 ===== */
.input-container {
  padding: 16px 24px 20px;
  background: var(--bg-card);
  border-top: 1px solid var(--border-color);
  transition: background var(--transition-slow), border-color var(--transition-slow);
}

.input-wrapper {
  display: flex;
  gap: 12px;
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  padding: 10px 12px 10px 18px;
  transition: all var(--transition-fast);
}

.input-wrapper:focus-within {
  border-color: var(--accent-cyan);
  box-shadow: 0 0 0 3px rgba(78, 205, 196, 0.1);
}

.input-wrapper textarea {
  flex: 1;
  border: none;
  background: transparent;
  resize: none;
  font-size: 14px;
  line-height: 1.5;
  max-height: 150px;
  color: var(--text-primary);
  outline: none;
  font-family: inherit;
}

.input-wrapper textarea::placeholder {
  color: var(--text-muted);
}

.send-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 12px 24px;
  background: var(--gradient-primary);
  color: white;
  border: none;
  border-radius: var(--radius);
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all var(--transition-fast);
  box-shadow: var(--shadow-sm);
}

.send-btn:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: var(--shadow-glow);
}

.send-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none;
}

/* ===== 流式输出光标 ===== */
.cursor {
  display: inline-block;
  animation: blink 1s infinite;
  font-weight: bold;
  color: var(--accent-cyan);
  margin-left: 2px;
}

@keyframes blink {
  0%, 45% { opacity: 1; }
  50%, 95% { opacity: 0; }
  100% { opacity: 1; }
}

/* ===== 加载动画 ===== */
.typing-indicator {
  display: flex;
  gap: 5px;
  padding: 18px;
}

.typing-indicator span {
  width: 7px;
  height: 7px;
  background: var(--accent-cyan);
  border-radius: 50%;
  animation: typing 1.2s infinite ease-in-out;
  opacity: 0.5;
}

.typing-indicator span:nth-child(2) {
  animation-delay: 0.15s;
}

.typing-indicator span:nth-child(3) {
  animation-delay: 0.3s;
}

@keyframes typing {
  0%, 60%, 100% {
    transform: translateY(0);
    opacity: 0.5;
  }
  30% {
    transform: translateY(-6px);
    opacity: 1;
  }
}

/* ===== 响应式 ===== */
@media (max-width: 768px) {
  .messages-container {
    padding: 16px;
  }

  .message-content {
    max-width: 85%;
  }

  .input-container {
    padding: 12px 16px 16px;
  }

  .quick-actions {
    flex-direction: column;
    align-items: center;
  }

  .quick-btn {
    width: 100%;
    max-width: 280px;
  }
}
```

- [ ] **Step 2: 验证文件更新**

```bash
head -50 web/static/css/chat.css
```

---

### Task 6: 更新知识库页面CSS

**Files:**
- Modify: `web/static/css/knowledge.css` (完全重写)

- [ ] **Step 1: 重写知识库页面样式**

```css
/* web/static/css/knowledge.css */

/* ===== 知识库主区域 ===== */
.knowledge-main {
  flex: 1;
  padding: 24px;
  overflow-y: auto;
  background: var(--bg-primary);
  transition: background var(--transition-slow);
}

.page-header {
  margin-bottom: 24px;
}

.page-header h2 {
  font-size: 20px;
  font-weight: 600;
  color: var(--text-primary);
}

/* ===== 上传区域 ===== */
.upload-section {
  margin-bottom: 24px;
}

.upload-section h3 {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 16px;
}

.upload-area {
  border: 2px dashed var(--border-color);
  border-radius: var(--radius-lg);
  padding: 40px;
  text-align: center;
  cursor: pointer;
  transition: all var(--transition-fast);
  background: var(--bg-card);
}

.upload-area:hover {
  border-color: var(--accent-cyan);
  background: rgba(78, 205, 196, 0.05);
}

.upload-icon {
  font-size: 40px;
  margin-bottom: 12px;
}

.upload-area p {
  font-size: 14px;
  color: var(--text-secondary);
  margin-bottom: 8px;
}

.upload-hint {
  font-size: 12px;
  color: var(--text-muted);
}

/* 上传表单 */
.upload-form {
  margin-top: 20px;
  padding: 20px;
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-color);
}

.form-row {
  display: flex;
  gap: 16px;
  margin-bottom: 16px;
}

.form-group {
  flex: 1;
}

.form-group label {
  display: block;
  font-size: 13px;
  font-weight: 500;
  color: var(--text-primary);
  margin-bottom: 8px;
}

.form-group input,
.form-group select {
  width: 100%;
  padding: 10px 14px;
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius);
  font-size: 14px;
  color: var(--text-primary);
  transition: all var(--transition-fast);
  outline: none;
}

.form-group input:focus,
.form-group select:focus {
  border-color: var(--accent-cyan);
  box-shadow: 0 0 0 3px rgba(78, 205, 196, 0.1);
}

/* ===== 统计卡片 ===== */
.stats-section h3 {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 16px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}

.stat-card {
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-color);
  padding: 20px;
  text-align: center;
  transition: all var(--transition-fast);
}

.stat-card:hover {
  border-color: var(--accent-cyan);
  transform: translateY(-2px);
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  background: var(--gradient-primary);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.stat-label {
  font-size: 12px;
  color: var(--text-secondary);
  margin-top: 4px;
}

/* 学科统计 */
.subject-stats {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
  gap: 12px;
}

.subject-stat {
  background: var(--bg-card);
  border-radius: var(--radius);
  border: 1px solid var(--border-color);
  padding: 14px 16px;
  text-align: center;
  transition: all var(--transition-fast);
}

.subject-stat:hover {
  border-color: var(--accent-cyan);
}

.subject-stat-name {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 4px;
}

.subject-stat-count {
  font-size: 12px;
  color: var(--text-muted);
}

/* ===== 文档列表 ===== */
.documents-section {
  margin-bottom: 24px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.section-header h3 {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
}

.filter-select {
  padding: 8px 14px;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius);
  font-size: 13px;
  color: var(--text-primary);
  cursor: pointer;
  transition: all var(--transition-fast);
  outline: none;
}

.filter-select:hover {
  border-color: var(--accent-cyan);
}

.documents-table-wrapper {
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-color);
  overflow: hidden;
}

.documents-table {
  width: 100%;
  border-collapse: collapse;
}

.documents-table th,
.documents-table td {
  padding: 14px 16px;
  text-align: left;
}

.documents-table th {
  background: var(--bg-secondary);
  font-size: 12px;
  font-weight: 600;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.03em;
  border-bottom: 1px solid var(--border-color);
}

.documents-table td {
  font-size: 14px;
  color: var(--text-primary);
  border-bottom: 1px solid var(--border-light);
}

.documents-table tr:last-child td {
  border-bottom: none;
}

.documents-table tr:hover td {
  background: var(--bg-secondary);
}

/* ===== 进度条 ===== */
.progress-bar {
  width: 100%;
  height: 4px;
  background: var(--bg-secondary);
  border-radius: 2px;
  overflow: hidden;
  margin-top: 12px;
}

.progress-bar-fill {
  height: 100%;
  background: var(--gradient-primary);
  border-radius: 2px;
  transition: width 0.3s ease;
}

/* ===== 响应式 ===== */
@media (max-width: 768px) {
  .knowledge-main {
    padding: 16px;
  }

  .stats-grid {
    grid-template-columns: 1fr;
  }

  .form-row {
    flex-direction: column;
  }

  .documents-table {
    font-size: 12px;
  }

  .documents-table th,
  .documents-table td {
    padding: 10px 12px;
  }
}
```

- [ ] **Step 2: 验证文件更新**

```bash
head -50 web/static/css/knowledge.css
```

---

### Task 7: 创建主题切换脚本

**Files:**
- Create: `web/static/js/theme.js`

- [ ] **Step 1: 创建主题切换逻辑**

```javascript
// web/static/js/theme.js

(function() {
  'use strict';

  const THEME_KEY = 'k12-theme';
  const DARK_THEME = 'dark';
  const LIGHT_THEME = 'light';

  // 获取当前主题
  function getTheme() {
    const saved = localStorage.getItem(THEME_KEY);
    if (saved) {
      return saved;
    }
    // 跟随系统
    return window.matchMedia('(prefers-color-scheme: dark)').matches
      ? DARK_THEME
      : LIGHT_THEME;
  }

  // 设置主题
  function setTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem(THEME_KEY, theme);
    updateToggleButtonText(theme);
  }

  // 更新切换按钮文字
  function updateToggleButtonText(theme) {
    const buttons = document.querySelectorAll('.theme-toggle');
    buttons.forEach(btn => {
      const icon = theme === DARK_THEME ? '☀️' : '🌙';
      const text = theme === DARK_THEME ? '亮色' : '暗色';
      btn.innerHTML = `<span>${icon}</span><span>${text}</span>`;
    });
  }

  // 切换主题
  function toggleTheme() {
    const current = getTheme();
    const next = current === DARK_THEME ? LIGHT_THEME : DARK_THEME;
    setTheme(next);
  }

  // 初始化
  function init() {
    // 立即应用主题，避免闪烁
    const theme = getTheme();
    document.documentElement.setAttribute('data-theme', theme);

    // DOM 加载完成后更新按钮
    document.addEventListener('DOMContentLoaded', () => {
      updateToggleButtonText(theme);

      // 绑定切换按钮
      document.querySelectorAll('.theme-toggle').forEach(btn => {
        btn.addEventListener('click', toggleTheme);
      });
    });

    // 监听系统主题变化
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
      if (!localStorage.getItem(THEME_KEY)) {
        setTheme(e.matches ? DARK_THEME : LIGHT_THEME);
      }
    });
  }

  // 暴露API
  window.theme = {
    get: getTheme,
    set: setTheme,
    toggle: toggleTheme
  };

  init();
})();
```

- [ ] **Step 2: 验证文件创建**

```bash
ls -la web/static/js/theme.js
```

---

### Task 8: 创建侧边栏拖拽脚本

**Files:**
- Create: `web/static/js/sidebar.js`

- [ ] **Step 1: 创建侧边栏拖拽逻辑**

```javascript
// web/static/js/sidebar.js

(function() {
  'use strict';

  let sidebar = null;
  let resizeHandle = null;
  let isResizing = false;
  let startX = 0;
  let startWidth = 0;

  const MIN_WIDTH = 160;
  const MAX_WIDTH = 320;
  const STORAGE_KEY = 'k12-sidebar-width';

  // 获取保存的宽度
  function getSavedWidth() {
    const saved = localStorage.getItem(STORAGE_KEY);
    return saved ? parseInt(saved, 10) : 220;
  }

  // 保存宽度
  function saveWidth(width) {
    localStorage.setItem(STORAGE_KEY, width);
  }

  // 设置侧边栏宽度
  function setWidth(width) {
    width = Math.max(MIN_WIDTH, Math.min(MAX_WIDTH, width));
    if (sidebar) {
      sidebar.style.width = width + 'px';
    }
  }

  // 开始拖拽
  function startResize(e) {
    isResizing = true;
    startX = e.clientX;
    startWidth = sidebar.offsetWidth;

    document.body.style.cursor = 'col-resize';
    document.body.style.userSelect = 'none';

    if (resizeHandle) {
      resizeHandle.classList.add('active');
    }

    e.preventDefault();
  }

  // 拖拽中
  function doResize(e) {
    if (!isResizing) return;

    const diff = e.clientX - startX;
    const newWidth = startWidth + diff;
    setWidth(newWidth);
  }

  // 结束拖拽
  function stopResize() {
    if (!isResizing) return;

    isResizing = false;
    document.body.style.cursor = '';
    document.body.style.userSelect = '';

    if (resizeHandle) {
      resizeHandle.classList.remove('active');
    }

    // 保存宽度
    if (sidebar) {
      saveWidth(sidebar.offsetWidth);
    }
  }

  // 移动端侧边栏切换
  function toggleMobileSidebar() {
    if (sidebar) {
      sidebar.classList.toggle('open');
    }
  }

  // 初始化
  function init() {
    document.addEventListener('DOMContentLoaded', () => {
      sidebar = document.querySelector('.sidebar');
      resizeHandle = document.querySelector('.resize-handle');

      if (!sidebar) return;

      // 应用保存的宽度
      const savedWidth = getSavedWidth();
      setWidth(savedWidth);

      // 绑定拖拽事件
      if (resizeHandle) {
        resizeHandle.addEventListener('mousedown', startResize);
      }

      document.addEventListener('mousemove', doResize);
      document.addEventListener('mouseup', stopResize);

      // 移动端菜单按钮
      const menuBtn = document.querySelector('.menu-toggle');
      if (menuBtn) {
        menuBtn.addEventListener('click', toggleMobileSidebar);
      }

      // 点击遮罩关闭
      const overlay = document.querySelector('.sidebar-overlay');
      if (overlay) {
        overlay.addEventListener('click', toggleMobileSidebar);
      }
    });
  }

  // 暴露API
  window.sidebar = {
    toggle: toggleMobileSidebar,
    setWidth: setWidth
  };

  init();
})();
```

- [ ] **Step 2: 验证文件创建**

```bash
ls -la web/static/js/sidebar.js
```

---

### Task 9: 更新对话页面HTML

**Files:**
- Modify: `web/static/index.html`

- [ ] **Step 1: 更新HTML结构和引入**

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>K12智能学习助手</title>
    <!-- CSS -->
    <link rel="stylesheet" href="/static/css/variables.css">
    <link rel="stylesheet" href="/static/css/base.css">
    <link rel="stylesheet" href="/static/css/layout.css">
    <link rel="stylesheet" href="/static/css/components.css">
    <link rel="stylesheet" href="/static/css/chat.css">
    <!-- KaTeX 数学公式渲染 -->
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.css">
    <script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.js"></script>
    <!-- Marked.js Markdown解析 -->
    <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
</head>
<body>
    <div class="app-container">
        <!-- 顶部导航栏 -->
        <nav class="top-nav">
            <div class="nav-left">
                <a href="/" class="logo">
                    <span class="logo-icon">K</span>
                    <span class="logo-text">K12学习助手</span>
                </a>
                <div class="nav-menu">
                    <a href="/" class="nav-item active">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
                        </svg>
                        <span>对话</span>
                    </a>
                    <a href="/knowledge" class="nav-item">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"></path>
                            <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"></path>
                        </svg>
                        <span>知识库</span>
                    </a>
                </div>
            </div>
            <div class="nav-right">
                <button class="theme-toggle" title="切换主题">
                    <span>🌙</span>
                    <span>暗色</span>
                </button>
            </div>
        </nav>

        <!-- 主内容区域 -->
        <div class="main-wrapper">
            <!-- 可调节侧边栏 -->
            <aside class="sidebar">
                <div class="sidebar-header">
                    <span class="sidebar-title">历史记录</span>
                    <button class="btn-icon btn-primary" id="newChatBtn" title="新建对话">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                            <line x1="12" y1="5" x2="12" y2="19"></line>
                            <line x1="5" y1="12" x2="19" y2="12"></line>
                        </svg>
                    </button>
                </div>
                <div class="sidebar-content">
                    <ul class="history-list" id="historyList">
                        <!-- 动态加载 -->
                    </ul>
                </div>
                <div class="resize-handle"></div>
            </aside>

            <!-- 聊天主区域 -->
            <main class="chat-main">
                <!-- 消息容器 -->
                <div class="messages-container" id="messagesContainer">
                    <!-- 欢迎消息 -->
                    <div class="welcome-message">
                        <div class="welcome-icon">🎓</div>
                        <h2>你好，我是K12学习助手</h2>
                        <p>我可以帮你解答学科问题、辅导作业、疏导情绪</p>
                        <div class="quick-actions">
                            <button class="quick-btn" data-query="请帮我讲解勾股定理">
                                📐 勾股定理讲解
                            </button>
                            <button class="quick-btn" data-query="这道方程题怎么做：2x + 5 = 13">
                                📝 作业辅导
                            </button>
                            <button class="quick-btn" data-query="最近学习压力有点大">
                                💬 情绪疏导
                            </button>
                        </div>
                    </div>
                </div>

                <!-- 输入区域 -->
                <div class="input-container">
                    <div class="input-wrapper">
                        <textarea
                            id="messageInput"
                            placeholder="请输入你的问题..."
                            rows="1"
                        ></textarea>
                        <button id="sendBtn" class="send-btn">
                            <span>发送</span>
                            <span>✨</span>
                        </button>
                    </div>
                </div>
            </main>
        </div>
    </div>

    <!-- JavaScript -->
    <script src="/static/js/theme.js"></script>
    <script src="/static/js/sidebar.js"></script>
    <script src="/static/js/api.js"></script>
    <script src="/static/js/markdown.js"></script>
    <script src="/static/js/app.js"></script>
</body>
</html>
```

- [ ] **Step 2: 验证文件更新**

```bash
head -80 web/static/index.html
```

---

### Task 10: 更新知识库页面HTML

**Files:**
- Modify: `web/static/knowledge.html`

- [ ] **Step 1: 更新HTML结构**

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>知识库管理 - K12智能学习助手</title>
    <!-- CSS -->
    <link rel="stylesheet" href="/static/css/variables.css">
    <link rel="stylesheet" href="/static/css/base.css">
    <link rel="stylesheet" href="/static/css/layout.css">
    <link rel="stylesheet" href="/static/css/components.css">
    <link rel="stylesheet" href="/static/css/knowledge.css">
</head>
<body>
    <div class="app-container">
        <!-- 顶部导航栏 -->
        <nav class="top-nav">
            <div class="nav-left">
                <a href="/" class="logo">
                    <span class="logo-icon">K</span>
                    <span class="logo-text">K12学习助手</span>
                </a>
                <div class="nav-menu">
                    <a href="/" class="nav-item">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
                        </svg>
                        <span>对话</span>
                    </a>
                    <a href="/knowledge" class="nav-item active">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"></path>
                            <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"></path>
                        </svg>
                        <span>知识库</span>
                    </a>
                </div>
            </div>
            <div class="nav-right">
                <button class="theme-toggle" title="切换主题">
                    <span>🌙</span>
                    <span>暗色</span>
                </button>
                <a href="/?new=true" class="btn btn-primary" style="padding: 8px 16px; font-size: 12px;">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                        <line x1="12" y1="5" x2="12" y2="19"></line>
                        <line x1="5" y1="12" x2="19" y2="12"></line>
                    </svg>
                    新建对话
                </a>
            </div>
        </nav>

        <!-- 主内容区域 -->
        <div class="main-wrapper">
            <main class="knowledge-main">
                <header class="page-header">
                    <h2>知识库管理</h2>
                </header>

                <!-- 上传区域 -->
                <section class="upload-section">
                    <div class="upload-area" id="uploadArea">
                        <div class="upload-icon">📁</div>
                        <p>拖拽文件到此处，或点击选择文件</p>
                        <p class="upload-hint">支持: PDF, Word, TXT, Markdown</p>
                        <input type="file" id="fileInput" accept=".pdf,.docx,.txt,.md" hidden>
                    </div>

                    <div class="upload-form" id="uploadForm" style="display: none;">
                        <div class="form-row">
                            <div class="form-group">
                                <label>学科</label>
                                <select id="subjectSelect">
                                    <option value="数学">数学</option>
                                    <option value="语文">语文</option>
                                    <option value="英语">英语</option>
                                    <option value="物理">物理</option>
                                    <option value="化学">化学</option>
                                    <option value="生物">生物</option>
                                    <option value="历史">历史</option>
                                    <option value="地理">地理</option>
                                    <option value="政治">政治</option>
                                </select>
                            </div>
                            <div class="form-group">
                                <label>适用年级</label>
                                <select id="gradeSelect" multiple>
                                    <option value="小学">小学</option>
                                    <option value="初一">初一</option>
                                    <option value="初二">初二</option>
                                    <option value="初三">初三</option>
                                    <option value="高一">高一</option>
                                    <option value="高二">高二</option>
                                    <option value="高三">高三</option>
                                </select>
                            </div>
                            <div class="form-group">
                                <label>文档标题</label>
                                <input type="text" id="titleInput" placeholder="如：函数知识点总结">
                            </div>
                        </div>
                        <button class="btn btn-primary" id="uploadBtn">上传并处理</button>
                    </div>
                </section>

                <!-- 统计信息 -->
                <section class="stats-section">
                    <h3>统计信息</h3>
                    <div class="stats-grid">
                        <div class="stat-card">
                            <div class="stat-value" id="totalDocs">0</div>
                            <div class="stat-label">总文档数</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-value" id="totalChunks">0</div>
                            <div class="stat-label">总切片数</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-value" id="storageSize">0 MB</div>
                            <div class="stat-label">存储大小</div>
                        </div>
                    </div>
                </section>

                <!-- 文档列表 -->
                <section class="documents-section">
                    <div class="section-header">
                        <h3>文档列表</h3>
                        <select id="filterSubject" class="filter-select">
                            <option value="">全部学科</option>
                            <option value="数学">数学</option>
                            <option value="物理">物理</option>
                            <option value="化学">化学</option>
                            <option value="英语">英语</option>
                        </select>
                    </div>

                    <div class="documents-table-wrapper">
                        <table class="documents-table">
                            <thead>
                                <tr>
                                    <th>文档名称</th>
                                    <th>学科</th>
                                    <th>切片数</th>
                                    <th>上传时间</th>
                                    <th>操作</th>
                                </tr>
                            </thead>
                            <tbody id="documentsList">
                                <!-- 动态加载 -->
                            </tbody>
                        </table>
                    </div>
                </section>
            </main>
        </div>
    </div>

    <!-- JavaScript -->
    <script src="/static/js/theme.js"></script>
    <script src="/static/js/api.js"></script>
    <script src="/static/js/knowledge.js"></script>
</body>
</html>
```

- [ ] **Step 2: 验证文件更新**

```bash
head -80 web/static/knowledge.html
```

---

### Task 11: 更新app.js适配新结构

**Files:**
- Modify: `web/static/js/app.js`

- [ ] **Step 1: 更新app.js中的newChat函数**

找到 `newChat` 函数（约351行），更新欢迎消息HTML：

```javascript
// 新建对话
function newChat() {
    const newId = generateSessionId();
    saveSessionId(newId);

    messagesContainer.innerHTML = `
        <div class="welcome-message">
            <div class="welcome-icon">🎓</div>
            <h2>你好，我是K12学习助手</h2>
            <p>我可以帮你解答学科问题、辅导作业、疏导情绪</p>
            <div class="quick-actions">
                <button class="quick-btn" data-query="请帮我讲解勾股定理">
                    📐 勾股定理讲解
                </button>
                <button class="quick-btn" data-query="这道方程题怎么做：2x + 5 = 13">
                    📝 作业辅导
                </button>
                <button class="quick-btn" data-query="最近学习压力有点大">
                    💬 情绪疏导
                </button>
            </div>
        </div>
    `;

    bindQuickButtons();
    loadSessionList();
}
```

- [ ] **Step 2: 更新消息气泡中的头像文本**

找到 `appendMessage` 函数（约314行），更新头像文本：

```javascript
// 添加消息
function appendMessage(role, content, metadata = {}) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;

    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.textContent = role === 'user' ? '我' : 'K';

    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';

    // 渲染Markdown
    if (role === 'assistant') {
        contentDiv.innerHTML = renderMarkdown(content);
    } else {
        contentDiv.textContent = content;
    }

    messageDiv.appendChild(avatar);
    messageDiv.appendChild(contentDiv);

    messagesContainer.appendChild(messageDiv);
    scrollToBottom();

    return messageDiv;
}
```

- [ ] **Step 3: 更新历史记录列表渲染**

找到 `renderSessionList` 函数（约105行），更新样式类名：

```javascript
// 渲染会话列表
function renderSessionList(sessions) {
    historyList.innerHTML = '';

    sessions.forEach(session => {
        const li = document.createElement('li');
        li.className = 'history-item' + (session.session_id === sessionId ? ' active' : '');
        li.dataset.sessionId = session.session_id;

        const time = new Date(session.updated_at).toLocaleString('zh-CN', {
            month: 'numeric',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });

        li.innerHTML = `
            <div class="history-item-title">${session.title || '新对话'}</div>
            <div class="history-item-time">${time}</div>
            <button class="history-item-delete" title="删除对话">✕</button>
        `;

        // 点击切换会话
        li.addEventListener('click', (e) => {
            if (!e.target.classList.contains('history-item-delete')) {
                switchSession(session.session_id);
            }
        });

        // 点击删除
        li.querySelector('.history-item-delete').addEventListener('click', (e) => {
            e.stopPropagation();
            deleteSession(session.session_id);
        });

        historyList.appendChild(li);
    });
}
```

---

### Task 12: 更新knowledge.js适配新结构

**Files:**
- Modify: `web/static/js/knowledge.js`

- [ ] **Step 1: 查看当前knowledge.js内容**

```bash
cat web/static/js/knowledge.js
```

- [ ] **Step 2: 更新文档列表渲染，使用新的标签样式**

在渲染文档列表时，将学科标签更新为新样式：

```javascript
// 渲染文档列表时，使用新的标签样式
function renderDocuments(documents) {
    const tbody = document.getElementById('documentsList');
    tbody.innerHTML = '';

    documents.forEach(doc => {
        // 学科标签颜色映射
        const tagClass = {
            '数学': 'tag-cyan',
            '物理': 'tag-purple',
            '化学': 'tag-blue',
            '英语': 'tag-cyan',
            '语文': 'tag-purple'
        }[doc.subject] || 'tag-cyan';

        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${doc.title}</td>
            <td><span class="tag ${tagClass}">${doc.subject}</span></td>
            <td>${doc.chunk_count || 0}</td>
            <td>${formatDate(doc.created_at)}</td>
            <td><button class="delete-btn" data-id="${doc.id}">删除</button></td>
        `;
        tbody.appendChild(row);
    });
}
```

---

### Task 13: 提交所有更改

- [ ] **Step 1: 查看所有更改**

```bash
cd /Users/wangyanjun/Desktop/my-project/rag-kb
git status
```

- [ ] **Step 2: 添加所有文件**

```bash
git add web/static/css/ web/static/js/ web/static/index.html web/static/knowledge.html
```

- [ ] **Step 3: 提交更改**

```bash
git commit -m "$(cat <<'EOF'
feat(web): redesign frontend with glassmorphism style

- Add CSS variables system for theming
- Implement dark/light dual theme support
- Add resizable sidebar with drag interaction
- Update chat page with gradient message bubbles
- Update knowledge page with new card styles
- Add glassmorphism effects (backdrop-filter)
- Add smooth animations and transitions

Visual changes:
- New color scheme: cyan-blue-purple gradient
- Top navigation bar with glass effect
- Semi-transparent cards and sidebars
- Gradient accent buttons and icons

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
EOF
)"
```

---

### Task 14: 测试和验证

- [ ] **Step 1: 启动开发服务器**

```bash
cd /Users/wangyanjun/Desktop/my-project/rag-kb
python run.py
```

- [ ] **Step 2: 在浏览器中测试**

1. 打开 http://localhost:8000
2. 测试亮色/暗色主题切换
3. 测试侧边栏拖拽调整宽度
4. 测试消息发送和显示
5. 测试知识库页面上传和列表

- [ ] **Step 3: 检查控制台错误**

打开浏览器开发者工具，检查是否有JavaScript错误。

---

## 设计稿参考

设计稿已保存在 `.superpowers/brainstorm/` 目录，可通过启动 Visual Companion 服务器查看。
