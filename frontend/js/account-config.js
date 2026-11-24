// Per-site settings for the accounts UI (auth.js, history.js).
window.ARTERION_APP = {
  slug: "dominance",
  name: "Arterion Coronary Dominance",
  home: "index.html",
  tasks: {
    "dominance": "Coronary dominance"
  },
  // One-line summary of a saved result, shown at the top of its details.
  headline: function (r) {
    return String(r.dominance_type || '').replace(/^./, function (c) { return c.toUpperCase(); }) + '-dominant · ' + Math.round((r.confidence || 0) * 100) + '% confidence';
  },
};
