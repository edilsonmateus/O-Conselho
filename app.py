"""
77Gira — Conselho Digital de Negócios
Deploy: Render.com
A chave da API Anthropic fica como variável de ambiente no Render (ANTHROPIC_API_KEY).
Histórico salvo em disco persistente em /data/historico.json
"""

import os, json, io
from datetime import datetime
from flask import Flask, request, jsonify, render_template_string, send_file
import anthropic

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.units import mm
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable, Table, TableStyle
    HAS_PDF = True
except ImportError:
    HAS_PDF = False

app = Flask(__name__)

DATA_DIR = os.environ.get("DATA_DIR", "./data")
HISTORY_FILE = os.path.join(DATA_DIR, "historico_77gira.json")
os.makedirs(DATA_DIR, exist_ok=True)

def get_client():
    key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not key:
        raise ValueError("ANTHROPIC_API_KEY não configurada no ambiente.")
    return anthropic.Anthropic(api_key=key)

ADVISORS = [
    {"id":"gates","name":"Bill Gates","initials":"BG","role":"Microsoft · Tecnologia","group":"global","color":"#E6F1FB","tc":"#0C447C",
     "philosophy":"Você é uma persona de IA inspirada na filosofia pública de Bill Gates. Baseie-se em seus escritos, entrevistas e declarações sobre tecnologia, negócios e filantropia. Pense em longo prazo, analise com dados, valorize inovação com impacto. Seja direto e pragmático. Responda em português do Brasil. Inicie direto com o conselho, sem saudações. Mencione ao final que é uma persona de IA."},
    {"id":"buffett","name":"Warren Buffett","initials":"WB","role":"Berkshire · Value Investing","group":"global","color":"#EAF3DE","tc":"#27500A",
     "philosophy":"Você é uma persona de IA inspirada na filosofia pública de Warren Buffett. Baseie-se em suas cartas aos acionistas e princípios de value investing. Use analogias simples e senso comum. Responda em português do Brasil. Inicie direto com o conselho. Mencione ao final que é uma persona de IA."},
    {"id":"musk","name":"Elon Musk","initials":"EM","role":"Tesla/SpaceX · Disrupção","group":"global","color":"#FAEEDA","tc":"#633806",
     "philosophy":"Você é uma persona de IA inspirada na filosofia pública de Elon Musk. Use raciocínio de primeiros princípios, questione premissas, pense grande e execute rápido. Responda em português do Brasil. Inicie direto com o conselho. Mencione ao final que é uma persona de IA."},
    {"id":"bezos","name":"Jeff Bezos","initials":"JB","role":"Amazon · Obsessão cliente","group":"global","color":"#FCEBEB","tc":"#791F1F",
     "philosophy":"Você é uma persona de IA inspirada na filosofia pública de Jeff Bezos. Baseie-se nas cartas anuais Amazon: obsessão pelo cliente, day one, experimentos. Responda em português do Brasil. Inicie direto com o conselho. Mencione ao final que é uma persona de IA."},
    {"id":"hoffman","name":"Reid Hoffman","initials":"RH","role":"LinkedIn · Redes e escala","group":"global","color":"#EEEDFE","tc":"#3C3489",
     "philosophy":"Você é uma persona de IA inspirada na filosofia pública de Reid Hoffman (Blitzscaling). Valorize redes, escala rápida e adaptabilidade. Responda em português do Brasil. Inicie direto com o conselho. Mencione ao final que é uma persona de IA."},
    {"id":"sandberg","name":"Sheryl Sandberg","initials":"SS","role":"Meta · Liderança","group":"global","color":"#FBEAF0","tc":"#72243E",
     "philosophy":"Você é uma persona de IA inspirada na filosofia pública de Sheryl Sandberg (Lean In). Valorize liderança inclusiva, resiliência e cultura organizacional forte. Responda em português do Brasil. Inicie direto com o conselho. Mencione ao final que é uma persona de IA."},
    {"id":"oprah","name":"Oprah Winfrey","initials":"OW","role":"OWN · Propósito","group":"global","color":"#FAECE7","tc":"#712B13",
     "philosophy":"Você é uma persona de IA inspirada na filosofia pública de Oprah Winfrey. Valorize storytelling autêntico, propósito e conexão humana. Responda em português do Brasil. Inicie direto com o conselho. Mencione ao final que é uma persona de IA."},
    {"id":"nooyi","name":"Indra Nooyi","initials":"IN","role":"PepsiCo · Estratégia","group":"global","color":"#E1F5EE","tc":"#085041",
     "philosophy":"Você é uma persona de IA inspirada na filosofia pública de Indra Nooyi. Valorize estratégia sustentável, Performance with Purpose e visão global. Responda em português do Brasil. Inicie direto com o conselho. Mencione ao final que é uma persona de IA."},
    {"id":"blakely","name":"Sara Blakely","initials":"SB","role":"Spanx · Empreendedorismo","group":"global","color":"#F1EFE8","tc":"#444441",
     "philosophy":"Você é uma persona de IA inspirada na filosofia pública de Sara Blakely. Valorize disrupção em mercados consolidados, bootstrap e fracasso como aprendizado. Responda em português do Brasil. Inicie direto com o conselho. Mencione ao final que é uma persona de IA."},
    {"id":"mgates","name":"Melinda Gates","initials":"MG","role":"Gates Foundation · Impacto","group":"global","color":"#EAF3DE","tc":"#3B6D11",
     "philosophy":"Você é uma persona de IA inspirada na filosofia pública de Melinda French Gates. Valorize impacto social, equidade e filantropia estratégica. Responda em português do Brasil. Inicie direto com o conselho. Mencione ao final que é uma persona de IA."},
    {"id":"lemann","name":"Jorge Paulo Lemann","initials":"JL","role":"3G Capital · Excelência","group":"br","color":"#E6F1FB","tc":"#0C447C",
     "philosophy":"Você é uma persona de IA inspirada na filosofia pública de Jorge Paulo Lemann. Valorize meritocracia, excelência operacional, gestão enxuta e sonhos grandes (BHAGs). Responda em português do Brasil. Inicie direto com o conselho. Mencione ao final que é uma persona de IA."},
    {"id":"luiza","name":"Luiza Trajano","initials":"LT","role":"Magalu · Varejo digital","group":"br","color":"#FBEAF0","tc":"#72243E",
     "philosophy":"Você é uma persona de IA inspirada na filosofia pública de Luiza Trajano. Valorize transformação digital humanizada, liderança feminina e propósito com lucro. Responda em português do Brasil. Inicie direto com o conselho. Mencione ao final que é uma persona de IA."},
    {"id":"flavio","name":"Flávio Augusto","initials":"FA","role":"Wise Up · Geração de valor","group":"br","color":"#FAEEDA","tc":"#633806",
     "philosophy":"Você é uma persona de IA inspirada na filosofia pública de Flávio Augusto da Silva. Valorize geração de valor, empreendedorismo do zero e mentalidade de vendedor. Responda em português do Brasil. Inicie direto com o conselho. Mencione ao final que é uma persona de IA."},
    {"id":"benchimol","name":"Guilherme Benchimol","initials":"GB","role":"XP Inc. · Finanças","group":"br","color":"#E1F5EE","tc":"#085041",
     "philosophy":"Você é uma persona de IA inspirada na filosofia pública de Guilherme Benchimol. Valorize cultura meritocrática, democratização financeira e disrupção de mercados tradicionais. Responda em português do Brasil. Inicie direto com o conselho. Mencione ao final que é uma persona de IA."},
    {"id":"slim","name":"Carlos Slim","initials":"CS","role":"Telmex · Infraestrutura","group":"latam","color":"#FCEBEB","tc":"#791F1F",
     "philosophy":"Você é uma persona de IA inspirada na filosofia pública de Carlos Slim. Valorize investimento contracíclico, infraestrutura de longo prazo e integração vertical. Responda em português do Brasil. Inicie direto com o conselho. Mencione ao final que é uma persona de IA."},
    {"id":"claure","name":"Marcelo Claure","initials":"MC","role":"SoftBank LatAm · Escala","group":"latam","color":"#EEEDFE","tc":"#3C3489",
     "philosophy":"Você é uma persona de IA inspirada na filosofia pública de Marcelo Claure. Valorize escala rápida, apoio a fundadores ambiciosos e transformação digital na América Latina. Responda em português do Brasil. Inicie direto com o conselho. Mencione ao final que é uma persona de IA."},
]

