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

  // 更新切换按钮
  function updateToggleButtonText(theme) {
    const buttons = document.querySelectorAll('.theme-toggle');
    const isDark = theme === DARK_THEME;
    buttons.forEach(btn => {
      const svg = btn.querySelector('svg');
      const text = btn.querySelector('span:last-child');
      if (svg) {
        // 切换月亮/太阳图标
        if (isDark) {
          svg.innerHTML = '<circle cx="12" cy="12" r="5"></circle><line x1="12" y1="1" x2="12" y2="3"></line><line x1="12" y1="21" x2="12" y2="23"></line><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line><line x1="1" y1="12" x2="3" y2="12"></line><line x1="21" y1="12" x2="23" y2="12"></line><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line>';
        } else {
          svg.innerHTML = '<path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path>';
        }
      }
      if (text) {
        text.textContent = isDark ? '亮色' : '暗色';
      }
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
