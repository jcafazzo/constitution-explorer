import * as THREE from './vendor/three.module.js';
import {OrbitControls} from './vendor/OrbitControls.js';
import {GLTFLoader} from './vendor/GLTFLoader.js';

export function studiesFor(ship){
 const base='assets/detail/';
 const studies=[
 {id:'ship',title:'Complete starship',file:base+ship.id+'.glb',pages:[ship.page,144,143],sources:[`assets/fleet/${ship.id}-plate.webp`,base+'page-144.webp',base+'page-143.webp'],description:'Detailed exterior: saucer panel divisions, registry lettering, rim windows, bridge ports, impulse vents and propulsion assemblies with ribbed chiller banks and raised intercooler loops.',note:`Hull proportions follow plate ${ship.plate}; component arrangements use the later propulsion sheets. Fine spacing, finishes and hidden curvature are reconstructed.`},
 {id:'nacelle',title:'Main propulsion / SW40',file:base+'nacelle.glb',pages:[144],description:'Inspect the acquisition dome, three sensor nodes, three power-stage and five main-stage chiller banks, raised constriction housing, aft intercooler loops and asymmetric restoration cowl.',note:'The manual’s external arrangement, TO 03:11:20. Rib spacing and hidden surfaces are interpreted; the standalone unit shows the heavy-cruiser arrangement.'},
 {id:'impulse',title:'Impulse engine / IP186',file:base+'impulse.glb',pages:[143],description:'Twelve circulation tubes surround the twin firing chambers. Explore the recessed throats, fuel-feed chute, five heat-exchanger connections and paired longitudinal constrictions.',note:'Component study from TO 03:10:20, with the stated 5.2 × 4.5 × 2.8 m envelope. Internal recess depths and its installation within each class are not fully specified.'},
 ];
 if(ship.id==='constitution')studies.push(
 {id:'bridge',title:'Main bridge / cutaway',file:base+'bridge.glb',pages:[94,95],description:'A sunken command well, captain’s chair, helm/navigation console, eight perimeter stations, service corridor and aft turbolift. The command and visual-display axis is offset 36° from the ship’s axis.',note:'Open-roof reconstruction from TO 01:06:10–11. The plan establishes the arrangement; undimensioned depths and small controls are interpreted. Scale is approximate.'},
 {id:'hangar',title:'MK-IX hangar / cutaway',file:base+'hangar.glb',pages:[149,150],description:'Six clamshell door segments, elevated observation galleries, paired control towers, landing floodlights, a rectangular landing target, elevator turntable and exposed maintenance level.',note:'The MK-IX bay described in TO 03:17:00–01. Door pose and hidden structure are reconstructed; this study does not assert an identical bay in every starship class.'}
 );
 return studies;
}

