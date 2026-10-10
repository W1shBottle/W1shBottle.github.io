(() => {
  const board = document.querySelector('.jobs-board'); if(!board)return;
  const api=window.WishJobs, results=document.getElementById('jobs-results'), total=document.getElementById('jobs-total');
  const company=document.getElementById('jobs-company'), type=document.getElementById('jobs-type'), direction=document.getElementById('jobs-direction');
  const format=new Intl.DateTimeFormat('zh-CN',{timeZone:'Asia/Shanghai',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit',hour12:false});
  let jobs=[], loading=false;
  const el=(tag,cls,text)=>{const node=document.createElement(tag);node.className=cls;if(text)node.textContent=text;return node;};
  function render() {
    results.replaceChildren(); const now=Date.now();
    const filtered=jobs.filter(job=>api.eligible(job,now)&&(!company.value||job.company===company.value)&&(!type.value||job.type===type.value)&&(!direction.value||job.direction===direction.value));
    document.getElementById('jobs-result-count').textContent=`符合筛选：${filtered.length} 个岗位`;
    if(!filtered.length)results.append(el('p','jobs-empty','暂时没有匹配岗位，可以调整筛选条件。'));
    for(const job of filtered) {
      const card=el('article','job-detail-card'), title=el('h2','',job.title), meta=el('p','jobs-meta',`${job.company} · ${job.type} · ${job.locations.join(' / ')}`);
      if(api.today(job.newAt,now))card.append(el('span','job-new','今日新收录'));
      card.append(title,meta);
      const facts=el('dl','job-facts');
      for(const [label,value] of [['学历',job.education||'未注明'],['届别',job.cohort||'见招聘原文'],['薪资',job.salary||'未公布'],['发布时间',job.publishedAt||'来源未提供']]) {
        const item=el('div','');item.append(el('dt','',label),el('dd','',value));facts.append(item);
      }
      card.append(facts);
      if(job.focus?.length)card.append(el('p','job-focus','工作方向：'+job.focus.join(' · ')));
      if(job.internshipDuration)card.append(el('p','job-focus','实习时长：'+job.internshipDuration));
      const tags=el('div','jobs-tags');(job.skills||[]).forEach(skill=>tags.append(el('span','',skill)));card.append(tags);
      const foot=el('div','job-card-foot');foot.append(el('span','',`${format.format(Date.parse(job.checkedAt))} 核验 · ${job.source}`));
      const link=el('a','jobs-original','查看招聘原文 ↗');link.href=api.safeLink(job.url);link.target='_blank';link.rel='noopener noreferrer';foot.append(link);card.append(foot);results.append(card);
    }
  }
  async function refresh() {
    if(loading)return;loading=true;
    try {
      const response=await fetch(board.dataset.feed,{cache:'no-store',signal:AbortSignal.timeout(10000)});
      if(!response.ok)throw new Error('Unavailable');const data=await response.json();
      if(!Array.isArray(data.jobs)||!Array.isArray(data.sources))throw new Error('Invalid feed');
      jobs=data.jobs.filter(job=>api.eligible(job));
      const selected=company.value;company.replaceChildren(new Option('全部企业',''));
      [...new Set(jobs.map(job=>job.company))].sort().forEach(name=>company.add(new Option(name,name)));
      if([...company.options].some(option=>option.value===selected))company.value=selected;
      const activity=api.changes(jobs), failed=data.sources.filter(source=>source.status!=='ok').length;
      total.textContent=`${new Set(jobs.map(job=>job.company)).size} 家企业 · ${jobs.length} 个岗位 · 今日新收录 ${activity.added} 个 · 信息更新 ${activity.changed} 个${failed?' · 部分来源同步失败':''}`;
      const sources=document.getElementById('jobs-source-list');sources.replaceChildren();
      for(const source of data.sources) {const p=el('p','',`${source.name} · ${source.count} 个匹配 · ${source.status==='ok'?'同步成功':'同步失败'}${source.checkedAt?' · '+format.format(Date.parse(source.checkedAt)):''}`);sources.append(p);}
      render();
    } catch {total.textContent='更新暂不可用，保留最近核验且未过期的岗位。';render();}
    finally{loading=false;}
  }
  [company,type,direction].forEach(input=>input.addEventListener('change',render));
  setInterval(()=>{if(!document.hidden)refresh();},600000);
  setInterval(render,60000);
  document.addEventListener('visibilitychange',()=>{if(!document.hidden)refresh();});refresh();
})();
