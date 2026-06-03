# K12智能学习助手 - 前端视觉重设计方案

## 1. 项目概述

### 1.1 设计目标
对 K12智能学习助手 Web 前端进行视觉风格升级，打造**活泼友好 + 现代科技**的用户体验。

### 1.2 核心设计方向
- **视觉风格**：科技感毛玻璃（Glassmorphism）风格
- **配色方案**：清新冷色系（青、蓝、紫渐变）
- **布局结构**：混合布局（顶部导航 + 可折叠侧边栏）
- **特性支持**：亮色/暗色双主题、流畅动画、移动端适配

---

## 2. 设计规范

### 2.1 配色系统

#### 共用强调色（亮/暗模式通用）
| 颜色名称 | 色值 | 用途 |
|---------|------|------|
| 青色 | `#4ECDC4` | 主强调色、按钮、链接 |
| 蓝色 | `#45B7D1` | 渐变中间色 |
| 紫色 | `#5C7AEA` | 辅助强调色、渐变终点色 |
| 深紫 | `#764ba2` | 特殊强调 |

**渐变定义**：
- 主渐变：`linear-gradient(135deg, #4ECDC4, #5C7AEA)`
- 强调渐变：`linear-gradient(135deg, #4ECDC4, #45B7D1, #5C7AEA)`

#### 亮色模式配色
| 元素 | 色值 | 说明 |
|------|------|------|
| 主背景 | `#f8fafc` | 浅灰白背景 |
| 次背景 | `#f1f5f9` | 区域分隔背景 |
| 卡片背景 | `#ffffff` | 纯白卡片 |
| 导航栏背景 | `rgba(255, 255, 255, 0.85)` | 白色毛玻璃 |
| 侧边栏背景 | `rgba(248, 250, 252, 0.9)` | 浅灰毛玻璃 |
| 主文字 | `#1e293b` | 深灰标题/正文 |
| 次要文字 | `#64748b` | 说明文字 |
| 辅助文字 | `#94a3b8` | 时间、提示 |
| 边框 | `#e2e8f0` | 分割线、卡片边框 |
| 成功色 | `#22c55e` | 成功提示 |
| 错误色 | `#f87171` | 错误、删除按钮 |
| 警告色 | `#fbbf24` | 警告提示 |

#### 暗色模式配色
| 元素 | 色值 | 说明 |
|------|------|------|
| 主背景 | `#0f0f1a` | 深蓝黑背景 |
| 次背景 | `#12121e` | 区域分隔背景 |
| 卡片背景 | `rgba(30, 30, 50, 0.5)` | 半透明毛玻璃 |
| 导航栏背景 | `rgba(18, 18, 30, 0.8)` | 深色毛玻璃 |
| 侧边栏背景 | `rgba(20, 20, 35, 0.6)` | 深色毛玻璃 |
| 主文字 | `#ffffff` | 白色标题/正文 |
| 次要文字 | `rgba(255, 255, 255, 0.6)` | 说明文字 |
| 辅助文字 | `rgba(255, 255, 255, 0.35)` | 时间、提示 |
| 边框 | `rgba(255, 255, 255, 0.08)` | 半透明边框 |
| 边框高亮 | `rgba(78, 205, 196, 0.3)` | 激活状态边框 |

### 2.2 字体规范

| 类型 | 字号 | 字重 | 行高 | 用途 |
|------|------|------|------|------|
| 页面标题 | `24px` | 600 | 1.3 | 欢迎语、页面标题 |
| 区块标题 | `18px` | 600 | 1.4 | 卡片标题、弹窗标题 |
| 正文 | `14px` | 400 | 1.6 | 正文内容、描述 |
| 辅助文字 | `12px` | 400 | 1.5 | 时间、标签、提示 |
| 按钮 | `13px` | 500 | 1.4 | 按钮文字 |
| 导航 | `13px` | 500 | 1.4 | 导航项 |

**字体族**：`-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif`

### 2.3 圆角规范

| 类型 | 圆角值 | 用途 |
|------|--------|------|
| 小圆角 | `6px` | 小按钮、标签、输入框 |
| 中圆角 | `10px` | 按钮、导航项 |
| 大圆角 | `12px` | 卡片、弹窗、侧边栏 |
| 胶囊 | `16px` | 消息气泡、快捷按钮 |
| 圆形 | `50%` | 头像、图标按钮 |

### 2.4 阴影规范

#### 亮色模式
```css
--shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.05);
--shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
--shadow-lg: 0 4px 12px rgba(0, 0, 0, 0.1);
--shadow-glow: 0 4px 20px rgba(92, 122, 234, 0.25);
```

