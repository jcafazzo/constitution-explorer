import fs from 'node:fs';
import path from 'node:path';
import * as T from '../dist/vendor/three.module.js';
import {STLLoader} from '../dist/vendor/STLLoader.js';
import {FontLoader} from '../dist/vendor/FontLoader.js';
import {TextGeometry} from '../dist/vendor/TextGeometry.js';
import {GLTFExporter} from '../dist/vendor/GLTFExporter.js';
import {mergeGeometries,mergeVertices,toCreasedNormals} from '../dist/vendor/utils/BufferGeometryUtils.js';
const ROOT=process.cwd(),OUT=path.join(ROOT,'dist/assets/detail');
const font=new FontLoader().parse(JSON.parse(fs.readFileSync('model-source/helvetiker_regular.typeface.json','utf8')));
const mats={};
for(const [k,color,roughness,metalness] of [['hull',0xd2d0c4,.64,.08],['panel',0x9faaa9,.65,.14],['seam',0x555e61,.73,.1],['dark',0x202a30,.58,.18],['red',0x833d34,.62,.08],['brass',0xb88b54,.4,.45],['window',0xe9e0ba,.45,.1],['cool',0x466a78,.43,.2]]){mats[k]=new T.MeshStandardMaterial({name:k,color,roughness,metalness});}
const V=(a)=>new T.Vector3(...a);
function mesh(g,geometry,key,name){const o=new T.Mesh(geometry,mats[key]);o.name=name;g.add(o);return o;}
function box(g,size,p,key='hull',name='panel'){const o=mesh(g,new T.BoxGeometry(...size),key,name);o.position.set(...p);return o;}
function sphere(g,r,p,key='hull',scale=[1,1,1],name='housing'){const o=mesh(g,new T.SphereGeometry(r,32,20),key,name);o.position.set(...p);o.scale.set(...scale);return o;}
function cyl(g,r,h,p,key='hull',axis='z',name='cylinder'){const o=mesh(g,new T.CylinderGeometry(r,r,h,64),key,name);if(axis==='z')o.rotation.x=Math.PI/2;else if(axis==='x')o.rotation.z=Math.PI/2;o.position.set(...p);return o;}
function ring(g,r,t,p,key='panel',axis='z',start=0,arc=Math.PI*2,name='collar'){const o=mesh(g,new T.TorusGeometry(r,t,8,96,arc),key,name);if(axis==='y')o.rotation.x=Math.PI/2;o.rotation.z+=start;o.position.set(...p);return o;}
function pipe(g,points,r=.15,key='panel',name='pipe'){const curve=new T.CatmullRomCurve3(points.map(V));return mesh(g,new T.TubeGeometry(curve,Math.max(16,points.length*6),r,6,false),key,name);}
function text(g,words,size,p,key='dark',rotation=[0,0,0],name='registry'){
 const geo=new TextGeometry(words,{font,size,depth:.035,curveSegments:4,bevelEnabled:false});geo.computeBoundingBox();geo.translate(-(geo.boundingBox.max.x+geo.boundingBox.min.x)/2,0,0);const o=mesh(g,geo,key,name);o.position.set(...p);o.rotation.set(...rotation);return o;
}
// Project detail vertices onto the actual dimensioned STL, not a parallel guessed shell.
// Axial 2-D triangle bins make thousands of exact barycentric surface queries practical.
const attachmentChecks=[];
class HullSurface {
 constructor(geometry,label){this.geometry=geometry;this.label=label;this.tables=new Map();this.position=geometry.attributes.position;this.normal=geometry.attributes.normal;this.index=geometry.index;}
 table(axis){
  if(this.tables.has(axis))return this.tables.get(axis);
  const uv=[0,1,2].filter(a=>a!==axis),bins=new Map(),tris=[],p=this.position,n=this.normal,cell=3;
  const get=(i,a)=>p.array[i*3+a],count=this.index?this.index.count:p.count;
  for(let f=0;f<count;f+=3){const ids=[0,1,2].map(j=>this.index?this.index.getX(f+j):f+j),q=ids.map(i=>[get(i,uv[0]),get(i,uv[1]),get(i,axis)]);
   const den=(q[1][1]-q[2][1])*(q[0][0]-q[2][0])+(q[2][0]-q[1][0])*(q[0][1]-q[2][1]);if(Math.abs(den)<1e-10)continue;
   const tri={q,den,ids},id=tris.push(tri)-1;
   const lo=[0,1].map(a=>Math.floor(Math.min(...q.map(v=>v[a]))/cell)),hi=[0,1].map(a=>Math.floor(Math.max(...q.map(v=>v[a]))/cell));
   for(let u=lo[0];u<=hi[0];u++)for(let v=lo[1];v<=hi[1];v++){const key=u+','+v,b=bins.get(key)||[];b.push(id);bins.set(key,b);}
  }
  const table={uv,bins,tris,cell};this.tables.set(axis,table);return table;
 }
 hit(point,axis,sign,range,offset=.025){
  const t=this.table(axis),u=point[t.uv[0]],v=point[t.uv[1]],ids=t.bins.get(Math.floor(u/t.cell)+','+Math.floor(v/t.cell))||[];let best=null,distance=Infinity;
  for(const id of ids){const{q,den,ids:vi}=t.tris[id];const a=((q[1][1]-q[2][1])*(u-q[2][0])+(q[2][0]-q[1][0])*(v-q[2][1]))/den,b=((q[2][1]-q[0][1])*(u-q[2][0])+(q[0][0]-q[2][0])*(v-q[2][1]))/den,c=1-a-b;
   if(Math.min(a,b,c)<-1e-6)continue;const value=a*q[0][2]+b*q[1][2]+c*q[2][2];if(value<range[0]||value>range[1])continue;
   const normal=new T.Vector3();for(let k=0;k<3;k++)normal.addScaledVector(new T.Vector3().fromBufferAttribute(this.normal,vi[k]),[a,b,c][k]);normal.normalize();if(normal.getComponent(axis)*sign<.12)continue;
   const d=Math.abs(value-point[axis]);if(d>=distance)continue;distance=d;const surface=V(point);surface.setComponent(axis,value);best={surface,normal,point:surface.clone().addScaledVector(normal,offset),distance};
  }
  return best;
 }
}
function checkRecord(name,surface,offset){const r={feature:name,surface:surface.label,requestedVertices:0,attachedVertices:0,rejectedVertices:0,triangles:0,maxSurfaceOffset:0,maxSeedCorrection:0,offset};attachmentChecks.push(r);return r;}
function projectGeometry(g,geometry,surface,axis,sign,range,key,name,offset=.025){
 const source=geometry.index?geometry.toNonIndexed():geometry,p=source.attributes.position,record=checkRecord(name,surface,offset),hits=[];
 for(let i=0;i<p.count;i++){const q=[p.getX(i),p.getY(i),p.getZ(i)],config=typeof axis==='function'?axis(q):[axis,sign,range],h=surface.hit(q,...config,offset);record.requestedVertices++;if(h){record.attachedVertices++;record.maxSurfaceOffset=Math.max(record.maxSurfaceOffset,h.point.distanceTo(h.surface));record.maxSeedCorrection=Math.max(record.maxSeedCorrection,h.distance);}else record.rejectedVertices++;hits.push(h);}
 const positions=[],normals=[];for(let i=0;i<hits.length;i+=3){const hs=hits.slice(i,i+3);if(hs.some(h=>!h))continue;
  // The projection may not jump across a hull gap, even if both endpoints hit.
  if(typeof axis!=='function'&&Math.max(...hs.map(h=>h.surface.getComponent(axis)))-Math.min(...hs.map(h=>h.surface.getComponent(axis)))>2.5)continue;
  const cross=new T.Vector3().subVectors(hs[1].point,hs[0].point).cross(new T.Vector3().subVectors(hs[2].point,hs[0].point));if(cross.dot(hs[0].normal)<0)[hs[1],hs[2]]=[hs[2],hs[1]];
  for(const h of hs){positions.push(...h.point.toArray());normals.push(...h.normal.toArray());}record.triangles++;
 }
 if(!positions.length)return null;const geo=new T.BufferGeometry();geo.setAttribute('position',new T.Float32BufferAttribute(positions,3));geo.setAttribute('normal',new T.Float32BufferAttribute(normals,3));const o=mesh(g,geo,key,name);o.userData.attachment={surface:surface.label,offset};return o;
}
function patch(g,surface,center,u,v,width,height,axis,sign,range,key,name,offset=.025){
 const geo=new T.PlaneGeometry(width,height,Math.max(2,Math.ceil(width/.65)),Math.max(2,Math.ceil(height/.65))),p=geo.attributes.position;
 for(let i=0;i<p.count;i++){const q=V(center).addScaledVector(V(u),p.getX(i)).addScaledVector(V(v),p.getY(i));p.setXYZ(i,...q.toArray());}return projectGeometry(g,geo,surface,axis,sign,range,key,name,offset);
}
function projectLine(g,surface,points,axis,sign,range,r,key,name){
 const hits=points.map(p=>surface.hit(p,axis,sign,range,.015)),record=checkRecord(name,surface,.015);record.requestedVertices=hits.length;record.attachedVertices=hits.filter(Boolean).length;record.rejectedVertices=hits.filter(h=>!h).length;record.maxSurfaceOffset=.015;
 // Split at unsupported points; no tube may bridge an unsupported span.
 let run=[];const emit=()=>{if(run.length>1){const curve=new T.CatmullRomCurve3(run.map(V)),segments=Math.max(24,run.length*2);mesh(g,new T.TubeGeometry(curve,segments,r,6,false),key,name);record.triangles+=segments*12;}run=[];};
 for(const h of hits){if(h){record.maxSeedCorrection=Math.max(record.maxSeedCorrection,h.distance);run.push(h.point.toArray());}else emit();}emit();
}
function curvedPanel(g,r,a,b,angle,width,key,name){
 const origin=g.userData.origin||[0,0,0],surface=g.userData.surface,arc=width/r,verts=[],indices=[],steps=Math.max(4,Math.ceil(width/.55)),rows=Math.max(1,Math.ceil(Math.abs(b-a)/1.1));
 for(let j=0;j<=rows;j++)for(let i=0;i<=steps;i++){const t=angle-arc/2+i*arc/steps;verts.push(r*Math.cos(t)+origin[0],a+(b-a)*j/rows+origin[1],r*Math.sin(t)+origin[2]);}
 for(let j=0;j<rows;j++)for(let i=0;i<steps;i++){const k=j*(steps+1)+i,l=k+steps+1;indices.push(k,l,k+1,l,l+1,k+1);}
 const geo=new T.BufferGeometry();geo.setAttribute('position',new T.Float32BufferAttribute(verts,3));geo.setIndex(indices);
 if(!surface){geo.computeVertexNormals();return mesh(g,geo,key,name);}
 const axis=Math.abs(Math.cos(angle))>.7?0:2,sign=(axis===0?Math.cos(angle):Math.sin(angle))>0?1:-1,range=sign>0?[origin[axis]+6.0,origin[axis]+9.1]:[origin[axis]-9.1,origin[axis]-6.0];
 const offset=name.includes('rib')?.055:name.includes('border')?.065:name.includes('channel')?.018:.035;
 const radial=q=>{const a=Math.abs(q[0]-origin[0])>Math.abs(q[2]-origin[2])?0:2,sgn=q[a]>origin[a]?1:-1;return[a,sgn,sgn>0?[origin[a]+.01,origin[a]+9.1]:[origin[a]-9.1,origin[a]-.01]];};
 const o=projectGeometry(g,geo,surface,name.includes('cowl')?radial:axis,sign,range,key,name,offset);if(o)o.position.set(-origin[0],-origin[1],-origin[2]);return o;
}
function subdivideFlat(geometry,maxEdge=.7){
 const g=geometry.index?geometry.toNonIndexed():geometry,p=g.attributes.position,verts=[];
 function tri(a,b,c,depth=0){const sides=[a.distanceTo(b),b.distanceTo(c),c.distanceTo(a)],m=Math.max(...sides);if(m<=maxEdge||depth>10){verts.push(...a.toArray(),...b.toArray(),...c.toArray());return;}const i=sides.indexOf(m);if(i===0){const q=a.clone().add(b).multiplyScalar(.5);tri(a,q,c,depth+1);tri(q,b,c,depth+1);}else if(i===1){const q=b.clone().add(c).multiplyScalar(.5);tri(a,b,q,depth+1);tri(a,q,c,depth+1);}else{const q=c.clone().add(a).multiplyScalar(.5);tri(a,b,q,depth+1);tri(q,b,c,depth+1);}}
 for(let i=0;i<p.count;i+=3)tri(new T.Vector3().fromBufferAttribute(p,i),new T.Vector3().fromBufferAttribute(p,i+1),new T.Vector3().fromBufferAttribute(p,i+2));const out=new T.BufferGeometry();out.setAttribute('position',new T.Float32BufferAttribute(verts,3));return out;
}
function nacelleRegistry(g,registry,side){
 const origin=g.userData.origin,surface=g.userData.surface,geo=subdivideFlat(new T.ShapeGeometry(font.generateShapes(registry,2.05),5)),p=geo.attributes.position;geo.computeBoundingBox();const mid=(geo.boundingBox.max.x+geo.boundingBox.min.x)/2;
 // Explicit right/up/normal bases: +X face reads along +Y; -X along -Y.
 // Both use +Z for letter-up. There is no mirrored scale or Euler ambiguity.
 for(let i=0;i<p.count;i++){const x=p.getX(i),y=p.getY(i);p.setXYZ(i,origin[0]+side*8.3,origin[1]+77+side*(x-mid),origin[2]-.78+y);}
 const range=side>0?[origin[0]+7,origin[0]+9]:[origin[0]-9,origin[0]-7];const o=projectGeometry(g,geo,surface,0,side,range,'dark','Outboard nacelle registry '+(side>0?'starboard':'port'),.045);if(o)o.position.set(...origin.map(x=>-x));
 const ns=o.geometry.attributes.normal;let minimumOutwardNormal=1;for(let i=0;i<ns.count;i++)minimumOutwardNormal=Math.min(minimumOutwardNormal,ns.getX(i)*side);if(minimumOutwardNormal<.95)throw Error('Registry does not face outward');
 attachmentChecks.push({feature:'Registry orientation',surface:surface.label,text:registry,side,minimumOutwardNormal,baseline:[0,side,0],up:[0,0,1],outward:[side,0,0],rightHanded:V([0,side,0]).cross(V([0,0,1])).dot(V([side,0,0]))===1});
}
function nacelle(start,x,z,side,registry,scout=false,standalone=false,surface=null){
 const g=new T.Group();g.name='Main propulsion — plate 03:11:20 / PDF 144';g.position.set(x,start,z);
 if(standalone){
  const profile=[];for(let n=0;n<=16;n++){const t=n*Math.PI/32;profile.push(new T.Vector2(8.65*Math.sin(t),8.65*(1-Math.cos(t))));}
  for(const [r,y] of [[8.65,12],[8.2,15],[8.2,111],[8.65,115],[8.65,137],[7.6,146]])profile.push(new T.Vector2(r,y));
  for(let n=1;n<=16;n++){const t=n*Math.PI/32;profile.push(new T.Vector2(7.6*Math.cos(t),146+7.6*Math.sin(t)));}profile.at(-1).set(0,153.6);
  const body=new T.LatheGeometry(profile,128);body.computeVertexNormals();mesh(g,body,'hull','Continuous dimensioned propulsion housing');surface=new HullSurface(body,'nacelle');
 }
 g.userData.surface=surface;g.userData.origin=[x,start,z];
 const radiusAt=y=>{const h=surface.hit([x+8.65,start+y,z],0,1,[x+0.01,x+9],0);return h?h.surface.x-x:7.6;};
 // Visible geometry follows the external arrangement: three first-stage, five main-stage banks.
 const dome=mesh(g,new T.SphereGeometry(8.69,48,24,0,Math.PI*2,0,Math.PI/2),'red','Acquisition dome');dome.rotation.z=Math.PI;dome.position.set(0,8.65,0);
 for(const y of [9.4,10.1,10.8,11.5,12.4])ring(g,radiusAt(y),.11,[0,y,0],'panel','y');
 for(const theta of [0,Math.PI*2/3,Math.PI*4/3])sphere(g,.56,[8.8*Math.cos(theta),9.9,8.8*Math.sin(theta)],'brass',[1,.7,1],'Three field sensors at 120 degrees');
 const inner=scout?-Math.PI/2:side<0?0:Math.PI,outer=inner+Math.PI;
 curvedPanel(g,8.68,25,131,inner,5.0,'dark','Long inset flux chiller channel');
 for(const [a,b,label]of [[25,34,'Power-stage chiller 1'],[35,44,'Power-stage chiller 2'],[45,54,'Power-stage chiller 3'],[60,73,'Main-stage chiller 1'],[74,87,'Main-stage chiller 2'],[88,101,'Main-stage chiller 3'],[102,115,'Main-stage chiller 4'],[116,129,'Main-stage chiller 5']]){
  curvedPanel(g,8.75,a,b,inner,4.0,'panel',label);
  for(let y=a+.5;y<b;y+=.65)curvedPanel(g,8.81,y,y+.16,inner,3.5,'dark',label+' rib');
  for(const ang of [inner-.26,inner+.26])curvedPanel(g,8.5,a,b,ang,.14,'panel','Chiller border');
 }
 const normal=[Math.cos(outer),0,Math.sin(outer)];
 const block=box(g,[2.8,5.8,3.7],[normal[0]*8.3,16,normal[2]*8.3],'panel','First-stage flux constriction housing');block.rotation.y=-outer;
 for(const a of [inner,outer]){
  curvedPanel(g,8.72,133,143,a,3.4,'dark','Final-stage flux chiller');
  for(let y=133.5;y<143;y+=.7)curvedPanel(g,8.8,y,y+.2,a,3.0,'panel','Final chiller rib');
  // External U-shaped intercoolers are raised geometry, not painted stripes.
  const q=(y,r)=>[r*Math.cos(a),y,r*Math.sin(a)];
  pipe(g,[q(114,radiusAt(114)-.1),q(114,10.0),q(118,10.6),q(140,10.6),q(144,10),q(144,radiusAt(144)-.1)],.40,'panel','U-shaped final-stage intercooler');
 }
 for(const y of [144.5,145.3,146.1])ring(g,radiusAt(y),.12,[0,y,0],'panel','y');
 // A partial cowl wraps the aft cap; source gives an asymmetric silhouette.
 curvedPanel(g,8.5,143.5,150,Math.PI/2,Math.PI*8.5,'hull','Half-wrap restoration cowl');
 const registrySides=scout?[1,-1]:[side];
 for(const sign of registrySides){const a=sign>0?0:Math.PI;
  // Separate stripe lengths reserve a clean registry field without painting over equipment.
  curvedPanel(g,8.3,27,61,a,1.25,'dark','Nacelle pennant forward');
  curvedPanel(g,8.3,93,105,a,1.25,'dark','Nacelle pennant aft');
  nacelleRegistry(g,registry,sign);
 }
 return g;
}
function saucerDetails(g,s,cy,cz,bulge=1){
 const surface=g.userData.surface,radius=s.width/2,scale=radius/63.55,topRange=[cz+16.8,cz+32.1];
 const topSeed=r=>{const rs=[0,18,25,45,59,63.55],zs=[23.4,23.4,22.1,19.6,17.8,17.2];let i=1;while(i<rs.length-1&&r/scale>rs[i])i++;const q=(r/scale-rs[i-1])/(rs[i]-rs[i-1]);return (zs[i-1]+q*(zs[i]-zs[i-1])-17)*bulge+17+cz;};
 if(s.id==='constitution'){
  for(const r0 of [20,27,34,41,48,55,61]){const r=r0*scale,pts=[];for(let n=0;n<=192;n++){const a=n*Math.PI/96;pts.push([r*Math.sin(a),cy-r*Math.cos(a),topSeed(r)]);}projectLine(g,surface,pts,2,1,topRange,.055,'seam','Saucer concentric panel seam');}
  for(let a=0;a<Math.PI*2;a+=Math.PI/12){const pts=[];for(let r=20*scale;r<=radius-.5;r+=1.2)pts.push([r*Math.sin(a),cy-r*Math.cos(a),topSeed(r)]);projectLine(g,surface,pts,2,1,topRange,.055,'seam','Radial saucer division');}
 }
 function rimPatch(a,r,z,w,h,key,name){const p=[r*Math.sin(a),cy-r*Math.cos(a),z],axis=Math.abs(Math.sin(a))>.707?0:1,sign=(axis===0?Math.sin(a):-Math.cos(a))>0?1:-1;return patch(g,surface,p,[Math.cos(a),Math.sin(a),0],[0,0,1],w,h,axis,sign,[p[axis]-1.5,p[axis]+1.5],key,name);}
 for(let n=0;n<96;n++)if(n%8<5){const a=n*Math.PI*2/96;rimPatch(a,radius-.2,cz+14,1.35,.52,n%5?'dark':'window','Saucer rim cabin window');}
 for(const sign of [-1,1])for(let i=0;i<8;i++){const a=sign*(.65+i*.065);rimPatch(a,s.id==='federation'?14.2:17.1,cz+(s.id==='federation'?28:25.15),.85,.55,'dark','Bridge module window');}
 const cap=surface.hit([0,cy,cz+31.8],2,1,[cz+29,cz+32.2],0);if(cap)cyl(g,1.3,.3,[0,cy,cap.surface.z+.1],'panel','z','Bridge upper sensor');
 for(const a of [0,Math.PI/2,Math.PI*1.5])for(const offset of [-.85,.85]){const r=34*scale,p=[r*Math.sin(a)+offset*Math.cos(a),cy-r*Math.cos(a)+offset*Math.sin(a),topSeed(r)],hit=surface.hit(p,2,1,topRange,.02);if(hit)sphere(g,.7,hit.point.toArray(),'brass',[1,1,.45],'Paired phaser emitters');}
 for(const a of [Math.PI/4,Math.PI*3/4,Math.PI*5/4,Math.PI*7/4]){const r=53*scale;patch(g,surface,[r*Math.sin(a),cy-r*Math.cos(a),topSeed(r)],[Math.cos(a),Math.sin(a),0],[-Math.sin(a),Math.cos(a),0],1.6,2.4,2,1,topRange,'panel','Rim service access hatch');}
 function hullText(words,size,p,angle=0){const geo=subdivideFlat(new T.ShapeGeometry(font.generateShapes(words,size),5));geo.computeBoundingBox();geo.translate(-(geo.boundingBox.max.x+geo.boundingBox.min.x)/2,0,0);geo.rotateZ(angle);geo.translate(...p);return projectGeometry(g,geo,surface,2,1,topRange,'dark','Saucer registry',.035);}
 for(const[i,ch]of[...s.registry].entries()){const a=(i-(s.registry.length-1)/2)*.104,r=51.3*scale;hullText(ch,5.2*scale,[r*Math.sin(a),cy-r*Math.cos(a),topSeed(r)],a);}
 hullText('U.S.S. '+s.name.toUpperCase(),1.7,[0,cy-38*scale,topSeed(38*scale)]);
 // Exhaust and cooling detail use the existing impulse housing faces.
 const aft=cy+66*scale;patch(g,surface,[0,aft,cz+15],[1,0,0],[0,0,1],27.6,3.4,1,1,[aft-2,aft+1],'dark','Impulse exhaust housing');
 for(const x of [-7,7]){patch(g,surface,[x,aft,cz+15],[1,0,0],[0,0,1],11.2,2.3,1,1,[aft-2,aft+1],'red','Impulse exhaust',.04);for(let n=0;n<10;n++)patch(g,surface,[x-5+n*1.1,aft,cz+15],[1,0,0],[0,0,1],.35,2.6,1,1,[aft-2,aft+1],'panel','Impulse exhaust louvre',.06);}
 for(let x=-12;x<=12;x+=1.8)patch(g,surface,[x,cy+62*scale,cz+17],[1,0,0],[0,1,0],.35,5.5,2,1,[cz+16.8,cz+18.2],'panel','Impulse upper cooling fin');
 for(const r of [4,6,10,15,20]){const pts=[];for(let n=0;n<=128;n++){const a=n*Math.PI/64;pts.push([r*Math.sin(a),cy-r*Math.cos(a),cz+Math.max(.5,(r-5)*.45)]);}projectLine(g,surface,pts,2,-1,[cz-10,cz+12.6],.07,'panel','Ventral sensor ring');}
 for(let i=0;i<8;i++)for(const sign of[-1,1])patch(g,surface,[sign*(4+i*.75),cy-11,cz+3.3],[1,0,0],[0,1,0],.5,.5,2,-1,[cz-10,cz+10],'dark','Lower sensor array port');
}
function engineering(g,s,center,y0,z0,federation=false){
 const surface=g.userData.surface,ys=federation?[68,88,108,128,148,162]:[-20,-5,10,25,40,50];
 for(const sign of[-1,1]){
  const hullRange=sign>0?[6,18]:[-18,-6];
  for(const y of ys)for(const dz of[-3,0,3])for(let k=0;k<3;k++)patch(g,surface,[sign*15,y-center[1]+k*2.4,z0+dz],[0,sign,0],[0,0,1],1.4,.62,0,sign,hullRange,'dark','Engineering hull window');
  patch(g,surface,[sign*16,y0,z0-1.5],[0,sign,0],[0,0,1],34,1.3,0,sign,hullRange,'red','Engineering pennant');
  // A narrow axial band admits only the neck face, never the hull behind a gap.
  const neckRange=sign>0?[2.8,3.7]:[-3.7,-2.8];
  for(let row=0;row<3;row++)for(let k=0;k<7;k++)patch(g,surface,[sign*3.5,(federation?63:-24)-center[1]-row*6+k*3.8,(federation?3:4)-row*3-center[2]],[0,sign,0],[0,0,1],1.5,.5,0,sign,neckRange,'dark','Neck cabin window');
 }
 const dishY=federation?52-center[1]:-44.8,rad=federation?7.5:12;
 for(let r=2;r<=rad;r+=2){const pts=[];for(let n=0;n<=128;n++){const a=n*Math.PI/64;pts.push([r*Math.cos(a),dishY,z0+r*Math.sin(a)]);}projectLine(g,surface,pts,1,-1,[dishY-3,dishY+5],.12,'brass','Deflector concentric ridge');}
 const centerHit=surface.hit([0,dishY,z0],1,-1,[dishY-3,dishY+5],0);if(centerHit)sphere(g,.8,centerHit.point.toArray(),'brass');
 const endY=federation?176-center[1]:69.6;
 for(let i=0;i<6;i++){const shape=new T.Shape(),a=i*Math.PI/6,b=(i+1)*Math.PI/6;shape.moveTo(0,0);shape.absarc(0,0,5.4,a,b,false);shape.lineTo(0,0);const geo=subdivideFlat(new T.ShapeGeometry(shape,12));geo.rotateX(Math.PI/2);geo.translate(0,endY,z0-2.5);projectGeometry(g,geo,surface,1,1,[endY-3,endY+2],i%2?'hull':'panel','Hangar clamshell segment '+(i+1));}
 patch(g,surface,[0,endY,z0+3.2],[1,0,0],[0,0,1],8,.3,1,1,[endY-3,endY+2],'dark','Hangar observation window strip');
 const beacon=surface.hit([0,endY,z0+4.1],1,1,[endY-3,endY+2],.05);if(beacon)sphere(g,.4,beacon.point.toArray(),'red',[1,1,1],'Hangar homing beacon');
}
function pylonGrilles(g,surface,root,tip,frontY,name){
 const along=V(tip).sub(V(root)).normalize(),across=new T.Vector3(-along.z,0,along.x);for(const t of [.36,.53,.70,.87]){
  const center=V(root).lerp(V(tip),t);center.y=frontY;const range=[frontY-.5,frontY+.6];
  patch(g,surface,center.toArray(),across.toArray(),along.toArray(),2.45,4.5,1,-1,range,'dark',name);
  for(let k=-2;k<=2;k++){const p=center.clone().addScaledVector(across,k*.43);patch(g,surface,p.toArray(),across.toArray(),along.toArray(),.19,4.0,1,-1,range,'panel',name+' rib',.045);}
 }
}
export function batch(root){root.updateMatrixWorld(true);const buckets=new Map();root.traverse(o=>{if(o.isMesh){let geo=o.geometry.index?o.geometry.toNonIndexed():o.geometry.clone();geo.applyMatrix4(o.matrixWorld);if(!geo.getAttribute('normal'))geo.computeVertexNormals();geo.deleteAttribute('uv');geo.deleteAttribute('color');const k=o.material.uuid;const b=buckets.get(k)||{geos:[],mat:o.material};b.geos.push(geo);buckets.set(k,b);}});const group=new T.Group();group.name=root.name;for(const[k,b]of buckets){const geo=mergeVertices(mergeGeometries(b.geos,false),.00001);const o=new T.Mesh(geo,b.mat);o.name=(b.mat.name||'Material')+' surface details';group.add(o);}return group;}
export function buildNacelleStudy(){const before=attachmentChecks.length,group=batch(nacelle(0,0,0,-1,'NCC-1700',false,true));group.userData.validation=summarizeChecks(attachmentChecks.slice(before));group.name='Main propulsion external arrangement — PDF 144';return{group,length:153.619,sourcePages:[144],description:'Three sensor nodes at 120°, eight ribbed chiller banks, constriction housing, raised intercooler loops and asymmetric restoration cowl.'};}
function buildExterior(s){
 const before=attachmentChecks.length;const root=new T.Group();root.name=s.name+' — detailed manual reconstruction';
 const parseFile=file=>{const data=fs.readFileSync(file);return new STLLoader().parse(data.buffer.slice(data.byteOffset,data.byteOffset+data.byteLength));};let geo=s.id==='constitution'?parseFile('model-source/constitution-base.stl'):parseFile(path.join(ROOT,'dist',s.model));
 geo.deleteAttribute('normal');geo=mergeVertices(geo,.0001);geo=toCreasedNormals(geo,Math.PI/5);const base=mesh(root,geo,'hull','Original dimensioned hull');const surface=new HullSurface(geo,s.id);root.userData.surface=surface;
 const center=s.id==='constitution'?[0,0,0]:s.id==='ptolemy'?[0,47.45,-1.2]:s.id==='federation'?[0,90,-3.05]:[0,57.7,1.8];
 const cy=s.id==='constitution'?-80.75:-center[1],cz=-center[2];saucerDetails(root,s,cy,cz,s.id==='federation'?1.5:1);
 if(s.id==='constitution'){
  for(const sign of[-1,1]){root.add(nacelle(-9.3,sign*46.1,27.65,sign,s.registry,false,false,surface));pylonGrilles(root,surface,[sign*10,31,-14],[sign*46.1,31,21],25.75,'Pylon grille');}
  engineering(root,s,center,0,-19.25);
 }else if(s.id==='saladin'||s.id==='hermes'){
  root.add(nacelle(25.35-center[1],0,-19.55-center[2],1,s.registry,true,false,surface));
  for(const sign of[-1,1])for(let row=0;row<3;row++)for(let n=0;n<8;n++)patch(root,surface,[sign*2.5,28-center[1]+n*3+row*8,7-center[2]-row*6],[0,sign,0],[0,0,1],1.4,.55,0,sign,sign>0?[2.35,2.7]:[-2.7,-2.35],'dark','Neck window');
  // The unarmed scout does not acquire the destroyer's torpedo tubes.
  if(s.id==='saladin')for(const x of[-2.8,2.8]){cyl(root,.85,.3,[x,cy-17.1,cz+26],'dark','y','Forward torpedo aperture');ring(root,.92,.12,[x,cy-17.3,cz+26],'brass','y');}
 }else if(s.id==='ptolemy'){
  for(const sign of[-1,1]){root.add(nacelle(4.85-center[1],sign*46.1,-25.55-center[2],sign,s.registry,false,false,surface));pylonGrilles(root,surface,[sign*23,45-center[1],12-center[2]],[sign*46.1,45-center[1],-20-center[2]],38-center[1],'Tug pylon access grille');}
  const y=74-center[1],z=-9.55-center[2];box(root,[24,27,.25],[0,y,z],'dark','Cargo coupling pad');for(const x of[-9,9])for(const dy of[-10,10])cyl(root,1.2,.6,[x,y+dy,z-.3],'brass','z','Tow-pad attachment lock');
  for(let i=0;i<7;i++)box(root,[19,.4,.5],[0,y-10+i*3,z-.2],'panel','Tow coupling rib');
 }else{
  for(const sign of[-1,1])root.add(nacelle(96.4-center[1],sign*53,6-center[2],sign,s.registry,false,false,surface));root.add(nacelle(30-center[1],0,31.8-center[2],1,s.registry,true,false,surface));engineering(root,s,center,80-center[1],-31.55-center[2],true);
 }
 const group=batch(root);group.userData.validation=summarizeChecks(attachmentChecks.slice(before));return group;
}
function summarizeChecks(checks){
 const features={};for(const c of checks){if(c.feature==='Registry orientation')continue;const r=features[c.feature]||{objects:0,vertices:0,attached:0,rejected:0,triangles:0,maxSurfaceOffset:0,maxSeedCorrection:0};r.objects++;r.vertices+=c.requestedVertices;r.attached+=c.attachedVertices;r.rejected+=c.rejectedVertices;r.triangles+=c.triangles;r.maxSurfaceOffset=Math.max(r.maxSurfaceOffset,c.maxSurfaceOffset);r.maxSeedCorrection=Math.max(r.maxSeedCorrection,c.maxSeedCorrection);features[c.feature]=r;}
 const orientation=checks.filter(c=>c.feature==='Registry orientation');if(orientation.some(c=>!c.rightHanded))throw Error('Registry orientation is not right-handed');
 for(const [name,v]of Object.entries(features)){if(name.includes('Outboard nacelle registry')&&v.rejected)throw Error('Unsupported nacelle text: '+name);if(v.maxSurfaceOffset>.071)throw Error('Excess surface offset: '+name);}
 return{method:'Exact barycentric projection onto intended STL face; bounded axial region prevents cross-hull attachment; unsupported triangles omitted. Surface offsets are in source metres.',normalMethod:'36 degree crease-aware vertex normals; original STL face-normal splits removed before smoothing.',features,registryOrientation:orientation};
}
// GLTFExporter uses FileReader for binary packing; this Node shim never touches browser state.
globalThis.FileReader=class{readAsArrayBuffer(b){b.arrayBuffer().then(v=>{this.result=v;this.onloadend?.();});}readAsDataURL(b){b.arrayBuffer().then(v=>{this.result='data:'+b.type+';base64,'+Buffer.from(v).toString('base64');this.onloadend?.();});}};
export async function exportStudy(group,file){const data=await new GLTFExporter().parseAsync(group,{binary:true,onlyVisible:true});fs.writeFileSync(path.join(OUT,file),Buffer.from(data));const box=new T.Box3().setFromObject(group);let vertices=0,triangles=0,meshes=0;group.traverse(o=>{if(o.isMesh){meshes++;vertices+=o.geometry.attributes.position.count;triangles+=(o.geometry.index?o.geometry.index.count:o.geometry.attributes.position.count)/3;for(const v of o.geometry.attributes.position.array)if(!Number.isFinite(v))throw Error('Nonfinite vertex');}});return{file,bytes:data.byteLength,meshes,vertices,triangles,bounds:[box.min.toArray(),box.max.toArray()],surfaceValidation:group.userData.validation||null};}
const first={id:'constitution',name:'Constitution',registry:'NCC-1700',length:288.6,width:127.1,height:72.6,model:'assets/constitution.stl'};
if(process.argv[1]===new URL(import.meta.url).pathname){const report=[];for(const s of[first,...JSON.parse(fs.readFileSync('dist/assets/fleet/ships.json'))]){report.push(await exportStudy(buildExterior(s),s.id+'.glb'));console.log(JSON.stringify(report.at(-1)));}report.push(await exportStudy(buildNacelleStudy().group,'nacelle.glb'));fs.writeFileSync('model-source/exterior-validation.json',JSON.stringify(report,null,2));}
