import fs from 'node:fs';
import * as T from '../dist/vendor/three.module.js';
import * as studies from '../dist/interior-studies.js';
import {batch,exportStudy} from './build-details.mjs';
const report=[];
for(const [id,fn] of [['bridge','buildBridgeStudy'],['hangar','buildHangarStudy'],['impulse','buildImpulseStudy']]){
 if(!studies[fn])continue;
 const study=studies[fn]();study.group.rotation.x=Math.PI/2;study.group.applyQuaternion(new T.Quaternion().setFromAxisAngle(new T.Vector3(0,0,1),Math.PI));
 const group=batch(study.group);
 report.push({...await exportStudy(group,id+'.glb'),description:study.description,sourcePages:study.sourcePages});
}
fs.writeFileSync('model-source/interior-validation.json',JSON.stringify(report,null,2));console.log(JSON.stringify(report));
