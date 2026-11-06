// Equipment Locker study builders. Units: centimetres. X width, Y length (front = -Y), Z up.
// Numbers marked "printed" come from the sheet; everything else is measured from the drawing at its
// scale bar or interpreted. Per-item sourcing lives in model-source/equipment-content.py (specs vs derived vs interpretation).
import {T,group,box,rbox,cyl,sphere,torus,lathe,sideProfile,planExtrude,slats,loft,smooth} from './equipment-kit.mjs';

const knurl=(g,r,len,[x,y,z],axis,n=36,mat='dark')=>{for(let i=0;i<n;i++){const a=i/n*Math.PI*2;const p=axis==='y'?[x+Math.cos(a)*r,y,z+Math.sin(a)*r]:[x+Math.cos(a)*r,y+Math.sin(a)*r,z];const b=box(g,axis==='y'?[.09,len,.09]:[.09,.09,len],p,mat,'knurl');b.rotation[axis]= -a;}};

// ---------- Hand Phaser Type I — PDF 103, TO 01:08:50 ----------
// Printed: W.O.A 49.40 mm, L.O.A 107.20 mm, D.O.A 27.00 mm. Body gloss black SF32UC, face plate br. antimony SF02UC.
function phaser1Parts(g,[ox,oy,oz]=[0,0,0]){
 const L=10.72,W=4.94,D=2.7,y0=oy-L/2;
 // Plan (top view) width and side-view depth stations, measured against the 0–30 mm bar (≈6.8 px/mm at 1400 px).
 // [fraction of length from emitter end, half-width, half-depth, z-offset of section centre]
 const st=[[0,.0,.0],[.01,1.55,.85,-.05],[.04,2.12,1.08,-.05],[.1,2.4,1.2,-.03],[.22,2.47,1.3,0],[.4,2.42,1.35,0],[.6,2.2,1.35,0],[.8,1.86,1.35,0],[.93,1.55,1.3,0],[.985,1.2,1.15,0],[1,.0,.0,0]];
 const stations=st.map(([f,hw,hh,zc])=>[y0+.25+f*(L-.35),hw,hh*.96,oz+(zc||0),ox]);
 loft(g,smooth(stations,5),'black','body shell',3.2);
 // Photon emitter on the front face, with the antimony face plate.
 rbox(g,[1.9,.28,1.25],[ox,y0+.32,oz+.05],.2,'metal','face plate');
 cyl(g,.42,.36,[ox,y0+.12,oz+.05],'y','metal','1.02 MeV photon emitter');
 cyl(g,.26,.06,[ox,y0-.07,oz+.05],'y','glass','emitter lens');
 box(g,[.5,.25,.22],[ox+.98,y0+.28,oz+.82],'metal','emitter sight');
 // Top: electron aspirator pile (cross-hatched panel), trigger, force wheel, light, indicator dial.
 const top=oz+1.27;
 rbox(g,[1.8,2.55,.14],[ox,y0+3.25,top-.02],.12,'dark','electron aspirator pile');
 for(let i=0;i<7;i++)box(g,[1.7,.05,.06],[ox,y0+2.1+i*.38,top+.06],'grey','pile lattice');
 rbox(g,[1.7,.6,.16],[ox,y0+4.95,top-.03],.15,'metal','trigger');
 for(let i=0;i<9;i++)box(g,[.32,.06,.18],[ox-1.15,y0+6.1+i*.13,top],'grey','force setting wheel');
 cyl(g,.15,.12,[ox-.3,y0+6.55,top],'z','blue','operational light (blue)');
 torus(g,.18,.035,[ox-.3,y0+6.55,top+.05],'z','metal','light bezel');
 rbox(g,[.62,1.4,.1],[ox+.82,y0+6.65,top-.01],.06,'white','force indicator dial');
 for(let i=0;i<5;i++)box(g,[.3,.03,.03],[ox+.82,y0+6.1+i*.28,top+.05],'black','dial graduations');
 // Side: deflector shield strip and access plate step; bottom: magnatomic adhesion area.
 for(const s of[-1,1])box(g,[.08,7.2,.18],[ox+s*2.38,y0+4.6,oz+.2],'metal','deflector shield');
 rbox(g,[2.4,2.3,.08],[ox,y0+7.0,oz-1.36],.4,'dark','magnatomic adhesion area');
 cyl(g,.18,.06,[ox,y0+9.5,oz-1.33],'z','metal','access plate screw');
}
export function phaser1(){const g=group('Hand Phaser Type I');phaser1Parts(g);return g;}

