/* ========== INIT ========== */
const tg = window.Telegram?.WebApp;
tg?.ready();
tg?.expand?.();

const params = new URLSearchParams(location.search);
const TID = parseInt(params.get("tid") || "0", 10);
const INIT_DATA = tg?.initData || "";

const els = {
  title: document.getElementById("title"),
  status: document.getElementById("status"),
  pokerView: document.getElementById("poker-view"),
  wheelView: document.getElementById("wheel-view"),
  pot: document.getElementById("pot"),
  community: document.getElementById("community"),
  ring: document.getElementById("players-ring"),
  logBox: document.getElementById("log-box"),
  actions: document.getElementById("poker-actions"),
  raiseRow: document.getElementById("raise-row"),
  raiseSlider: document.getElementById("raise-slider"),
  raiseAmount: document.getElementById("raise-amount"),
  timerFill: document.getElementById("timer-fill"),
  wheel: document.getElementById("wheel"),
  spinBtn: document.getElementById("spin-btn"),
  elimList: document.getElementById("eliminated-list"),
  actList: document.getElementById("active-list"),
  prize: document.getElementById("wheel-prize"),
  modal: document.getElementById("modal"),
  modalTitle: document.getElementById("modal-title"),
  modalBody: document.getElementById("modal-body"),
  modalClose: document.getElementById("modal-close"),
  confetti: document.getElementById("confetti"),
};

let WS = null;
let MY_ID = null;
let GAME_TYPE = null;
let LAST_POKER = null;
let LAST_WHEEL = null;
let WHEEL_ANGLE = 0;
let WHEEL_SPINNING = false;

/* ========== BOOT ========== */
(async function boot() {
  if (!TID || !INIT_DATA) {
    setStatus("Нет данных Mini App", "err");
    return;
  }
  try {
    const r = await fetch(`/api/tournament/${TID}?initData=${encodeURIComponent(INIT_DATA)}`);
    if (!r.ok) throw new Error(await r.text());
    const info = await r.json();
    GAME_TYPE = info.game_type;
    MY_ID = info.user_id;
    els.title.textContent = `🏆 ${info.name}`;
    if (GAME_TYPE === "poker") {
      els.pokerView.classList.remove("hidden");
    } else {
      els.wheelView.classList.remove("hidden");
    }
    connectWS();
  } catch (e) {
    setStatus("Ошибка: " + e.message, "err");
  }
})();

function setStatus(t, cls) {
  els.status.textContent = t;
  els.status.className = "status " + (cls || "");
}

/* ========== WEBSOCKET ========== */
function connectWS() {
  const proto = location.protocol === "https:" ? "wss" : "ws";
  const url = `${proto}://${location.host}/ws/${TID}?initData=${encodeURIComponent(INIT_DATA)}`;
  WS = new WebSocket(url);

  WS.onopen = () => setStatus("🟢 Онлайн", "ok");
  WS.onclose = () => { setStatus("🔴 Оффлайн", "err"); setTimeout(connectWS, 2000); };
  WS.onerror = () => setStatus("⚠ Ошибка", "err");

  WS.onmessage = (ev) => {
    const msg = JSON.parse(ev.data);
    if (msg.type === "poker_state") renderPoker(msg);
    else if (msg.type === "wheel_state") renderWheel(msg);
    else if (msg.type === "tournament_cancelled") {
      showModal("🛑 Турнир отменён", "Администратор остановил турнир.");
    }
  };
}

function wsSend(obj) {
  if (WS && WS.readyState === 1) WS.send(JSON.stringify(obj));
}