#### 暗色模式
```css
--shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.2);
--shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
--shadow-lg: 0 8px 24px rgba(0, 0, 0, 0.4);
--shadow-glow: 0 4px 20px rgba(92, 122, 234, 0.35);
```

### 2.5 毛玻璃效果

```css
/* 亮色模式毛玻璃 */
.glass-light {
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border: 1px solid rgba(0, 0, 0, 0.06);
}

/* 暗色模式毛玻璃 */
.glass-dark {
  background: rgba(30, 30, 50, 0.5);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border: 1px solid rgba(255, 255, 255, 0.08);
}
```

---

## 3. 布局设计

### 3.1 页面结构

```
┌─────────────────────────────────────────────────────────┐
│                     顶部导航栏 (固定)                      │
│  Logo | 导航菜单 | 主题切换 | 设置                         │
├──────────┬──────────────────────────────────────────────┤
│          │                                              │
│  可调节   │              主内容区域                       │
│  侧边栏   │                                              │
│          │    - 欢迎区域 / 消息列表                       │
│  历史    │    - 输入区域                                 │
│  记录    │                                              │
│          │                                              │
│  (可拖拽 │                                              │
│   调整)  │                                              │
│          │                                              │
└──────────┴──────────────────────────────────────────────┘
```

### 3.2 尺寸规范

| 元素 | 尺寸 |
|------|------|
| 顶部导航栏高度 | `56px` |
| 侧边栏默认宽度 | `220px` |
| 侧边栏最小宽度 | `160px` |
| 侧边栏最大宽度 | `320px` |
| 内容区最小宽度 | `600px` |
| 输入区域高度 | `72px`（固定） |
| 消息气泡最大宽度 | `65%` |

### 3.3 响应式断点

| 断点 | 宽度范围 | 布局调整 |
|------|---------|---------|
| 桌面 | `≥1024px` | 完整布局，侧边栏展开 |
| 平板 | `768px - 1023px` | 侧边栏收起为图标 |
| 手机 | `<768px` | 侧边栏隐藏，汉堡菜单 |

---

## 4. 组件设计

### 4.1 导航栏

**亮色模式**：
- 背景：白色毛玻璃 `rgba(255, 255, 255, 0.85)`
- 底部边框：`1px solid rgba(0, 0, 0, 0.06)`
- Logo：渐变文字 + 渐变图标
- 导航项：圆角背景，激活态青色高亮

**暗色模式**：
- 背景：深色毛玻璃 `rgba(18, 18, 30, 0.8)`
- 底部边框：`1px solid rgba(255, 255, 255, 0.06)`
- 导航项：激活态青色边框

### 4.2 侧边栏

**功能**：
- 历史记录列表
- 新建对话按钮
- 可拖拽调整宽度

**交互**：
- 鼠标拖拽右边缘调整宽度
- 移动端点击汉堡菜单展开/收起
- 历史项 hover 高亮，点击加载对话

### 4.3 消息气泡

**用户消息**：
- 背景：渐变 `linear-gradient(135deg, #4ECDC4, #5C7AEA)`
- 文字：白色
- 圆角：`16px 16px 4px 16px`（右下角小圆角）
- 阴影：渐变发光阴影

**AI消息**：
- 亮色：白色背景 + 浅灰边框
- 暗色：毛玻璃背景 `rgba(30, 30, 50, 0.5)`
- 圆角：`16px 16px 16px 4px`（左下角小圆角）

### 4.4 输入区域

**布局**：
- 固定在底部
- 输入框 + 发送按钮

**样式**：
- 亮色：浅灰背景 `#f8fafc` + 灰色边框
- 暗色：深灰背景 `rgba(30, 30, 50, 0.6)` + 半透明边框
- 发送按钮：渐变背景 + 发光阴影

### 4.5 快捷操作按钮

**样式**：
- 背景：渐变半透明 `linear-gradient(135deg, rgba(78, 205, 196, 0.08), rgba(92, 122, 234, 0.08))`
- 边框：渐变色边框
- 文字：对应的强调色
- 圆角：`12px`
- Hover：背景加深 + 轻微上移

### 4.6 统计卡片

**布局**：三列等宽网格

**样式**：
- 数字：渐变文字 `background-clip: text`
- 暗色模式：毛玻璃背景
- Hover：边框高亮 + 轻微上移

---

## 5. 动效规范

### 5.1 过渡动画