// ---------- Hand Phaser Type II — PDF 104–105, TO 01:08:52–53 ----------
// Printed: L.O.A 221.00 mm, W.O.A 49.40 mm, D.O.A 157.50 mm (assembly with Type I locked on).
// Colours: br. antimony SF02UC, gl. bluegray SF31UC, gloss black SF32UC, (P) clear white topaz beam shield.
export function phaser2(){
 const g=group('Hand Phaser Type II');const Y0=-11.05;
 // Beam emitter and topaz beam shield.
 lathe(g,[[0,0],[.18,0],[.32,.6],[.42,1.6],[.5,2.05],[0,2.05]],[0,Y0,0],'y','metal','beam emitter');
 cyl(g,.12,1.6,[0,Y0+.85,0],'y','glass','beam shield (P)');
 // Photon accelerator: antimony collars either side of a knurled band.
 cyl(g,1.5,.45,[0,Y0+2.3,0],'y','metal','accelerator collar');
 cyl(g,1.66,1.2,[0,Y0+3.1,0],'y','dark','photon accelerator');
 knurl(g,1.66,1.2,[0,Y0+3.1,0],'y',40,'grey');
 cyl(g,1.5,.85,[0,Y0+4.1,0],'y','metal','accelerator collar');
 // Forward lockplate: flared block; its top recess receives the Type I face plate.
 loft(g,[[Y0+4.5,1.2,1.25,0],[Y0+5.4,1.68,1.38,.1],[Y0+6.1,1.68,1.38,.1]],'bluegray','forward lockplate',4);
 box(g,[3.2,.55,2.0],[0,Y0+5.85,2.2],'bluegray','forward lockplate upstand');
 // Main body: blue-grey bar, slightly tapering to the rear grip-butt.
 loft(g,smooth([[Y0+6.0,1.45,1.2,0],[Y0+8,1.55,1.22,0],[Y0+12,1.55,1.22,0],[Y0+16,1.48,1.2,0],[Y0+19.6,1.3,1.2,0],[Y0+21.9,1.15,1.05,-.05],[Y0+22.1,.9,.8,-.05]],4),'bluegray','body',3.4);
 // Dilithium crystal cell (side) and deflector-shield ribs (top).
 for(const s of[-1,1]){cyl(g,.75,.12,[s*1.56,Y0+7.9,.1],'x','metal','dilithium crystal cell');box(g,[.06,1.4,.08],[s*1.62,Y0+7.9,.1],'dark','cell slot');}
 for(let i=0;i<3;i++)box(g,[.08,8.6,.14],[-.25+i*.25,Y0+11.1,1.22],'metal','deflector shield');
 // Rear lockplate and force setting dial on the butt.
 box(g,[2.6,.7,.75],[0,Y0+17.2,1.55],'bluegray','rear lockplate');
 cyl(g,.55,.45,[0,Y0+19.0,-1.4],'z','metal','force setting dial',.85);
 cyl(g,.42,.35,[0,Y0+19.0,-1.8],'z','grey','force setting dial knob');
 for(let i=0;i<4;i++)box(g,[.12,1.8,.12],[-.38+i*.25,Y0+20.6,1.18],'dark','rear deflector shield');
 cyl(g,.42,.06,[1.5,Y0+16.6,0],'x','metal','lock release');
 // Grip: raked 21° rearward from vertical (lines-and-sections sheet).
 const grip=group('grip');const gl=11.1;
 loft(grip,smooth([[0,1.35,2.3,0],[1.5,1.38,2.15,0],[5,1.35,2.0,0],[9,1.32,1.95,0],[gl-.5,1.22,1.85,0],[gl,.9,1.5,0]],4),'black','grip',3.2);
 for(const s of[-1,1])rbox(grip,[.1,7,2.4],[s*1.36,5.2,.2],.6,'dark','magnatomic adhesion area');
 rbox(grip,[.9,1.9,.25],[0,1.7,-2.15],.15,'metal','firing triggers (S/T)');
 box(grip,[.95,.05,.27],[0,1.7,-2.17],'black','S/T divide');
 grip.rotation.x=-(Math.PI/2-THREE_RAD(21));grip.position.set(0,Y0+10.2,-.6);
 g.add(grip);
 // Type I locked on top between the lockplates.
 phaser1Parts(g,[0,Y0+6.2+5.36,1.2+1.35]);
 return g;
}
function THREE_RAD(d){return d*Math.PI/180;}

// ---------- Ray Gun — PDF 106, TO 01:08:58 ----------
// Printed: length overall 23.5 cm, maximum diameter 8.4 cm, weight 630 gm, model Type I.
// Colours: translucent (emitter tube), antimony SF02UC, gray SF30UC, black SF32UC.
// Radii are measured on the plan at the 0–5 cm bar (58 px/cm at 1400 px); the broken-out side view shows a round body.
export function rayGun(){
 const g=group('Ray Gun');const L=23.5,y=t=>t-L/2;// t = cm from the emitter tip
 const steps=[[0,1.64,.52],[1.64,3.1,.73],[3.1,4.05,.86],[4.05,5.34,.99],[5.34,6.64,1.09],[6.64,7.85,1.22]];
 for(const [a,b,r] of steps){cyl(g,r,b-a,[0,y((a+b)/2),0],'y','glass','diamond emitter tube');torus(g,r,.025,[0,y(b),0],'y','metal','tube step ring');}
 cyl(g,.28,7.9,[0,y(3.95),0],'y','dark','emitter core');
 sphere(g,.3,[0,y(-.02),0],'black',[1,.25,1],'emitter aperture');
 // Collette: stepped antimony rings.
 const col=[[7.85,1.55],[8.15,1.9],[8.45,2.2],[8.75,2.45],[9.05,2.62],[9.35,2.72]];
 col.forEach(([t,r],i)=>cyl(g,r,(col[i+1]?.[0]??9.55)-t,[0,y(t+((col[i+1]?.[0]??9.55)-t)/2),0],'y','metal','collette'));
 // Body housing: turned ogive, widest 8.4 cm, tapering to the tail.
 const prof=[[0,9.55],[3.95,9.6],[4.12,10.6],[4.2,11.8],[4.2,13.3],[4.05,14.9],[3.6,16.6],[3.0,18.4],[2.15,20.2],[1.2,21.9],[.45,23.0],[0,23.5]];
 lathe(g,prof.map(([r,t])=>[r,y(t)]),[0,0,0],'y','grey','body housing',64);
 // Triggers: antimony oval strip on the upper surface, divided offensive / defensive.
 // Triggers: antimony oval strip seated on the upper surface, divided offensive / defensive (t = 10.3–19.3 cm on the plan).
 const R=t=>{for(let i=0;i<prof.length-1;i++){const [r0,t0]=prof[i],[r1,t1]=prof[i+1];if(t>=t0&&t<=t1)return r0+(r1-r0)*(t-t0)/(t1-t0);}return 0;};
 const ts=[0,.25,1.2,2.5,4.5,6.5,7.8,8.75,9].map(u=>10.3+u),hw=[0,.6,.85,.88,.88,.88,.85,.6,0];
 loft(g,ts.map((t,i)=>[y(t),hw[i],.12,R(t)+.01]),'metal','triggers',2.2);
 for(const u of[1.05,4.5,7.95]){const t=10.3+u;box(g,[1.8,.05,.32],[0,y(t),R(t)],'black','trigger divide');}
 return g;
}

