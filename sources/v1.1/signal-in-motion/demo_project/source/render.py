"""SIGNAL IN MOTION — editable deterministic 2D/2.5D motion compositor.
No image generation, online assets, or generative video model is used.
All source frames map 1:1 to output frames; use prepare_assets.py first.
"""
import math, subprocess, json, argparse
from functools import lru_cache
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops
ROOT=Path(__file__).resolve().parents[1]
W,H,FPS,N=1920,1080,24,240
NAVY=(7,19,33);CYAN=(99,243,230);WHITE=(244,241,232);PINK=(241,108,163)
TAU=math.tau
FONTS={'bold':ROOT/'assets'/'DejaVuSansCondensed-Bold.ttf','mono':ROOT/'assets'/'DejaVuSansMono.ttf'}
@lru_cache(None)
def font(size,style='bold'):return ImageFont.truetype(str(FONTS[style]),max(1,int(size)))
def ease(v):return (lambda x:x*x*(3-2*x))(min(1,max(0,v)))
def mix(a,b,u):return a+(b-a)*u

def base_bg():
    yy,xx=np.mgrid[:H,:W];r=np.sqrt(((xx-960)/1120)**2+((yy-490)/810)**2)
    a=np.clip(1-r,0,1)[...,None]
    bg=np.asarray(NAVY)[None,None,:]+a*np.array([6,19,25])[None,None,:]
    cyan=np.exp(-((xx-1250)**2/480000+(yy-290)**2/200000))[...,None]
    violet=np.exp(-((xx-410)**2/300000+(yy-610)**2/260000))[...,None]
    bg=bg+cyan*np.array([0,10,13])[None,None,:]+violet*np.array([11,0,10])[None,None,:]
    return Image.fromarray(np.uint8(bg),'RGB').convert('RGBA')
BASE=base_bg()
@lru_cache(maxsize=1024)
def text_sprite(text,size,color=WHITE,stroke=0,style='bold'):
    f=font(size,style);box=f.getbbox(text,stroke_width=stroke);pad=20
    sw,sh=max(1,box[2]-box[0]+pad*2),max(1,box[3]-box[1]+pad*2)
    mask=Image.new('L',(sw,sh),0);md=ImageDraw.Draw(mask)
    md.text((pad-box[0],pad-box[1]),text,font=f,fill=255,stroke_width=stroke,stroke_fill=255)
    im=Image.new('RGBA',(sw,sh),(0,0,0,0))
    if size>=70 and color in [WHITE,CYAN]:
        # Restrained metallic gradient and a diffuse cyan bounce, not a flat fill.
        top=np.array(color,float)*.98+np.array([255,255,255])*.02
        bottom=np.array([181,209,211] if color==WHITE else [65,185,184],float)
        g=np.clip((np.arange(sh)-pad)/max(1,sh-2*pad),0,1)[:,None,None]
        rgb=np.tile(np.uint8(top[None,None,:]*(1-g)+bottom[None,None,:]*g),(1,sw,1))
        fill=Image.fromarray(rgb,'RGB').convert('RGBA');fill.putalpha(mask)
        halo=Image.new('RGBA',(sw,sh),(*CYAN,0));halo.putalpha(mask.filter(ImageFilter.GaussianBlur(4)).point(lambda x:int(x*.22)))
        im.alpha_composite(halo);im.alpha_composite(fill)
    else:
        im=Image.new('RGBA',(sw,sh),(*color,255));im.putalpha(mask)
    return im

def paste(im,sprite,x,y,center=True,alpha=1,angle=0):
    if angle:sprite=sprite.rotate(angle,resample=Image.Resampling.BICUBIC,expand=True)
    if alpha<1:
        sprite=sprite.copy();sprite.putalpha(sprite.getchannel('A').point(lambda p:int(p*alpha)))
    x=int(x-sprite.width/2 if center else x);y=int(y-sprite.height/2 if center else y)
    im.alpha_composite(sprite,(x,y))

def txt(im,text,x,y,size,color=WHITE,center=True,alpha=1,angle=0,style='bold'):
    if not center:x-=12;y-=12
    paste(im,text_sprite(text,int(size),color,style=style),x,y,center,alpha,angle)

