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