// ---------- Communicator Type I — PDF 137, TO 03:02:00 ----------
// Printed: L.O.A 113.5 mm, W.O.A 63.5 mm, H.O.A 28 mm, weight 200 gm, range 12 000 km.
// Colours: gold SF03UC, antimony SF02UC, black SF32UC. Measured at the 0–5 cm bar (68 px/cm).
export function communicator(open=true){
 const g=group('Communicator');const L=11.35,W=6.35,H=2.8;
 // Lower and upper body shells meeting at a gold equatorial band.
 rbox(g,[W-.12,L-.12,1.32],[0,0,.66],1.0,'black','lower body shell (removable bottom)');
 rbox(g,[W-.1,L-.1,1.05],[0,0,1.32+.5],1.0,'black','upper body shell');
 const band=group('band');rbox(band,[W,L,.16],[0,0,0],1.05,'gold','gold trim band');band.position.z=1.36;g.add(band);
 // Hinge barrel at the antenna end (front, -Y) and tuned ferrite loop.
 cyl(g,.42,4.6,[0,-L/2+.62,2.3],'x','gold','antenna hinge');
 for(const s of[-1,1])box(g,[.3,.9,.5],[s*2.45,-L/2+.85,2.25],'gold','hinge cheek');
 box(g,[3.9,.18,.32],[0,-L/2+1.15,2.3],'metal','tuned ferrite loop');
 // Antenna grille: perforated antimony plate hinged open about the barrel.
 const lid=group('antenna grille');const gw=4.4,gl=8.3;
 rbox(lid,[gw,gl,.14],[0,gl/2,0],.25,'metal','antenna grille');
 for(let i=0;i<12;i++)for(let j=0;j<22;j++){const x=-gw/2+.32+i*(gw-.64)/11+(j%2)*.16,yy=.45+j*(gl-.9)/21;if(Math.abs(x)>gw/2-.25)continue;cyl(lid,.13,.06,[x,yy,.07],'z','dark','grille perforation',.13,10);}
 lid.position.set(0,-L/2+.62,2.62);lid.rotation.x=open?THREE_RAD(110):0;g.add(lid);
 // Exposed control deck under the open grille: LEDs and switches called out on the sheet.
 rbox(g,[4.3,8.1,.08],[0,.6,2.35],.3,'dark','control deck');
 for(const [x,yy,m,n] of[[-.9,-.6,'red','red (on) L.E.D.'],[.2,-.6,'amber','yellow (T) L.E.D.'],[1.3,-.6,'blue','blue (R) L.E.D.']])cyl(g,.16,.12,[x,yy,2.42],'z',m,n);
 cyl(g,.38,.12,[-1.1,1.9,2.42],'z','metal','transmit/receive switch (SW1)');
 cyl(g,.3,.12,[1.0,1.9,2.42],'z','metal','channel switch (SW2)');
 slats(g,5,[1.4,.12,.06],[0,3.7,2.42],'y',.32,'grey','vent');
 // Bottom: magnatomic adhesion surface, two attach screws, on/off switch.
 rbox(g,[2.8,4.0,.06],[0,-.4,-.01],.2,'dark','magnatomic adhesion surface');
 for(const s of[-1,1])cyl(g,.2,.05,[0,-.4+s*2.6,-.01],'z','metal','attach screw');
 box(g,[.5,.7,.08],[-2.3,-4.6,-.02],'gold','on/off switch (SW)');
 return g;
}

