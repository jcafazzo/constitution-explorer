import * as THREE from './vendor/three.module.js';
import {OrbitControls} from './vendor/OrbitControls.js';
import {GLTFLoader} from './vendor/GLTFLoader.js';

const V='eq4';
const esc=s=>String(s??'').replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const plateUrl=p=>`assets/equipment/page-${p}.webp`;
const categories=['all','weapons','communications','sciences','medical'];
const titleCase=s=>s[0].toUpperCase()+s.slice(1);
let catalogue=null;
async function load(){if(!catalogue){const r=await fetch(`assets/equipment/equipment.json?v=${V}`);if(!r.ok)throw Error('Equipment catalogue unavailable');catalogue=await r.json();}return catalogue;}
const folio=(name,code)=>`<div class="folio"><span><a href="#/">COMMAND SECTION</a> / <a href="#/equipment">EQUIPMENT LOCKER</a>${name?` / ${esc(name)}`:''}</span><span>${code?`TECHNICAL ORDER ${esc(code)}`:'STANDARD FIELD EQUIPMENT'}</span></div>`;
const dims=x=>esc(x.printedSize||'');

export function renderEquipment(main,path){
 let alive=true,viewer=null;const id=path.split('/')[2];
 main.innerHTML=folio('')+'<p class="loading-inline" role="status">Opening the equipment locker…</p>';
 load().then(items=>{if(!alive)return;const item=items.find(x=>x.id===id);if(id&&!item){main.innerHTML=folio('ENTRY NOT FOUND')+'<h1>That sheet is not in this edition.</h1><a class="btn" href="#/equipment">Return to the equipment locker</a>';document.title='Not found · Star Fleet Manual';return;}if(item){detail(main,item,items);viewer=mountEquipmentViewer(main.querySelector('#scene'),item);document.title=`${item.title} · Star Fleet Manual`;}else{index(main,items);}}).catch(e=>{console.error(e);if(alive)main.innerHTML=folio('')+'<h1>The equipment locker could not load.</h1><p>Please reload to try again.</p>';});
 return ()=>{alive=false;viewer?.dispose();};
}

function index(main,items){
 let category='all';
 main.innerHTML=folio('')+`<section class="eq-heading"><div><span class="eyebrow">03 / Standard field equipment</span><h1>The equipment<br>locker.</h1><p class="intro">Phasers, communicators, tricorders and the instruments of the ship’s surgeon — each drawn from its technical order and rebuilt as an object you can turn in your hand.</p></div><div class="eq-hero"><img src="${plateUrl(104)}" alt="Manual PDF page 104: Hand Phaser Type II general arrangement"><span>TO 01:08:52 · HAND PHASER TYPE II<br>PDF 104</span></div></section><div class="colour-toolbar"><div class="colour-filters" role="group" aria-label="Filter equipment">${categories.map(c=>`<button data-category="${c}" aria-pressed="${c==='all'}">${titleCase(c)}</button>`).join('')}</div><label class="search">FIND <input id="eq-search" type="search" placeholder="Name, model or section" autocomplete="off"></label></div><div class="eq-grid" id="eq-grid"></div><p id="eq-none" hidden>No matching equipment. Try a name such as “tricorder”.</p><div class="archive-note"><span class="eyebrow">How these studies are made</span><p>Printed specifications are transcribed from each sheet with their PDF page. Each model is built in Blender from outlines measured on the drawing at its own scale bar, then checked by overlaying exact-scale renders on the plate. Every reliable view matches to within about half a millimetre on average. Surfaces the drawings don’t show are interpretations, and each study says which.</p></div>`;
 const grid=main.querySelector('#eq-grid'),search=main.querySelector('#eq-search');
 function render(){const q=search.value.trim().toLowerCase();const list=items.filter(x=>(category==='all'||x.category===category)&&`${x.title} ${x.model||''} ${x.category} ${x.subtitle||''}`.toLowerCase().includes(q));grid.innerHTML=list.map(x=>`<a class="eq-card" href="#/equipment/${x.id}"><div class="eq-card-art"><img src="${x.thumb||plateUrl(x.pages[0])}" alt="" loading="lazy"><span class="colour-plate-no">${String(items.indexOf(x)+1).padStart(2,'0')} / ${x.category.toUpperCase()}</span></div><div class="eq-card-copy"><h2>${esc(x.title)} <span>↗</span></h2><p>${esc(x.model||x.subtitle||'')}</p><div class="eq-card-meta"><span>${dims(x)}</span><span>PDF ${x.pages.length>1?x.pages[0]+'–'+x.pages.at(-1):x.pages[0]}</span></div></div></a>`).join('');main.querySelector('#eq-none').hidden=!!list.length;}
 main.querySelectorAll('[data-category]').forEach(b=>b.onclick=()=>{category=b.dataset.category;main.querySelectorAll('[data-category]').forEach(x=>x.setAttribute('aria-pressed',String(x===b)));render();});
 search.oninput=render;render();
}