def glow_lines(im,drawfn,radius=6):
    l=Image.new('RGBA',(W,H));drawfn(ImageDraw.Draw(l));g=l.filter(ImageFilter.GaussianBlur(radius));im.alpha_composite(g);im.alpha_composite(l)

def ellipse(d,box,color,width=2):d.ellipse(tuple(int(v) for v in box),outline=color,width=width)
def poly(cx,cy,r,n=6,rot=math.pi/6,sy=1):return [(cx+math.cos(rot+k*TAU/n)*r,cy+math.sin(rot+k*TAU/n)*r*sy) for k in range(n)]

def common(t,scene):
    im=BASE.copy()
    atmosphere=Image.new('RGBA',(W,H));ad=ImageDraw.Draw(atmosphere)
    for j in range(32):
        x=(83+j*197.17+math.sin(j*3.1+t*.29)*32)%W
        y=(130+j*113.41-t*(6+j%5))%H
        if 700<x<1220:continue
        r=2+(j%7==0)*7;col=CYAN if j%4 else PINK
        ad.ellipse((x-r,y-r,x+r,y+r),fill=(*col,24+j%5*7))
    ad.ellipse((510,868,1410,982),fill=(*CYAN,24))
    im.alpha_composite(atmosphere.filter(ImageFilter.GaussianBlur(5)))
    d=ImageDraw.Draw(im)
    # Perspective floor is deliberately quiet, under the composited actor.
    horizon=766
    for x in range(-1440,3361,240):d.line([(960,horizon),(x,H)],fill=(18,48,61),width=1)
    for yy in [790,831,887,962,1060]:d.line([(0,yy),(W,yy)],fill=(19,48,60),width=1)
    d.line([(82,75),(W-82,75)],fill=(32,66,77),width=1)
    d.line([(82,1005),(W-82,1005)],fill=(32,66,77),width=1)
    d.rectangle((82,72,82+int((W-164)*min(1,t/9.5)),77),fill=CYAN)
    txt(im,f'0{scene+1} / 06',92,37,24,CYAN,False,style='mono')
    txt(im,'24 FPS  /  10 S',W-346,37,22,(130,160,169),False,style='mono')
    # Tiny coordinate ticks reinforce a single signal-station visual language.
    for x in [82,480,960,1440,1838]:d.line([(x,997),(x,1013)],fill=(77,116,127),width=1)
    for y in [180,360,540,720,900]:
        d.line([(42,y),(54,y)],fill=(55,92,104),width=1);d.line([(1866,y),(1878,y)],fill=(55,92,104),width=1)
    return im

@lru_cache(maxsize=12)
def actor(n):return Image.open(ROOT/'render'/'actor'/f'{n:04d}.png').convert('RGBA')
def put_actor(im,n,cx=960,bottom=939,scale=1.18,opacity=1):
    a=actor(n);a=a.resize((round(a.width*scale),round(a.height*scale)),Image.Resampling.LANCZOS)
    # Native source subject center is x=290; soles at y~663.
    halo=Image.new('RGBA',a.size,(*CYAN,0));halo.putalpha(a.getchannel('A').filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.GaussianBlur(5)).point(lambda x:int(x*.13)))
    paste(im,halo,cx-290*scale,bottom-663*scale,False,opacity)
    paste(im,a,cx-290*scale,bottom-663*scale,False,opacity)

def platform(im,t,front=True):
    d=ImageDraw.Draw(im)
    if not front:
        for k in range(3):ellipse(d,(960-350-k*42,914-36-k*10,960+350+k*42,914+36+k*10),(*CYAN,75-k*15),2)
        return
    # A physical front lip intentionally covers the source's mat/sole contact.
    d.polygon([(558,939),(1362,939),(1316,968),(604,968)],fill=(12,36,48))
    d.line([(558,939),(1362,939)],fill=CYAN,width=3)
    d.line([(604,968),(1316,968)],fill=(33,89,103),width=2)
    d.line([(604,969),(604,975),(1316,975),(1316,969)],fill=(14,41,54),width=3)