// ---------- Tricorders — Sciences PDF 112–114 (TO 02:04:00–03), Medical PDF 124–126 (TO 02:11:00–02) ----------
// Printed (both): 177.8 mm high closed, 114.3 mm wide, 48.3 mm deep; 127 cm naugahyde strap. Medical: 900 gm.
// Colours: antimony SF02UC, olive SF14UC, black SF32UC (pebbled). The studies show the open arrangement
// (PDF 113 / 125): display head raised ≈15 mm (measured 193 mm overall), drawn upright as in the front views.
// Front-view layout measured at 69 px/cm on PDF 125; X = width, Y = depth (front face toward -Y), Z = up.
function roundRectPts(y0,y1,z0,z1,r,n=6){const pts=[],arc=(cy,cz,a0)=>{for(let i=0;i<=n;i++){const a=a0+i/n*Math.PI/2;pts.push([cy+r*Math.cos(a),cz+r*Math.sin(a)]);}};arc(y1-r,z0+r,-Math.PI/2);arc(y1-r,z1-r,0);arc(y0+r,z1-r,Math.PI/2);arc(y0+r,z0+r,Math.PI);return pts;}
function tricorder(kind){
 const g=group(kind==='medical'?'Medical Tricorder':'Sciences Tricorder');
 const W=11.43,H=17.78,D=4.83,X=px=>(px-848)/69,Zf=py=>(1680-py)/68.6,front=-D/2+.22;
 // Side body storage shells: rounded narrow-side silhouette, deepest in the upper third.
 for(const s of[-1,1]){
  const pts=roundRectPts(-D/2,D/2,0,H,1.0);const shell=sideProfile(g,pts,1.05,[s*(W/2-.525),0,0],'black','side body storage shell',.4);
  shell.scale.y=1;// taper toward the base: pinch the lower front
  box(g,[.12,.6,.6],[s*(W/2-.07),-D/2+.9,H*.62],'metal','hinge plate');
  cyl(g,.32,.1,[s*(W/2-.05),-D/2+1.3,H-1.854],'x','metal','head pivot screw');
  for(let i=0;i<11;i++)cyl(g,.15,.06,[s*(W/2-.01),D/2-1.1,2.2+i*.55],'x','dark','vent hole');
  box(g,[.22,.5,.35],[s*(W/2-.03),-D/2+.35,1.1],'metal','lower catch');
  // Case frames (brushed) between shells and core.
  box(g,[.22,D-.35,H-.1],[s*(W/2-1.16),0,H/2],'metal','case frame (brushed)');
 }
 // Core body behind the front panels.
 if(kind==='medical'){const zb=Zf(1315),zt=Zf(1015);box(g,[W-2.5,D-.5,H-.15-zt],[0,.05,zt+(H-.15-zt)/2],'black','core body');box(g,[W-2.5,D-2.4,zt-.05],[0,1.0,zt/2],'black','core body (behind analyzer bay)');}
 else box(g,[W-2.5,D-.5,H-.15],[0,.05,H/2],'black','core body');
 // Display-control head, raised: black cover, antimony faceplate.
 const hz0=Zf(670),hz1=Zf(362),hw=8.82;
 rbox(g,[hw,D-.6,hz1-hz0],[0,.1,(hz0+hz1)/2],.35,'black','display-control head cover');
 box(g,[hw-.4,.12,Zf(390)-Zf(655)],[0,-D/2+.25,(Zf(390)+Zf(655))/2],'metal','video/controls faceplate');
 rbox(g,[4.84,.14,3.29],[X(745),-D/2+.2,(Zf(415)+Zf(640))/2],.55,'screen','video display');
 box(g,[1.29,.14,1.32],[X(1022),-D/2+.2,Zf(455)],'dark','sensor array');
 for(let i=0;i<4;i++){box(g,[1.29,.16,.04],[X(1022),-D/2+.18,Zf(455)-.5+i*.33],'grey','sensor lattice');}
 const leds=[['blue','matched comparison (blue) L.E.D.'],['amber','sub-normal (amber) L.E.D.'],['red','danger-alarm (red) L.E.D.']];
 [960,1028,1098].forEach((px,i)=>{cyl(g,.31,.25,[X(px),-D/2+.3,Zf(545)],'y','metal','L.E.D. bezel');cyl(g,.22,.1,[X(px),-D/2+.13,Zf(545)],'y',leds[i][0],leds[i][1]);});
 ['disc selector','channel selector','record/play w/ volume'].forEach((n,i)=>{const x=X([960,1028,1098][i]);cyl(g,.43,.32,[x,-D/2+.3,Zf(618)],'y','grey',n+' control');knurl(g,.43,.32,[x,-D/2+.3,Zf(618)],'y',18,'dark');cyl(g,.1,.1,[x,-D/2+.1,Zf(618)],'y','green','green L.E.D.');});
 // Frame member band.
 box(g,[W-2.6,.2,Zf(670)-Zf(755)],[0,front,(Zf(670)+Zf(755))/2],'metal','frame member');
 // Record-compare section: eight removable record/play discs on edge, compression plate, speaker/mic faceplate.
 const rz0=Zf(1000),rz1=Zf(755);
 box(g,[X(870)-X(545),.15,rz1-rz0],[(X(545)+X(870))/2,front+.6,(rz0+rz1)/2],'dark','disc holder frame');
 for(let i=0;i<8;i++){const x=X(565)+i*.59;cyl(g,1.59,.5,[x+.22,front+1.55,(rz0+rz1)/2+.05],'x','glass','removable play/record disc');}
 box(g,[.12,1.8,rz1-rz0-.2],[X(545)+.06,front+1.4,(rz0+rz1)/2],'metal','compression plate');
 box(g,[X(870)-X(545),.6,.25],[(X(545)+X(870))/2,front+1.2,rz0+.12],'metal','disc holder plate');
 box(g,[X(1150)-X(885),.18,rz1-rz0],[(X(885)+X(1150))/2,front,(rz0+rz1)/2],'black','faceplate');
 const sx=X(1020),sz=Zf(875);torus(g,1.48,.12,[sx,front-.1,sz],'y','metal','speaker-microphone ring');
 cyl(g,1.38,.08,[sx,front-.06,sz],'y','dark','speaker-microphone');
 for(let i=-5;i<=5;i++){const w=2*Math.sqrt(Math.max(0,1.3**2-(i*.24)**2));if(w>.2)box(g,[w,.05,.04],[sx,front-.11,sz+i*.24],'grey','speaker grille');}
 // Record/play section lid, folded open below the rack.
 box(g,[W-2.6,.15,Zf(1015)-Zf(1060)],[0,front-.05,(Zf(1015)+Zf(1060))/2],'black','R/P section lid (open)');
 if(kind==='medical'){
  // Analyzer bay: life-form functions sensor/analyzer; lower compartment lid partially open.
  box(g,[W-2.6,.1,Zf(1060)-Zf(1315)],[0,-.15,(Zf(1060)+Zf(1315))/2],'dark','analyzer bay');
  box(g,[X(668)-X(548),1.3,Zf(1065)-Zf(1665)],[(X(548)+X(668))/2,front+1.05,(Zf(1065)+Zf(1665))/2],'olive','life form functions sensor/analyzer');
  box(g,[X(668)-X(548)-.1,.1,.4],[(X(548)+X(668))/2,front-.22,Zf(1080)],'metal','analyzer label plate');
  const lid=group('lower compartment lid');box(lid,[W-2.6,.18,Zf(1315)],[0,0,Zf(1315)/2],'black','lower compartment lid (partially open)');
  box(lid,[2.9,.1,.32],[X(845),-.12,Zf(1418)],'metal','lid pull');lid.position.set(0,front,0);lid.rotation.x=THREE_RAD(14);g.add(lid);
  for(const z of[Zf(1015),Zf(670)])box(g,[3.0,.06,.55],[-1.2,front-.12,z-.45],'white','antimony label plate');
 }else{
  // Circuitry/power-supply section, closed ("to be opened only by Class A specialist ratings").
  box(g,[W-2.6,.18,Zf(1060)],[0,front,Zf(1060)/2],'black','circuitry/power supply section lid');
  box(g,[3.0,.06,.55],[-1.2,front-.12,Zf(1060)-.6],'white','antimony label plate');
  for(let i=0;i<3;i++)box(g,[W-2.7,.04,.04],[0,front-.11,1.2+i*.12],'dark','pebbled seam');
 }
 // Shoulder strap lugs (127 cm naugahyde strap, shown as the two attachment loops).
 for(const s of[-1,1]){box(g,[.1,1.1,.45],[s*(W/2-.04),.6,H*.72],'dark','shoulder strap lug');}
 return g;
}
export const communicatorClosed=()=>communicator(false);
export const sciencesTricorder=()=>tricorder('sciences');
export const medicalTricorder=()=>tricorder('medical');

