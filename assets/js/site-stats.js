(function () {
  'use strict';

  var snapshotUrl =
    'https://raw.githubusercontent.com/lkq1220/lkq1220.github.io/site-stats/site_stats.json';
  var storageKey = 'lkq_site_stats_v1';

  function parseCounter(value) {
    var counter = Number(value);
    return Number.isSafeInteger(counter) && counter > 0 ? counter : null;
  }

  function readStoredCounters() {
    try {
      var stored = JSON.parse(localStorage.getItem(storageKey) || '{}');
      return {
        views: parseCounter(stored.views),
        visitors: parseCounter(stored.visitors)
      };
    } catch (error) {
      return { views: null, visitors: null };
    }
  }

  function writeStoredCounters(counters) {
    try {
      localStorage.setItem(storageKey, JSON.stringify(counters));
    } catch (error) {
      // The visible counters still work when storage is unavailable.
    }
  }

  function maximumCounter() {
    var values = Array.prototype.slice.call(arguments)
      .map(parseCounter)
      .filter(function (value) {
        return value !== null;
      });
    return values.length ? Math.max.apply(Math, values) : null;
  }

  function render(remote) {
    var viewsNode = document.getElementById('site_stat_views');
    var visitorsNode = document.getElementById('site_stat_visitors');
    if (!viewsNode || !visitorsNode) return;

    var stored = readStoredCounters();
    var counters = {
      views: maximumCounter(
        viewsNode.getAttribute('data-floor'),
        viewsNode.textContent,
        stored.views,
        remote && remote.views
      ),
      visitors: maximumCounter(
        visitorsNode.getAttribute('data-floor'),
        visitorsNode.textContent,
        stored.visitors,
        remote && remote.visitors
      )
    };

    if (counters.views !== null) {
      viewsNode.textContent = String(counters.views);
    }
    if (counters.visitors !== null) {
      visitorsNode.textContent = String(counters.visitors);
    }
    if (counters.views !== null && counters.visitors !== null) {
      writeStoredCounters(counters);
    }
  }

  window.refreshSiteStats = function () {
    if (
      !document.getElementById('site_stat_views') ||
      !document.getElementById('site_stat_visitors')
    ) {
      return Promise.resolve(null);
    }

    render(null);

    return fetch(snapshotUrl + '?v=' + Date.now(), { cache: 'no-store' })
      .then(function (response) {
        if (!response.ok) {
          throw new Error('Could not load the site statistics snapshot');
        }
        return response.json();
      })
      .then(function (snapshot) {
        render(snapshot);
        return snapshot;
      })
      .catch(function (error) {
        console.warn(error);
        return null;
      });
  };

  window.refreshSiteStats();
})();