function detail(main,x,items){
 const i=items.indexOf(x),prev=items[(i+items.length-1)%items.length],next=items[(i+1)%items.length],code=x.codes?.[x.pages[0]]||'';
 const specRows=(x.specs||[]).map(s=>`<div><dt>${esc(s.label)}</dt><dd>${esc(s.value)}${s.unit?` ${esc(s.unit)}`:''}</dd></div>`).join('');
 const derived=(x.derived||[]).map(s=>`<div><dt>${esc(s.label)}</dt><dd>${esc(s.value)}</dd></div>`).join('');
 const colours=(x.colourKey||[]).map(c=>`<li><b>${esc(c.code)}</b> ${esc(c.name)}</li>`).join('');
 const parts=(x.components||[]).map(c=>`<li>${esc(c)}</li>`).join('');
 main.innerHTML=folio(x.title.toUpperCase(),code)+`<div class="sheet-title"><div><span class="eyebrow">${esc(titleCase(x.category))} / ${esc(x.subtitle||'Field equipment')}</span><h1>${esc(x.title)}</h1><p class="subtitle">${esc(x.model||'')}${x.model?' · ':''}EQUIPMENT TECHNICAL STUDY</p></div><div class="sheet-code">SOURCE: PDF ${x.pages.join(', ')}<br><b>LOCKER ITEM ${String(i+1).padStart(2,'0')}</b></div></div>
<div class="sheet"><section class="drawing" aria-label="${esc(x.title)} interactive study"><div class="drawing-bar"><div class="tabs" role="tablist" aria-label="Study mode"><button role="tab" id="model-tab" class="active" aria-selected="true" aria-controls="model-panel">3D study</button><button role="tab" id="plate-tab" aria-selected="false" aria-controls="plate-panel" tabindex="-1">Technical plate</button></div><span class="paper-code">${code?`TO:${esc(code)}`:''}</span></div>
<div id="model-panel" role="tabpanel" aria-labelledby="model-tab"><div id="scene" tabindex="0" role="group" aria-roledescription="3D viewer" aria-label="${esc(x.title)} model. Drag to orbit. Arrow keys rotate; plus and minus zoom."><span class="scene-caption" id="view-name">PERSPECTIVE / RECONSTRUCTION</span><span class="loading" role="status">Preparing the study…</span></div><div class="drawing-controls"><div class="view-buttons" aria-label="Camera view">${['3D','Top','Side','Front'].map((v,k)=>`<button data-view="${v}" class="${k?'':'active'}" aria-pressed="${!k}">${v}</button>`).join('')}</div><div class="tools"><button class="icon-btn" id="turn" aria-pressed="false" aria-label="Toggle turntable">↻ Orbit</button><button class="icon-btn" id="zoom-in" aria-label="Zoom in">+</button><button class="icon-btn" id="zoom-out" aria-label="Zoom out">−</button><button class="icon-btn" id="reset">Fit model</button><button class="icon-btn" id="fullscreen" aria-label="Toggle fullscreen">⛶</button></div></div><p class="drawing-hint">DRAG TO ORBIT · SCROLL TO ZOOM · RIGHT-DRAG TO PAN</p></div>
<div id="plate-panel" role="tabpanel" aria-labelledby="plate-tab" hidden><div class="plate-tools"><button class="icon-btn" id="plate-zoom" aria-pressed="false">Enlarge drawing</button><label class="source-selector">SOURCE <select id="source-select" aria-label="Source sheet">${x.pages.map(p=>`<option value="${p}">PDF ${p}${x.codes?.[p]?` · TO ${esc(x.codes[p])}`:''}</option>`).join('')}</select></label><a id="source-open" href="${plateUrl(x.pages[0])}" target="_blank" rel="noopener">Open source sheet ↗</a></div><div class="plate-view"><img src="${plateUrl(x.pages[0])}" alt="Manual PDF page ${x.pages[0]}: ${esc(x.title)} source drawing"></div></div>
<div class="study-notes"><strong>${esc(x.title)}</strong><p>${esc(x.summary||'')}</p><p class="small">${esc(x.interpretation||'')}</p></div></section>
<aside class="particulars"><h2>SPECIFICATION</h2><p class="description">${esc(x.description||'')}</p>${specRows?`<span class="eyebrow">Printed on the sheet</span><dl>${specRows}</dl>`:''}${derived?`<span class="eyebrow">Measured from the drawing</span><dl class="derived">${derived}</dl>`:''}<span class="eyebrow">Drawing finish</span><div class="finishes">${['Ivory','Blueprint','Mesh'].map((f,k)=>`<button data-finish="${f}" class="${k?'':'active'}" aria-pressed="${!k}">${f}</button>`).join('')}</div><a class="btn" id="glb-download" href="assets/equipment/${x.id}.glb" download="${x.id}-study.glb">Download 3D study (GLB) <span>↓</span></a><p class="small">Display study in metres, glTF Y-up. Not a print-ready mesh.</p></aside></div>
<div class="spec-strip"><div><strong>01 / THE SOURCE</strong><p>${x.pages.map(p=>`PDF ${p}${x.codes?.[p]?`, TO ${esc(x.codes[p])}`:''}`).join('; ')}.${colours?'':' '}</p>${colours?`<ul class="eq-colours">${colours}</ul>`:''}</div><div><strong>02 / CALLED OUT ON THE SHEET</strong>${parts?`<ul class="eq-parts">${parts}</ul>`:'<p>See the technical plate.</p>'}</div><div><strong>03 / THE INTERPRETATION</strong><p>${esc(x.interpretation||'Hidden surfaces and small controls are interpretations.')}</p></div></div>
<div class="pagination"><a href="#/equipment/${prev.id}">← ${esc(prev.title)}</a><a href="#/equipment">All equipment</a><a href="#/equipment/${next.id}">${esc(next.title)} →</a></div>`;
 const $=s=>main.querySelector(s);
 const switchTab=mode=>{const is3D=mode==='model';$('#model-panel').hidden=!is3D;$('#plate-panel').hidden=is3D;for(const t of ['model','plate']){const b=$(`#${t}-tab`);b.classList.toggle('active',t===mode);b.setAttribute('aria-selected',String(t===mode));b.tabIndex=t===mode?0:-1;}window.dispatchEvent(new Event('resize'));};
 $('#model-tab').onclick=()=>switchTab('model');$('#plate-tab').onclick=()=>switchTab('plate');
 for(const t of ['model','plate'])$(`#${t}-tab`).onkeydown=e=>{if(['ArrowLeft','ArrowRight'].includes(e.key)){e.preventDefault();const n=t==='model'?'plate':'model';switchTab(n);$(`#${n}-tab`).focus();}};
 $('#plate-zoom').onclick=e=>{const on=$('.plate-view').classList.toggle('zoomed');e.currentTarget.setAttribute('aria-pressed',String(on));e.currentTarget.textContent=on?'Fit drawing':'Enlarge drawing';};
 $('#source-select').onchange=e=>{const p=e.target.value,img=$('.plate-view img');img.src=plateUrl(p);img.alt=`Manual PDF page ${p}: ${x.title} source drawing`;$('#source-open').href=plateUrl(p);};
 $('#fullscreen').hidden=!document.fullscreenEnabled;$('#fullscreen').onclick=async()=>{try{if(document.fullscreenElement)await document.exitFullscreen();else await $('.drawing').requestFullscreen();}catch{}};
}