/* ========== POKER RENDER ========== */
function renderPoker(s) {
  LAST_POKER = s;

  // pot
  els.pot.textContent = `💰 Банк: ${s.pot}`;

  // community
  els.community.innerHTML = "";
  s.community.forEach(c => els.community.appendChild(makeCard(c)));

  // players around the oval
  const total = s.players.length;
  const cx = 50, cy = 50, rx = 40, ry = 42;
  els.ring.innerHTML = "";
  s.players.forEach((p, i) => {
    const angle = (i / total) * Math.PI * 2 - Math.PI / 2;
    const x = cx + rx * Math.cos(angle);
    const y = cy + ry * Math.sin(angle);
    const div = document.createElement("div");
    div.className = "player" + (p.is_turn ? " turn" : "") + (p.folded ? " folded" : "");
    div.style.left = x + "%";
    div.style.top = y + "%";
    const cardsHTML = (p.cards || []).map(c => {
      if (c === "?") return `<div class="mini back">?</div>`;
      const red = c.includes("♥") || c.includes("♦");
      return `<div class="mini ${red ? "red" : ""}">${c}</div>`;
    }).join("");
    div.innerHTML = `
      <div class="name">${escapeHtml(p.name)}</div>
      <div class="chips">💰 ${p.chips}</div>
      ${p.bet ? `<div class="bet">Ставка: ${p.bet}</div>` : ""}
      <div class="cards">${cardsHTML}</div>
    `;
    els.ring.appendChild(div);
  });

  // log
  els.logBox.textContent = (s.log || []).join("\n");

  // buttons
  const me = s.players.find(p => p.user_id === MY_ID);
  const myTurn = me && s.turn_idx >= 0 &&
    s.players[s.turn_idx] && s.players[s.turn_idx].user_id === MY_ID &&
    !me.folded && !me.all_in;
  [...els.actions.querySelectorAll("button")].forEach(b => {
    b.disabled = !myTurn;
  });

  // check/call visibility
  const toCall = me ? Math.max(0, s.current_bet - me.bet) : 0;
  const checkBtn = els.actions.querySelector('[data-act="check"]');
  const callBtn = els.actions.querySelector('[data-act="call"]');
  checkBtn.classList.toggle("hidden", toCall > 0);
  callBtn.classList.toggle("hidden", toCall === 0);
  if (toCall > 0) callBtn.textContent = `Колл ${Math.min(toCall, me.chips)}`;
  else callBtn.textContent = "Колл";

  // raise slider
  if (myTurn && me) {
    const minRaise = s.min_raise || s.big_blind;
    const maxRaise = me.chips;
    els.raiseSlider.min = minRaise;
    els.raiseSlider.max = Math.max(minRaise, maxRaise);
    els.raiseSlider.value = minRaise;
    els.raiseAmount.textContent = minRaise;
    els.raiseRow.classList.remove("hidden");
  } else {
    els.raiseRow.classList.add("hidden");
  }

  // timer
  if (s.turn_deadline && myTurn) {
    const total = s.turn_time || 20;
    const remaining = Math.max(0, s.turn_deadline - Date.now() / 1000);
    els.timerFill.style.width = Math.min(100, (remaining / total) * 100) + "%";
  } else {
    els.timerFill.style.width = "0%";
  }

  // winner / finished
  if (s.finished && s.winner_info) {
    showModal(
      "🏆 ТУРНИР ЗАВЕРШЁН!",
      `Победитель: <b>${escapeHtml(s.winner_info.name)}</b><br>Награда: ${s.winner_info.amount}`
    );
    fireConfetti();
  }
}

function makeCard(c) {
  const div = document.createElement("div");
  const red = c.includes("♥") || c.includes("♦");
  div.className = "card" + (red ? " red" : "");
  if (c === "?") div.classList.add("back");
  div.textContent = c;
  return div;
}

/* ========== WHEEL RENDER ========== */
function renderWheel(s) {
  LAST_WHEEL = s;
  els.prize.textContent = "🏆 " + (s.prize || "Приз");

  // eliminated list
  els.elimList.innerHTML = (s.eliminated || [])
    .slice()
    .sort((a, b) => b.place - a.place)
    .map(p => `<li>${escapeHtml(p.name)} — место ${p.place}</li>`)
    .join("");

  els.actList.innerHTML = (s.active || [])
    .map(p => `<li>${escapeHtml(p.name)}</li>`)
    .join("");

  const spinDisabled = s.finished || s.active.length < 2;
  els.spinBtn.disabled = spinDisabled;

  drawWheel(s.active, s.finished ? 0 : null);

  // handle last spin event
  if (s.last_spin && s.last_spin._shownFor !== s.spin_count) {
    s.last_spin._shownFor = s.spin_count;
    animateSpinToEliminated(s);
  }

  if (s.finished && s.winner) {
    setTimeout(() => {
      showModal(
        "🏆 ПОБЕДИТЕЛЬ!",
        `<b>${escapeHtml(s.winner.name)}</b><br>${escapeHtml(s.prize || "")}`
      );
      fireConfetti();
    }, 1200);
  }
}

function drawWheel(active, _) {
  const canvas = els.wheel;
  const ctx = canvas.getContext("2d");
  const W = canvas.width, H = canvas.height;
  const cx = W / 2, cy = H / 2, r = Math.min(W, H) / 2 - 20;
  ctx.clearRect(0, 0, W, H);

  const n = Math.max(active.length, 1);
  const palette = ["#ef4444","#f59e0b","#10b981","#3b82f6","#8b5cf6","#ec4899","#14b8a6","#f43f5e","#84cc16","#06b6d4"];

  for (let i = 0; i < n; i++) {
    const a0 = (i / n) * Math.PI * 2 - Math.PI / 2 + WHEEL_ANGLE;
    const a1 = ((i + 1) / n) * Math.PI * 2 - Math.PI / 2 + WHEEL_ANGLE;
    ctx.beginPath();
    ctx.moveTo(cx, cy);
    ctx.arc(cx, cy, r, a0, a1);
    ctx.closePath();
    ctx.fillStyle = palette[i % palette.length];
    ctx.fill();
    ctx.strokeStyle = "#0f172a";
    ctx.lineWidth = 2;
    ctx.stroke();

    // text
    const mid = (a0 + a1) / 2;
    ctx.save();
    ctx.translate(cx, cy);
    ctx.rotate(mid);
    ctx.textAlign = "right";
    ctx.fillStyle = "#fff";
    ctx.font = "bold 16px sans-serif";
    const label = active[i] ? active[i].name : "";
    ctx.fillText(label.length > 12 ? label.slice(0, 12) + "…" : label, r - 12, 6);
    ctx.restore();
  }

  // hub
  ctx.beginPath();
  ctx.arc(cx, cy, 42, 0, Math.PI * 2);
  ctx.fillStyle = "#0f172a";
  ctx.fill();
  ctx.strokeStyle = "#fbbf24";
  ctx.lineWidth = 4;
  ctx.stroke();
  ctx.fillStyle = "#fbbf24";
  ctx.font = "bold 22px sans-serif";
  ctx.textAlign = "center";
  ctx.textBaseline = "middle";
  ctx.fillText("🎡", cx, cy);
}