// ---------- Heartbeat Reader — PDF 127, TO 02:11:04 ----------
// Printed: model SFAF/SG-MK06-Type M; length overall 17.75 cm; maximum diameter 5.2 cm; weight 230 gm.
// Colours: antimony SF02UC, black SF32UC, blue and red L.E.D.s. Upright, Z = length. Measured at 67.2 px/cm (1400 px plate).
export function heartbeatReader(){
 const g=group('Heartbeat Reader');const z=py=>(1550-py)/65.6;// stretched 2.4% so the plate length meets the printed 17.75 cm
 // Base with the solo/multiple reading selector and audible volume control, flanked by grip tabs.
 cyl(g,1.04,z(1445)-z(1550),[0,0,(z(1445)+z(1550))/2],'z','metal','reading selector / volume control');
 for(let i=0;i<24;i++){const a=i/24*Math.PI*2;box(g,[.04,.04,.6],[Math.cos(a)*1.06,Math.sin(a)*1.06,.8],'dark','graduation');}
 rbox(g,[4.3,.56,1.45],[0,0,.78],.25,'metal','grip tabs');
 // Body shell: gently tapering tube.
 lathe(g,[[0,z(1445)],[1.0,z(1445)],[1.07,z(1100)],[1.15,z(640)],[0,z(640)]],[0,0,0],'z','metal','body shell',48);
 // Controls on the front (-Y) face.
 rbox(g,[.5,.1,1.25],[.3,-1.12,z(765)],.08,'black','digital readout with floating decimal');
 for(let i=0;i<4;i++)box(g,[.3,.04,.22],[.3,-1.18,z(733)-i*.3],'red','readout digit');
 cyl(g,.11,.08,[-.35,-1.14,z(722)],'y','blue','multiple reading cancel indicator');
 cyl(g,.11,.08,[-.35,-1.14,z(803)],'y','red','unit go indicator');
 for(const [py,n] of[[848,'slide switch: activate'],[905,'slide switch: audible']]){rbox(g,[1.15,.1,.48],[0,-1.1,z(py)],.06,'black',n);box(g,[.3,.12,.4],[-.25,-1.15,z(py)],'metal',n+' slider');}
 // Head: omnidirectional sensor under guard/ground-plane screens, joined by the clamp band.
 sphere(g,2.42,[0,0,z(548)],'dark',[1,1,1],'guard and anti-stray audible noise screen');
 for(let i=0;i<12;i++){const a=i/12*Math.PI;torus(g,2.43,.025,[0,0,z(548)],'z','grey','screen mesh').rotation.set(Math.PI/2,a,0);}
 for(let k=-4;k<=4;k++){const r=Math.sqrt(2.43**2-(k*.5)**2);torus(g,r,.025,[0,0,z(548)+k*.5],'z','grey','screen mesh');}
 cyl(g,2.64,.5,[0,0,z(495)],'z','metal','clamp band');
 return g;
}

// ---------- Spray Applicator — PDF 128, TO 02:11:06 ----------
// Printed: model SFAF/SG-MK01-70, size 70; length overall (loaded) 6.5 cm; maximum diameter 1.9 cm; weight loaded 160 gm;
// vial: 70 cc, 80 gm loaded, pressurised to 1.30 kg/cm². Nozzles: extra fine .0025, fine .025, medium .20 mm, coarse special order.
export function sprayApplicator(){
 const g=group('Spray Applicator');const z=py=>(770-py)/68.4;// 68.4 px/cm on the 1400 px plate
 // (A) applicator body, (B) spray trigger, (E) interchangeable nozzle at the base.
 cyl(g,.93,z(627)-z(770),[0,0,(z(627)+z(770))/2],'z','metal','applicator body');
 cyl(g,.38,.08,[0,-.9,z(728)],'y','white','spray trigger (press to spray)');torus(g,.38,.03,[0,-.92,z(728)],'y','metal','trigger ring');
 for(const [a,b] of[[560,590],[597,627]])cyl(g,.95,z(a)-z(b),[0,0,(z(a)+z(b))/2],'z','grey','collar band');
 cyl(g,.6,.06,[0,0,.03],'z','grey','interchangeable nozzle');cyl(g,.08,.04,[0,0,.02],'z','black','nozzle orifice');
 // (C) interchangeable vial: transparent pressurised vial with fluted grip, (D) dispensing teat.
 cyl(g,.88,z(325)-z(560),[0,0,(z(325)+z(560))/2],'z','glass','interchangeable vial');
 for(let i=0;i<20;i++){const a=i/20*Math.PI*2;box(g,[.06,.06,z(330)-z(555)],[Math.cos(a)*.9,Math.sin(a)*.9,(z(330)+z(555))/2],'metal','vial flute');}
 cyl(g,.82,.12,[0,0,z(325)-.06],'z','metal','vial cap');
 return g;
}