def radial(im,t):
    lay=Image.new('RGBA',(W,H));d=ImageDraw.Draw(lay)
    for k in range(5):
        r=140+((t*115+k*115)%570);a=int(108*(1-r/790))
        ellipse(d,(960-r,531-r*.73,960+r,531+r*.73),(*CYAN,a),2 if k%2 else 3)
    for i in range(80):
        a=i*TAU/80+t*.12;r=410+8*math.sin(t*5+i)
        p=(960+math.cos(a)*r,530+math.sin(a)*r*.78)
        q=(960+math.cos(a)*(r+(27 if i%5==0 else 8)),530+math.sin(a)*(r+(27 if i%5==0 else 8))*.78)
        d.line([p,q],fill=(*CYAN,105 if i%5==0 else 45),width=2)
    im.alpha_composite(lay.filter(ImageFilter.GaussianBlur(5)))
    im.alpha_composite(lay)

def scene_intro(n,t):
    im=common(t,0);radial(im,t);platform(im,t,False)
    # Two title banks leave the actor and held panel visibly unobstructed.
    en=ease(t/.35);dx=(1-en)*80
    jitter=(math.sin(n*2.5)*5 if 8<=n<=12 or 24<=n<=26 else 0)
    txt(im,'SIGNAL',380-dx+jitter,423,145,WHITE,alpha=en)
    txt(im,'IN',1470+dx-jitter,376,85,CYAN,alpha=en)
    txt(im,'MOTION',1470+dx+jitter,489,126,WHITE,alpha=en)
    if jitter:
        txt(im,'SIGNAL',387+jitter,423,145,PINK,alpha=.20)
    put_actor(im,n);platform(im,t)
    d=ImageDraw.Draw(im)
    d.line([(133,580),(605,580)],fill=CYAN,width=3)
    d.line([(1252,580),(1743,580)],fill=CYAN,width=3)
    return im

def orbit_entries(u):
    text='STAY IN ORBIT  '
    alltext=text*2;entries=[]
    for j,ch in enumerate(alltext):
        if ch==' ':continue
        a=j/len(alltext)*TAU+u*TAU/2.28-.6
        z=math.cos(a);x=960+math.sin(a)*670;y=600+z*155
        size=round(66+34*(z+1)/2)
        # Project the tangent of the 3D elliptical baseline. Its screen-space
        # length foreshortens every glyph at the left/right limbs.
        tangent_x=abs(math.cos(a));tangent_y=-math.sin(a)*155/670
        foreshorten=math.sqrt(tangent_x*tangent_x+tangent_y*tangent_y)
        angle=-math.degrees(math.atan2(tangent_y,max(.001,tangent_x)))
        entries.append((z,ch,x,y,size,angle,foreshorten))
    return sorted(entries)

def scene_orbit(n,t):
    im=common(t,1);u=t-1.5
    txt(im,'STAY IN ORBIT',960,173,112,WHITE)
    d=ImageDraw.Draw(im);ellipse(d,(280,446,1640,762),(*CYAN,70),2)
    ellipse(d,(309,472,1611,743),(*PINK,55),1)
    entries=orbit_entries(u)
    for z,ch,x,y,s,a,fx in entries:
        if z<0:
            glyph=text_sprite(ch,s,CYAN);glyph=glyph.resize((max(1,round(glyph.width*fx)),glyph.height),Image.Resampling.BICUBIC)
            paste(im,glyph,x,y,True,.40+.20*(z+1),a)
    platform(im,t,False);put_actor(im,n)
    for z,ch,x,y,s,a,fx in entries:
        if z>=0:
            glyph=text_sprite(ch,s,WHITE if z>.40 else CYAN);glyph=glyph.resize((max(1,round(glyph.width*fx)),glyph.height),Image.Resampling.BICUBIC)
            paste(im,glyph,x,y,True,.8+.2*z,a)
    platform(im,t)
    return im

def card_actor(n,scale,cx,cy,anchor):
    card=Image.new('RGBA',(548,744),(12,31,45,255));cd=ImageDraw.Draw(card)
    for r in range(80,580,65):ellipse(cd,(274-r,340-r,274+r,340+r),(*CYAN,28),1)
    a=actor(n).resize((round(550*scale),round(720*scale)),Image.Resampling.LANCZOS)
    card.alpha_composite(a,(round(cx-anchor[0]*scale),round(cy-anchor[1]*scale)))
    return card

