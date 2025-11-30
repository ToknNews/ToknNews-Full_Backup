// =============================
// TOKNNews System + Reddit Gauges
// =============================
const blueScale = ['#5ac8ff','#00aaff','#0070cc','#004f99'];

function drawArcGauge(ctx,value,max,label){
  const pct=value/max;
  const start=-Math.PI, end=start+Math.PI*pct;
  const grd=ctx.createLinearGradient(0,0,300,0);
  blueScale.forEach((c,i)=>grd.addColorStop(i/(blueScale.length-1),c));
  ctx.lineWidth=15;ctx.strokeStyle=grd;ctx.lineCap="round";
  ctx.beginPath();ctx.arc(150,150,100,start,end,false);ctx.stroke();
  ctx.font="16px Inter";ctx.fillStyle="#5ac8ff";ctx.textAlign="center";
  ctx.fillText(label,150,180);
}

async function loadHeartbeat(){
  try{
    const r=await fetch("/data/heartbeat.json",{cache:"no-store"});
    const hb=await r.json();
    const ok=Object.values(hb).filter(v=>v==="ok").length;
    const total=Object.keys(hb).length-3;
    const pct=Math.round((ok/total)*100);
    const ctx=document.getElementById("systemGauge").getContext("2d");
    ctx.clearRect(0,0,300,150);
    drawArcGauge(ctx,pct,100,`System Health ${pct}%`);
  }catch(e){console.error("SystemGauge",e);}
}

async function loadReddit(){
  try{
    const r=await fetch("/data/reddit_sentiment.json",{cache:"no-store"});
    const data=await r.json();
    if(!Array.isArray(data)||data.length===0)return;
    const counts={bullish:0,bearish:0,neutral:0};
    data.forEach(d=>{
      const s=(d.sentiment||"neutral").toLowerCase();
      if(counts[s]!=undefined)counts[s]++;else counts.neutral++;
    });
    const total=Object.values(counts).reduce((a,b)=>a+b,0)||1;
    const pctBull=Math.round((counts.bullish/total)*100);
    const ctx=document.getElementById("redditGauge").getContext("2d");
    ctx.clearRect(0,0,300,150);
    drawArcGauge(ctx,pctBull,100,`Community Bullish ${pctBull}%`);
    document.getElementById("reddit-summary")
      .textContent=`Community Sentiment — Bullish ${pctBull}%`;
  }catch(e){console.error("RedditGauge",e);}
}

loadHeartbeat();loadReddit();
setInterval(loadHeartbeat,60000);
setInterval(loadReddit,60000);
