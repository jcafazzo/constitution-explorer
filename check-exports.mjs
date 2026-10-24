import {readFileSync} from 'node:fs';
import assert from 'node:assert/strict';
import {scaleBinarySTL} from './dist/stl-export.js';
const ships=['constitution','saladin','hermes','ptolemy','federation'];
function bounds(buffer){
 const v=new DataView(buffer),n=v.getUint32(80,true),min=[Infinity,Infinity,Infinity],max=[-Infinity,-Infinity,-Infinity];
 for(let i=0;i<n;i++)for(let j=0;j<9;j++){const axis=j%3,x=v.getFloat32(84+50*i+12+4*j,true);min[axis]=Math.min(min[axis],x);max[axis]=Math.max(max[axis],x);}
 return {min,max,extents:max.map((x,i)=>x-min[i])};
}
for(const id of ships){
 const bytes=readFileSync(new URL(`./dist/assets/fleet/${id}-100mm.stl`,import.meta.url));const data=bytes.buffer.slice(bytes.byteOffset,bytes.byteOffset+bytes.byteLength);const before=Buffer.from(data).toString('base64');
 const original=bounds(data);assert.ok(Math.abs(original.extents[1]-100)<.001,id+' base length');
 for(const length of [100,121.25,144.3,160,200]){
  const scaled=scaleBinarySTL(data,length),b=bounds(scaled);
  assert.ok(Math.abs(b.extents[1]-length)<.001,id+' scaled length');
  for(let k=0;k<3;k++)assert.ok(Math.abs(b.extents[k]-original.extents[k]*length/100)<.001,id+' uniform scale');
  const a=new DataView(data),v=new DataView(scaled);for(let k=0;k<3;k++)assert.equal(a.getFloat32(84+k*4,true),v.getFloat32(84+k*4,true),'normal unchanged');
 }
 assert.equal(Buffer.from(data).toString('base64'),before,'input model remains unchanged');
 for(const bad of [0,99,201,NaN,Infinity])assert.throws(()=>scaleBinarySTL(data,bad));
 console.log(id+': 5 lengths passed, source unchanged');
}
assert.throws(()=>scaleBinarySTL(new ArrayBuffer(80),100));
console.log('All STL export checks passed.');
