import * as THREE from './vendor/three.module.js';

// Manual-derived dollhouse studies, in approximate metres. Undimensioned depth and
// fine button layouts are reconstructions; no hidden machinery is claimed exact.
const TAU = Math.PI * 2;
const palette = {
  shell: 0xd9d7cc, trim: 0xb9b9ac, floor: 0x8c8174, dark: 0x242c30,
  black: 0x10191e, red: 0x9b3831, ochre: 0xc4a04a, white: 0xeee9d9,
  display: 0x35576a, blue: 0x83acb5,
};
function kit(name) {
  const group = new THREE.Group(); group.name = name;
  const mats = Object.fromEntries(Object.entries(palette).map(([key,color]) => [key,new THREE.MeshStandardMaterial({color, roughness:.7, metalness:key==='trim'?.28:.08})]));
  function mesh(geometry, material, name, parent=group) { const o=new THREE.Mesh(geometry,mats[material]||material);o.name=name; parent.add(o); return o; }
  function box(name,x,y,z,w,h,d,mat='shell',parent=group) { const o=mesh(new THREE.BoxGeometry(w,h,d),mat,name,parent);o.position.set(x,y,z);return o; }
  function cylinder(name,x,y,z,r,h,mat='shell',parent=group,rTop=r) { const o=mesh(new THREE.CylinderGeometry(rTop,r,h,64),mat,name,parent);o.position.set(x,y,z);return o; }
  function tube(name,points,r,mat='trim',parent=group) { return mesh(new THREE.TubeGeometry(new THREE.CatmullRomCurve3(points.map(p=>new THREE.Vector3(...p))),Math.max(12,points.length*5),r,8,false),mat,name,parent); }
  function arc(name,ri,ro,y,h,start,end,mat='shell',parent=group) {
    const positions=[],n=Math.max(2,Math.ceil((end-start)*24));
    function v(r,a,b){return [r*Math.sin(a),b,r*Math.cos(a)];}
    function q(a,b,c,d){positions.push(...a,...b,...c,...a,...c,...d);}
    for(let i=0;i<n;i++){const a=start+(end-start)*i/n,b=start+(end-start)*(i+1)/n; q(v(ri,a,y),v(ri,b,y),v(ro,b,y),v(ro,a,y)); q(v(ro,a,y+h),v(ro,b,y+h),v(ri,b,y+h),v(ri,a,y+h));q(v(ro,a,y),v(ro,b,y),v(ro,b,y+h),v(ro,a,y+h));q(v(ri,b,y),v(ri,a,y),v(ri,a,y+h),v(ri,b,y+h));}
    q(v(ri,start,y),v(ro,start,y),v(ro,start,y+h),v(ri,start,y+h));q(v(ro,end,y),v(ri,end,y),v(ri,end,y+h),v(ro,end,y+h));
    const geo=new THREE.BufferGeometry();geo.setAttribute('position',new THREE.Float32BufferAttribute(positions,3));geo.computeVertexNormals();return mesh(geo,mat,name,parent);
  }
  function chair(name,x,z,angle=0,parent=group,accent='dark') {
    const g=new THREE.Group();g.name=name;g.position.set(x,.35,z);g.rotation.y=angle;parent.add(g);
    cylinder('Chair foot',0,.04,0,.25,.07,'trim',g);cylinder('Chair pedestal',0,.3,0,.07,.5,'trim',g);
    box('Seat cushion',0,.58,0,.58,.16,.57,accent,g);box('Upholstered back',0,.98,.25,.58,.72,.13,accent,g).rotation.x=-.1;
    for(const s of [-1,1]){box('Armrest',s*.34,.81,0,.11,.09,.45,'dark',g);box('Arm support',s*.34,.69,.16,.055,.28,.055,'trim',g);}
    return g;
  }
  function buttons(parent,x,y,z,cols=7) {for(let row=0;row<2;row++)for(let col=0;col<cols;col++)box('Control key',x+(col-(cols-1)/2)*.12,y,z+row*.14,.075,.025,.07,(col+row)%5===0?'red':(col+row)%3===0?'ochre':'white',parent);}
  return {group,mats,mesh,box,cylinder,tube,arc,chair,buttons};
}

