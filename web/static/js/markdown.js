// web/static/js/markdown.js

/**
 * Markdown渲染器 - 支持表格和数学公式
 */

function renderMarkdown(text) {
    if (!text) return '';

    // 预处理：保护数学公式不被Markdown解析器破坏
    let processed = protectMathFormulas(text);

    // 使用marked解析Markdown
    let html;
    if (typeof marked !== 'undefined') {
        html = marked.parse(processed);
    } else {
        // 降级到简单解析
        html = simpleMarkdown(processed);
    }

    // 后处理：渲染数学公式
    html = renderMathInHtml(html);

    return html;
}

// 保护数学公式
function protectMathFormulas(text) {
    // 行内公式 $...$  -> 使用占位符
    // 块级公式 $$...$$ -> 使用占位符
    const placeholders = [];

    // 先处理块级公式 $$...$$
    text = text.replace(/\$\$([\s\S]+?)\$\$/g, (match, formula) => {
        const index = placeholders.length;
        placeholders.push({ type: 'block', formula: formula.trim() });
        return `%%MATH_BLOCK_${index}%%`;
    });

    // 再处理行内公式 $...$
    // 注意：要避免匹配到价格如 $5.99
    text = text.replace(/\$([^\$\n]+?)\$/g, (match, formula) => {
        // 检查是否像价格（数字开头）
        if (/^\d+(\.\d+)?$/.test(formula.trim())) {
            return match; // 保持原样
        }
        const index = placeholders.length;
        placeholders.push({ type: 'inline', formula: formula.trim() });
        return `%%MATH_INLINE_${index}%%`;
    });

    // 存储占位符供后续使用
    window._mathPlaceholders = placeholders;

    return text;
}

// 渲染数学公式
function renderMathInHtml(html) {
    const placeholders = window._mathPlaceholders || [];

    // 渲染块级公式
    placeholders.forEach((item, index) => {
        if (item.type === 'block') {
            const rendered = renderKatex(item.formula, true);
            html = html.replace(`%%MATH_BLOCK_${index}%%`, rendered);
        } else {
            const rendered = renderKatex(item.formula, false);
            html = html.replace(`%%MATH_INLINE_${index}%%`, rendered);
        }
    });

    return html;
}

// 使用KaTeX渲染公式
function renderKatex(formula, displayMode) {
    if (typeof katex === 'undefined') {
        // KaTeX未加载，返回原始公式
        return displayMode
            ? `<div class="math-block">$$${formula}$$</div>`
            : `$${formula}$`;
    }

    try {
        return katex.renderToString(formula, {
            displayMode: displayMode,
            throwOnError: false,
            trust: true
        });
    } catch (e) {
        console.warn('KaTeX render error:', e);
        return displayMode
            ? `<div class="math-error">$$${formula}$$</div>`
            : `$${formula}$`;
    }
}

// 简单Markdown解析（降级方案）
function simpleMarkdown(text) {
    let html = text
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;');

    // 标题
    html = html.replace(/^### (.+)$/gm, '<h3>$1</h3>');
    html = html.replace(/^## (.+)$/gm, '<h2>$1</h2>');
    html = html.replace(/^# (.+)$/gm, '<h1>$1</h1>');

    // 粗体
    html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');

    // 斜体
    html = html.replace(/\*(.+?)\*/g, '<em>$1</em>');

    // 代码块
    html = html.replace(/```(\w*)\n([\s\S]+?)```/g, '<pre><code class="language-$1">$2</code></pre>');

    // 行内代码
    html = html.replace(/`(.+?)`/g, '<code>$1</code>');

    // 列表
    html = html.replace(/^- (.+)$/gm, '<li>$1</li>');
    html = html.replace(/(<li>.*<\/li>\n?)+/g, '<ul>$&</ul>');

    // 有序列表
    html = html.replace(/^\d+\. (.+)$/gm, '<li>$1</li>');

    // 段落
    html = html.replace(/\n\n/g, '</p><p>');
    html = '<p>' + html + '</p>';

    // 清理空段落
    html = html.replace(/<p>\s*<\/p>/g, '');

    return html;
}