```css
/* 通用过渡 */
--transition-fast: 0.15s ease;
--transition: 0.2s ease;
--transition-slow: 0.3s ease;

/* 示例 */
.button {
  transition: all 0.2s ease;
}

.button:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(92, 122, 234, 0.3);
}
```

### 5.2 消息进入动画

```css
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

.message {
  animation: messageIn 0.25s ease;
}
```

### 5.3 侧边栏宽度调节

```css
.sidebar {
  transition: width 0.2s ease;
}
```

### 5.4 主题切换

```css
body {
  transition: background-color 0.3s ease, color 0.3s ease;
}
```

---

## 6. 页面设计详述

### 6.1 对话页面

**欢迎区域**：
- 居中布局
- 渐变图标（80x80px，圆角22px）
- 标题 + 描述
- 三个快捷操作按钮

**消息列表**：
- 支持滚动
- 用户消息靠右，AI消息靠左
- 显示时间戳

**输入区域**：
- 固定底部
- 自适应高度（最大150px）
- 发送按钮渐变色

### 6.2 知识库页面

**上传区域**：
- 虚线边框
- 拖拽上传支持
- 支持格式：PDF, Word, TXT, Markdown

**统计卡片**：
- 三列布局
- 渐变数字
- 图标说明

**文档列表**：
- 表格形式
- 学科标签（彩色）
- 删除操作

---

## 7. 交互规范

### 7.1 按钮状态

| 状态 | 样式 |
|------|------|
| 默认 | 渐变背景 |
| Hover | 上移1px + 发光阴影 |
| Active | 下移1px + 阴影减淡 |
| Disabled | 灰色背景 + 禁止光标 |

### 7.2 输入框状态

| 状态 | 样式 |
|------|------|
| 默认 | 灰色边框 |
| Focus | 青色边框 + 发光阴影 |
| Error | 红色边框 |

### 7.3 导航项状态

| 状态 | 样式 |
|------|------|
| 默认 | 透明背景 |
| Hover | 浅色背景 |
| Active | 青色背景 + 青色文字 |

---

## 8. 实现要点

### 8.1 主题切换实现

```javascript
// 主题切换逻辑
const toggleTheme = () => {
  const isDark = document.body.classList.toggle('dark-mode');
  localStorage.setItem('theme', isDark ? 'dark' : 'light');
};

// 初始化主题
const initTheme = () => {
  const savedTheme = localStorage.getItem('theme');
  const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;

  if (savedTheme === 'dark' || (!savedTheme && prefersDark)) {
    document.body.classList.add('dark-mode');
  }
};
```

### 8.2 侧边栏拖拽实现

```javascript
// 拖拽调整宽度
const handleResize = (e) => {
  const sidebar = document.querySelector('.sidebar');
  const newWidth = e.clientX;
  const minWidth = 160;
  const maxWidth = 320;

  if (newWidth >= minWidth && newWidth <= maxWidth) {
    sidebar.style.width = `${newWidth}px`;
  }
};
```

### 8.3 毛玻璃兼容性

```css
/* 检测 backdrop-filter 支持 */
@supports (backdrop-filter: blur(16px)) {
  .glass {
    backdrop-filter: blur(16px);
  }
}

@supports not (backdrop-filter: blur(16px)) {
  .glass {
    /* 降级为纯色背景 */
    background: rgba(255, 255, 255, 0.95);
  }
}
```

---

## 9. 文件结构

```
web/static/
├── css/
│   ├── variables.css      # CSS变量定义
│   ├── base.css           # 基础样式、重置
│   ├── components.css     # 组件样式
│   ├── layout.css         # 布局样式
│   ├── chat.css           # 对话页面样式
│   └── knowledge.css      # 知识库页面样式
├── js/
│   ├── theme.js           # 主题切换逻辑
│   ├── sidebar.js         # 侧边栏交互
│   ├── app.js             # 主应用逻辑
│   ├── api.js             # API请求
│   └── markdown.js        # Markdown渲染
└── index.html
    knowledge.html
```

---

## 10. 设计资源

### 10.1 图标
- 使用系统 emoji 作为图标
- 或引入 Feather Icons / Lucide Icons

### 10.2 字体
- 系统默认字体栈
- 可选引入 Inter 字体增强体验

### 10.3 动画库
- CSS 原生动画
- 可选 Animate.css 用于复杂动画

---

## 附录：设计稿预览

设计稿已保存至 `.superpowers/brainstorm/` 目录，包含：
- 聊天页面亮色/暗色模式
- 知识库页面亮色/暗色模式
- 消息气泡样式
- 配色方案详情

可通过启动 Visual Companion 服务器查看完整设计稿。