export function buildBridgeStudy(){
  const k=kit('Main bridge · PDF 94–95');const {group,box,cylinder,arc,tube,chair,buttons}=k;
  cylinder('Deck structure',0,-.28,0,7.9,.5,'trim');
  arc('Raised station floor',3.25,7.7,0,.35,0,TAU,'floor');
  cylinder('Depressed command-well floor',0,.015,0,3.26,.1,'dark');
  cylinder('Command-well inset',0,.07,0,3.08,.06,'floor');
  // Outer service corridor remains on ship axis. Front segment is cut low for inspection.
  for(let i=0;i<24;i++){
    const a=i*TAU/24+.018,b=(i+1)*TAU/24-.018;
    arc(`Outer hull panel ${i+1}`,7.55,7.85,.35,i>=9&&i<=14?1.05:2.45,a,b,'shell');
    arc(`Service-ring lighting cove ${i+1}`,7.2,7.5,2.82,.08,a,b,'ochre');
  }
  arc('Service corridor inner boundary',6.42,6.55,.35,.12,0,TAU,'trim');
  // Source calls out a 36° offset of bridge command/visual axis, not of whole dome.
  const commandAxis=new THREE.Group();commandAxis.name='Command axis · 36° to ship';commandAxis.rotation.y=Math.PI/5;group.add(commandAxis);
  for(let i=0;i<10;i++){
    const a=i*TAU/10+.06,b=(i+1)*TAU/10-.06;
    // Access gaps leave visible steps into the well.
    arc(`Command handrail base ${i+1}`,3.12,3.23,.32,.09,a,b,'dark',commandAxis);
    arc(`Command handrail ${i+1}`,3.12,3.2,1.03,.075,a,b,'red',commandAxis);
    for(const ang of [a,b])cylinder('Rail stanchion',3.16*Math.sin(ang),.69,3.16*Math.cos(ang),.035,.67,'trim',commandAxis);
  }
  for(let i=0;i<3;i++)box('Command-well access step',0,.1+i*.1,3.3+i*.19,1.05,.12,.21,'shell',commandAxis);
  chair('Captain chair',0,1.2,0,commandAxis,'black');
  chair('Helm chair',-.69,-.67,0,commandAxis);chair('Navigation chair',.69,-.67,0,commandAxis);
  box('Helm/navigation console pedestal',0,.67,-1.57,1.6,.64,.65,'trim',commandAxis);
  const helm=box('Helm/navigation sloped desk',0,1.02,-1.65,1.9,.12,.86,'dark',commandAxis);helm.rotation.x=.15;
  for(const s of [-1,1]){box('Flight display',s*.47,1.1,-1.85,.53,.04,.25,'display',commandAxis);buttons(commandAxis,s*.47,1.12,-1.54,4);}
  box('Captain command arm panel',.36,1.22,1.13,.18,.08,.4,'dark',commandAxis);buttons(commandAxis,.36,1.28,1.1,1);
  const stations=['Communications','Command intelligence','Navigation','Defense weapons','Defense monitor','Environmental','Engineering','Engineering monitor'];
  const angles=[.48,1.12,1.8,2.41,2.99,4.49,5.13,5.73];
  stations.forEach((name,i)=>{
    const a=angles[i],g=new THREE.Group();g.name=`${name} station`;g.rotation.y=a;group.add(g);
    box('Station plinth',0,.62,5.65,2.15,.55,1.03,'dark',g);
    box('Angled operator console',0,1.05,5.27,2.12,.17,.72,'dark',g).rotation.x=-.25;
    box('Screen wall',0,1.83,6.08,2.18,1.42,.23,'shell',g);
    for(let j=-1;j<=1;j++){box('Inset display bezel',j*.67,1.91,5.94,.6,.71,.06,'dark',g);box('Monitor glass',j*.67,1.91,5.9,.49,.57,.025,'display',g);for(let r=0;r<3;r++)box('Monitor trace',j*.67,1.74+r*.13,5.88,.28+.04*r,.018,.01,'blue',g);}
    buttons(g,0,1.17,5.1,14);chair(`${name} operator chair`,0,4.28,Math.PI,g);
  });
  // Main visual screen sits on the offset command axis.
  box('Primary visual display housing',0,1.62,-5.95,3.5,2.15,.38,'shell',commandAxis);
  box('Primary visual display bezel',0,1.67,-5.71,3.18,1.76,.09,'dark',commandAxis);
  box('Primary visual display glass',0,1.67,-5.65,2.93,1.52,.025,'black',commandAxis);
  // Restrained display graphics are illustration only, not a reproduced screen.
  for(let i=0;i<19;i++) {const star=cylinder('Screen star',Math.sin(i*17)*1.28,1.08+(i%7)*.18,-5.63,.012,.012,'white',commandAxis);star.rotation.x=Math.PI/2;}
  // Aft turbolift is on the ship centerline, per plan.
  cylinder('Turbolift floor',0,.18,8.05,1.29,.35,'dark');
  arc('Turbolift shell',1.1,1.29,.35,2.35,-Math.PI*.7,Math.PI*.7,'shell').position.z=8.05;
  box('Turbolift port door',-.48,1.52,7.3,.94,2.34,.1,'red');box('Turbolift starboard door',.48,1.52,7.3,.94,2.34,.1,'red');
  box('Turbolift lintel',0,2.78,7.3,2.25,.15,.24,'trim');
  // Forward descending gangway and recognizable annular service infrastructure.
  for(let i=0;i<6;i++)box('Forward gangway stair',0,.3-i*.12,-6.7-i*.17,.95,.13,.19,'shell');
  for(const a of [.88,2.4,4.1,5.5]){const x=7*Math.sin(a),z=7*Math.cos(a);const o=box('Service isolation door',x,1.49,z,.86,2.13,.09,'trim');o.rotation.y=a;}
  return {group,length:17.3,sourcePages:[94,95],description:'Open-roof bridge reconstruction from deck plan and cross-sections. Offset command axis, sunken well, perimeter stations, service ring and aft turbolift; approximate metre scale.'};
}

