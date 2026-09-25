import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import uvicorn
from datetime import datetime, timezone

from config import PORT, FETCH_INTERVAL, WARMUP_ROUNDS, MAX_HISTORY
from core.fetch import fetch_data
from core.state import load_state, save_state
from core.ensemble import ensemble_predict

state = load_state()
history = state.get("history", [])
stats = state.get("stats", {"total": 0, "correct": 0, "wrong": 0})
last_session = state.get("last_session")
websocket_clients: set[WebSocket] = set()


async def broadcast_update():
    if not websocket_clients:
        return

    payload = {
        "status": "running",
        "lastSession": last_session,
        "historyCount": len(history),
        "stats": stats,
        "prediction": ensemble_predict(history),
        "canPredict": len(history) >= WARMUP_ROUNDS,
    }
    disconnected = set()
    for client in websocket_clients:
        try:
            await client.send_json(payload)
        except Exception:
            disconnected.add(client)
    websocket_clients.difference_update(disconnected)


async def background_loop():
    global history, stats, last_session
    while True:
        try:
            data = await fetch_data()
            if not data:
                await asyncio.sleep(FETCH_INTERVAL)
                continue

            data.sort(key=lambda x: x.get("GameSessionID", 0))
            new_items = [x for x in data if x.get("GameSessionID", 0) > (last_session or 0)]

            for item in new_items:
                sid = item["GameSessionID"]
                d1, d2, d3 = int(item["Dice1"]), int(item["Dice2"]), int(item["Dice3"])
                total = d1 + d2 + d3
                outcome = "TAI" if total > 10 else "XIU"

                pred_result = ensemble_predict(history)

                if history and history[-1].get("pred"):
                    stats["total"] += 1
                    if history[-1]["pred"] == outcome:
                        stats["correct"] += 1
                    else:
                        stats["wrong"] += 1

                history.append({
                    "sessionId": sid,
                    "dice": [d1, d2, d3],
                    "sum": total,
                    "outcome": outcome,
                    "pred": pred_result.get("pred"),
                    "confidence": pred_result.get("confidence", 0),
                    "reason": pred_result.get("reason", ""),
                    "receivedAt": datetime.now(timezone.utc).isoformat(),
                })

                if len(history) > MAX_HISTORY:
                    history = history[-1800:]

                last_session = sid
                print(f"Van {sid}: {d1}-{d2}-{d3} = {total} ({outcome})")
                if pred_result.get("pred"):
                    print(f"Du doan: {pred_result['pred']} ({pred_result.get('confidence')}%) | {pred_result.get('reason')}")

            if new_items:
                save_state({"history": history, "stats": stats, "last_session": last_session})
                await broadcast_update()

        except Exception as e:
            print("Loop error:", e)
        await asyncio.sleep(FETCH_INTERVAL)


@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(background_loop())
    try:
        yield
    finally:
        task.cancel()
        await asyncio.gather(task, return_exceptions=True)
        websocket_clients.clear()