// ---------- Medical Scanner — PDF 129, TO 02:11:07 ----------
// Printed: length overall 6.05 cm; maximum diameter 3.5 cm; weight 230 gm; sensitivity to .0001 EmV/AU²; reading groups A, B, Γ, K, Θ, Ξ.
// Colours: antimony SF02UC, gray SF30UC, black SF32UC. Measured at 68.75 px/cm.
export function medicalScanner(){
 const g=group('Medical Scanner');const z=py=>(742-py)/68.9;
 // (C) scanner housing with 48-mesh screen and (D) rotating scanner inside; (G) ground plane screen underneath.
 cyl(g,1.3,z(735)-z(742),[0,0,(z(735)+z(742))/2],'z','metal','base ring');
 cyl(g,1.24,z(590)-z(735),[0,0,(z(590)+z(735))/2],'z','mesh','scanner housing (48 mesh screen)');
 for(let i=0;i<10;i++)torus(g,1.25,.02,[0,0,z(735)+.15+i*.2],'z','grey','mesh');
 const rot=group('rotating scanner');box(rot,[.9,.25,1.7],[.55,0,0],'metal','rotating scanner vane');sphere(rot,.4,[.8,-.1,.2],'metal',[1,1,1],'scanner element');rot.position.set(0,0,(z(590)+z(735))/2);rot.rotation.z=.6;g.add(rot);
 torus(g,1.2,.06,[0,0,.08],'z','grey','life form type selection scale');
 cyl(g,.9,.04,[0,0,.02],'z','black','ground plane screen (48 mesh)');cyl(g,.22,.06,[0,0,.0],'z','metal','hub');
 // Collar and (A) computer housing with eight scalloped flutes; (B) activating switch; (E) readings dial on top.
 cyl(g,1.5,z(548)-z(590),[0,0,(z(548)+z(590))/2],'z','white','collar');
 const zt=z(325),zb=z(548);
 lathe(g,[[0,zb],[1.75,zb],[1.75,zt-.3],[1.62,zt-.06],[1.45,zt],[0,zt]],[0,0,0],'z','grey','computer housing',64);
 for(let i=0;i<8;i++){const a=i/8*Math.PI*2+Math.PI/8;cyl(g,.16,zt-zb-.45,[Math.cos(a)*1.66,Math.sin(a)*1.66,(zt+zb)/2-.1],'z','dark','housing flute');}
 box(g,[.48,.12,.95],[0,-1.72,z(515)],'black','activating switch (press on-off)');
 cyl(g,1.22,.06,[0,0,zt-.06],'z','white','readings dial');
 for(let i=0;i<6;i++){box(g,[.06,1.2,.03],[-.75+i*.3,0,zt-.02],'black','reading group bar');box(g,[.16,.12,.035],[-.75+i*.3,(i%3-1)*.3,zt-.01],'red','reading marker');}
 box(g,[1.9,.04,.035],[0,0,zt-.015],'blue','normal terran range');
 return g;
}

// ---------- Anabolic Protoplaser — PDF 130 (size 0, TO 02:11:13) and PDF 131 (size 2) ----------
// Printed size 0: model SFAF/SG-MK08-0; length 25, width 3.8, height 4.2 cm; 450 gm; intensity 0–100 EmV/AU².
// Printed size 2: length 35, width 5.6, height 6.95 cm (PDF 131). Colours: antimony SF02UC, gray SF30UC, red SF10UC, black SF32UC.
// Size-0 stations measured at 44 px/cm on the 1400 px plate; the size-2 unit reuses that layout scaled to its printed envelope.
function protoplaser(g,[ox,oy,oz],[sx,sy,sz],label){
 const p=group(label);const Y=py=>(py-865)/44;// plate y → cm, centred; front (cone tip) is +py, so negate
 const at=(py)=>-Y(py);
 // Housing: rounded-square section; flat black removable bottom panel, gray upper shell rising toward the front.
 const st=[[320,1.53,3.05],[600,1.65,3.2],[900,1.82,3.4],[1135,1.95,3.55],[1140,1.95,3.55]];
 loft(p,st.map(([py,hw,h])=>[at(py),hw,.34,.34]),'black','removable bottom panel',4);
 loft(p,st.map(([py,hw,h])=>[at(py),hw-.02,(h-.55)/2,.55+(h-.55)/2]),'grey','housing',4);
 // Antimony switch strip on top: activating switch and intensity control (D), with intensity force light (J).
 loft(p,smooth([[at(325),.45,.04,3.05],[at(600),.45,.12,3.22],[at(960),.45,.42,3.5],[at(965),.42,.05,3.42]],3),'metal','activating switch and intensity control',4);
 box(p,[.42,.42,.08],[0,at(820),3.86],'red','intensity force light');
 box(p,[2.6,1.3,.06],[0,at(1050),3.55],'white','top panel');
 box(p,[.06,1.1,.6],[1.95,at(1040),1.4],'metal','specifications plate');
 cyl(p,.22,.3,[0,at(1120),3.65],'z','red','effectivity sensor');
 cyl(p,.8,.05,[0,at(318),1.6],'y','dark','recharging chamber');
 // DNA match synthesization unit (F) and ray emission duct (G).
 cyl(p,1.28,Y(1275)-Y(1140),[0,at((1140+1275)/2),1.8],'y','metal','DNA match synthesization unit');
 cyl(p,.15,Y(1410)-Y(1275),[0,at((1275+1410)/2),1.8],'y','metal','ray emission duct',1.28);
 p.position.set(ox,oy,oz);p.scale.set(sx,sy,sz);g.add(p);
}
// Size 2, modelled from its own sheet (PDF 131, TO 02:11:12) at 34 px/cm (stretched 3% to the printed 35 cm).
function protoplaser2([ox,oy,oz]){
 const p=group('size 2 (PDF 131)'),at=py=>-(py-910)/34,zc=2.8;
 const st=[[315,1.53,3.3],[600,1.85,3.95],[900,2.2,4.6],[1200,2.75,5.6],[1206,2.75,5.6]];
 loft(p,st.map(([py,hw])=>[at(py),hw,.34,.34]),'grey','removable bottom panel',4);
 loft(p,st.map(([py,hw,h])=>[at(py),hw-.03,(h-.6)/2,.6+(h-.6)/2]),'grey','housing',4);
 for(const s of[-1,1])loft(p,st.map(([py,hw])=>[at(py),.02,.05,.62,s*(hw-.04)]),'dark','panel seam',2);
 // (D) intensity control strip on top with (K) intensity force light; (C) activating switch on the side; (J) specifications plate.
 const top=py=>{for(let i=0;i<st.length-1;i++){const [a,,h0]=st[i],[b,,h1]=st[i+1];if(py>=a&&py<=b)return h0+(h1-h0)*(py-a)/(b-a);}return 5.6;};
 loft(p,[320,600,900,1025,1030].map((py,i)=>[at(py),.8,[.05,.15,.38,.6,.05][i],top(py)+[.05,.15,.38,.6,.05][i]-.04]),'metal','intensity control (depress to increase intensity)',4);
 box(p,[.75,.75,.1],[0,at(885),top(885)+.62],'red','intensity force light');
 box(p,[3.8,2.1,.06],[0,at(1112),top(1112)],'white','specifications plate');
 box(p,[.1,1.0,2.9],[2.32,at(922),2.4],'black','activating switch (black off / red on)');
 for(let i=0;i<6;i++)box(p,[.12,.1,.42],[2.34,at(885)+i*.12,2.4],'red','switch ridges');
 cyl(p,1.2,.06,[0,at(318),2.3],'y','dark','recharging chamber');
 // (E) effectivity sensor nub at the front top, (F) DNA match synthesization unit flaring to the (G) ray emission duct.
 rbox(p,[1.4,1.0,1.4],[0,at(1180),5.6+.65],.3,'grey','effectivity sensor housing');cyl(p,.4,.08,[0,at(1180)-.52,6.25],'y','red','effectivity sensor');
 cyl(p,.86,(1245-1206)/34,[0,at(1225),zc],'y','metal','neck');
 cyl(p,1.86,(1355-1245)/34,[0,at(1300),zc],'y','metal','DNA match synthesization unit',.86);
 cyl(p,1.86,(1505-1355)/34,[0,at(1430),zc],'y','metal','ray emission duct housing');
 cyl(p,1.4,1.3,[0,at(1505)+.62,zc],'y','dark','recessed ray emission duct',.35);
 p.position.set(ox,oy,oz);return p;
}
export function anabolicProtoplaser(){
 const g=group('Anabolic Protoplaser');
 // Envelope of the size-0 layout before scaling: 3.9 × 24.8 × 3.92 cm; each unit is scaled to its printed W × L × H.
 protoplaser(g,[-3.3,0,0],[3.8/3.9,25/24.8,4.2/3.92],'size 0 (PDF 130)');
 g.add(protoplaser2([3.0,0,0]));
 return g;
}

