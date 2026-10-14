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
  function bachelorEligible(education) {
    if (typeof education !== 'string') return false;
    const text = education.replace(/\s+/g, '').toLowerCase();
    return /本科|学士|bachelor/.test(text)
      && !/大专|专科|中专|高中|不限|无要求|不接受本科|不招本科|本科不可/.test(text)
      && !/(?:硕士(?:研究生)?|博士(?:研究生)?|研究生)(?:及以上|以上|起步|起)/.test(text)
      && !/(?:仅限|只招|必须|要求|至少|最低)(?:为)?(?:硕士|博士|研究生)/.test(text);
  }
  function eligible(job, now=Date.now()) {
    const age = now - Date.parse(job.checkedAt);
    return bachelorEligible(job.education) && job.location === '杭州' && ['实习','校招'].includes(job.type) && typeof job.title === 'string' && !!safeLink(job.url) && Number.isFinite(age) && age >= -300000 && age <= 72*3600000;
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
  return {dayKey,bachelorEligible,eligible,safeLink,daily,changes,today};
});