app = FastAPI(title="Bot MD5 Python", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


@app.get("/", response_class=HTMLResponse)
def root():
    return """
<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<title>MD5 SERVER</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@500;700;800&family=Inter:wght@400;500;600;700;800&display=swap');
*{margin:0;padding:0;box-sizing:border-box}
body{
  background:#05080f;color:#e2e8f0;min-height:100vh;font-family:'Inter',system-ui,sans-serif;padding:12px;
  background-image:linear-gradient(rgba(14,165,233,.03) 1px,transparent 1px),linear-gradient(90deg,rgba(14,165,233,.03) 1px,transparent 1px);
  background-size:28px 28px;
}
.wrap{max-width:420px;margin:0 auto}
.top-stats{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:12px}
.top-card{
  background:linear-gradient(165deg,#0f172a,#0b1220);border:1px solid rgba(34,211,238,.18);
  border-radius:14px;padding:12px 14px;text-align:center;
}
.top-card .lab{font-size:10px;letter-spacing:1.5px;color:#64748b;font-weight:600}
.top-card .val{font-size:22px;font-weight:800;color:#22d3ee;font-family:Orbitron,sans-serif;margin-top:4px}
.server-card{
  background:linear-gradient(165deg,rgba(15,23,42,.98),rgba(8,12,22,.98));
  border:1px solid rgba(34,211,238,.22);border-radius:18px;padding:16px;margin-bottom:12px;
  box-shadow:0 12px 40px rgba(0,0,0,.45),inset 0 1px 0 rgba(255,255,255,.04);position:relative;overflow:hidden;
}
.server-card::before{
  content:'';position:absolute;inset:0;border-radius:18px;padding:1px;
  background:linear-gradient(135deg,rgba(34,211,238,.45),transparent 40%,transparent 60%,rgba(34,211,238,.2));
  -webkit-mask:linear-gradient(#000 0 0) content-box,linear-gradient(#000 0 0);
  -webkit-mask-composite:xor;mask-composite:exclude;pointer-events:none;
}
.server-head{display:flex;align-items:center;gap:8px;margin-bottom:10px}
.dot{width:9px;height:9px;border-radius:50%;background:#22d3ee;box-shadow:0 0 10px #22d3ee;animation:pulse 2s infinite}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.45}}
.server-name{font-size:13px;font-weight:800;color:#22d3ee;letter-spacing:1.2px;font-family:Orbitron,sans-serif}
.session{font-size:12px;color:#94a3b8;margin-bottom:8px}
.pred{font-size:42px;font-weight:800;letter-spacing:2px;font-family:Orbitron,sans-serif;line-height:1.1;margin:6px 0 10px;text-shadow:0 0 24px currentColor}
.pred.tai{color:#4ade80}.pred.xiu{color:#f87171}.pred.wait{color:#fbbf24;font-size:26px}
.meta{font-size:12px;color:#94a3b8;margin-bottom:8px}.meta b{color:#e2e8f0;font-weight:600}
.verdict{font-size:13px;font-weight:700;margin-top:4px}
.verdict.ok{color:#4ade80}.verdict.bad{color:#f87171}.verdict.idle{color:#64748b}
.dice-row{display:flex;gap:10px;justify-content:center;margin:10px 0}
.dice{width:52px;height:52px;border-radius:12px;display:flex;align-items:center;justify-content:center;font-size:22px;font-weight:800;background:#0f172a;border:1px solid #1e293b;color:#e2e8f0}
.dice.tai{border-color:#16a34a;color:#4ade80;background:#052e1a}
.dice.xiu{border-color:#dc2626;color:#f87171;background:#3a0a0a}
.dice.dim{opacity:.35}
.stats-card{background:linear-gradient(165deg,#0f172a,#0b1220);border:1px solid rgba(34,211,238,.15);border-radius:18px;padding:14px 16px;margin-bottom:12px}
.stats-card .title{font-size:12px;font-weight:800;color:#22d3ee;letter-spacing:1.5px;font-family:Orbitron,sans-serif;margin-bottom:10px}
.stat-line{display:flex;justify-content:space-between;align-items:center;padding:7px 0;border-bottom:1px solid rgba(30,41,59,.8);font-size:13px;color:#94a3b8}
.stat-line:last-child{border-bottom:none}
.stat-line b{font-weight:800;font-size:15px}
.stat-line b.g{color:#4ade80}.stat-line b.r{color:#f87171}.stat-line b.c{color:#22d3ee}.stat-line b.w{color:#e2e8f0}
.cau-box{background:#0b1220;border:1px solid #1e293b;border-radius:14px;padding:12px;margin-bottom:12px}
.cau-box .lab{font-size:11px;color:#64748b;margin-bottom:6px;letter-spacing:.5px}
.cau-str{display:flex;flex-wrap:wrap;gap:4px;font-family:monospace;font-weight:700;font-size:15px}
.cau-str .t{color:#4ade80}.cau-str .x{color:#f87171}
.actions{display:flex;gap:8px;margin-bottom:10px;flex-wrap:wrap}
.btn{flex:1;min-width:30%;border:none;border-radius:12px;padding:11px;font-weight:700;font-size:12px;cursor:pointer;background:#1e293b;color:#e2e8f0}
.btn.primary{background:linear-gradient(135deg,#0e7490,#155e75);color:#ecfeff}
.btn.danger{background:#3f1d1d;color:#fca5a5}
.btn.soft{background:#132033;color:#7dd3fc}
.log{background:#070b14;border:1px solid #1e293b;border-radius:12px;padding:10px;max-height:120px;overflow-y:auto;font-family:ui-monospace,monospace;font-size:11px;color:#94a3b8}
.log div{padding:2px 0}
.status{text-align:center;font-size:12px;color:#fbbf24;margin:8px 0}
#exportBox{display:none;position:fixed;inset:8% 4%;z-index:99;background:#0b1220;border:1px solid #0e7490;border-radius:14px;padding:12px;flex-direction:column;gap:8px}
#exportBox textarea{flex:1;min-height:160px;width:100%;background:#020617;color:#e2e8f0;border:1px solid #1e293b;border-radius:8px;padding:8px;font-size:11px}
</style>
</head>
<body>
<div class="wrap">
  <div class="top-stats">
    <div class="top-card"><div class="lab">TOTAL PREDICTIONS</div><div class="val" id="totalPred">0</div></div>
    <div class="top-card"><div class="lab">TOTAL WINS</div><div class="val" id="totalWins">0</div></div>
  </div>

  <div class="server-card">
    <div class="server-head"><span class="dot"></span><span class="server-name">MD5 SERVER</span></div>
    <div class="session" id="sessionLine">Phiên dự đoán: #---</div>
    <div class="pred wait" id="predMain">---</div>
    <div class="meta">Độ tin cậy: <b id="confTxt">—</b> | Phương pháp: <b id="methodTxt">ASYM</b></div>
    <div class="verdict idle" id="verdict">Chờ kết quả phiên...</div>
    <div class="dice-row">
      <div class="dice dim" id="d1">-</div>
      <div class="dice dim" id="d2">-</div>
      <div class="dice dim" id="d3">-</div>
    </div>
    <div class="meta" style="text-align:center;margin-top:4px">Tổng: <b id="sumTxt">—</b> · Kết quả: <b id="lastResult">—</b></div>
  </div>

  <div class="stats-card">
    <div class="title">MD5 SERVER</div>
    <div class="stat-line"><span>Tổng phiên</span><b class="w" id="stTotal">0</b></div>
    <div class="stat-line"><span>Thắng</span><b class="g" id="stWin">0</b></div>
    <div class="stat-line"><span>Thua</span><b class="r" id="stLose">0</b></div>
    <div class="stat-line"><span>Tỉ lệ thắng</span><b class="c" id="stRate">0%</b></div>
    <div class="stat-line"><span>Streak</span><b class="w" id="stStreak">0</b></div>
    <div class="stat-line"><span>Kho lịch sử</span><b class="c" id="stKho">0</b></div>
  </div>

  <div class="cau-box">
    <div class="lab">CHUỖI CẦU (25 gần nhất)</div>
    <div class="cau-str" id="cauStr">⏳</div>
  </div>

  <div class="status" id="statusText">⏳ Đang khởi tạo...</div>
  <div class="actions">
    <button class="btn primary" type="button" id="btnRefresh">🔄 Cập nhật</button>
    <button class="btn soft" type="button" id="btnExport">📄 Xuất</button>
    <button class="btn danger" type="button" id="btnReset">🗑 Xóa</button>
  </div>
  <div class="log" id="logArea"></div>
</div>

<div id="exportBox">
  <div style="font-weight:800;color:#22d3ee" id="exportTitle">Lịch sử</div>
  <textarea id="exportTA" readonly></textarea>
  <div style="display:flex;gap:8px">
    <button class="btn primary" type="button" id="btnCopy">📋 Sao chép</button>
    <button class="btn" type="button" id="btnCloseExport">Đóng</button>
  </div>
</div>

<script>
const TOKEN = 'chLmUUptYvufnvOrhlAZ4wK0sk9/ugVPdm3g06QugeLZ50dsPLBpQlEj4B+PoU7ghDbdWO9iczXNufe2vZbA7s8UxdFtG5rG9n3sF4C4BEfT0qYp/26beKLdBOwfD2e/IgjZLVzIlnA0KIM4b5E6UMhWljGsSPQh';
const API_URL = 'https://md5.changdelamgica.xyz/api/GetListSoiCau';
const STORAGE_KEY = 'md5_server_complete_v3';
const INTERVAL_MS = 1000;
const GATE = { XIU: 1, TAI: 2 };

const $ = id => document.getElementById(id);

let history = [];
let lastSession = null;
let pendingPred = null;
let perf = { total: 0, win: 0, lose: 0, streak: 0, maxStreak: 0 };
const brain = { cell: {}, recent: [], chuoiSai: 0, adaptBias: 0 };

function addLog(msg){
  const el = document.createElement('div');
  el.textContent = msg;
  $('logArea').prepend(el);
  while($('logArea').children.length > 60) $('logArea').removeChild($('logArea').lastChild);
}

function save(){
  try{
    localStorage.setItem(STORAGE_KEY, JSON.stringify({ history, lastSession, pendingPred, perf, brain }));
  }catch(e){}
}
function load(){
  try{
    const d = JSON.parse(localStorage.getItem(STORAGE_KEY) || 'null');
    if(!d) return;
    history = d.history || [];
    lastSession = d.lastSession || null;
    pendingPred = d.pendingPred || null;
    perf = d.perf || perf;
    if(d.brain) Object.assign(brain, d.brain);
  }catch(e){}
}

function resultFromSum(sum){
  sum = Number(sum);
  if(isNaN(sum) || sum < 3 || sum > 18) return null;
  return sum >= 11 ? 'TAI' : 'XIU';
}

function toTX(item){
  if(!item) return null;
  if(item.result === 'TAI' || item.result === 'XIU') return item.result;
  if(item.LocationIDWin === 'TAI' || item.LocationIDWin === 'XIU') return item.LocationIDWin;
  return resultFromSum(item.DiceSum != null ? item.DiceSum : (Number(item.Dice1)||0)+(Number(item.Dice2)||0)+(Number(item.Dice3)||0));
}

function getStreak(arr){
  if(!arr.length) return [null, 0];
  const last = arr[arr.length - 1];
  let n = 1;
  for(let i = arr.length - 2; i >= 0; i--){
    if(arr[i] === last) n++; else break;
  }
  return [last, n];
}

function cellKey(side, leng){ return side + 'x' + Math.min(leng, 8); }
function learnCell(side, leng, ok){
  const k = cellKey(side, leng);
  if(!brain.cell[k]) brain.cell[k] = { t: 0, h: 0 };
  brain.cell[k].t++;
  if(ok) brain.cell[k].h++;
  brain.recent.push(ok ? 1 : 0);
  if(brain.recent.length > 40) brain.recent.shift();
  if(ok){ brain.chuoiSai = 0; brain.adaptBias *= 0.85; }
  else { brain.chuoiSai++; brain.adaptBias = Math.max(-0.08, (brain.adaptBias || 0) - 0.015); }
}
function cellAcc(side, leng){
  const c = brain.cell[cellKey(side, leng)];
  if(!c || c.t < 6) return 0.5;
  return c.h / c.t;
}

function smartPredict(results){
  const WARMUP = 6;
  if(!results || results.length < WARMUP){
    return {
      huong: null,
      conf: 0,
      method: 'WARMUP_' + (results ? results.length : 0) + '/' + WARMUP,
      scoreT: 0.5,
      signals: 0,
      strong: false,
      detail: 'Đang theo nhịp · chưa chốt'
    };
  }

  const n = results.length;
  const clamp=(x,a,b)=>Math.max(a,Math.min(b,x));
  const probT = arr => arr.length ? arr.filter(x=>x==='T').length/arr.length : 0.5;

  function patternStats(pattern){
    const L=pattern.length, hits=[];
    for(let i=L;i<n;i++){
      let ok=true;
      for(let j=0;j<L;j++) if(results[i-L+j]!==pattern[j]) {ok=false;break;}
      if(ok && i<n) hits.push({i,next:results[i]});
    }
    if(!hits.length) return null;
    const ys=hits.map(h=>h.next==='T'?1:0);
    const k=ys.reduce((a,b)=>a+b,0), m=ys.length;
    const mean=(k+1)/(m+2);
    const z=1.645, den=1+z*z/m;
    const center=(mean+z*z/(2*m))/den;
    const margin=z*Math.sqrt((mean*(1-mean)/m)+(z*z/(4*m*m)))/den;
    const low=clamp(center-margin,0,1);
    const high=clamp(center+margin,0,1);
    const reliability=Math.max(0,(low-0.5)*2,(0.5-high)*2);

    const chunks=[];
    const third=Math.max(1,Math.floor(m/3));
    for(let c=0;c<3;c++){
      const a=c*third, b=c===2?m:(c+1)*third;
      if(b>a) chunks.push(ys.slice(a,b).reduce((x,y)=>x+y,0)/(b-a));
    }
    const stab=chunks.length>1 ? clamp(1-((Math.max(...chunks)-Math.min(...chunks))/0.5),0,1) : 0.5;
    const recent=ys.slice(-Math.min(5,m));
    const recentP=recent.length?recent.reduce((a,b)=>a+b,0)/recent.length:mean;
    const recency=clamp(0.5+Math.abs(recentP-0.5)*1.4,0,1);
    const sample=clamp(m/12,0,1);
    const specificity=clamp((L-1)/5,0,1);
    const strength=100*clamp(
      0.34*reliability + 0.26*stab + 0.18*sample + 0.12*recency + 0.10*specificity,
      0,1
    );
    return {pattern,L,hits:m,p:mean,low,high,stability:stab,reliability,sample,recency,strength,recentP};
  }

  const candidates=[];
  for(let L=1;L<=Math.min(6,n-1);L++){
    const pattern=results.slice(n-L).join('');
    const st=patternStats(pattern);
    if(st && st.hits>=4) candidates.push(st);
  }

  candidates.sort((a,b)=>b.strength-a.strength);
  let best=candidates[0]||null;
  if(best){
    for(const c of candidates.slice(1)){
      const materiallyBetter = c.strength >= best.strength+7 && c.hits>=best.hits;
      if(materiallyBetter) best=c;
    }
  }

  const baseVotes=[];
  for(const w of [8,16,32,64]){
    if(n<w) continue;
    const p=probT(results.slice(-w));
    baseVotes.push({p,w});
  }
  const baseP=baseVotes.length ? baseVotes.reduce((a,v)=>a+v.p,0)/baseVotes.length : 0.5;

  function markov(order){
    if(n<=order) return null;
    const key=results.slice(n-order).join('');
    let m=0,k=0;
    for(let i=order;i<n;i++){
      if(results.slice(i-order,i).join('')===key){m++; if(results[i]==='T')k++;}
    }
    return m>=4 ? {p:(k+1)/(m+2),m}:null;
  }
  const m1=markov(1), m2=markov(2);

  const strong = best && best.hits>=6 && best.stability>=0.70 && best.reliability>=0.20 && best.strength>=70;

  let scoreT=0.5;
  let detail='Không có cầu mạnh · theo nền';
  let method='NO_STRONG_CAU';

  if(strong){
    const p=best.p;
    scoreT = 0.62*p + 0.20*baseP + 0.10*(m1?m1.p:0.5) + 0.08*(m2?m2.p:0.5);
    method='CAU_' + Math.round(best.strength) + '/100';
    detail='Cầu ' + best.pattern + ' · mẫu ' + best.hits + ' · ổn định ' + Math.round(best.stability*100) + '%';
  }else{
    scoreT = 0.58*baseP + 0.22*(m1?m1.p:0.5) + 0.20*(m2?m2.p:0.5);
    if(Math.abs(scoreT-0.5)<0.055){
      return {huong:null,conf:0,method:'NO_STRONG_CAU',scoreT,signals:candidates.length,strong:false,detail};
    }
  }

  const disagreement = strong ? Math.abs(best.p-baseP) : 0;
  if(strong && disagreement>0.28){
    return {huong:null,conf:0,method:'CAU_XUNG_DOT',scoreT,signals:candidates.length,strong:false,
      detail:'Có cầu nhưng xung đột nền · chưa chốt'};
  }

  const edge=Math.abs(scoreT-0.5);
  let conf=clamp(0.50+edge*1.55,0.50,0.78);
  if(strong) conf=clamp(Math.max(conf,0.62 + (best.strength-70)/500),0.62,0.78);
  else conf=Math.min(conf,0.60);

  return {
    huong:scoreT>=0.5?'TAI':'XIU',
    conf,
    method,
    scoreT,
    signals:candidates.length,
    strong:!!strong,
    strengthScore:best?Math.round(best.strength):0,
    bestPattern:best?best.pattern:null,
    detail
  };
}

function normalizeItem(raw){
  if(!raw || typeof raw !== 'object') return null;
  const id = raw.GameSessionID ?? raw.gameSessionID ?? raw.SessionID ?? raw.id;
  if(id == null) return null;
  const d1 = Number(raw.Dice1 ?? raw.dice1 ?? (raw.dices && raw.dices[0]));
  const d2 = Number(raw.Dice2 ?? raw.dice2 ?? (raw.dices && raw.dices[1]));
  const d3 = Number(raw.Dice3 ?? raw.dice3 ?? (raw.dices && raw.dices[2]));
  let sum = raw.DiceSum ?? raw.diceSum ?? raw.point;
  if(sum == null && [d1, d2, d3].every(x => !isNaN(x))) sum = d1 + d2 + d3;
  sum = Number(sum);

  let result = null;
  const loc = raw.LocationIDWin ?? raw.locationIDWin;
  if(loc === GATE.TAI || loc === '2' || loc === 2 || loc === 'TAI' || loc === 'Tai') result = 'TAI';
  else if(loc === GATE.XIU || loc === '1' || loc === 1 || loc === 'XIU' || loc === 'Xiu') result = 'XIU';

  const bySum = resultFromSum(sum);
  if(bySum){
    if(result && result !== bySum) result = bySum;
    else if(!result) result = bySum;
  }
  if(!result && raw.resultTruyenThong)
    result = String(raw.resultTruyenThong).toUpperCase().includes('TAI') ? 'TAI' : 'XIU';
  if(!result) return null;

  return {
    GameSessionID: Number(id),
    Dice1: isNaN(d1) ? null : d1,
    Dice2: isNaN(d2) ? null : d2,
    Dice3: isNaN(d3) ? null : d3,
    DiceSum: isNaN(sum) ? null : sum,
    LocationIDWin: result,
    Md5Result: raw.Md5Result ?? raw.md5Result ?? raw.md5 ?? null,
    result
  };
}

function extractList(payload){
  if(Array.isArray(payload)) return payload;
  if(!payload || typeof payload !== 'object') return null;
  if(payload.Code != null && payload.Code !== 0 && payload.Code !== 200){
    const msg = typeof payload.Data === 'string' ? payload.Data : (payload.Message || 'API từ chối');
    throw new Error(msg);
  }
  if(Array.isArray(payload.Data)) return payload.Data;
  if(Array.isArray(payload.data)) return payload.data;
  if(Array.isArray(payload.list)) return payload.list;
  if(Array.isArray(payload.Result)) return payload.Result;
  return null;
}

async function fetchHistory(){
  const res = await fetch(API_URL, {
    headers: { 'Authorization': 'Bearer ' + TOKEN, 'Accept': 'application/json' },
    cache: 'no-store'
  });
  if(!res.ok) throw new Error('HTTP ' + res.status);
  const data = await res.json();
  const list = extractList(data);
  if(!list) throw new Error('Data không hợp lệ');
  const norm = list.map(normalizeItem).filter(Boolean);
  norm.sort((a, b) => a.GameSessionID - b.GameSessionID);
  return norm;
}

function renderPerf(){
  $('totalPred').textContent = perf.total;
  $('totalWins').textContent = perf.win;
  $('stTotal').textContent = perf.total;
  $('stWin').textContent = perf.win;
  $('stLose').textContent = perf.lose;
  $('stRate').textContent = perf.total ? (perf.win / perf.total * 100).toFixed(1) + '%' : '0%';
  $('stStreak').textContent = perf.streak;
  $('stKho').textContent = history.length;
}

function renderCau(){
  const slice = history.slice(-25);
  if(!slice.length){ $('cauStr').textContent = '⏳'; return; }
  $('cauStr').innerHTML = slice.map(h => {
    const r = h.result;
    return '<span class="' + (r === 'TAI' ? 't' : 'x') + '">' + (r === 'TAI' ? 'T' : 'X') + '</span>';
  }).join('');
}

function renderDice(item){
  if(!item){
    ['d1','d2','d3'].forEach(id => { $(id).textContent = '-'; $(id).className = 'dice dim'; });
    $('sumTxt').textContent = '—';
    $('lastResult').textContent = '—';
    return;
  }
  const res = toTX(item);
  const cls = res === 'TAI' ? 'tai' : 'xiu';
  [['d1', item.Dice1], ['d2', item.Dice2], ['d3', item.Dice3]].forEach(([id, v]) => {
    $(id).textContent = v == null ? '-' : v;
    $(id).className = 'dice ' + cls;
  });
  const sum = item.DiceSum != null ? item.DiceSum : (Number(item.Dice1)||0)+(Number(item.Dice2)||0)+(Number(item.Dice3)||0);
  $('sumTxt').textContent = sum || '—';
  $('lastResult').textContent = res === 'TAI' ? 'TÀI' : 'XỈU';
  $('lastResult').style.color = res === 'TAI' ? '#4ade80' : '#f87171';
}

function renderPending(){
  if(!pendingPred){
    $('sessionLine').textContent = 'Phiên dự đoán: #---';
    $('predMain').textContent = '---';
    $('predMain').className = 'pred wait';
    $('confTxt').textContent = '—';
    $('methodTxt').textContent = 'ASYM';
    $('verdict').textContent = 'Chờ dữ liệu...';
    $('verdict').className = 'verdict idle';
    return;
  }
  $('sessionLine').textContent = 'Phiên dự đoán: #' + pendingPred.sessionPredictFor;
  if(!pendingPred.huong){
    $('predMain').textContent = 'CHỜ NHỊP';
    $('predMain').className = 'pred wait';
    $('confTxt').textContent = '—';
    $('methodTxt').textContent = pendingPred.method;
    $('verdict').textContent = 'Đang thu thập nhịp...';
    $('verdict').className = 'verdict idle';
    return;
  }
  const isTai = pendingPred.huong === 'TAI';
  $('predMain').textContent = isTai ? 'Tài' : 'Xỉu';
  $('predMain').className = 'pred ' + (isTai ? 'tai' : 'xiu');
  $('confTxt').textContent = Math.round(pendingPred.conf * 100) + '%';
  $('methodTxt').textContent = pendingPred.method;
  $('verdict').textContent = 'Đang chờ kết quả...';
  $('verdict').className = 'verdict idle';
}

async function processData(manual){
  try{
    const raw = await fetchHistory();
    if(!raw.length) return;
    const latest = raw[raw.length - 1];
    const sid = latest.GameSessionID;
    const result = toTX(latest);

    if(pendingPred && pendingPred.sessionPredictFor === sid){
      const ok = pendingPred.huong ? pendingPred.huong === result : null;
      if(ok !== null) {
        perf.total++;
        if(ok){ perf.win++; perf.streak++; }
        else { perf.lose++; perf.streak = 0; }
        $('verdict').textContent = ok ? ('✓ ĐÚNG (Kết quả: ' + (result === 'TAI' ? 'Tài' : 'Xỉu') + ')') : ('✗ SAI (Kết quả: ' + (result === 'TAI' ? 'Tài' : 'Xỉu') + ')');
        $('verdict').className = 'verdict ' + (ok ? 'ok' : 'bad');
        addLog((ok ? '✅' : '❌') + ' #' + sid + ' pred ' + (pendingPred.huong || 'CHƯA CHỐT') + ' → ' + result + ' | ' + pendingPred.method);
        pendingPred = null;
        renderPerf();
        save();
      }
    }

    if(sid === lastSession){
      $('statusText').textContent = (manual ? '⏳ Chưa có ván mới · ' : '⏳ Chờ ván mới · ') + new Date().toLocaleTimeString();
      renderDice(latest);
      return;
    }

    history.push({
      session: sid,
      dice: [latest.Dice1, latest.Dice2, latest.Dice3],
      sum: latest.DiceSum,
      md5: latest.Md5Result,
      result
    });
    if(history.length > 2000) history = history.slice(-2000);
    lastSession = sid;

    const series = history.map(h => h.result === 'TAI' ? 'T' : 'X');
    const pred = smartPredict(series);
    const [pside, pleng] = getStreak(series);
    pendingPred = {
      sessionPredictFor: sid + 1,
      huong: pred.huong,
      conf: pred.conf,
      method: pred.method,
      side: pside,
      leng: pleng,
      signals: pred.signals || 1
    };

    renderDice(latest);
    renderPending();
    renderCau();
    renderPerf();
    save();

    $('statusText').textContent = '✅ Cập nhật ' + new Date().toLocaleTimeString();
    addLog('🎯 #' + sid + ' ' + [latest.Dice1, latest.Dice2, latest.Dice3].join('-') + ' = ' + (latest.DiceSum != null ? latest.DiceSum : '?') + ' ' + result);
    addLog('🔮 Next #' + (sid + 1) + ' → ' + (pred.huong || 'CHỜ NHỊP') + ' (' + (pred.huong ? Math.round(pred.conf * 100) + '%' : '—') + ' · ' + pred.method + ' · sig ' + (pred.signals || 0) + ')');
  }catch(e){
    $('statusText').textContent = '❌ ' + e.message;
    addLog('❌ ' + e.message);
  }
}

function resetData(){
  if(!confirm('Xóa toàn bộ lịch sử & thống kê?')) return;
  history = []; lastSession = null; pendingPred = null;
  perf = { total: 0, win: 0, lose: 0, streak: 0, maxStreak: 0 };
  brain.cell = {}; brain.recent = []; brain.chuoiSai = 0; brain.adaptBias = 0;
  localStorage.removeItem(STORAGE_KEY);
  renderPerf(); renderPending(); renderDice(null);
  $('cauStr').textContent = '⏳';
  $('logArea').innerHTML = '';
  addLog('🗑️ Đã reset');
  $('statusText').textContent = 'Đã xóa dữ liệu';
}

function exportHistory(){
  save();
  if(!history.length){ alert('Chưa có lịch sử.'); return; }
  const tai = history.filter(h => h.result === 'TAI').length;
  const payload = {
    list: history.map(h => ({
      id: h.session,
      resultTruyenThong: h.result,
      dices: h.dice,
      point: h.sum,
      md5: h.md5 || null
    })),
    exportedAt: new Date().toISOString(),
    count: history.length,
    typeStat: { TAI: tai, XIU: history.length - tai },
    perf: perf,
    source: 'md5_server_complete_v3'
  };
  const raw = JSON.stringify(payload, null, 2);
  try{
    const blob = new Blob([raw], { type: 'application/json' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = 'lich_su_md5_' + history.length + '.json';
    a.click();
  }catch(e){}
  $('exportTitle').textContent = 'Lịch sử · ' + history.length + ' phiên';
  $('exportTA').value = raw;
  $('exportBox').style.display = 'flex';
}

$('btnRefresh').onclick = () => processData(true);
$('btnReset').onclick = resetData;
$('btnExport').onclick = exportHistory;
$('btnCloseExport').onclick = () => { $('exportBox').style.display = 'none'; };
$('btnCopy').onclick = async () => {
  const ta = $('exportTA');
  ta.focus(); ta.select();
  try{ await navigator.clipboard.writeText(ta.value); alert('Đã sao chép'); }
  catch(e){ try{ document.execCommand('copy'); alert('Đã sao chép'); }catch(e2){ alert('Copy thủ công trong ô'); } }
};

load();
renderPerf();
renderPending();
renderCau();
if(history.length){
  const last = history[history.length - 1];
  renderDice({ Dice1: last.dice[0], Dice2: last.dice[1], Dice3: last.dice[2], DiceSum: last.sum, result: last.result });
}
addLog('MD5 SERVER · V7 · Warmup 6 · Strong-cau filter · No forced TAI/XIU');
processData(true);
setInterval(() => processData(false), INTERVAL_MS);
</script>
</body>
</html>
    """


@app.get("/api/bot/status")
def status():
    pred = ensemble_predict(history)
    return {
        "status": "running",
        "lastSession": last_session,
        "historyCount": len(history),
        "stats": stats,
        "prediction": pred,
        "canPredict": len(history) >= WARMUP_ROUNDS,
    }


@app.get("/api/bot/predict")
def predict():
    pred = ensemble_predict(history)
    return {
        "status": "running",
        "lastSession": last_session,
        "historyCount": len(history),
        "canPredict": len(history) >= WARMUP_ROUNDS,
        "prediction": pred,
    }


@app.get("/api/bot/history")
def history_api():
    return {
        "status": "running",
        "historyCount": len(history),
        "lastSession": last_session,
        "history": history[-50:],
    }


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    websocket_clients.add(websocket)
    try:
        await websocket.send_json(status())
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        websocket_clients.discard(websocket)


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=PORT)