// ---------- Surgical Scalpels — PDF 132, TO 02:11:14 ----------
// Printed: models SFAF/SG-MK10-000 / -00 / -0; cutting widths 1, 2, 3 AU; intensity 0–80, 0–75, 0–70 EmV/AU²;
// weights 227, 220, 220 gm; housing material rodinium (printed "RODINIUN"), antimony SF02UC. No dimensions printed:
// all sizes are measured at 68 px/cm on the 1400 px plate.
export function surgicalScalpels(){
 const g=group('Surgical Scalpels');
 const models=[{x:-4.4,body:[500,690],cone:[310,490],tip:0,name:'MK10-000'},{x:0,body:[985,1170],cone:[775,975],tip:.27,name:'MK10-00'},{x:4.4,body:[1555,1735],cone:[1262,1545],tip:.43,name:'MK10-0'}];
 for(const m of models){
  const s=group(m.name),k=68,bh=(m.body[1]-m.body[0])/k,ch=(m.cone[1]-m.cone[0])/k,r=1.88;
  cyl(s,r-.07,.25,[0,0,.12],'z','metal','body base');
  cyl(s,r,bh-.25,[0,0,.25+(bh-.25)/2],'z','metal','surgeon\'s grip');
  for(let i=0;i<14;i++)torus(s,r,.025,[0,0,.4+i*(bh-.6)/13],'z','grey','grip rib');
  cyl(s,r+.02,.16,[0,0,bh+.02],'z','white','intensity scale');
  for(let i=0;i<24;i++){const a=-.5+i*.045;box(s,[.02,.04,.1],[Math.sin(a)*(r+.03),-Math.cos(a)*(r+.03),bh+.05],'black','scale tick');}
  sphere(s,.48,[-1.0,-1.62,bh*.6],'dark',[1,.3,1.3],'trigger');
  box(s,[1.0,.12,bh*.42],[0,-r+.02,bh*.32],'grey','range scale lock');
  box(s,[1.0,.08,bh*.42],[0,-r+.08,bh*.74],'dark','intensity slide');
  cyl(s,r-.05,ch,[0,0,bh+.1+ch/2],'z','metal','prime focus / cutting tip',m.tip||.02);
  if(m.tip)cyl(s,m.tip*.5,.03,[0,0,bh+.1+ch],'z','glass','cutting tip');
  s.position.x=m.x;g.add(s);
 }
 return g;
}

