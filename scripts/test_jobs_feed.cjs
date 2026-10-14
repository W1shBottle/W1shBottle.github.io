const assert = require('node:assert/strict');
const api = require('../assets/js/jobs-feed.js');
const now=Date.parse('2026-10-10T04:00:00Z');
const jobs=Array.from({length:18},(_,i)=>({id:String(i),title:'Java岗位',company:'企业'+(i%6),location:'杭州',type:'实习',education:'本科及以上',url:'https://dptech.zhiye.com/jobs',checkedAt:new Date(now).toISOString(),publishedAt:'2026-10-01'}));
assert.equal(api.daily(jobs,now).length,8);
assert.equal(new Set(api.daily(jobs,now).map(j=>j.company)).size,6);
assert.deepEqual(api.daily(jobs,now),api.daily([...jobs].reverse(),now));
assert.notDeepEqual(api.daily(jobs,now).map(j=>j.id),api.daily(jobs,now+86400000).map(j=>j.id));
assert.notDeepEqual(api.daily(jobs,now).map(j=>j.id).sort(),api.daily(jobs,now+86400000).map(j=>j.id).sort());
assert.equal(api.dayKey(Date.parse('2026-10-10T16:00:00Z')),'2026-10-11');
assert.equal(api.daily(jobs,now+73*3600000).length,0);
assert.equal(api.safeLink('javascript:alert(1)'),null);
assert.equal(api.safeLink('https://dptech.zhiye.com.evil.example/jobs'),null);
assert.equal(api.eligible({...jobs[0],location:'北京'},now),false);
const added={...jobs[17],newAt:new Date(now).toISOString()};
assert.equal(api.daily([...jobs.slice(0,17),added],now)[0].id,added.id);
assert.equal(api.changes([added],now).added,1);
assert.equal(api.changes([added],now+86400000).added,0);
console.log('PASS: daily rotation, company coverage, stable order, new priority, Beijing midnight, TTL and URL validation');

const degreeCases = require('./education_cases.json');
for (const [education,expected] of degreeCases) {
  assert.equal(api.bachelorEligible(education),expected,JSON.stringify(education));
  assert.equal(api.eligible({...jobs[0],education},now),expected,JSON.stringify(education));
}
const mixed=degreeCases.map(([education],i)=>({...jobs[0],id:'degree-'+i,education}));
const selected=api.daily(mixed,now,100);
assert.equal(selected.length,degreeCases.filter(([,ok])=>ok).length);
assert(selected.every(job=>api.bachelorEligible(job.education)));
console.log('PASS: explicit bachelor requirements and exclusion from daily recommendations');
