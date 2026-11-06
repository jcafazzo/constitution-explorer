// Shared modelling kit for the Equipment Locker studies.
// Author in centimetres: X = width (port→starboard), Y = length (front is -Y), Z = up.
// exportItem() scales to metres for glTF and records bounds for validation.
import fs from 'node:fs';
import path from 'node:path';
import * as T from '../dist/vendor/three.module.js';
import {GLTFExporter} from '../dist/vendor/GLTFExporter.js';
import {mergeGeometries,mergeVertices} from '../dist/vendor/utils/BufferGeometryUtils.js';
export {T};
// GLTFExporter uses FileReader for binary packing; this Node shim never touches browser state.
globalThis.FileReader??=class{readAsArrayBuffer(b){b.arrayBuffer().then(v=>{this.result=v;this.onloadend?.();});}readAsDataURL(b){b.arrayBuffer().then(v=>{this.result='data:'+b.type+';base64,'+Buffer.from(v).toString('base64');this.onloadend?.();});}};

export const mats={};
for(const [k,color,roughness,metalness] of [
 ['black',0x24272a,.55,.15],['grey',0x8a9093,.5,.2],['metal',0xc9cbc8,.38,.28],['dark',0x3b4144,.5,.3],
 ['white',0xe6e4dc,.6,.05],['red',0xa1342c,.5,.1],['blue',0x39588f,.45,.15],['bluegray',0x5d6c7c,.32,.2],['gold',0xc69a4c,.36,.35],
 ['glass',0x6f97a6,.15,.1],['screen',0x1d3a40,.25,.1],['amber',0xd59b3a,.4,.1],['green',0x3f7a52,.45,.1],['olive',0x6b6a3e,.6,.08],['copper',0xb06b41,.38,.35]]){
 mats[k]=new T.MeshStandardMaterial({name:k,color,roughness,metalness});
}
// Transparent parts (emitter tube, vial, ear-piece, display cover) export as glTF alpha-blended.
Object.assign(mats.glass,{transparent:true,opacity:.42,depthWrite:false});
mats.mesh=new T.MeshStandardMaterial({name:'mesh',color:0x2a2e31,roughness:.6,metalness:.2,transparent:true,opacity:.55,depthWrite:false});
const add=(g,geo,mat,name)=>{const m=new T.Mesh(geo,mats[mat]||mats.grey);m.name=name||mat;g.add(m);return m;};
export function group(name){const g=new T.Group();g.name=name;return g;}
export function box(g,[w,l,h],[x,y,z],mat='grey',name){const m=add(g,new T.BoxGeometry(w,l,h),mat,name);m.position.set(x,y,z);return m;}
// Rounded box via a beveled extrusion of a rounded rectangle in the XY plane, height along Z.
export function rbox(g,[w,l,h],[x,y,z],r=.3,mat='grey',name){
 r=Math.min(r,w/2-.001,l/2-.001);const s=new T.Shape(),a=w/2,b=l/2;
 s.moveTo(-a+r,-b);s.lineTo(a-r,-b);s.quadraticCurveTo(a,-b,a,-b+r);s.lineTo(a,b-r);s.quadraticCurveTo(a,b,a-r,b);s.lineTo(-a+r,b);s.quadraticCurveTo(-a,b,-a,b-r);s.lineTo(-a,-b+r);s.quadraticCurveTo(-a,-b,-a+r,-b);
 const bev=Math.min(r*.5,h*.25);const geo=new T.ExtrudeGeometry(s,{depth:h-2*bev,bevelEnabled:true,bevelThickness:bev,bevelSize:bev*.9,bevelOffset:-bev*.9,bevelSegments:3,curveSegments:6});
 geo.translate(0,0,-(h-2*bev)/2);const m=add(g,geo,mat,name);m.position.set(x,y,z);return m;
}
// Cylinder/cone along an axis. r is the radius at the negative end, r2 at the positive end.
export function cyl(g,r,len,[x,y,z],axis='y',mat='grey',name,r2=r,seg=40){
 const m=add(g,new T.CylinderGeometry(r2,r,len,seg),mat,name);
 if(axis==='z')m.rotation.x=Math.PI/2;if(axis==='x')m.rotation.z=-Math.PI/2;
 m.position.set(x,y,z);return m;
}
export function sphere(g,r,[x,y,z],mat='grey',scale=[1,1,1],name){const m=add(g,new T.SphereGeometry(r,32,18),mat,name);m.position.set(x,y,z);m.scale.set(...scale);return m;}
export function torus(g,r,t,[x,y,z],axis='y',mat='grey',name,arc=Math.PI*2){const m=add(g,new T.TorusGeometry(r,t,10,48,arc),mat,name);if(axis==='y')m.rotation.x=Math.PI/2;if(axis==='x')m.rotation.y=Math.PI/2;m.position.set(x,y,z);return m;}
// Lathe: profile [[radius, position-along-axis], ...] revolved around the axis.
export function lathe(g,profile,[x,y,z],axis='y',mat='grey',name,seg=48){
 const geo=new T.LatheGeometry(profile.map(([r,t])=>new T.Vector2(r,t)),seg);// lathe axis is +Y
 const m=add(g,geo,mat,name);if(axis==='z')m.rotation.x=Math.PI/2;if(axis==='x')m.rotation.z=-Math.PI/2;m.position.set(x,y,z);return m;
}
// Extrude a 2-D side profile. Points are [y, z] (length, height); thickness along X, centred on x.
const PERMUTE=new T.Matrix4().set(0,0,1,0, 1,0,0,0, 0,1,0,0, 0,0,0,1);// shape x->Y, shape y->Z, depth->X
export function sideProfile(g,pts,thick,[x,y,z]=[0,0,0],mat='grey',name,bevel=.15,holes=[]){
 const s=new T.Shape(pts.map(([a,b])=>new T.Vector2(a,b)));for(const h of holes)s.holes.push(new T.Path(h.map(([a,b])=>new T.Vector2(a,b))));
 const bev=Math.min(bevel,thick*.3);const geo=new T.ExtrudeGeometry(s,{depth:thick-2*bev,bevelEnabled:bev>0,bevelThickness:bev,bevelSize:bev,bevelOffset:-bev,bevelSegments:3,curveSegments:16});
 geo.translate(0,0,-(thick-2*bev)/2);geo.applyMatrix4(PERMUTE);geo.computeVertexNormals();
 const m=add(g,geo,mat,name);m.position.set(x,y,z);return m;
}
// Extrude a 2-D plan (top view) outline [x, y]; height along Z from z0.
export function planExtrude(g,pts,h,[x,y,z]=[0,0,0],mat='grey',name,bevel=.15){
 const s=new T.Shape(pts.map(([a,b])=>new T.Vector2(a,b)));const bev=Math.min(bevel,h*.3);
 const geo=new T.ExtrudeGeometry(s,{depth:h-2*bev,bevelEnabled:bev>0,bevelThickness:bev,bevelSize:bev,bevelOffset:-bev,bevelSegments:3,curveSegments:16});geo.translate(0,0,bev);geo.computeVertexNormals();
 const m=add(g,geo,mat,name);m.position.set(x,y,z);return m;
}
// Grille: n parallel slats across a face.
export function slats(g,n,[w,l,h],[x,y,z],axis='y',gap=.5,mat='dark',name='grille'){
 for(let i=0;i<n;i++){const t=(i-(n-1)/2)*gap;box(g,[w,l,h],axis==='y'?[x,y+t,z]:axis==='x'?[x+t,y,z]:[x,y,z+t],mat,name);}
}
export function batch(root){
 root.updateMatrixWorld(true);const buckets=new Map();
 root.traverse(o=>{if(!o.isMesh)return;let geo=o.geometry.index?o.geometry.toNonIndexed():o.geometry.clone();geo.applyMatrix4(o.matrixWorld);for(const k of Object.keys(geo.attributes))if(k!=='position'&&k!=='normal')geo.deleteAttribute(k);if(!geo.getAttribute('normal'))geo.computeVertexNormals();const b=buckets.get(o.material.name)||{geos:[],mat:o.material};b.geos.push(geo);buckets.set(o.material.name,b);});
 const out=new T.Group();out.name=root.name;for(const [k,b] of buckets){const geo=mergeVertices(mergeGeometries(b.geos,false),1e-5);const m=new T.Mesh(geo,b.mat);m.name=k;out.add(m);}return out;
}
export async function exportItem(root,file,outDir){
 const g=batch(root);g.scale.setScalar(.01);g.rotation.x=-Math.PI/2;g.updateMatrixWorld(true);// author Z-up/front −Y → glTF Y-up/front +Z
 const wrap=new T.Group();wrap.name=root.name;wrap.add(g);
 const data=await new GLTFExporter().parseAsync(wrap,{binary:true});fs.writeFileSync(path.join(outDir,file),Buffer.from(data));
 const box=new T.Box3().setFromObject(root);let tris=0;g.traverse(o=>{if(o.isMesh){tris+=(o.geometry.index?o.geometry.index.count:o.geometry.attributes.position.count)/3;for(const v of o.geometry.attributes.position.array)if(!Number.isFinite(v))throw Error('Non-finite vertex in '+file);}});
 const size=box.getSize(new T.Vector3());
 return {file,bytes:data.byteLength,triangles:tris,sizeCm:{width:+size.x.toFixed(2),length:+size.y.toFixed(2),height:+size.z.toFixed(2)}};
}
// Loft: sweep superelliptic cross-sections along Y. stations: [[y, halfWidth, halfHeight, zCentre=0, xCentre=0], ...]
// p = superellipse exponent (2 = ellipse, 3-5 = rounded rectangle). Ends are capped.
export function loft(g,stations,mat='grey',name='shell',p=2.6,seg=48){
 const pos=[],idx=[],n=seg,ring=(st)=>{const [y,hw,hh,zc=0,xc=0]=st;const out=[];for(let i=0;i<n;i++){const a=i/n*Math.PI*2,c=Math.cos(a),s=Math.sin(a);out.push([xc+hw*Math.sign(c)*Math.abs(c)**(2/p),y,zc+hh*Math.sign(s)*Math.abs(s)**(2/p)]);}return out;};
 stations.forEach(st=>pos.push(...ring(st)));
 for(let k=0;k<stations.length-1;k++)for(let i=0;i<n;i++){const a=k*n+i,b=k*n+(i+1)%n,c=(k+1)*n+i,d=(k+1)*n+(i+1)%n;idx.push(a,c,b,b,c,d);}
 const cap=(k,flip)=>{const [y,,,zc=0,xc=0]=stations[k];const ci=pos.length;pos.push([xc,y,zc]);for(let i=0;i<n;i++){const a=k*n+i,b=k*n+(i+1)%n;flip?idx.push(ci,a,b):idx.push(ci,b,a);}};
 cap(0,true);cap(stations.length-1,false);
 const geo=new T.BufferGeometry();geo.setAttribute('position',new T.Float32BufferAttribute(pos.flat(),3));geo.setIndex(idx);geo.computeVertexNormals();
 const m=add(g,geo,mat,name);return m;
}
// Smoothly interpolate a station table at many y positions (Catmull-Rom on each column) for a fair shell.
export function smooth(stations,steps=6){
 const out=[];for(let k=0;k<stations.length-1;k++){const p0=stations[Math.max(0,k-1)],p1=stations[k],p2=stations[k+1],p3=stations[Math.min(stations.length-1,k+2)];
  for(let s=0;s<steps;s++){const t=s/steps,t2=t*t,t3=t2*t;out.push(p1.map((_,j)=>{const a=p0[j]??0,b=p1[j]??0,c=p2[j]??0,d=p3[j]??0;return .5*(2*b+(-a+c)*t+(2*a-5*b+4*c-d)*t2+(-a+3*b-3*c+d)*t3);}));}}
 out.push(stations.at(-1));return out;
}
