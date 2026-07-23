// pjax.js — 完整版：导航高亮 + 子导航平滑滚动 + 兼容 GitHub Pages 子路径
document.addEventListener('DOMContentLoaded', () => {
  const container = document.getElementById('pjax-container');
  const topLinks = Array.from(document.querySelectorAll('.masthead__menu-item a'));

  // 更新主导航高亮，兼容仓库子路径
  function updateTopnavHighlight() {
    const currentPath = window.location.pathname.replace(/\/+$/, '/');
    topLinks.forEach(link => {
      // 用 link.pathname 确保拿到带仓库前缀的绝对路径
      const hrefPath = link.pathname.replace(/\/+$/, '/');
      if (hrefPath === currentPath || (hrefPath !== '/' && currentPath.startsWith(hrefPath))) {
        link.classList.add('active');
        link.setAttribute('aria-current', 'page');
      } else {
        link.classList.remove('active');
        link.removeAttribute('aria-current');
      }
    });
  }

  // 重新执行 pjax-container 内的脚本（innerHTML 插入的 script 不会自动执行）
  function rerunScripts() {
    if (!container) return;
    container.querySelectorAll('script').forEach(oldScript => {
      // Vercount script is reloaded after PJAX swaps the page content.
      if (oldScript.src && oldScript.src.indexOf('events.vercount.one') !== -1) return;

      const newScript = document.createElement('script');
      Array.from(oldScript.attributes).forEach(attr => {
        newScript.setAttribute(attr.name, attr.value);
      });
      if (oldScript.textContent) {
        newScript.textContent = oldScript.textContent;
      }
      oldScript.parentNode.replaceChild(newScript, oldScript);
    });
  }

  // Reload the visitor counter after PJAX swaps page content.
  function reloadVercount() {
    // Skip pages without the visitor counter.
    if (!document.getElementById('site_stat_views')) return;

    // Remove old counter scripts before loading a fresh one.
    document.querySelectorAll('script[src*="events.vercount.one"]').forEach(function(s) {
      s.parentNode.removeChild(s);
    });

    // Load from head so it runs after the new content is in place.
    var script = document.createElement('script');
    script.src = 'https://events.vercount.one/js?' + Date.now();
    script.defer = true;
    document.head.appendChild(script);
  }

  // 绑定子导航锚点滚动（覆盖 base target）
  function bindSubnav() {
    document.querySelectorAll('.subnav a[href^="#"]').forEach(link => {
      link.target = '_self';
      link.addEventListener('click', e => {
        e.preventDefault();
        const targetEl = document.querySelector(link.hash);
        if (targetEl) {
          targetEl.scrollIntoView({ behavior: 'smooth' });
          history.replaceState(null, '', window.location.pathname + link.hash);
        }
      });
    });
  }

  // PJAX 加载页面并替换内容
  function loadPage(url, addToHistory = true) {
    fetch(url)
      .then(res => res.text())
      .then(html => {
        const parser = new DOMParser();
        const doc = parser.parseFromString(html, 'text/html');
        const next = doc.getElementById('pjax-container');
        if (next && container) {
          container.innerHTML = next.innerHTML;
        }
        // 更新浏览器标签页标题
        const docTitle = doc.querySelector('title');
        if (docTitle) {
          document.title = docTitle.textContent;
        }

        // 先更新历史记录
        if (addToHistory) {
          history.pushState(null, '', url);
          window.scrollTo(0, 0);
        }
        // 再更新主导航高亮
        updateTopnavHighlight();
        // 重新绑定子导航
        bindSubnav();
        // 重新执行页面内的脚本
        rerunScripts();
        // Reload visitor stats after PJAX navigation.
        reloadVercount();
        if (window.refreshSiteStats) {
          window.refreshSiteStats();
        }
        if (window.refreshGoogleScholarStats) {
          window.refreshGoogleScholarStats();
        }
      })
      .catch(console.error);
  }

  // 拦截主导航点击
  topLinks.forEach(a => {
    a.addEventListener('click', e => {
      e.preventDefault();
      loadPage(a.href);
    });
  });

  // 处理浏览器前进/后退
  window.addEventListener('popstate', () => {
    loadPage(location.href, false);
  });

  // 首次加载时，设置高亮并绑定子导航
  updateTopnavHighlight();
  bindSubnav();
});
