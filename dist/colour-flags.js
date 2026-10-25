// Vector reconstructions of Technical Manual PDF plates 35, 36 and 45.
// Colour assignments follow each plate's SFnnUC key. Palette selection is external.
const star=(x,y,r=14,inner=.42,rotation=-90)=>{
  const pts=Array.from({length:10},(_,i)=>{const a=(rotation+i*36)*Math.PI/180,q=i%2?r*inner:r;return `${(x+Math.cos(a)*q).toFixed(2)},${(y+Math.sin(a)*q).toFixed(2)}`;}).join(' ');
  return `<polygon points="${pts}"/>`;
};
const fieldTexture=id=>`<defs><linearGradient id="${id}-cloth" x1="0" y1="0" x2="1" y2="0"><stop stop-color="#fff" stop-opacity=".08"/><stop offset=".28" stop-color="#fff" stop-opacity="0"/><stop offset=".7" stop-color="#000" stop-opacity=".07"/><stop offset="1" stop-color="#fff" stop-opacity=".06"/></linearGradient><linearGradient id="${id}-metal" x1="0" y1="0" x2=".65" y2="1"><stop stop-color="#fff" stop-opacity=".28"/><stop offset=".45" stop-color="#fff" stop-opacity=".02"/><stop offset=".65" stop-color="#000" stop-opacity=".1"/><stop offset="1" stop-color="#fff" stop-opacity=".14"/></linearGradient></defs>`;
function banner(p,id){
 const outline='M128 40H472L374 660L300 470L226 660Z';
 let stars=[185,242.5,300,357.5,415].map(x=>star(x,103,22)).join('');
 for(const [y,d,r] of [[198,105,21],[290,90,21],[382,75,21],[474,61,20]]) stars+=star(300-d,y,r)+star(300+d,y,r);
 // Hand-built elongated monogram preserves the plate's sharp U, deep F and angled P.
 const monogram=`<path d="M242 192H258V336L276 363V192H292V401L242 345Z M301 192H337V211H319V265H334V283H319V430L301 410Z M346 192H382V263L363 289V398L346 418Z M363 210V265L370 253V210Z" fill-rule="evenodd"/>`;
 return `${fieldTexture(id)}<path d="${outline}" fill="${p.SF10}"/><path d="${outline}" fill="url(#${id}-cloth)"/><g fill="${p.SF01}">${stars}${monogram}</g><g fill="url(#${id}-metal)">${stars}${monogram}</g>`;
}
function seal(p,id){
 const cx=300,cy=300,r=221;
 const wreath=`<path d="M200 89C161 109 126 141 103 177C94 189 89 202 87 214C73 230 58 249 52 263C48 274 55 282 61 288C54 306 42 322 45 336C47 345 57 348 62 356C58 368 48 384 53 396C55 403 65 408 74 410C70 425 69 439 80 447C90 453 99 451 107 456C108 471 117 481 130 484C142 486 155 481 163 489C179 504 192 512 210 517C175 497 143 465 121 430C97 392 82 349 79 304C78 263 88 223 105 188C126 144 160 110 200 89Z"/><path d="M400 89C439 109 474 141 497 177C506 189 511 202 513 214C527 230 542 249 548 263C552 274 545 282 539 288C546 306 558 322 555 336C553 345 543 348 538 356C542 368 552 384 547 396C545 403 535 408 526 410C530 425 531 439 520 447C510 453 501 451 493 456C492 471 483 481 470 484C458 486 445 481 437 489C421 504 408 512 390 517C425 497 457 465 479 430C503 392 518 349 521 304C522 263 512 223 495 188C474 144 440 110 400 89Z"/><path d="M94 492C129 531 173 534 217 547C235 553 240 573 241 589C211 574 188 559 166 553C139 545 116 526 94 492Z M506 492C471 531 427 534 383 547C365 553 360 573 359 589C389 574 412 559 434 553C461 545 484 526 506 492Z"/>`;
 const grid=[73.7,147.3].map(v=>`<circle cx="300" cy="300" r="${v}"/>`).join('')+Array.from({length:4},(_,i)=>{const a=i*Math.PI/4,dx=Math.cos(a)*r,dy=Math.sin(a)*r;return `<path d="M${cx-dx} ${cy-dy}L${cx+dx} ${cy+dy}"/>`;}).join('');
 // Celestial point positions follow the distinctive three-rings chart on PDF 36.
 const points=[[262,105,8,16],[222,160,8,17],[310,188,4,10],[313,196,4,8],[344,183,4,9],[277,219,5,11],[391,230,5,10],[437,205,3,0],[139,204,3,0],[112,258,7,16],[156,261,4,10],[200,265,4,9],[208,282,4,10],[216,243,4,9],[225,241,4,8],[238,243,4,11],[238,274,4,10],[249,271,5,11],[287,241,5,10],[296,242,4,9],[306,241,4,10],[317,283,8,16],[300,298,4,0],[229,296,4,9],[229,308,4,9],[202,305,4,10],[228,331,4,10],[170,328,4,9],[203,351,6,13],[241,383,6,14],[284,385,4,9],[319,375,8,16],[349,396,8,16],[346,409,4,9],[321,423,4,9],[236,445,5,12],[300,489,3,0],[431,357,5,10],[438,276,4,9],[405,301,5,11],[367,298,4,9],[359,308,4,8],[371,314,4,9],[373,334,5,10]];
 const planets=points.map(([x,y,q,orbit])=>`${orbit?`<g fill="none" stroke="${p.SF01}" stroke-width=".8"><circle cx="${x}" cy="${y}" r="${orbit}" stroke-dasharray="2 1.6"/><path d="M${x-orbit} ${y}H${x+orbit}M${x} ${y-orbit}V${y+orbit}"/></g>`:''}<circle cx="${x}" cy="${y}" r="${q}" fill="${p.SF01}"/>`).join('');
 return `${fieldTexture(id)}<g fill="${p.SF01}">${wreath}</g><circle cx="300" cy="300" r="224" fill="${p.SF01}"/><circle cx="300" cy="300" r="221" fill="${p.SF20}"/><circle cx="300" cy="300" r="221" fill="url(#${id}-cloth)"/><g stroke="${p.SF01}" stroke-width=".9" fill="none">${grid}</g>${planets}<text x="300" y="595" text-anchor="middle" font-family="Georgia,'Times New Roman',serif" font-size="68" font-weight="700" letter-spacing="-3" fill="${p.SF01}">UFP</text><g fill="url(#${id}-metal)">${wreath}</g>`;
}
function centauri(p,id){
 const outline='M49 155L558 202L423 349L558 493L49 529Z';
 // Rearing centaur, sword and shield: one figure, not a horse and rider.
 const centaur=`<path d="M279 263C277 250 282 240 293 240C307 240 316 249 313 260L307 272C322 273 338 281 348 293L358 274L370 279L358 310C351 319 342 307 333 301L328 325C337 340 349 351 355 365C369 359 380 361 384 374L386 395L380 413L372 411L375 390L368 377L351 389L345 405L338 413L328 408L337 398L337 382C319 388 303 393 287 388L278 410L290 438L286 452L276 453L271 440L262 418L264 390C250 389 245 382 244 374C236 380 225 391 212 389C200 387 191 380 185 372L191 367C200 376 211 373 217 361C226 345 237 343 248 346C258 331 277 331 294 332L298 300L282 296L259 320L247 325L241 317L251 310L270 280C276 273 282 273 285 271Z"/><path d="M354 242C377 250 389 264 391 289C392 308 385 324 375 336C367 317 361 294 358 273Z"/><path d="M247 320L195 271L190 258L201 265L253 314Z"/><path d="M240 310L258 329L254 333L236 314Z"/>`;
 // Small unfilled cuts describe hair, shield rim and leg articulations without new colours.
 const contours=`<path d="M283 250C288 245 300 245 309 252M282 255L280 267M287 253L285 270M292 254L291 270M298 255L298 268M303 256L303 266M361 251C378 261 386 280 385 300C383 313 380 319 377 324M310 281C321 286 327 291 331 298M301 305L315 310M302 327L323 335M275 351C279 364 291 371 307 371M253 351C249 360 250 369 255 374M265 389L275 391M340 379L351 374M277 440L286 439M377 396L384 394M194 370C207 387 219 379 224 368M197 373C206 379 214 374 219 363"/>`;
 const ring=Array.from({length:15},(_,i)=>{const a=(-90+i*24)*Math.PI/180,b=(-78+i*24)*Math.PI/180;return `<circle cx="${290+128*Math.cos(a)}" cy="${348+129*Math.sin(a)}" r="6.5"/>${star(290+128*Math.cos(b),348+129*Math.sin(b),2.3,.38)}`;}).join('');
 return `${fieldTexture(id)}<path d="${outline}" fill="${p.SF26}" stroke="${p.SF03}" stroke-width="8" stroke-linejoin="miter"/><path d="${outline}" fill="url(#${id}-cloth)"/><g fill="${p.SF03}">${ring}${centaur}</g><g fill="none" stroke="${p.SF26}" stroke-width=".8" stroke-linecap="round" opacity=".65">${contours}</g><g fill="url(#${id}-metal)">${centaur}</g>`;
}
export function flagArt(kind,palette,prefix='flag'){
 const id=String(prefix).replace(/[^a-zA-Z0-9_-]/g,'');
 if(kind==='banner')return banner(palette,id);
 if(kind==='seal')return seal(palette,id);
 if(kind==='centauri')return centauri(palette,id);
 throw new Error(`Unknown flag artwork: ${kind}`);
}