export function buildHangarStudy(){
  const k=kit('MK-IX hangar · PDF 149–150');const {group,box,cylinder,arc,mesh,tube}=k;
  // Approximate proportions read from the 10 m scale bars: 20 m wide, 37 m long.
  const floor=new THREE.Shape();floor.moveTo(-10,-18);floor.lineTo(10,-18);floor.lineTo(10,8);floor.absarc(0,8,10,0,Math.PI,false);floor.lineTo(-10,-18);
  const geo=new THREE.ExtrudeGeometry(floor,{depth:.5,bevelEnabled:false,curveSegments:48});geo.rotateX(Math.PI/2);geo.translate(0,0,0);
  // Shape Y maps to Z after rotation; depth projects below deck.
  mesh(geo,'floor','Hangar deck 19 and curved stern');
  box('Forward bulkhead',0,3.3,-18,20,6.6,.38,'shell');
  for(const x of [-7.7,0,7.7]){box('Forward pocket-door frame',x,1.6,-17.77,2.6,3.2,.18,'trim');box('Forward pocket door',x,1.5,-17.64,2.26,2.9,.09,'dark');box('Door center seam',x,1.5,-17.57,.035,2.85,.02,'trim');}
  for(const s of [-1,1]){
    // Side walls include service recesses, raised gallery and dense window rhythm.
    box('Hangar side shell',s*10.05,3.35,-5, .35,6.7,26,'shell');
    box('Observation gallery lower fascia',s*9.25,4.4,-5,1.25,.42,25.7,'trim');
    box('Gallery upper fascia',s*9.25,5.8,-5,1.25,.28,25.7,'shell');
    box('Gallery ceiling lighting strip',s*8.57,4.12,-5,.075,.085,25.2,'ochre');
    for(let i=0;i<22;i++){
      const z=-17+i*1.17;box('Gallery mullion',s*8.61,5.13,z,.14,1.32,.1,'shell');
      box('Observation window',s*8.68,5.14,z+.54,.065,1.07,.92,'display');
      box('Gallery lower vent',s*8.58,3.82,z+.45,.08,.16,.59,'dark');
    }
    for(const z of [-16,-7,5]){
      box('Pylon structural bulkhead',s*9.25,2.1,z,1.2,4.2,.65,'trim');
      box('Side storage-pocket recess',s*9.82,1.35,z+1.3,.07,2.5,1.8,'dark');
      for(let r=0;r<7;r++)box('Scaling ladder rung',s*9.55,.28+r*.31,z+2.7,.58,.055,.055,'trim');
    }
    // Twin deck operations control towers at the stern, paired by P/S labels.
    box('Operations tower pedestal',s*8.05,2.6,7.3,1.5,1.25,1.6,'trim');
    box('Operations tower booth',s*8.05,3.68,7.3,1.9,1.05,2,'shell');
    for(let i=0;i<3;i++)box('Control-tower window',s*7.07,3.69,6.65+i*.63,.035,.72,.5,'display');
    box('Control-tower front glass',s*8.05,3.69,8.32,1.62,.72,.035,'display');
    const light=cylinder('Landing floodlight',s*7.7,4.7,9,.42,.3,'ochre');light.rotation.x=Math.PI/2;
    box('Air supply duct',s*9.55,6.13,-4,.54,.5,24.4,'trim');
    box('Flush cargo hatch',s*5.6,.04,10,3,.07,2.8,'dark');
    box('Cargo-hatch inset',s*5.6,.09,10,2.75,.035,2.55,'trim');
    box('Reserve fuel store hatch',s*8.67,1.1,3,.1,2.1,2.3,'dark');
  }
  // Circular marking is specifically the elevator/turntable, not a landing pad.
  cylinder('Maintenance elevator rim',0,.035,-5.1,3.9,.085,'dark');
  cylinder('Elevator platform',0,.09,-5.1,3.7,.08,'trim');
  arc('Turntable circular seam',3.37,3.43,.14,.025,0,TAU,'dark').position.z=-5.1;
  box('Elevator platform center seam',0,.15,-5.1,.025,.015,6.7,'dark');
  for(const x of [-3.52,3.52])box('Elevator safety edge',x,.16,-5.1,.09,.02,1.6,'ochre');
  // Source: four rectangular fields on stern deck.
  for(let row=0;row<2;row++)for(let col=0;col<2;col++)box('Spot landing target quarter',(col-.5)*1.7,.055,10.8+row*2.8,1.65,.035,2.75,(row+col)%2?'red':'ochre');
  for(const x of [-6.8,6.8])for(let i=0;i<14;i++)box('Deck guide stripe',x,.025,-15+i*1.55,.07,.02,.75,'white');
  // Six angular panels follow the curved stern. Part-open height is a display choice;
  // the manual establishes six clamshell segments, not their exact hinge trajectory.
  const rr=10,hingeZ=8;
  for(let i=0;i<6;i++){
    const verts=[],a0=i*Math.PI/6+.009,a1=(i+1)*Math.PI/6-.009,n=12,m=10;
    const point=(a,p)=>[rr*Math.cos(a)*Math.cos(p),6.3*Math.sin(p),hingeZ+rr*Math.sin(a)*Math.cos(p)];
    for(let j=0;j<n;j++)for(let l=0;l<m;l++){
      const a=a0+(a1-a0)*j/n,b=a0+(a1-a0)*(j+1)/n,p=l*.43/m,q=(l+1)*.43/m;
      const A=point(a,p),B=point(b,p),C=point(b,q),D=point(a,q);verts.push(...A,...B,...C,...A,...C,...D);
    }
    const g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.Float32BufferAttribute(verts,3));g.computeVertexNormals();const material=k.mats.shell.clone();material.side=THREE.DoubleSide;mesh(g,material,`Clamshell door segment ${i+1}`);
    for(const a of [a0,a1])tube('Clamshell radial frame',Array.from({length:10},(_,j)=>point(a,j*.43/9)),.075,'trim');
  }
  // Separate rim identifies fantail beyond door mechanism.
  arc('Stern fantail rim',10,10.55,-.27,.28,-Math.PI/2,Math.PI/2,'trim').position.z=8;
  box('Overhead cosmic-ray shield cutaway',0,6.85,8.1,6.8,.3,1.5,'shell');
  const beacon=cylinder('Stern homing beacon',0,7.13,8.1,.54,.31,'ochre');
  // Side section exposes one maintenance-shop strip beneath Deck 19.
  box('Deck 20 maintenance shelf',-8.05,-2.65,-4,3.4,.25,24,'trim');
  for(let i=0;i<5;i++){box('Maintenance partition',-8.05,-1.35,-15+i*4.8,3.4,2.4,.12,'shell');box('Maintenance workbench',-8.9,-1.43,-13+i*4.8,1.2,.12,2.2,'dark');}
  return {group,length:37,sourcePages:[149,150],description:'MK-IX hangar dollhouse from Deck 19 plan and port elevation. Six clamshell segments, galleries, paired control towers, landing target, elevator turntable and Deck 20 shop section. Approximate dimensions; doors posed partly open.'};
}