export function mountViewer(host,ship,onStudy){
 let disposed=false,request=0,model=null,observer,renderer,controls,scene,camera,radius=1,halfSize=new THREE.Vector3(1,1,1),active,finish='Ivory',framed=true,currentView='3D';
 const loading=host.querySelector('.loading'),$=s=>document.querySelector(s);
 const studies=studiesFor(ship),selector=$('#study-select');
 const release=root=>{const gs=new Set(),ms=new Set();root?.traverse(o=>{if(o.geometry)gs.add(o.geometry);if(o.material)for(const m of Array.isArray(o.material)?o.material:[o.material])ms.add(m);});gs.forEach(g=>g.dispose());ms.forEach(m=>m.dispose());};
 function resize(){const w=host.clientWidth,h=host.clientHeight;if(!w||!h||!renderer)return;renderer.setSize(w,h);const changed=Math.abs(camera.aspect-w/h)>.001;camera.aspect=w/h;camera.updateProjectionMatrix();if(changed&&model&&framed)view(currentView);}
 function view(name='3D'){
  if(!model)return;currentView=name;framed=true;controls.autoRotate=false;const damping=controls.enableDamping;controls.enableDamping=false;controls.update();controls.enableDamping=damping;$('#turn').setAttribute('aria-pressed','false');controls.target.set(0,0,0);camera.up.set(0,0,1);
  const vectors={'3D':active.id==='bridge'||active.id==='hangar'?[.8,-1,1.4]:[.8,-1,.85],Top:[0,-.0001,1],Side:[1,0,0],Front:[0,-1,0]};
  const fov=THREE.MathUtils.degToRad(camera.fov),tanV=Math.tan(fov/2),tanH=tanV*camera.aspect,dir=new THREE.Vector3(...vectors[name]).normalize(),right=new THREE.Vector3().crossVectors(camera.up,dir).normalize(),up=new THREE.Vector3().crossVectors(dir,right);let d=0;
  model.updateMatrixWorld(true);const point=new THREE.Vector3();model.traverse(o=>{if(!o.isMesh)return;const positions=o.geometry.attributes.position;for(let i=0;i<positions.count;i++){point.fromBufferAttribute(positions,i).applyMatrix4(o.matrixWorld);const depth=point.dot(dir);d=Math.max(d,Math.abs(point.dot(right))/(tanH*.88)+depth,Math.abs(point.dot(up))/(tanV*.88)+depth);}});
  camera.position.copy(dir.multiplyScalar(d));controls.update();
  $('#view-name').textContent=`${name==='3D'?'PERSPECTIVE':name.toUpperCase()} / ${active.title.toUpperCase()}`;
  document.querySelectorAll('[data-view]').forEach(b=>{b.classList.toggle('active',b.dataset.view===name);b.setAttribute('aria-pressed',String(b.dataset.view===name));});
 }
 function markInteractive(){framed=false;if(!active)return;$('#view-name').textContent=`INTERACTIVE / ${active.title.toUpperCase()}`;document.querySelectorAll('[data-view]').forEach(b=>{b.classList.remove('active');b.setAttribute('aria-pressed','false');});}
 function zoom(f){if(!model)return;markInteractive();const offset=camera.position.clone().sub(controls.target);offset.setLength(THREE.MathUtils.clamp(offset.length()*f,controls.minDistance,controls.maxDistance));camera.position.copy(offset.add(controls.target));controls.update();}
 function applyFinish(){model?.traverse(o=>{if(!o.isMesh)return;for(const m of Array.isArray(o.material)?o.material:[o.material]){if(!m.userData.originalColor)m.userData.originalColor=m.color.clone();m.color.copy(m.userData.originalColor);m.wireframe=finish==='Mesh';if(finish==='Blueprint')m.color.lerp(new THREE.Color(0x397993),.78);if(finish==='Mesh')m.color.set(0x4e6259);}});}
 async function select(id){
  const own=++request;active=studies.find(x=>x.id===id)||studies[0];onStudy(active);loading.hidden=false;loading.textContent='Preparing the detailed study…';
  if(model){scene.remove(model);release(model);model=null;}
  try{
   const result=await new GLTFLoader().loadAsync(active.file+'?v=quality4');
   if(disposed||own!==request){release(result.scene);return;}
   model=result.scene;const bounds=new THREE.Box3().setFromObject(model);model.position.sub(bounds.getCenter(new THREE.Vector3()));radius=bounds.getBoundingSphere(new THREE.Sphere()).radius;bounds.getSize(halfSize).multiplyScalar(.5);
   camera.near=Math.max(radius*.0005,.001);camera.far=radius*20;controls.minDistance=radius*.18;controls.maxDistance=radius*15;camera.updateProjectionMatrix();scene.add(model);applyFinish();loading.hidden=true;resize();view();
  }catch(e){if(disposed||own!==request)return;console.error(e);loading.hidden=false;loading.textContent='This study could not load. Choose another study or open its technical plate.';}
 }
 try{
  renderer=new THREE.WebGLRenderer({antialias:true,alpha:true});renderer.setPixelRatio(Math.min(devicePixelRatio,2));renderer.outputColorSpace=THREE.SRGBColorSpace;renderer.toneMapping=THREE.ACESFilmicToneMapping;renderer.toneMappingExposure=1.0;host.append(renderer.domElement);
  scene=new THREE.Scene();camera=new THREE.PerspectiveCamera(34,1,.01,4000);camera.up.set(0,0,1);
  controls=new OrbitControls(camera,renderer.domElement);controls.enableDamping=true;controls.autoRotateSpeed=.6;controls.addEventListener('start',markInteractive);
  scene.add(new THREE.HemisphereLight(0xffffff,0x73746d,1.5));
  for(const [pos,power] of [[[80,-200,300],2.3],[[-150,60,120],1.1]]){const l=new THREE.DirectionalLight(0xffffff,power);l.position.set(...pos);scene.add(l);}
  observer=new ResizeObserver(resize);observer.observe(host);resize();selector.onchange=()=>select(selector.value);
  document.querySelectorAll('[data-view]').forEach(b=>b.onclick=()=>view(b.dataset.view));$('#reset').onclick=()=>view();$('#zoom-in').onclick=()=>zoom(.8);$('#zoom-out').onclick=()=>zoom(1.25);
  $('#turn').onclick=e=>{markInteractive();controls.autoRotate=!controls.autoRotate;e.currentTarget.setAttribute('aria-pressed',String(controls.autoRotate));};
  document.querySelectorAll('[data-finish]').forEach(b=>b.onclick=()=>{finish=b.dataset.finish;applyFinish();document.querySelectorAll('[data-finish]').forEach(x=>{x.classList.toggle('active',x===b);x.setAttribute('aria-pressed',String(x===b));});});
  host.onkeydown=e=>{if(!model||!['ArrowLeft','ArrowRight','ArrowUp','ArrowDown','+','=','-'].includes(e.key))return;e.preventDefault();if(e.key==='+'||e.key==='=')zoom(.9);else if(e.key==='-')zoom(1.1);else{markInteractive();const v=camera.position.clone().sub(controls.target),horizontal=['ArrowLeft','ArrowRight'].includes(e.key);const axis=horizontal?new THREE.Vector3(0,0,1):new THREE.Vector3().crossVectors(v,camera.up).normalize();v.applyAxisAngle(axis,['ArrowLeft','ArrowUp'].includes(e.key)?.12:-.12);camera.position.copy(v.add(controls.target));controls.update();}};
  renderer.setAnimationLoop(()=>{if(!document.hidden&&!$('#model-panel')?.hidden){controls.update();renderer.render(scene,camera);}});
  renderer.domElement.addEventListener('webglcontextlost',()=>{if(!disposed){loading.hidden=false;loading.textContent='3D display interrupted. Reload or open the technical plate.';}});
  select('ship');
 }catch(e){console.error(e);loading.textContent='3D unavailable. Technical plates and downloads remain available.';selector.onchange=()=>onStudy(studies.find(x=>x.id===selector.value));onStudy(studies[0]);}
 return {resize,dispose(){disposed=true;request++;renderer?.setAnimationLoop(null);observer?.disconnect();controls?.dispose();release(model);renderer?.dispose();renderer?.forceContextLoss();host.onkeydown=null;}};
}