function animateSpinToEliminated(s) {
  if (WHEEL_SPINNING) return;
  WHEEL_SPINNING = true;
  const activeBefore = s.active.concat([s.last_spin.eliminated]);
  const n = activeBefore.length;
  const idx = s.last_spin.sector_index;
  // target: pointer is at top (angle -PI/2). We need sector idx to land under pointer.
  // sector i center before spin: (i + 0.5)/n * 2PI - PI/2 + WHEEL_ANGLE
  // We want after spin: (idx+0.5)/n*2PI - PI/2 + newAngle ≡ -PI/2 (mod 2PI)
  // => newAngle = -(idx+0.5)/n*2PI  + 2PI*turns
  const turns = 6 + Math.random() * 2;
  const baseAngle = WHEEL_ANGLE;
  const target = baseAngle + turns * Math.PI * 2 +
                 (((- (idx + 0.5) / n * Math.PI * 2) - baseAngle) % (Math.PI * 2));
  const duration = 4200;
  const start = performance.now();
  const startA = WHEEL_ANGLE;

  const oldActive = s.active.slice(); // already after elimination
  // For drawing during spin, we show the "before" wheel (with all n sectors)
  function frame(t) {
    const k = Math.min(1, (t - start) / duration);
    const eased = 1 - Math.pow(1 - k, 3);
    WHEEL_ANGLE = startA + (target - startA) * eased;
    drawWheel(activeBefore, null);
    if (k < 1) {
      requestAnimationFrame(frame);
    } else {
      WHEEL_ANGLE = target;
      drawWheel(oldActive, null);
      WHEEL_SPINNING = false;
      // show modal
      showModal("❌ Выбывает", `<b>${escapeHtml(s.last_spin.eliminated.name)}</b><br>покидает турнир!`);
    }
  }
  requestAnimationFrame(frame);
}

/* ========== CONTROLS ========== */
els.actions.addEventListener("click", (e) => {
  const btn = e.target.closest("button");
  if (!btn || btn.disabled) return;
  const act = btn.dataset.act;
  let amount = 0;
  if (act === "raise") {
    amount = parseInt(els.raiseSlider.value, 10) || 0;
  }
  wsSend({ type: "poker_action", action: act, amount });
});
els.raiseSlider?.addEventListener("input", () => {
  els.raiseAmount.textContent = els.raiseSlider.value;
});

els.spinBtn.addEventListener("click", () => {
  if (WHEEL_SPINNING) return;
  wsSend({ type: "spin" });
});

els.modalClose.addEventListener("click", () => {
  els.modal.classList.add("hidden");
  els.confetti.classList.add("hidden");
});

/* ========== HELPERS ========== */
function showModal(title, body) {
  els.modalTitle.textContent = title;
  els.modalBody.innerHTML = body;
  els.modal.classList.remove("hidden");
}
function escapeHtml(s) {
  return String(s || "").replace(/[&<>"']/g, c => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
  }[c]));
}

/* ========== CONFETTI ========== */
function fireConfetti() {
  const canvas = els.confetti;
  canvas.classList.remove("hidden");
  canvas.width = window.innerWidth;
  canvas.height = window.innerHeight;
  const ctx = canvas.getContext("2d");
  const pieces = Array.from({ length: 160 }, () => ({
    x: Math.random() * canvas.width,
    y: -20 - Math.random() * 200,
    vy: 2 + Math.random() * 3,
    vx: -1 + Math.random() * 2,
    r: 4 + Math.random() * 5,
    color: `hsl(${Math.random()*360}, 90%, 60%)`,
    rot: Math.random() * Math.PI,
    vr: -0.1 + Math.random() * 0.2,
  }));
  let frames = 0;
  function loop() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    pieces.forEach(p => {
      p.x += p.vx; p.y += p.vy; p.rot += p.vr;
      ctx.save();
      ctx.translate(p.x, p.y);
      ctx.rotate(p.rot);
      ctx.fillStyle = p.color;
      ctx.fillRect(-p.r, -p.r, p.r * 2, p.r * 0.6);
      ctx.restore();
    });
    frames++;
    if (frames < 400) requestAnimationFrame(loop);
    else canvas.classList.add("hidden");
  }
  loop();
}