function mountEquipmentViewer(host,item){
 let disposed=false,model=null,renderer,controls,scene,camera,observer,finish='Ivory',framed=true,currentView='3D';
 const loading=host.querySelector('.loading'),$=s=>document.querySelector(s);
 const release=root=>{root?.traverse(o=>{o.geometry?.dispose();for(const m of [].concat(o.material||[]))m.dispose();});};
 function resize(){const w=host.clientWidth,h=host.clientHeight;if(!w||!h||!renderer)return;renderer.setSize(w,h);const changed=Math.abs(camera.aspect-w/h)>.001;camera.aspect=w/h;camera.updateProjectionMatrix();if(changed&&model&&framed)view(currentView);}
 function view(name='3D'){
  if(!model)return;currentView=name;framed=true;controls.autoRotate=false;$('#turn')?.setAttribute('aria-pressed','false');controls.target.set(0,0,0);camera.up.set(0,0,1);
  const vectors={'3D':[.9,-1,.75],Top:[0,-.0001,1],Side:[1,0,0],Front:[0,-1,0]};
  const tanV=Math.tan(THREE.MathUtils.degToRad(camera.fov)/2),tanH=tanV*camera.aspect,dir=new THREE.Vector3(...vectors[name]).normalize(),right=new THREE.Vector3().crossVectors(camera.up,dir).normalize(),up=new THREE.Vector3().crossVectors(dir,right);let d=0;const p=new THREE.Vector3();
  model.updateMatrixWorld(true);model.traverse(o=>{if(!o.isMesh)return;const a=o.geometry.attributes.position;for(let i=0;i<a.count;i++){p.fromBufferAttribute(a,i).applyMatrix4(o.matrixWorld);const depth=p.dot(dir);d=Math.max(d,Math.abs(p.dot(right))/(tanH*.82)+depth,Math.abs(p.dot(up))/(tanV*.82)+depth);}});
  camera.position.copy(dir.multiplyScalar(d));controls.update();
  $('#view-name').textContent=`${name==='3D'?'PERSPECTIVE':name.toUpperCase()} / ${item.title.toUpperCase()}`;
  document.querySelectorAll('[data-view]').forEach(b=>{b.classList.toggle('active',b.dataset.view===name);b.setAttribute('aria-pressed',String(b.dataset.view===name));});
 }
 function interactive(){framed=false;$('#view-name').textContent=`INTERACTIVE / ${item.title.toUpperCase()}`;document.querySelectorAll('[data-view]').forEach(b=>{b.classList.remove('active');b.setAttribute('aria-pressed','false');});}
 function zoom(f){if(!model)return;interactive();const o=camera.position.clone().sub(controls.target);o.setLength(THREE.MathUtils.clamp(o.length()*f,controls.minDistance,controls.maxDistance));camera.position.copy(o.add(controls.target));controls.update();}
 function applyFinish(){model?.traverse(o=>{if(!o.isMesh)return;for(const m of [].concat(o.material)){if(!m.userData.base)m.userData.base=m.color.clone();m.color.copy(m.userData.base);m.wireframe=finish==='Mesh';if(finish==='Blueprint')m.color.lerp(new THREE.Color(0x397993),.78);if(finish==='Mesh')m.color.set(0x4e6259);}});}
 try{
  renderer=new THREE.WebGLRenderer({antialias:true,alpha:true});renderer.setPixelRatio(Math.min(devicePixelRatio,2));renderer.outputColorSpace=THREE.SRGBColorSpace;renderer.toneMapping=THREE.ACESFilmicToneMapping;host.append(renderer.domElement);
  scene=new THREE.Scene();camera=new THREE.PerspectiveCamera(30,1,.001,100);camera.up.set(0,0,1);
  controls=new OrbitControls(camera,renderer.domElement);controls.enableDamping=true;controls.autoRotateSpeed=.8;controls.addEventListener('start',interactive);
  scene.add(new THREE.HemisphereLight(0xffffff,0x6f706a,1.6));for(const [pos,power] of [[[2,-4,5],2.4],[[-4,2,2],1.0],[[0,3,-2],.5]]){const l=new THREE.DirectionalLight(0xffffff,power);l.position.set(...pos);scene.add(l);}
  observer=new ResizeObserver(resize);observer.observe(host);
  document.querySelectorAll('[data-view]').forEach(b=>b.onclick=()=>view(b.dataset.view));$('#reset').onclick=()=>view();$('#zoom-in').onclick=()=>zoom(.8);$('#zoom-out').onclick=()=>zoom(1.25);
  $('#turn').onclick=e=>{interactive();controls.autoRotate=!controls.autoRotate;e.currentTarget.setAttribute('aria-pressed',String(controls.autoRotate));};
  document.querySelectorAll('[data-finish]').forEach(b=>b.onclick=()=>{finish=b.dataset.finish;applyFinish();document.querySelectorAll('[data-finish]').forEach(x=>{x.classList.toggle('active',x===b);x.setAttribute('aria-pressed',String(x===b));});});
  host.onkeydown=e=>{if(!model||!['ArrowLeft','ArrowRight','ArrowUp','ArrowDown','+','=','-'].includes(e.key))return;e.preventDefault();if(e.key==='+'||e.key==='=')zoom(.9);else if(e.key==='-')zoom(1.1);else{interactive();const v=camera.position.clone().sub(controls.target),h=['ArrowLeft','ArrowRight'].includes(e.key);const axis=h?new THREE.Vector3(0,0,1):new THREE.Vector3().crossVectors(v,camera.up).normalize();v.applyAxisAngle(axis,['ArrowLeft','ArrowUp'].includes(e.key)?.12:-.12);camera.position.copy(v.add(controls.target));controls.update();}};
  renderer.setAnimationLoop(()=>{if(!document.hidden&&!$('#model-panel')?.hidden){controls.update();renderer.render(scene,camera);}});
  new GLTFLoader().loadAsync(`assets/equipment/${item.id}.glb?v=${V}`).then(r=>{if(disposed){release(r.scene);return;}model=r.scene;model.rotation.x=Math.PI/2;model.updateMatrixWorld(true);const b=new THREE.Box3().setFromObject(model);model.position.sub(b.getCenter(new THREE.Vector3()));const radius=b.getBoundingSphere(new THREE.Sphere()).radius;camera.near=radius*.005;camera.far=radius*40;controls.minDistance=radius*.25;controls.maxDistance=radius*12;camera.updateProjectionMatrix();scene.add(model);applyFinish();loading.hidden=true;resize();view();}).catch(e=>{if(disposed)return;console.error(e);loading.textContent='This study could not load. Open the technical plate instead.';});
 }catch(e){console.error(e);loading.textContent='3D unavailable. The technical plate and specification remain available.';}
 return {dispose(){disposed=true;renderer?.setAnimationLoop(null);observer?.disconnect();controls?.dispose();release(model);renderer?.dispose();renderer?.forceContextLoss();host.onkeydown=null;}};
}