def scene_split(n,t):
    im=common(t,2);u=t-4;d=ImageDraw.Draw(im)
    xs=[94,686,1278];words=['CAPTURE','SPLIT','RECOMBINE']
    scales=[1.05,1.68,2.25];anchors=[(285,355),(280,245),(239,210)]
    for j,x in enumerate(xs):
        move=round((1-ease(u/.22))*([80,-80,80][j]))
        panel=card_actor(n,scales[j],274,385,anchors[j])
        im.alpha_composite(panel,(x,144+move))
        d=ImageDraw.Draw(im);d.rectangle((x,144+move,x+548,888+move),outline=CYAN if j!=1 else PINK,width=2)
        d.rectangle((x,815+move,x+548,888+move),fill=(*NAVY,255))
        txt(im,words[j],x+274,853+move,57 if j==2 else 66,WHITE)
        txt(im,f'0{j+1}',x+25,169+move,25,CYAN,False,style='mono')
    return im

def wave_segments(u):
    # A sinusoidal ribbon has an explicit front/back depth component.
    items=[]
    for x in range(-80,W+80,20):
        phase=(x-960)/345-u*3.3
        z=math.sin(phase);y=570+z*104
        nx=x+20;nphase=(nx-960)/345-u*3.3;ny=570+math.sin(nphase)*104
        items.append((z,[(x,y-42),(nx,ny-42),(nx,ny+42),(x,y+42)]))
    return items

def ribbon(im,u,front):
    layer=Image.new('RGBA',(W,H));d=ImageDraw.Draw(layer)
    for z,pts in wave_segments(u):
        if (z>=0)==front:d.polygon(pts,fill=(*CYAN,225 if front else 100))
    # Per-glyph wave text follows the same spatial/depth path.
    phrase='RIDE THE WAVE   '
    for k in range(36):
        x=(k*61-u*180)%2180-130;phase=(x-960)/345-u*3.3;z=math.sin(phase)
        if (z>=0)!=front:continue
        y=570+z*104;angle=-math.degrees(math.atan(math.cos(phase)*104/345))
        txt(layer,phrase[k%len(phrase)],x,y,48,NAVY if front else CYAN,angle=angle)
    im.alpha_composite(layer)

def scene_wave(n,t):
    im=common(t,3);u=t-5.5
    d=ImageDraw.Draw(im)
    for row in range(6):
        points=[(x,355+row*66+math.sin(x/190-u*3+row*.45)*(33+row*4)) for x in range(0,W+1,10)]
        d.line(points,fill=(24,60+row*6,72+row*5),width=2)
    txt(im,'RIDE THE WAVE',960,166,113,WHITE)
    ribbon(im,u,False);platform(im,t,False);put_actor(im,n);ribbon(im,u,True);platform(im,t)
    return im

def scene_lock(n,t):
    im=common(t,4);u=t-7;d=ImageDraw.Draw(im)
    for k in range(5):d.polygon(poly(960,530,210+k*88,rot=math.pi/6+u*.08),outline=(*CYAN,60-k*7),width=2)
    platform(im,t,False);put_actor(im,n);platform(im,t)
    # True hexagonal aperture: visible interior and opaque exterior.
    if u<.60:r=mix(1180,122,ease(u/.6))
    else:r=mix(122,1360,ease((u-.6)/.62))
    aperture=Image.new('L',(W,H),255);ad=ImageDraw.Draw(aperture);ad.polygon(poly(960,515,r),fill=0)
    outside=Image.new('RGBA',(W,H),(*NAVY,255));outside.putalpha(aperture);im.alpha_composite(outside)
    d=ImageDraw.Draw(im);d.polygon(poly(960,515,r),outline=CYAN,width=5)
    d.polygon(poly(960,515,r+18),outline=(*PINK,110),width=1)
    txt(im,'LOCK ON',960,173,118,WHITE)
    # Stable crosshair remains readable even at maximum iris contraction.
    for sx in [-1,1]:
        for sy in [-1,1]:
            x=960+sx*210;y=520+sy*230
            d.line([(x-sx*31,y),(x,y),(x,y-sy*31)],fill=CYAN,width=3)
    return im

