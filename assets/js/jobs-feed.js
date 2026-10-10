(function(root, factory) {
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  else root.WishJobs = api;
})(typeof globalThis !== 'undefined' ? globalThis : this, function() {
  const hosts = new Set(['dptech.zhiye.com','talent.hikvision.com','hscampus.zhiye.com','h3c.zhiye.com','dahua.zhiye.com','campus.10jqka.com.cn']);
  const dayKey = now => new Date(now + 8*3600000).toISOString().slice(0,10);
  const ordinal = now => Math.floor((now + 8*3600000)/86400000);
  function safeLink(value) {
    try { const url = new URL(value); return url.protocol === 'https:' && hosts.has(url.hostname) && !url.username && !url.password ? url.href : null; } catch { return null; }
  }
  function eligible(job, now=Date.now()) {
    const age = now - Date.parse(job.checkedAt);
    return job.location === '杭州' && ['实习','校招'].includes(job.type) && typeof job.title === 'string' && !!safeLink(job.url) && Number.isFinite(age) && age >= -300000 && age <= 72*3600000;
  }
  function today(value, now) {
    const time = Date.parse(value);
    return Number.isFinite(time) && time <= now && dayKey(time) === dayKey(now);
  }
  function changes(jobs, now=Date.now()) {
    return {added:jobs.filter(job=>today(job.newAt,now)).length,changed:jobs.filter(job=>today(job.changedAt,now)).length};
  }
  function daily(all, now=Date.now(), limit=8) {
    const pool = all.filter(job=>eligible(job,now));
    const groups = new Map();
    for (const job of pool) { if(!groups.has(job.company))groups.set(job.company,[]);groups.get(job.company).push(job); }
    const companies = [...groups.keys()].sort();
    if (!companies.length) return [];
    const day = ordinal(now), offset = day % companies.length;
    const companyOrder = companies.slice(offset).concat(companies.slice(0,offset));
    for (const [company, items] of groups) {
      items.sort((a,b)=>(b.publishedAt||'').localeCompare(a.publishedAt||'')||a.id.localeCompare(b.id));
      const n = day % items.length;
      groups.set(company, items.slice(n).concat(items.slice(0,n)));
    }
    const fresh = pool.filter(job=>today(job.newAt,now)).sort((a,b)=>b.newAt.localeCompare(a.newAt));
    const selected = [], ids = new Set();
    const add = job => { if(job && !ids.has(job.id) && selected.length<limit){selected.push(job);ids.add(job.id);} };
    fresh.forEach(add);
    for(let round=0; round<pool.length && selected.length<Math.min(pool.length,limit);round++) {
      for(const company of companyOrder) add(groups.get(company)[round]);
    }
    return selected;
  }
  return {dayKey,eligible,safeLink,daily,changes,today};
});