export function buildImpulseStudy(){
  const k=kit('Impulse power unit · PDF 143');const {group,mesh,box,cylinder,tube}=k;
  // Stated source envelope: 5.2 m long × 4.5 m wide × 2.8 m high.
  // Tube positions/counts, twin firing chambers and five front connections follow
  // TO:03:10:20. Recess depths, subtle colors and fine seam widths are reconstructed.
  function wedge(name,y,height,mat,inset=0,start=-2.6,end=2.6){
    const fw=1.4+.85*(start+2.6)/5.2-inset,rw=1.4+.85*(end+2.6)/5.2-inset;
    const s=new THREE.Shape();s.moveTo(-fw,start);s.lineTo(fw,start);s.lineTo(rw,end);s.lineTo(-rw,end);s.closePath();
    const g=new THREE.ExtrudeGeometry(s,{depth:height,bevelEnabled:false});g.rotateX(Math.PI/2);g.translate(0,y+height,0);return mesh(g,mat,name);
  }
  wedge('Twin-unit upper housing',2.54,.23,'shell');
  wedge('Twin-unit lower housing',0,.24,'shell');
  wedge('Inner reactor casing',.24,2.30,'trim',.27,-2.53,2.29);
  // Six vertical circulation tubes per flank, twelve total. Slightly slanted
  // source elevation is represented by angled tube axes matching the flare.
  for(const side of [-1,1])for(let i=0;i<6;i++){
    const z=-2.18+i*.86,halfWidth=1.4+.85*(z+2.6)/5.2;
    const x=side*(halfWidth-.165);
    const assembly=new THREE.Group();assembly.name=`Circulation tube assembly ${side}:${i+1}`;assembly.position.set(x,1.41,z);assembly.rotation.z=side*.045;group.add(assembly);
    cylinder(`Flux circulation tube ${side<0?'port':'starboard'} ${i+1}`,0,0,0,.145,2.18,'shell',assembly);
    cylinder('Upper tube socket',0,1.10,0,.185,.10,'dark',assembly);
    cylinder('Lower tube socket',0,-1.13,0,.185,.12,'dark',assembly);
    cylinder('Tube socket retaining collar',0,-1.02,0,.17,.10,'ochre',assembly);
  }
  // Two long rounded constriction channels are explicit in the top plan.
  for(const side of [-1,1]){
    const x=side*.78;
    // One continuous rounded-ended surface, separated from the top housing.
    const channel=new THREE.Shape();channel.moveTo(x-.075,-2.21);channel.absarc(x,-2.21,.075,Math.PI,Math.PI*2,false);channel.lineTo(x+.075,2.57);channel.lineTo(x-.075,2.57);channel.closePath();
    const channelGeo=new THREE.ExtrudeGeometry(channel,{depth:.011,bevelEnabled:false,curveSegments:20});channelGeo.rotateX(Math.PI/2);channelGeo.translate(0,2.788,0);mesh(channelGeo,'dark','Field-flux dip constriction channel');
    tube('Constriction channel inner ridge',[[x,2.778,-2.18],[x,2.778,.3],[x,2.778,2.55]],.022,'ochre');
  }
  // Rear elevation shows one half of a twin arrangement. Tapered square chamber
  // surrounds and concentric throats are repeated across the rear centerline.
  for(const side of [-1,1]){
    const cx=side*.98,cy=1.45,outer=.73,inner=.28,zOuter=2.6,zInner=2.38;
    const corners=[[-1,-1],[1,-1],[1,1],[-1,1]],p=[];
    for(let i=0;i<4;i++){
      const a=corners[i],b=corners[(i+1)%4];
      const A=[cx+a[0]*outer,cy+a[1]*outer,zOuter],B=[cx+b[0]*outer,cy+b[1]*outer,zOuter];
      const C=[cx+b[0]*inner,cy+b[1]*inner,zInner],D=[cx+a[0]*inner,cy+a[1]*inner,zInner];p.push(...A,...B,...C,...A,...C,...D);
    }
    const g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.Float32BufferAttribute(p,3));g.computeVertexNormals();const mat=k.mats.shell.clone();mat.side=THREE.DoubleSide;mesh(g,mat,`Firing chamber ${side<0?'port':'starboard'} tapered surround`);
    for(const [r,d,material] of [[.275,.018,'dark'],[.205,.022,'trim'],[.15,.025,'dark'],[.075,.028,'ochre']]){
      const throat=cylinder('Concentric firing throat',cx,cy,zInner+d/2,r,d,material);throat.rotation.x=Math.PI/2;
    }
    box('Rear chamber upper frame',cx,cy+outer,2.575,1.53,.07,.05,'dark');
    box('Rear chamber lower frame',cx,cy-outer,2.575,1.53,.07,.05,'dark');
    for(const s of [-1,1])box('Rear chamber side frame',cx+s*outer,cy,2.575,.07,1.53,.05,'dark');
  }
  // Front feed chute and exactly five recirculation connections.
  box('Fuel hopper feed chute surround',0,1.99,-2.55,.85,.56,.06,'shell');
  box('Fuel hopper feed chute opening',0,1.99,-2.589,.68,.39,.012,'dark');
  box('Feed chute lower lip',0,1.79,-2.59,.77,.06,.02,'trim');
  for(let i=0;i<5;i++){
    const x=(i-2)*.44;
    for(const [r,z,mat] of [[.115,-2.56,'dark'],[.078,-2.575,'trim'],[.05,-2.587,'black']]){
      const port=cylinder(`Heat-exchanger recirculation connection ${i+1}`,x,.45,z,r,.018,mat);port.rotation.x=Math.PI/2;
    }
  }
  // Central seam identifies twin units without inventing extra exhausts.
  box('Twin-unit housing center seam',0,2.780,0,.025,.008,5.15,'trim');
  return {group,length:5.2,sourcePages:[143],description:'Impulse power unit IP186E/2-IR reconstructed from three views. Stated envelope 5.2 × 4.5 × 2.8 m; twelve circulation tubes, twin firing chambers, feed chute and five heat-exchanger connections. Undimensioned recess depths are interpreted.'};
}
