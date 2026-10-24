import * as THREE from 'three';
import { OrbitControls } from './vendor/OrbitControls.js';
import { STLLoader } from './vendor/STLLoader.js';
const host=document.querySelector('#scene'), loading=document.querySelector('#loading');
const dialog=document.querySelector('#blueprint-dialog');
document.querySelector('#blueprint-open').onclick=()=>dialog.showModal();
document.querySelector('#blueprint-close').onclick=()=>dialog.close();
dialog.addEventListener('click',e=>{if(e.target===dialog){const r=dialog.getBoundingClientRect();if(e.clientX<r.left||e.clientX>r.right||e.clientY<r.top||e.clientY>r.bottom)dialog.close();}});
async function init(){
const renderer=new THREE.WebGLRenderer({antialias:true,alpha:true});renderer.setPixelRatio(Math.min(devicePixelRatio,2));renderer.outputColorSpace=THREE.SRGBColorSpace;renderer.toneMapping=THREE.ACESFilmicToneMapping;renderer.toneMappingExposure=1.0;host.appendChild(renderer.domElement);
const scene=new THREE.Scene(),camera=new THREE.PerspectiveCamera(38,1,.5,4000);camera.up.set(0,0,1);
const controls=new OrbitControls(camera,renderer.domElement);controls.enableDamping=true;controls.dampingFactor=.075;controls.minDistance=150;controls.maxDistance=1100;controls.autoRotateSpeed=.65;
scene.add(new THREE.HemisphereLight(0xe1f2ff,0x33444d,1.8));
for(const [color,intensity,pos] of [[0xffedda,3.5,[100,-240,300]],[0xb2dfff,2.5,[-200,70,130]],[0xffffff,2,[60,220,80]]]){const light=new THREE.DirectionalLight(color,intensity);light.position.set(...pos);scene.add(light);}
const material=new THREE.MeshStandardMaterial({color:0xcbd2d0,metalness:.16,roughness:.51});
const geometry=await new STLLoader().loadAsync('./assets/constitution.stl',p=>{if(p.total)loading.textContent=`Loading model · ${Math.round(p.loaded/p.total*100)}%`;});
const ship=new THREE.Mesh(geometry,material);scene.add(ship);loading.hidden=true;
const bounds=new THREE.Box3().setFromObject(ship);const center=bounds.getCenter(new THREE.Vector3());controls.target.copy(center);
let currentView='Perspective';
matchMedia('(max-width:760px)').addEventListener('change',()=>setView(currentView));
function setView(name){currentView=name;controls.autoRotate=false;document.querySelector('#rotate').setAttribute('aria-pressed','false');controls.target.copy(center);camera.up.set(0,0,1);const distance=host.clientWidth<650?560:(name==='Top'?510:340);const positions={Perspective:[.8,-1, .85],Top:[0,-.0001,1],Side:[1,0,0],Front:[0,-1,0]};camera.position.copy(new THREE.Vector3(...positions[name]).normalize().multiplyScalar(distance).add(center));controls.update();document.querySelector('#view-name').textContent=name.toUpperCase();document.querySelectorAll('[data-view]').forEach(b=>{b.classList.toggle('active',b.dataset.view===name);b.setAttribute('aria-pressed',String(b.dataset.view===name));});}
setView('Perspective');document.querySelectorAll('[data-view]').forEach(b=>b.onclick=()=>setView(b.dataset.view));
document.querySelector('#rotate').onclick=()=>{if(currentView==='Top')setView('Perspective');controls.autoRotate=!controls.autoRotate;document.querySelector('#rotate').setAttribute('aria-pressed',String(controls.autoRotate));};
function zoom(f){camera.position.sub(controls.target).multiplyScalar(f).add(controls.target);controls.update();}
document.querySelector('#zoom-in').onclick=()=>zoom(.84);document.querySelector('#zoom-out').onclick=()=>zoom(1.19);document.querySelector('#reset').onclick=()=>setView('Perspective');
document.querySelector('#fullscreen').onclick=async()=>{try{if(document.fullscreenElement)await document.exitFullscreen();else await document.querySelector('.viewer').requestFullscreen();}catch{document.querySelector('#fullscreen').hidden=true;}};
if(!document.fullscreenEnabled)document.querySelector('#fullscreen').hidden=true;
document.querySelectorAll('[data-finish]').forEach(b=>b.onclick=()=>{const f=b.dataset.finish;material.wireframe=f==='wire';material.color.set(f==='porcelain'?0xcbd2d0:f==='blueprint'?0x3a93b3:0x83c0d5);material.metalness=f==='porcelain'?.16:.05;material.roughness=f==='porcelain'?.51:.8;document.querySelectorAll('[data-finish]').forEach(x=>{x.classList.toggle('active',x===b);x.setAttribute('aria-pressed',String(x===b));});});
host.addEventListener('keydown',e=>{if(['ArrowLeft','ArrowRight','ArrowUp','ArrowDown','+','=','-'].includes(e.key)){e.preventDefault();if(e.key==='+'||e.key==='=')zoom(.9);else if(e.key==='-')zoom(1.1);else{let v=camera.position.clone().sub(controls.target);if(e.key==='ArrowLeft'||e.key==='ArrowRight')v.applyAxisAngle(new THREE.Vector3(0,0,1),e.key==='ArrowLeft'?.12:-.12);else{const axis=new THREE.Vector3().crossVectors(v,camera.up).normalize();v.applyAxisAngle(axis,e.key==='ArrowUp'?.1:-.1);}camera.position.copy(v.add(controls.target));controls.update();}}});
const resize=()=>{const w=host.clientWidth,h=host.clientHeight;renderer.setSize(w,h);camera.aspect=w/h;camera.updateProjectionMatrix();};new ResizeObserver(resize).observe(host);resize();
let last=0;renderer.setAnimationLoop(t=>{if(document.hidden)return;const dt=Math.min((t-last)/1000,.1);last=t;controls.update(dt);renderer.render(scene,camera);});
renderer.domElement.addEventListener('webglcontextlost',e=>{e.preventDefault();loading.hidden=false;loading.textContent='3D display interrupted. Reload this page to restore the viewer.';});
}
init().catch(e=>{console.error(e);loading.replaceChildren();const msg=document.createElement('p');msg.textContent='The 3D viewer could not start on this device.';const a=document.createElement('a');a.href='assets/poster.png';a.textContent='View the rendered ship ↗';loading.append(msg,a);document.querySelectorAll('.controls button,.finishes button').forEach(b=>b.disabled=true);});
