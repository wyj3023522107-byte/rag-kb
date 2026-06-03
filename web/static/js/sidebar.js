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
