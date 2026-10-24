import fs from 'node:fs';
import path from 'node:path';
import * as T from '../dist/vendor/three.module.js';
import {STLLoader} from '../dist/vendor/STLLoader.js';
import {FontLoader} from '../dist/vendor/FontLoader.js';
import {TextGeometry} from '../dist/vendor/TextGeometry.js';
import {GLTFExporter} from '../dist/vendor/GLTFExporter.js';
import {mergeGeometries,mergeVertices} from '../dist/vendor/utils/BufferGeometryUtils.js';
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
function curvedPanel(g,r,a,b,angle,width,key,name){
 const arc=width/r,verts=[],indices=[],steps=8;
 for(let j=0;j<=1;j++)for(let i=0;i<=steps;i++){const t=angle-arc/2+i*arc/steps;verts.push(r*Math.cos(t),j?b:a,r*Math.sin(t));}
 for(let i=0;i<steps;i++){const j=i+steps+1;indices.push(i,j,i+1,j,j+1,i+1);}
 const geo=new T.BufferGeometry();geo.setAttribute('position',new T.Float32BufferAttribute(verts,3));geo.setIndex(indices);geo.computeVertexNormals();const o=mesh(g,geo,key,name);return o;
}
function nacelle(start,x,z,side,registry,scout=false,standalone=false){
 const g=new T.Group();g.name='Main propulsion — plate 03:11:20 / PDF 144';g.position.set(x,start,z);
 if(standalone){cyl(g,8.2,133,[0,77,0],'hull','y','Propulsion housing');sphere(g,8.65,[0,8.65,0],'red',[1,1,1],'Matter acquisition dome');sphere(g,7.6,[0,146,0],'panel',[1,1,1],'Field restoration cap');}
 // Visible geometry follows the external arrangement: three first-stage, five main-stage banks.
 const dome=mesh(g,new T.SphereGeometry(8.69,48,24,0,Math.PI*2,0,Math.PI/2),'red','Acquisition dome');dome.rotation.z=Math.PI;dome.position.set(0,8.65,0);
 for(const y of [9.4,10.1,10.8,11.5,12.4])ring(g,8.6,.16,[0,y,0],'panel','y');
 for(const theta of [0,Math.PI*2/3,Math.PI*4/3])sphere(g,.56,[8.8*Math.cos(theta),9.9,8.8*Math.sin(theta)],'brass',[1,.7,1],'Three field sensors at 120 degrees');
 const inner=scout?-Math.PI/2:side<0?0:Math.PI,outer=inner+Math.PI;
 curvedPanel(g,8.68,25,131,inner,5.0,'dark','Long inset flux chiller channel');
 for(const [a,b,label]of [[25,34,'Power-stage chiller 1'],[35,44,'Power-stage chiller 2'],[45,54,'Power-stage chiller 3'],[60,73,'Main-stage chiller 1'],[74,87,'Main-stage chiller 2'],[88,101,'Main-stage chiller 3'],[102,115,'Main-stage chiller 4'],[116,129,'Main-stage chiller 5']]){
  curvedPanel(g,8.75,a,b,inner,4.0,'panel',label);
  for(let y=a+.5;y<b;y+=.65)curvedPanel(g,8.81,y,y+.16,inner,3.5,'dark',label+' rib');
  for(const ang of [inner-.26,inner+.26])pipe(g,[[8.82*Math.cos(ang),a,8.82*Math.sin(ang)],[8.82*Math.cos(ang),b,8.82*Math.sin(ang)]],.1,'panel','Chiller border');
 }
 const normal=[Math.cos(outer),0,Math.sin(outer)];
 const block=box(g,[2.8,5.8,3.7],[normal[0]*8.3,16,normal[2]*8.3],'panel','First-stage flux constriction housing');block.rotation.y=-outer;
 for(const a of [inner,outer]){
  curvedPanel(g,8.72,133,143,a,3.4,'dark','Final-stage flux chiller');
  for(let y=133.5;y<143;y+=.7)curvedPanel(g,8.8,y,y+.2,a,3.0,'panel','Final chiller rib');
  // External U-shaped intercoolers are raised geometry, not painted stripes.
  const q=(y,r)=>[r*Math.cos(a),y,r*Math.sin(a)];
  pipe(g,[q(114,8.25),q(114,10.0),q(118,10.6),q(140,10.6),q(144,10),q(144,8)],.48,'panel','U-shaped final-stage intercooler');
 }
 for(const y of [144.5,145.3,146.1])ring(g,7.8,.19,[0,y,0],'panel','y');
 // A partial cowl wraps the aft cap; source gives an asymmetric silhouette.
 curvedPanel(g,8.5,143.5,150,Math.PI/2,Math.PI*8.5,'hull','Half-wrap restoration cowl');
 for(const a of [0,Math.PI]){
  curvedPanel(g,8.24,27,105,a,1.7,'dark','Nacelle pennant stripe');
  curvedPanel(g,8.30,64,90,a,2.5,'hull','Registry clear field');
  const tx=text(g,registry,2.0,[a===0?8.37:-8.37,77,-.8],'dark',[Math.PI/2,Math.PI/2,a===0?0:Math.PI],'Nacelle registry');
 }
 return g;
}
function saucerDetails(g,s,cy,cz,bulge=1){
 const radius=s.width/2,scale=radius/63.55;
 const top=r=>{const rs=[0,18,25,45,59,63.55],zs=[23.4,23.4,22.1,19.6,17.8,17.2];let i=1;while(i<rs.length-1&&r/scale>rs[i])i++;const q=(r/scale-rs[i-1])/(rs[i]-rs[i-1]);return ((zs[i-1]+q*(zs[i]-zs[i-1]))-17)*bulge+17+cz;};
 // Fine dark engraved rings and radial divisions retain the manual's panel layout.
 if(s.id==='constitution'){for(const r0 of [20,27,34,41,48,55,61])ring(g,r0*scale,.07,[0,cy,top(r0*scale)+.16],'seam');
 for(let a=0;a<Math.PI*2;a+=Math.PI/12){
  const points=[];for(let r=20*scale;r<=radius-.5;r+=1.8)points.push([r*Math.sin(a),cy-r*Math.cos(a),top(r)+.16]);pipe(g,points,.07,'seam','Radial saucer division');
 }
 }
 ring(g,radius-.22,.16,[0,cy,cz+12.6],'panel');ring(g,radius-.3,.07,[0,cy,cz+16.1],'dark');
 // Rim cabin windows, grouped rather than an unbroken decorative ring.
 for(let n=0;n<96;n++)if(n%8<5){const a=n*Math.PI*2/96,r=radius-.05;const win=box(g,[1.35,.10,.52],[r*Math.sin(a),cy-r*Math.cos(a),cz+14.0],n%5?'dark':'window','Saucer rim cabin window');win.rotation.z=a;}
 for(const sign of [-1,1])for(let i=0;i<8;i++){const a=(sign<0?-1:1)*(.65+i*.065);const r=17.1;const o=box(g,[.85,.14,.55],[r*Math.sin(a),cy-r*Math.cos(a),cz+25.15],'dark','Bridge module window');o.rotation.z=a;}
 ring(g,5.85,.16,[0,cy,cz+30.35],'panel');cyl(g,1.3,.4,[0,cy,cz+31.8],'panel','z','Bridge upper sensor');
 for(const a of [0,Math.PI/2,Math.PI*1.5])for(const offset of [-.85,.85]){const r=34*scale;sphere(g,.7,[r*Math.sin(a)+offset*Math.cos(a),cy-r*Math.cos(a)+offset*Math.sin(a),top(r)+.2],'brass',[1,1,.45],'Paired phaser emitters');}
 for(const a of [Math.PI/4,Math.PI*3/4,Math.PI*5/4,Math.PI*7/4]){const r=53*scale;const o=box(g,[1.6,2.4,.16],[r*Math.sin(a),cy-r*Math.cos(a),top(r)+.05],'panel','Rim service access hatch');o.rotation.z=a;}
 function conform(o){const pos=o.geometry.attributes.position,c=Math.cos(o.rotation.z),sn=Math.sin(o.rotation.z);for(let i=0;i<pos.count;i++){const x=pos.getX(i),y=pos.getY(i),r=Math.hypot(x*c-y*sn+o.position.x,x*sn+y*c+o.position.y-cy);pos.setZ(i,top(r)+.12+pos.getZ(i));}o.geometry.computeVertexNormals();}
 for(const [i,ch] of [...s.registry].entries()){const a=(i-(s.registry.length-1)/2)*.104,r=51.3*scale;conform(text(g,ch,5.2*scale,[r*Math.sin(a),cy-r*Math.cos(a),0],'dark',[0,0,a]));}
 conform(text(g,'U.S.S. '+s.name.toUpperCase(),1.7,[0,cy-38*scale,0],'dark'));
 // Impulse unit: source p143. Paired exhaust recesses and transverse cooling ribs.
 box(g,[28,1.0,3.5],[0,cy+65.4*scale,cz+14.9],'dark','Impulse exhaust housing');
 for(const x of [-7,7]){box(g,[11.2,.4,2.3],[x,cy+66*scale,cz+15],'red','Impulse exhaust');for(let n=0;n<10;n++)box(g,[.35,.65,2.6],[x-5+n*1.1,cy+66.2*scale,cz+15],'panel','Impulse exhaust louvre');}
 for(let x=-12;x<=12;x+=1.8)box(g,[.35,6,.12],[x,cy+62*scale,cz+17.1],'panel','Impulse upper cooling fin');
 // Ventral sensor rings and sensor-grid windows remain visible from below.
 for(const r of [4,6,10,15,20])ring(g,r,.10,[0,cy,cz+Math.max(.6,(r-5)*.45)],'panel');
 for(let i=0;i<8;i++)for(const sign of[-1,1])box(g,[.85,.35,.4],[sign*(4+i*.75),cy-11,cz+3.3],'dark','Lower sensor array ports');
}
function engineering(g,s,center,y0,z0,federation=false){
 const yz=federation?[[68,15],[88,15],[108,15],[128,13.7],[148,12],[162,11]]:[[-20,15.6],[-5,17],[10,16.4],[25,15.3],[40,13.3],[50,11.6]];
 for(const sign of[-1,1]){
  for(const[y,r]of yz)for(const dz of[-3,0,3])for(let k=0;k<3;k++)box(g,[.12,1.4,.62],[sign*(r-.2),y-center[1]+k*2.4,z0+dz],'dark','Engineering hull window');
  const side=box(g,[.15,34,1.3],[sign*(federation?14.8:16.8),y0,z0-1.5],'red','Engineering pennant');
  for(let row=0;row<3;row++)for(let k=0;k<7;k++)box(g,[.16,1.5,.5],[sign*3.56,(federation?63:-24)-center[1]-row*6+k*3.8,(federation?3:4)-row*3-center[2]],'dark','Neck cabin windows');
 }
 const dishY=federation?52-center[1]:-44.8,rad=federation?8:12.0;
 for(let r=2;r<=rad;r+=2)ring(g,r,.15,[0,dishY-.1,z0],'brass','y',0,Math.PI*2,'Deflector concentric ridge');
 sphere(g,1,[0,dishY-1,z0],'brass');
 const endY=federation?176-center[1]:69.6;
 // Closed six-leaf clamshell relief; the complete interior has a separate cutaway study.
 for(let i=0;i<6;i++){
  const arc=new T.Shape();const a=i*Math.PI/6,b=(i+1)*Math.PI/6;
  arc.moveTo(0,0);arc.absarc(0,0,5.4,a,b,false);arc.lineTo(0,0);
  const o=mesh(g,new T.ExtrudeGeometry(arc,{depth:.16,bevelEnabled:false,curveSegments:8}),i%2?'hull':'panel','Hangar clamshell segment '+(i+1));o.rotation.x=Math.PI/2;o.position.set(0,endY+.12,z0-2.5);
 }
 box(g,[8,.25,.3],[0,endY+.3,z0+3.2],'dark','Hangar observation window strip');
 sphere(g,.4,[0,endY+.35,z0+4.1],'red',[1,1,1],'Hangar homing beacon');
}
export function batch(root){root.updateMatrixWorld(true);const buckets=new Map();root.traverse(o=>{if(o.isMesh){let geo=o.geometry.index?o.geometry.toNonIndexed():o.geometry.clone();geo.applyMatrix4(o.matrixWorld);if(!geo.getAttribute('normal'))geo.computeVertexNormals();geo.deleteAttribute('uv');geo.deleteAttribute('color');const k=o.material.uuid;const b=buckets.get(k)||{geos:[],mat:o.material};b.geos.push(geo);buckets.set(k,b);}});const group=new T.Group();group.name=root.name;for(const[k,b]of buckets){const geo=mergeVertices(mergeGeometries(b.geos,false),.00001);const o=new T.Mesh(geo,b.mat);o.name=(b.mat.name||'Material')+' surface details';group.add(o);}return group;}
export function buildNacelleStudy(){const group=batch(nacelle(0,0,0,-1,'NCC-1700',false,true));group.name='Main propulsion external arrangement — PDF 144';return{group,length:153.619,sourcePages:[144],description:'Three sensor nodes at 120°, eight ribbed chiller banks, constriction housing, raised intercooler loops and asymmetric restoration cowl.'};}
function buildExterior(s){
 const root=new T.Group();root.name=s.name+' — detailed manual reconstruction';
 const parseFile=file=>{const data=fs.readFileSync(file);return new STLLoader().parse(data.buffer.slice(data.byteOffset,data.byteOffset+data.byteLength));};let geo=s.id==='constitution'?parseFile('model-source/constitution-base.stl'):parseFile(path.join(ROOT,'dist',s.model));
 geo=mergeVertices(geo,.0001);geo.computeVertexNormals();const base=mesh(root,geo,'hull','Original dimensioned hull');
 const center=s.id==='constitution'?[0,0,0]:s.id==='ptolemy'?[0,47.45,-1.2]:s.id==='federation'?[0,90,-3.05]:[0,57.7,1.8];
 const cy=s.id==='constitution'?-80.75:-center[1],cz=-center[2];saucerDetails(root,s,cy,cz,s.id==='federation'?1.5:1);
 if(s.id==='constitution'){
  for(const sign of[-1,1]){root.add(nacelle(-9.3,sign*46.1,27.65,sign,s.registry));for(let n=0;n<4;n++){const t=.35+n*.17,pt=new T.Vector3(sign*(10+36.1*t),25.7,-14+35*t);const o=box(root,[6.1,.18,2.6],pt.toArray(),'dark','Pylon grille');for(let k=0;k<5;k++)box(root,[.4,.22,2.3],[pt.x-2.5+k*1.2,pt.y-.1,pt.z],'panel','Pylon grille rib');}}
  engineering(root,s,center,0,-19.25);
 }else if(s.id==='saladin'||s.id==='hermes'){
  root.add(nacelle(25.35-center[1],0,-19.55-center[2],1,s.registry,true));
  for(const sign of[-1,1])for(let row=0;row<3;row++)for(let n=0;n<8;n++)box(root,[.12,1.4,.55],[sign*2.55,28-center[1]+n*3+row*8,7-center[2]-row*6],'dark','Neck window');
  // The unarmed scout does not acquire the destroyer's torpedo tubes.
  if(s.id==='saladin')for(const x of[-2.8,2.8]){cyl(root,.85,.3,[x,cy-17.1,cz+26],'dark','y','Forward torpedo aperture');ring(root,.92,.12,[x,cy-17.3,cz+26],'brass','y');}
 }else if(s.id==='ptolemy'){
  for(const sign of[-1,1]){root.add(nacelle(4.85-center[1],sign*46.1,-25.55-center[2],sign,s.registry));for(let n=0;n<4;n++)box(root,[2.8,.2,2.1],[sign*(27+n*4.2),39.9-center[1],9-center[2]-n*6],'dark','Tug pylon access grille');}
  const y=74-center[1],z=-9.55-center[2];box(root,[24,27,.25],[0,y,z],'dark','Cargo coupling pad');for(const x of[-9,9])for(const dy of[-10,10])cyl(root,1.2,.6,[x,y+dy,z-.3],'brass','z','Tow-pad attachment lock');
  for(let i=0;i<7;i++)box(root,[19,.4,.5],[0,y-10+i*3,z-.2],'panel','Tow coupling rib');
 }else{
  for(const sign of[-1,1])root.add(nacelle(96.4-center[1],sign*53,6-center[2],sign,s.registry));root.add(nacelle(30-center[1],0,31.8-center[2],1,s.registry));engineering(root,s,center,80-center[1],-31.55-center[2],true);
 }
 return batch(root);
}
// GLTFExporter uses FileReader for binary packing; this Node shim never touches browser state.
globalThis.FileReader=class{readAsArrayBuffer(b){b.arrayBuffer().then(v=>{this.result=v;this.onloadend?.();});}readAsDataURL(b){b.arrayBuffer().then(v=>{this.result='data:'+b.type+';base64,'+Buffer.from(v).toString('base64');this.onloadend?.();});}};
export async function exportStudy(group,file){const data=await new GLTFExporter().parseAsync(group,{binary:true,onlyVisible:true});fs.writeFileSync(path.join(OUT,file),Buffer.from(data));const box=new T.Box3().setFromObject(group);let vertices=0,triangles=0,meshes=0;group.traverse(o=>{if(o.isMesh){meshes++;vertices+=o.geometry.attributes.position.count;triangles+=(o.geometry.index?o.geometry.index.count:o.geometry.attributes.position.count)/3;for(const v of o.geometry.attributes.position.array)if(!Number.isFinite(v))throw Error('Nonfinite vertex');}});return{file,bytes:data.byteLength,meshes,vertices,triangles,bounds:[box.min.toArray(),box.max.toArray()]};}
const first={id:'constitution',name:'Constitution',registry:'NCC-1700',length:288.6,width:127.1,height:72.6,model:'assets/constitution.stl'};
if(process.argv[1]===new URL(import.meta.url).pathname){const report=[];for(const s of[first,...JSON.parse(fs.readFileSync('dist/assets/fleet/ships.json'))]){report.push(await exportStudy(buildExterior(s),s.id+'.glb'));console.log(JSON.stringify(report.at(-1)));}report.push(await exportStudy(buildNacelleStudy().group,'nacelle.glb'));fs.writeFileSync('model-source/exterior-validation.json',JSON.stringify(report,null,2));}