_rng=np.random.default_rng(100)
CONF=[(float(_rng.uniform(150,1770)),float(_rng.uniform(210,680)),float(_rng.uniform(7,15)),float(_rng.uniform(0,TAU)),int(_rng.integers(0,3))) for _ in range(24)]
def scene_outro(n,t):
    im=common(min(t,9.5),5);u=t-8.5;stable=min(u,1.0);d=ImageDraw.Draw(im)
    # Final geometric rostrum: clean hierarchy, restrained confetti.
    for k in range(4):
        d.polygon(poly(960,580,300+k*86,n=6,rot=math.pi/6),outline=(29,82-k*8,92-k*6),width=2)
    for x,y,size,a,c in CONF:
        y+=stable*50;x+=math.sin(a+stable*1.8)*26
        if 670<x<1250:continue
        pts=poly(x,y,size,n=4,rot=a+stable*.9)
        d.polygon(pts,fill=(*[CYAN,PINK,WHITE][c],140))
    platform(im,t,False);put_actor(im,n,bottom=939,scale=1.1);platform(im,t)
    titleu=ease(u/.22);txt(im,'SIGNAL RECEIVED',960,164,130,WHITE,alpha=titleu)
    # Symmetric signal bars lock in place for the final half second.
    for side in [-1,1]:
        for j in range(8):
            x=960+side*(350+j*55);height=18+((j*19)%70)
            d.rounded_rectangle((x-8,825-height,x+8,825+height),radius=6,fill=(*CYAN,190))
    return im

FUN=[scene_intro,scene_orbit,scene_split,scene_wave,scene_lock,scene_outro]
BOUNDS=[0,36,96,132,168,204,240]
def render_frame(n):
    t=n/FPS;scene=next(j for j in range(6) if BOUNDS[j]<=n<BOUNDS[j+1])
    im=FUN[scene](n,t)
    # A short scan wipe at editorial cuts, without flashes or fake actor frames.
    phase=n-BOUNDS[scene]
    if scene in [1,2,3,5] and phase<4:
        lay=Image.new('RGBA',(W,H));d=ImageDraw.Draw(lay);x=int(phase/3*W)
        d.rectangle((x-6,82,x+6,990),fill=(*CYAN,95));im.alpha_composite(lay)
    return im.convert('RGB')

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--stills',action='store_true');ap.add_argument('--video',default='reference.mp4');args=ap.parse_args()
    qa=ROOT/'qa';qa.mkdir(exist_ok=True)
    if args.stills:
        for n in [12,35,36,48,66,84,95,96,111,131,132,150,167,168,181,195,203,204,222,239]:
            render_frame(n).save(qa/f'frame_{n:04d}.jpg',quality=93)
        return
    out=ROOT/args.video
    cmd=['ffmpeg','-y','-hide_banner','-loglevel','error','-f','rawvideo','-pixel_format','rgb24','-video_size',f'{W}x{H}','-framerate',str(FPS),'-i','-','-i',str(ROOT/'assets'/'soundtrack.wav'),'-map','0:v:0','-map','1:a:0','-c:v','libx264','-preset','medium','-crf','19','-pix_fmt','yuv420p','-color_primaries','bt709','-color_trc','bt709','-colorspace','bt709','-c:a','aac','-b:a','192k','-t','10','-metadata','title=SIGNAL IN MOTION','-metadata','comment=Tears of Steel shot 04_3b; (CC) Blender Foundation | https://mango.blender.org ; CC BY 3.0 https://creativecommons.org/licenses/by/3.0/ . Adapted: frames 00000-00239, BT.709 conversion, crop/key, typography/compositing, original procedural music. No endorsement implied.','-movflags','+faststart',str(out)]
    p=subprocess.Popen(cmd,stdin=subprocess.PIPE)
    for n in range(N):
        im=render_frame(n);p.stdin.write(im.tobytes())
        if n%24==0:print('Rendered',n,'/',N,flush=True)
        if n in [12,35,36,48,66,84,95,96,111,131,132,150,167,168,181,195,203,204,222,239]:im.save(qa/f'frame_{n:04d}.jpg',quality=93)
    p.stdin.close()
    if p.wait():raise RuntimeError('Encode failed')
    print(out,flush=True)
if __name__=='__main__':main()