// ---------- Ear Receiver — PDF 138, TO 03:02:02 ----------
// Printed: model SFAF/CC-MK05-0, size 0; length overall 6.55 cm; width overall 3.15 cm; maximum diameter 2.6 cm; 57 gm.
// Colours: antimony SF02UC, black SF32UC; transparent half-hard plastic ear-piece. Upright; 68.75 px/cm.
export function earReceiver(){
 const g=group('Ear Receiver');const z=py=>(770-py)/69.5,X=px=>(px-880)/68.75;
 // (F) high gain antenna grid and heat sink, (E) energy cell housing, (D) finned receiver housing.
 cyl(g,1.12,z(745)-z(770),[0,0,(z(745)+z(770))/2],'z','metal','high gain antenna grid and heat sink');
 for(let i=0;i<6;i++)box(g,[2.0,.05,.06],[0,-.5+i*.2,.02],'black','antenna grid');
 cyl(g,1.0,z(560)-z(745),[0,0,(z(560)+z(745))/2],'z','black','receiver housing core');
 for(let i=0;i<9;i++)cyl(g,1.3,.09,[0,0,z(735)+i*(z(570)-z(735))/8],'z','metal','receiver housing fin');
 for(const s of[-1,1])box(g,[.08,.08,z(560)-z(745)],[s*.02,s*1.02,(z(560)+z(745))/2],'metal','housing seam');
 cyl(g,1.18,z(520)-z(560),[0,0,(z(520)+z(560))/2],'z','black','receiver cone',.4);
 cyl(g,.18,z(445)-z(520),[0,0,(z(445)+z(520))/2],'z','metal','stem');
 // (G) swivel, (C) earphone housing at 40°, (B) retention plate, (A) transparent moulded ear-piece.
 const head=group('earphone');
 cyl(head,.55,1.1,[0,0,0],'z','metal','earphone housing');
 rbox(head,[1.5,1.35,.08],[0,0,.58],.35,'metal','ear-piece retention plate');
 lathe(head,[[0,.6],[.5,.6],[.42,1.0],[.3,1.35],[.36,1.5],[0,1.5]],[0,0,0],'z','glass','molded plastic ear-piece');
 const lobe=sideProfile(head,[[-.5,.62],[.5,.62],[.9,.9],[.3,1.0],[-.6,.85]],.25,[0,0,0],'glass','ear-piece lobe',.08);lobe.rotation.z=Math.PI/2;
 sphere(head,.22,[0,0,-.55],'metal',[1,1,1],'swivel (ear-piece swivels stiffly here)');
 head.position.set(-.35,0,z(400));head.rotation.y=-THREE_RAD(50);g.add(head);
 return g;
}

// ---------- Universal Translator — PDF 139, TO 03:02:04 ----------
// Printed: model SFAF/CC-MK-01, Type I; length overall 28 cm; maximum diameter 4.8 cm; 500 gm.
// Colours: antimony SF02UC, black SF32UC. Measured at 44.2 px/cm (side profile and top plan). Y = length, A end forward.
export function universalTranslator(){
 const g=group('Universal Translator');const y=py=>(py-942)/43.7;// centred; stretched 1% to the printed 28 cm
 const seg=(a,b,r,mat,name,r2=r)=>cyl(g,r,y(b)-y(a),[0,(y(a)+y(b))/2,0],'y',mat,name,r2);
 // (A) speech characteristics sensors: block with a raked face; (B) other party speaker/microphones either side.
 sideProfile(g,[[y(410),-1.2],[y(410),1.5],[y(330),1.5],[y(330),-1.2],[y(395),-1.2]],1.6,[0,0,0],'metal','sensor block',.08);
 const rake=sideProfile(g,[[y(330),.8],[y(330),1.52],[y(372),1.52]],1.62,[0,0,0],'black','speech characteristics sensors',.02);
 for(let i=0;i<5;i++)box(g,[1.5,.05,.05],[0,y(334),-1+i*.4],'grey','sensor mesh');
 for(const s of[-1,1]){cyl(g,.55,.06,[s*1.15,y(410)-.02,0],'y','dark','other party speaker/microphone');}
 seg(410,480,1.87,'metal','forward cap');
 // (C) decoding/encoding section: knurled ring, the widest point (4.8 cm).
 seg(480,550,2.4,'metal','decoding/encoding section');
 for(let i=0;i<64;i++){const a=i/64*Math.PI*2;box(g,[.05,y(548)-y(482),.05],[Math.cos(a)*2.4,(y(480)+y(550))/2,Math.sin(a)*2.4],'dark','knurl');}
 seg(550,575,2.0,'metal','collar');
 // (L) housing / (E) primary computer section with (D) display panel, (J) transparent cover, (F) operator's speaker.
 seg(575,1000,1.89,'metal','housing / primary computer section');
 rbox(g,[2.6,y(965)-y(645),.25],[0,(y(645)+y(965))/2,1.8],.15,'grey','panel frame');
 for(let i=0;i<9;i++)for(let j=0;j<10;j++){const on=(i*7+j*3)%5===0;box(g,[.2,.2,.08],[-1.0+i*.25,y(655)+.12+j*.37,1.95],on?'amber':'black','computer functions display panel');}
 rbox(g,[2.5,y(815)-y(645)+.05,.06],[0,(y(645)+y(815))/2,2.05],.15,'glass','transparent cover');
 for(let i=0;i<8;i++)box(g,[2.3,.05,.06],[0,y(825)+i*.42,1.95],'dark',"operator's speaker/microphone");
 for(const py of[1000,1012,1030])torus(g,1.9,.05,[0,y(py),0],'y','grey','section joint');
 // (H) data storage banks section, (G) activating switch at 45°, (K) rear cover.
 seg(1035,1535,1.89,'metal','data storage banks section');
 const sw=group('switch');rbox(sw,[1.4,.65,.2],[0,0,0],.08,'black','activating switch');box(sw,[.4,.4,.12],[-.3,0,.1],'metal','switch slider');
 sw.position.set(Math.sin(THREE_RAD(45))*1.88,y(1060),Math.cos(THREE_RAD(45))*1.88);sw.rotation.y=THREE_RAD(45);g.add(sw);
 seg(1535,1555,1.95,'black','rear cover');
 for(let i=0;i<48;i++){const a=i/48*Math.PI*2;box(g,[.04,y(1553)-y(1537),.04],[Math.cos(a)*1.95,(y(1535)+y(1555))/2,Math.sin(a)*1.95],'grey','rear cover knurl');}
 return g;
}
