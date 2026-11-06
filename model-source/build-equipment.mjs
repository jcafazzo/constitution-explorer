// Builds every Equipment Locker study: `node model-source/build-equipment.mjs [id ...]`
// Each item in dist/assets/equipment/equipment.json declares `size` [width, length, height] in cm,
// taken from printed dimensions where the sheet gives them, otherwise measured against the sheet's scale bar.
// The generated model must match that envelope within `tolerance` (default 5%).
import fs from 'node:fs';
import path from 'node:path';
import {exportItem} from './equipment-kit.mjs';
import * as builders from './equipment-builders.mjs';

const ROOT=process.cwd(),OUT=path.join(ROOT,'dist/assets/equipment');
const items=JSON.parse(fs.readFileSync(path.join(OUT,'equipment.json'),'utf8'));
const only=process.argv.slice(2);
const reportPath='model-source/equipment-validation.json';
const report=fs.existsSync(reportPath)?JSON.parse(fs.readFileSync(reportPath,'utf8')):{};
let failed=0;
for(const item of items){
 if(only.length&&!only.includes(item.id))continue;
 const fn=builders[item.id.replace(/-([a-z0-9])/g,(_,c)=>c.toUpperCase())];
 if(!fn){console.log(`${item.id}: no builder yet`);failed++;continue;}
 const root=fn();root.name=`${item.title} — PDF ${item.pages.join(', ')}`;
 const r=await exportItem(root,item.id+'.glb',OUT);
 // Where a study is posed open, the envelope is checked on its closed pose (same builder).
 const closedFn=builders[fn.name+'Closed'];if(closedFn){const c=closedFn(),{T:TT}=await import('./equipment-kit.mjs');const v=new TT.Box3().setFromObject(c).getSize(new TT.Vector3());r.sizeCm={width:+v.x.toFixed(2),length:+v.y.toFixed(2),height:+v.z.toFixed(2)};r.checkedPose='closed';}
 const tol=item.tolerance??.05,[w,l,h]=item.size,got=[r.sizeCm.width,r.sizeCm.length,r.sizeCm.height];
 r.target={width:w,length:l,height:h,basis:item.sizeBasis||'',tolerance:tol};
 r.deviation=got.map((v,i)=>+((v-[w,l,h][i])/[w,l,h][i]).toFixed(3));
 const axes=item.checkAxes||[1,1,1];r.pass=r.deviation.every((d,i)=>!axes[i]||Math.abs(d)<=tol)&&r.bytes<2_500_000;
 if(!r.pass)failed++;
 report[item.id]=r;
 console.log(`${r.pass?'PASS':'FAIL'} ${item.id}: ${got.join(' × ')} cm (target ${w} × ${l} × ${h}), ${(r.bytes/1024).toFixed(0)} KB, ${r.triangles} tris`);
}
fs.writeFileSync(reportPath,JSON.stringify(report,null,2));
if(failed){console.log(`${failed} item(s) failed or missing.`);process.exitCode=1;}
