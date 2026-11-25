(() => {
  const $ = (id) => document.getElementById(id);
  const API = window.API_BASE.replace(/\/$/, "");
  const MAX_PER_VIEW = 4;
  const PERF = { RCA: "94%", LCA: "88%" };            // single-run balanced accuracy on 117 held-out studies
  const show = (el, on) => (el.hidden = !on);
  const study = { RCA: [], LCA: [] };
  let truth = null;

  /* ---------- status ---------- */
  async function ping() {
    const el = $("status");
    try {
      if (!(await fetch(API + "/health", { cache: "no-store" })).ok) throw 0;
      el.className = "status ok"; el.textContent = "API online";
    } catch {
      el.className = "status bad"; el.textContent = "API offline at " + API; setTimeout(ping, 4000);
    }
  }
  ping();

  /* ---------- slots ---------- */
  ["RCA", "LCA"].forEach((view) => {
    $("in-" + view).addEventListener("change", (e) => { addFiles(view, [...e.target.files]); e.target.value = ""; });
    const dz = document.querySelector(`#slot-${view} .dz`);
    ["dragenter", "dragover"].forEach((ev) => dz.addEventListener(ev, (x) => { x.preventDefault(); dz.classList.add("over"); }));
    ["dragleave", "drop"].forEach((ev) => dz.addEventListener(ev, (x) => { x.preventDefault(); dz.classList.remove("over"); }));
    dz.addEventListener("drop", (e) => addFiles(view, [...e.dataTransfer.files]));
  });

  function addFiles(view, files) {
    setError(""); truth = null;
    for (const f of files) {
      if (study[view].length >= MAX_PER_VIEW) { setError(`At most ${MAX_PER_VIEW} runs per view.`); break; }
      if (!/^(video|image)\//.test(f.type) && !/\.(npz|avi|mp4|mov|png|jpe?g)$/i.test(f.name)) { setError(`“${f.name}” is not a video, .npz or image.`); continue; }
      study[view].push(f);
    }
    renderChips();
  }

  function renderChips() {
    ["RCA", "LCA"].forEach((view) => {
      const ul = $("chips-" + view); ul.innerHTML = "";
      study[view].forEach((f, i) => {
        const li = document.createElement("li");
        li.innerHTML = `<span title="${f.name.replace(/"/g, "")}"></span><button aria-label="Remove ${view} run" type="button">×</button>`;
        li.firstChild.textContent = f.name;
        li.lastChild.addEventListener("click", () => { study[view].splice(i, 1); truth = null; renderChips(); });
        ul.appendChild(li);
      });
    });
    const n = study.RCA.length + study.LCA.length;
    $("go").disabled = n === 0; show($("clear"), n > 0);
  }
  $("clear").addEventListener("click", reset);

  function reset() {
    study.RCA = []; study.LCA = []; truth = null; renderChips(); setError(""); show($("notice"), false);
    show($("reading"), false); show($("idleNote"), true); $("figure").dataset.state = "idle";
  }

  const setError = (m) => { $("error").textContent = m || ""; show($("error"), !!m); };

  /* ---------- samples ---------- */
  (async () => {
    try {
      const list = await (await fetch("samples/index.json")).json();
      if (!list.length) return;
      show($("samples"), true);
      list.forEach((s) => {
        const b = document.createElement("button"); b.type = "button"; b.textContent = s.title;
        b.addEventListener("click", async () => {
          setError("");
          study.RCA = []; study.LCA = [];
          for (const f of s.files) {
            const blob = await (await fetch(f.file)).blob();
            study[f.view].push(new File([blob], f.file.split("/").pop(), { type: blob.type || "video/mp4" }));
          }
          truth = s.truth; renderChips(); run();
        });
        $("sampleBtns").appendChild(b);
      });
    } catch {}
  })();

  /* ---------- run ---------- */
  async function post(path, body, isForm) {
    const r = await fetch(API + path, { method: "POST", headers: isForm ? undefined : { "Content-Type": "application/json" }, body: isForm ? body : JSON.stringify(body) });
    let j = null; try { j = await r.json(); } catch {}
    if (!r.ok) {
      const d = j && j.detail;
      throw new Error(typeof d === "string" ? d : Array.isArray(d) ? "The study could not be read (check the files and views)." : `Request failed (${r.status})`);
    }
    return j;
  }
  $("go").addEventListener("click", run);

  async function run() {
    setError(""); show($("notice"), false);
    const items = [...study.RCA.map((f) => ["RCA", f]), ...study.LCA.map((f) => ["LCA", f])];
    if (!items.length) return;
    show($("busy"), true); $("busyText").textContent = "Uploading runs…";
    try {
      const videos = [];
      for (const [view, f] of items) {
        const fd = new FormData(); fd.append("file", f);
        videos.push({ file_url: (await post("/uploads", fd, true)).file_url, view });
      }
      $("busyText").textContent = "Reading study…";
      render(await post("/dominance/predict", { videos }));
    } catch (e) {
      setError(e.message === "Failed to fetch" ? `Cannot reach the API at ${API}. Is the backend running?` : e.message);
    } finally { show($("busy"), false); }
  }

  function render(r) {
    if (r.dominance_type === "unknown") {
      $("notice").innerHTML = "The model weights are not installed, so no reading was produced. Run <code>scripts/fetch_weights</code> (or place <code>dominance_model.onnx</code> in <code>backend/app/dominance/weights/</code>) and restart the API.";
      show($("notice"), true); return;
    }
    const d = r.dominance_type;
    const fig = $("figure"); fig.dataset.state = d;
    document.querySelectorAll(".vessel").forEach((p) => { p.classList.remove("draw"); void p.getBoundingClientRect(); });
    document.querySelectorAll(d === "right" ? ".rca,.pda-r" : ".lcx,.pda-l").forEach((p) => p.classList.add("draw"));
    $("figcap").textContent = d === "right" ? "Right-dominant: the RCA gives off the posterior descending artery (PDA)." : "Left-dominant: the circumflex (LCx) gives off the posterior descending artery (PDA).";

    show($("idleNote"), false); show($("reading"), true);
    $("reading").className = "reading " + d;
    $("verdict").innerHTML = `<em>${d === "right" ? "Right" : "Left"}</em>-dominant`;
    $("kicker").textContent = "Predicted";
    $("conf").textContent = `${Math.round(r.confidence * 100)}% model confidence`;
    requestAnimationFrame(() => ($("mark").style.left = (r.p_left * 100).toFixed(1) + "%"));

    const ul = $("runs"); ul.innerHTML = "";
    r.per_video.forEach((v) => {
      const li = document.createElement("li"); li.style.setProperty("--c", v.view === "RCA" ? "var(--red)" : "var(--blue)");
      li.innerHTML = `<b>${v.view}</b><div class="mini" style="--p:${(v.p_left * 100).toFixed(1)}%"><i></i></div><span>${v.p_left > 0.5 ? "left" : "right"} ${(Math.max(v.p_left, 1 - v.p_left) * 100).toFixed(0)}%</span>`;
      ul.appendChild(li);
    });

    const note = $("viewNote");
    if (r.views_used.length === 1) {
      note.textContent = `Only the ${r.views_used[0]} view was provided. On held-out studies a single ${r.views_used[0]} run was right about ${PERF[r.views_used[0]]} of the time (balanced accuracy); adding the other view helps.`;
      show(note, true);
    } else show(note, false);

    const t = $("truth");
    if (truth) { t.textContent = `Reference label for this sample study: ${truth}-dominant (${truth === d ? "matches" : "does not match"} the prediction).`; show(t, true); } else show(t, false);
  }
  renderChips();
})();