def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_to_history(entry):
    history = load_history()
    history.insert(0, entry)
    history = history[:100]  # keep last 100
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

HTML = r"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>77Gira · Conselho Digital de Negócios</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:#F7F6F3;color:#1A1A2E;min-height:100vh}
.topbar{background:#534AB7;color:#fff;padding:0 24px;height:50px;display:flex;align-items:center;justify-content:space-between;position:sticky;top:0;z-index:100;box-shadow:0 2px 8px rgba(83,74,183,.3)}
.logo{font-size:15px;font-weight:600;letter-spacing:-.3px;display:flex;align-items:center;gap:8px}
.logo span{opacity:.65;font-weight:400;font-size:13px}
.topbar-right{display:flex;align-items:center;gap:10px}
.topdate{font-size:12px;opacity:.6}
.hist-btn{background:rgba(255,255,255,.15);border:1px solid rgba(255,255,255,.2);color:#fff;border-radius:6px;padding:5px 12px;font-size:12px;cursor:pointer;font-family:inherit}
.hist-btn:hover{background:rgba(255,255,255,.25)}
.layout{display:flex;height:calc(100vh - 50px)}
.sidebar{width:290px;background:#fff;border-right:1px solid #E8E6F0;overflow-y:auto;flex-shrink:0;display:none;flex-direction:column}
.sidebar.open{display:flex}
.sidebar-hdr{padding:14px 16px;border-bottom:1px solid #EEE;font-size:13px;font-weight:600;color:#534AB7;display:flex;justify-content:space-between;align-items:center;flex-shrink:0}
.sidebar-hdr button{background:none;border:none;cursor:pointer;color:#AAA;font-size:20px;line-height:1;padding:0}
.hist-scroll{overflow-y:auto;flex:1}
.hist-item{padding:12px 16px;border-bottom:1px solid #F5F3FF;cursor:pointer;transition:background .12s}
.hist-item:hover{background:#F5F3FF}
.hist-date{font-size:10px;color:#AAA;margin-bottom:3px}
.hist-q{font-size:12px;color:#333;line-height:1.45;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
.hist-tags{font-size:10px;color:#7F77DD;margin-top:3px}
.main{flex:1;overflow-y:auto;padding:20px 24px}
.container{max-width:720px;margin:0 auto}
.slbl{font-size:10px;font-weight:700;color:#AAA;letter-spacing:.08em;text-transform:uppercase;margin:14px 0 7px;display:flex;align-items:center;gap:8px}
.slbl::after{content:'';flex:1;height:.5px;background:#E0DEF0}
.grid{display:grid;gap:7px;margin-bottom:4px}
.g5{grid-template-columns:repeat(5,1fr)}
.g4{grid-template-columns:repeat(4,1fr)}
.g2{grid-template-columns:repeat(2,1fr)}
@media(max-width:600px){.g5,.g4{grid-template-columns:repeat(3,1fr)}.g2{grid-template-columns:repeat(2,1fr)}}
.ac{background:#fff;border:1px solid #E8E6F0;border-radius:9px;padding:9px 6px;cursor:pointer;text-align:center;position:relative;user-select:none;transition:all .15s}
.ac:hover{border-color:#AFA9EC;background:#FAFAFF}
.ac.sel{border:1.5px solid #7F77DD;background:#EEEDFE}
.ac.sel .aname{color:#3C3489}
.ava{width:36px;height:36px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:12px;font-weight:700;margin:0 auto 5px}
.aname{font-size:10px;font-weight:500;color:#333;line-height:1.3;margin-bottom:1px}
.arole{font-size:9px;color:#999;line-height:1.3}
.ck{position:absolute;top:3px;right:3px;width:14px;height:14px;background:#534AB7;border-radius:50%;display:none;align-items:center;justify-content:center;font-size:8px;color:#fff;font-weight:700}
.ac.sel .ck{display:flex}
.ctrlbar{display:flex;gap:8px;margin:10px 0 8px;align-items:center;flex-wrap:wrap}
.hint{font-size:12px;color:#999;flex:1}
.sbtn{font-size:11px;padding:4px 10px;border:1px solid #D0CDE8;border-radius:20px;background:transparent;color:#666;cursor:pointer;font-family:inherit;transition:background .12s}
.sbtn:hover{background:#EEEDFE;border-color:#AFA9EC;color:#3C3489}
.qbox{border:1px solid #D0CDE8;border-radius:10px;overflow:hidden;background:#fff;margin-bottom:6px;box-shadow:0 1px 4px rgba(83,74,183,.06)}
textarea{width:100%;border:none;outline:none;padding:13px 15px;font-size:14px;color:#1A1A2E;background:transparent;resize:none;font-family:inherit;line-height:1.65;min-height:85px}
.qfooter{display:flex;justify-content:space-between;align-items:center;padding:8px 12px;border-top:1px solid #EEE;gap:8px;flex-wrap:wrap}
.sc{font-size:12px;color:#AAA}
.btns-row{display:flex;gap:8px}
.abtn{background:#534AB7;color:#fff;border:none;border-radius:7px;padding:8px 18px;font-size:13px;font-weight:500;cursor:pointer;font-family:inherit;transition:background .15s}
.abtn:hover{background:#3C3489}
.abtn:disabled{opacity:.3;cursor:default}
.abtn.sec{background:transparent;color:#534AB7;border:1.5px solid #AFA9EC}
.abtn.sec:hover{background:#EEEDFE}
.responses{margin-top:18px;display:flex;flex-direction:column;gap:12px}
.rcard{background:#fff;border:1px solid #E8E6F0;border-radius:10px;overflow:hidden;box-shadow:0 1px 4px rgba(0,0,0,.04)}
.rhdr{display:flex;align-items:center;gap:10px;padding:10px 14px;border-bottom:1px solid #F5F3FF;background:#FAFAFA}
.rava{width:32px;height:32px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:11px;font-weight:700;flex-shrink:0}
.rname{font-size:13px;font-weight:600;color:#1A1A2E}
.rrole{font-size:11px;color:#AAA}
.rbody{padding:13px 15px;font-size:13.5px;color:#2A2A3E;line-height:1.8;white-space:pre-wrap}
.rbody.loading{color:#BBB;font-style:italic;font-size:13px;padding:16px 15px}
.sintese-box{background:#EAF3DE;border:1px solid #9FE1CB;border-radius:10px;padding:15px}
.slbl-g{font-size:10px;font-weight:700;color:#27500A;letter-spacing:.08em;text-transform:uppercase;margin-bottom:6px}
.sintese-txt{font-size:13.5px;color:#1A3010;line-height:1.8}
.exp-bar{display:flex;justify-content:flex-end;gap:8px;margin-top:6px}
.disc{font-size:10.5px;color:#CCC;margin-top:10px;line-height:1.5;text-align:center;padding-top:8px;border-top:1px solid #EEE}
.empty-hist{padding:30px 16px;text-align:center;color:#CCC;font-size:13px}
.toast{position:fixed;bottom:24px;right:24px;background:#534AB7;color:#fff;padding:10px 18px;border-radius:8px;font-size:13px;opacity:0;pointer-events:none;transition:opacity .25s;z-index:999;box-shadow:0 4px 12px rgba(83,74,183,.4)}
.toast.show{opacity:1}
.status-bar{background:#EEEDFE;border:1px solid #AFA9EC;border-radius:8px;padding:8px 14px;font-size:12px;color:#3C3489;margin-bottom:14px;display:none}
.status-bar.show{display:flex;align-items:center;gap:8px}
.spinner{width:14px;height:14px;border:2px solid #AFA9EC;border-top-color:#534AB7;border-radius:50%;animation:spin .7s linear infinite;flex-shrink:0}
@keyframes spin{to{transform:rotate(360deg)}}
</style>
</head>
<body>

<div class="topbar">
  <div class="logo">🎵 77Gira <span>· Conselho Digital de Negócios</span></div>
  <div class="topbar-right">
    <span class="topdate" id="topdate"></span>
    <button class="hist-btn" onclick="toggleSidebar()">📋 Histórico</button>
  </div>
</div>

<div class="layout">
  <div class="sidebar" id="sidebar">
    <div class="sidebar-hdr">
      Consultas anteriores
      <button onclick="toggleSidebar()">×</button>
    </div>
    <div class="hist-scroll" id="hist-list">
      <div class="empty-hist">Nenhuma consulta ainda.</div>
    </div>
  </div>

  <div class="main">
    <div class="container">

      <div class="status-bar" id="status-bar">
        <div class="spinner"></div>
        <span id="status-msg">Consultando conselheiros...</span>
      </div>

      <div class="slbl">🌍 Global</div>
      <div class="grid g5" id="grid-global"></div>
      <div class="slbl">🇧🇷 Brasil</div>
      <div class="grid g4" id="grid-br"></div>
      <div class="slbl">🌎 América Latina</div>
      <div class="grid g2" id="grid-latam"></div>

      <div class="ctrlbar">
        <span class="hint" id="hint">Nenhum conselheiro selecionado</span>
        <button class="sbtn" onclick="selAll()">Todos</button>
        <button class="sbtn" onclick="selBr()">Só brasileiros</button>
        <button class="sbtn" onclick="selNone()">Limpar</button>
      </div>

      <div class="qbox">
        <textarea id="question" placeholder="Descreva seu desafio ou dúvida de negócio..." rows="4" oninput="updateUI()"></textarea>
        <div class="qfooter">
          <span class="sc" id="sc">0 selecionados</span>
          <div class="btns-row">
            <button class="abtn sec" id="pdf-btn" style="display:none" onclick="exportPDF()">⬇ PDF</button>
            <button class="abtn" id="ask-btn" onclick="consultar()" disabled>Consultar →</button>
          </div>
        </div>
      </div>

      <div class="responses" id="responses"></div>
    </div>
  </div>
</div>

<div class="toast" id="toast"></div>

<script>
const ADVISORS = """ + json.dumps(ADVISORS) + r""";
const GROUPS = {global:'grid-global', br:'grid-br', latam:'grid-latam'};
let selected = new Set();
let isLoading = false;

document.getElementById('topdate').textContent = new Date().toLocaleDateString('pt-BR',{weekday:'long',day:'2-digit',month:'long'});

function renderGroups(){
  Object.keys(GROUPS).forEach(g=>{
    const el = document.getElementById(GROUPS[g]);
    el.innerHTML = '';
    ADVISORS.filter(a=>a.group===g).forEach(a=>{
      const c = document.createElement('div');
      c.className = 'ac'+(selected.has(a.id)?' sel':'');
      c.innerHTML = `<div class="ck">✓</div><div class="ava" style="background:${a.color};color:${a.tc}">${a.initials}</div><div class="aname">${a.name}</div><div class="arole">${a.role}</div>`;
      c.onclick = ()=>{ selected.has(a.id)?selected.delete(a.id):selected.add(a.id); renderGroups(); };
      el.appendChild(c);
    });
  });
  updateUI();
}

function updateUI(){
  const n = selected.size;
  document.getElementById('hint').textContent = n===0?'Nenhum conselheiro selecionado':`${n} de ${ADVISORS.length} selecionados`;
  document.getElementById('sc').textContent = `${n} selecionado${n!==1?'s':''}`;
  const q = document.getElementById('question').value.trim();
  document.getElementById('ask-btn').disabled = n===0||!q||isLoading;
}

function selAll(){ ADVISORS.forEach(a=>selected.add(a.id)); renderGroups(); }
function selBr(){ selected.clear(); ADVISORS.filter(a=>a.group==='br').forEach(a=>selected.add(a.id)); renderGroups(); }
function selNone(){ selected.clear(); renderGroups(); }
function toast(msg,dur=2500){ const t=document.getElementById('toast'); t.textContent=msg; t.classList.add('show'); setTimeout(()=>t.classList.remove('show'),dur); }
function setStatus(show, msg=''){ const b=document.getElementById('status-bar'); b.classList.toggle('show',show); if(msg) document.getElementById('status-msg').textContent=msg; }

function toggleSidebar(){
  const s = document.getElementById('sidebar');
  s.classList.toggle('open');
  if(s.classList.contains('open')) loadHistory();
}

function loadHistory(){
  fetch('/api/history').then(r=>r.json()).then(data=>{
    const el = document.getElementById('hist-list');
    if(!data.length){ el.innerHTML='<div class="empty-hist">Nenhuma consulta ainda.</div>'; return; }
    el.innerHTML = data.map((h,i)=>`
      <div class="hist-item" onclick="loadEntry(${i})">
        <div class="hist-date">${h.date}</div>
        <div class="hist-q">${h.question}</div>
        <div class="hist-tags">${(h.advisors||[]).slice(0,3).join(' · ')}${h.advisors&&h.advisors.length>3?' +'+( h.advisors.length-3):''}</div>
      </div>`).join('');
  });
}

function loadEntry(i){
  fetch('/api/history').then(r=>r.json()).then(data=>{
    const h = data[i];
    if(!h) return;
    document.getElementById('question').value = h.question;
    renderResponses(h.responses||[], h.sintese||'');
    document.getElementById('sidebar').classList.remove('open');
    toast('Consulta carregada ✓');
  });
}

async function consultar(){
  const q = document.getElementById('question').value.trim();
  if(!q||selected.size===0) return;
  isLoading = true;
  updateUI();
  setStatus(true, 'Consultando conselheiros...');
  document.getElementById('responses').innerHTML='';
  document.getElementById('pdf-btn').style.display='none';

  const active = ADVISORS.filter(a=>selected.has(a.id));

  try {
    setStatus(true, `Consultando ${active.length} conselheiro${active.length>1?'s':''} em paralelo...`);
    const res = await fetch('/api/consult-all', {
      method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify({question: q, advisor_ids: active.map(a=>a.id)})
    });
    const data = await res.json();
    if(data.error){ toast('Erro: '+data.error, 4000); setStatus(false); isLoading=false; updateUI(); return; }

    const results = data.responses||[];

    setStatus(true, 'Gerando síntese do conselho...');
    let sintese = '';
    if(results.length>=2){
      const sr = await fetch('/api/sintese',{
        method:'POST',headers:{'Content-Type':'application/json'},
        body:JSON.stringify({question:q, responses:results.map(r=>r.name+': '+r.text.slice(0,350)).join('\n\n')})
      });
      const sd = await sr.json();
      sintese = sd.sintese||'';
    }

    renderResponses(results, sintese);

    fetch('/api/history',{
      method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify({
        date: new Date().toLocaleDateString('pt-BR',{day:'2-digit',month:'short',year:'numeric',hour:'2-digit',minute:'2-digit'}),
        question: q, advisors: active.map(a=>a.name), responses: results, sintese
      })
    });

    toast('Consulta concluída ✓');
  } catch(e){
    toast('Erro de rede: '+e.message, 4000);
  }

  setStatus(false);
  isLoading = false;
  updateUI();
}

function renderResponses(results, sintese){
  const resp = document.getElementById('responses');
  resp.innerHTML='';
  results.forEach(r=>{
    const a = ADVISORS.find(x=>x.id===r.id);
    if(!a) return;
    const card = document.createElement('div');
    card.className='rcard';
    card.innerHTML=`
      <div class="rhdr">
        <div class="rava" style="background:${a.color};color:${a.tc}">${a.initials}</div>
        <div><div class="rname">${a.name}</div><div class="rrole">${a.role}</div></div>
      </div>
      <div class="rbody">${r.text}</div>`;
    resp.appendChild(card);
  });
  if(sintese){
    resp.insertAdjacentHTML('beforeend',`
      <div class="sintese-box">
        <div class="slbl-g">💡 Síntese do conselho</div>
        <div class="sintese-txt">${sintese}</div>
      </div>`);
  }
  resp.insertAdjacentHTML('beforeend',`
    <div class="exp-bar"><button class="abtn sec" onclick="exportPDF()">⬇ Exportar PDF</button></div>
    <div class="disc">Personas de IA inspiradas na filosofia pública dessas figuras. Não representam opiniões reais.</div>`);
  window._lastExport = {q: document.getElementById('question').value.trim(), results, sintese};
}

async function exportPDF(){
  const {q,results,sintese} = window._lastExport||{};
  if(!results) return;
  toast('Gerando PDF...');
  const res = await fetch('/api/pdf',{
    method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({question:q,responses:results,sintese})
  });
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href=url; a.download='conselho-77gira-'+new Date().toISOString().slice(0,10)+'.pdf'; a.click();
  toast('PDF baixado ✓');
}

renderGroups();
</script>
</body>
</html>"""


@app.route("/")
def index():
    return render_template_string(HTML)


@app.route("/api/consult-all", methods=["POST"])
def consult_all():
    data = request.json
    question  = data.get("question", "")
    advisor_ids = data.get("advisor_ids", [])

    try:
        client = get_client()
    except ValueError as e:
        return jsonify({"error": str(e)}), 500

    results = []
    for aid in advisor_ids:
        advisor = next((a for a in ADVISORS if a["id"] == aid), None)
        if not advisor:
            continue
        try:
            resp = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=1000,
                system=advisor["philosophy"] + "\n\nResponda de forma concisa (3 parágrafos). Sem markdown, apenas texto simples.",
                messages=[{"role": "user", "content": f"Pergunta do empresário: {question}"}]
            )
            results.append({"id": advisor["id"], "name": advisor["name"], "text": resp.content[0].text})
        except Exception as e:
            results.append({"id": advisor["id"], "name": advisor["name"], "text": f"Erro: {str(e)}"})

    return jsonify({"responses": results})


@app.route("/api/sintese", methods=["POST"])
def sintese():
    data = request.json
    try:
        client = get_client()
        resp = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=300,
            system="Você sintetiza conselhos de um conselho de negócios. Responda em português do Brasil, texto simples sem markdown.",
            messages=[{"role": "user", "content": f"Pergunta: {data.get('question','')}\n\nRespostas:\n{data.get('responses','')}\n\nEscreva uma síntese de 2-3 frases integrando os pontos mais relevantes."}]
        )
        return jsonify({"sintese": resp.content[0].text})
    except Exception as e:
        return jsonify({"sintese": ""}), 200


@app.route("/api/history", methods=["GET"])
def get_history():
    return jsonify(load_history())


@app.route("/api/history", methods=["POST"])
def add_history():
    save_to_history(request.json)
    return jsonify({"ok": True})


@app.route("/api/pdf", methods=["POST"])
def generate_pdf():
    if not HAS_PDF:
        return "ReportLab não instalado.", 500

    data      = request.json
    question  = data.get("question", "")
    responses = data.get("responses", [])
    sintese   = data.get("sintese", "")

    buf = io.BytesIO()
    M   = 22 * mm
    CW  = A4[0] - 2 * M

    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=M, rightMargin=M, topMargin=18*mm, bottomMargin=20*mm)

    PURPLE    = colors.HexColor("#534AB7")
    PURPLE_DK = colors.HexColor("#3C3489")
    GRAY_L    = colors.HexColor("#F5F4FB")
    GRAY_M    = colors.HexColor("#D3D1C7")
    TEXT      = colors.HexColor("#1A1A2E")
    TEXT_M    = colors.HexColor("#666677")
    GREEN_BG  = colors.HexColor("#EAF3DE")
    GREEN_BD  = colors.HexColor("#9FE1CB")
    GREEN_T   = colors.HexColor("#1A3010")

    def ps(n, **k): return ParagraphStyle(n, **k)
    s_q    = ps("q",  fontSize=10,  leading=15, textColor=TEXT,      fontName="Helvetica", alignment=TA_JUSTIFY)
    s_lbl  = ps("l",  fontSize=7.5, leading=10, textColor=TEXT_M,    fontName="Helvetica-Bold", spaceAfter=3)
    s_name = ps("nm", fontSize=13,  leading=16, textColor=PURPLE_DK, fontName="Helvetica-Bold", spaceAfter=1)
    s_role = ps("rl", fontSize=8.5, leading=12, textColor=TEXT_M,    fontName="Helvetica",      spaceAfter=5)
    s_body = ps("bd", fontSize=9.5, leading=15, textColor=TEXT,      fontName="Helvetica", alignment=TA_JUSTIFY, spaceAfter=4)
    s_sint = ps("st", fontSize=9.5, leading=15, textColor=GREEN_T,   fontName="Helvetica", alignment=TA_JUSTIFY)
    s_slbl = ps("sl", fontSize=7.5, leading=10, textColor=colors.HexColor("#27500A"), fontName="Helvetica-Bold", spaceAfter=4)
    s_disc = ps("dc", fontSize=7,   leading=10, textColor=colors.HexColor("#AAAAAA"), fontName="Helvetica-Oblique", alignment=TA_CENTER)

    story = []

    hdr = Table([[
        Paragraph("<font color='white'><b>77Gira · Conselho Digital de Negócios</b></font>",
                  ps("h", fontSize=14, leading=18, textColor=colors.white, fontName="Helvetica-Bold")),
        Paragraph(f"<font color='#C8C4F0'>{datetime.now().strftime('%d/%m/%Y %H:%M')}</font>",
                  ps("hd", fontSize=9, leading=12, textColor=colors.HexColor("#C8C4F0"), fontName="Helvetica", alignment=TA_CENTER))
    ]], colWidths=[CW*0.7, CW*0.3])
    hdr.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,-1),PURPLE),("ROWPADDING",(0,0),(-1,-1),13),("VALIGN",(0,0),(-1,-1),"MIDDLE")]))
    story += [hdr, Spacer(1,7*mm)]

    story.append(Paragraph("PERGUNTA CONSULTADA", s_lbl))
    qt = Table([[Paragraph(question, s_q)]], colWidths=[CW])
    qt.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,-1),GRAY_L),("ROWPADDING",(0,0),(-1,-1),10),("BOX",(0,0),(-1,-1),0.4,GRAY_M)]))
    story += [qt, Spacer(1,6*mm), HRFlowable(width=CW,thickness=0.5,color=GRAY_M), Spacer(1,5*mm)]

    for i, r in enumerate(responses):
        adv = next((a for a in ADVISORS if a["id"]==r["id"]), None)
        if not adv: continue
        av = Table([[Paragraph(f"<font color='{adv['tc']}'><b>{adv['initials']}</b></font>",
                               ps("av",fontSize=11,leading=13,fontName="Helvetica-Bold",alignment=TA_CENTER))]],
                   colWidths=[9*mm],rowHeights=[9*mm])
        av.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,-1),colors.HexColor(adv["color"])),("VALIGN",(0,0),(-1,-1),"MIDDLE"),("ALIGN",(0,0),(-1,-1),"CENTER"),("ROWPADDING",(0,0),(-1,-1),0)]))
        hr = Table([[av,[Paragraph(adv["name"],s_name),Paragraph(adv["role"],s_role)]]],colWidths=[11*mm,CW-11*mm])
        hr.setStyle(TableStyle([("VALIGN",(0,0),(-1,-1),"MIDDLE"),("LEFTPADDING",(1,0),(1,0),8),("TOPPADDING",(0,0),(-1,-1),0),("BOTTOMPADDING",(0,0),(-1,-1),0)]))
        story += [hr, Spacer(1,3)]
        for para in r["text"].split("\n\n"):
            if para.strip(): story.append(Paragraph(para.strip(),s_body))
        if i < len(responses)-1:
            story += [Spacer(1,4*mm),HRFlowable(width=CW,thickness=0.3,color=GRAY_M,dash=[2,3]),Spacer(1,4*mm)]

    if sintese:
        st = Table([[Paragraph("SÍNTESE DO CONSELHO",s_slbl)],[Paragraph(sintese,s_sint)]],colWidths=[CW])
        st.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,-1),GREEN_BG),("BOX",(0,0),(-1,-1),0.5,GREEN_BD),("ROWPADDING",(0,0),(-1,-1),10),("TOPPADDING",(0,0),(0,0),10)]))
        story += [Spacer(1,6*mm), st]

    story += [Spacer(1,6*mm),HRFlowable(width=CW,thickness=0.4,color=GRAY_M),Spacer(1,3*mm),
              Paragraph("Aviso: gerado por IA com base na filosofia pública das figuras mencionadas. Não representa opiniões reais. 77Gira · Conselho Digital.",s_disc)]

    doc.build(story)
    buf.seek(0)
    return send_file(buf, mimetype="application/pdf",
                     download_name=f"conselho-77gira-{datetime.now().strftime('%Y-%m-%d')}.pdf")


if __name__ == "__main__":
    print("\n🎵 77Gira · Conselho Digital — modo local")
    print("Acesse: http://localhost:5001\n")
    app.run(debug=True, port=5001)
