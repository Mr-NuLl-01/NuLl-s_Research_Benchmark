"""Extract a precise, reproducible actor matte and synthesize original 120 BPM audio.
New code and original soundtrack: licensed under the repository MIT license.
The actor footage retains CC BY 3.0; see SOURCE_LICENSE.md.
"""
from pathlib import Path
import subprocess, sys, wave, json, argparse
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from scipy.ndimage import label, binary_fill_holes
ROOT=Path(__file__).resolve().parents[1]
FPS=24; N=240; W,H=550,720
(ROOT/'qa').mkdir(parents=True,exist_ok=True)
(ROOT/'assets').mkdir(parents=True,exist_ok=True)

SOURCE=None
def source_command():
    source=SOURCE or ROOT/'assets'/'source.mp4'
    if not source.is_file():
        raise FileNotFoundError(f'Pass --source /path/to/source.mp4; missing {source}')
    return ['ffmpeg','-v','error','-i',str(source),'-frames:v','240','-vf','crop=550:720:800:292,format=rgb24','-f','rawvideo','-']

def matte(a):
    f=a.astype(np.float32); r,g,b=f[:,:,0],f[:,:,1],f[:,:,2]
    # The source's actor and held board are one connected component. The
    # garbage mask removes studio equipment before component analysis.
    excess=g-np.maximum(r,b)
    alpha=np.clip((29-excess)/25,0,1)
    yy,xx=np.mgrid[:H,:W]
    alpha[(xx<3)|(xx>442)|(yy<58)|(yy>671)]=0
    # The standing feet meet a brown studio mat. A source-space garbage
    # polygon follows the two trouser cuffs, retaining boots; a foreground
    # stage lip deliberately covers the last few pixels of the sole.
    spans=[]
    hits=(alpha[598]>.8)&((r[598]-g[598])>8)
    ids=np.flatnonzero(hits)
    for group in np.split(ids,np.where(np.diff(ids)>1)[0]+1):
        if len(group)>12:spans.append((int(group[0]),int(group[-1])))
    ground=Image.new('L',(W,H),0);gd=ImageDraw.Draw(ground)
    gd.rectangle((0,0,W,601),fill=255)
    if len(spans)>=2:
        for j,(l,rr) in enumerate(spans[:2]):
            if j==0:
                pts=[(l-4,596),(rr+4,596),(rr+3,635),(rr-5,648),(rr-17,658),(l-26,666),(l-40,663),(l-40,653),(l-16,640),(l-4,624)]
            else:
                pts=[(l-4,596),(rr+4,596),(rr+4,637),(rr-1,652),(rr-13,665),(l-8,667),(l-12,659),(l-9,646),(l-2,628)]
            gd.polygon(pts,fill=255)
    alpha*=np.asarray(ground)/255
    alpha[(yy>601)&(g>r*.93)&(g>b*1.3)]=0
    binary=alpha>.42
    lab,n=label(binary)
    if n:
        sizes=np.bincount(lab.ravel()); sizes[0]=0
        body=lab==int(sizes.argmax())
        # Retain soft antialiased boundary only adjacent to true actor pixels.
        bodyim=Image.fromarray(np.uint8(body)*255).filter(ImageFilter.MaxFilter(3))
        alpha*=np.asarray(bodyim)/255
    # Neutralize only green spill; original warm keylight is retained.
    f[:,:,1]=np.minimum(g,np.maximum(r,b)+5)
    out=np.dstack([np.uint8(np.clip(f,0,255)),np.uint8(alpha*255)])
    return Image.fromarray(out,'RGBA')

def extract():
    out=ROOT/'render'/'actor';out.mkdir(parents=True,exist_ok=True)
    p=subprocess.Popen(source_command(),stdout=subprocess.PIPE)
    for n in range(N):
        raw=p.stdout.read(W*H*3)
        if len(raw)!=W*H*3:raise RuntimeError(f'Incomplete source at frame {n}')
        a=np.frombuffer(raw,np.uint8).reshape(H,W,3)
        im=matte(a);im.save(out/f'{n:04d}.png',compress_level=2)
        if n in [0,35,95,131,167,203,239]:
            bg=Image.new('RGBA',(W,H),(7,19,33,255));bg.alpha_composite(im);bg.convert('RGB').save(ROOT/'qa'/f'matte_{n:04d}.jpg',quality=94)
        if n%48==0:print('Matte',n,flush=True)
    if p.wait()!=0:raise RuntimeError('Source decode failed')

def soundtrack():
    sr=48000;n=sr*10;t=np.arange(n)/sr
    rng=np.random.default_rng(37)
    stereo=np.zeros((n,2),np.float64)
    def add(start, tone, amp=.1, pan=0):
        start=int(start*sr);end=min(n,start+len(tone));tone=tone[:end-start]*amp
        stereo[start:end,0]+=tone*np.sqrt((1-pan)/2)
        stereo[start:end,1]+=tone*np.sqrt((1+pan)/2)
    def sine(freq,dur):
        q=np.arange(int(sr*dur))/sr
        e=np.minimum(1,q/.012)*np.exp(-q*3.1)
        return (np.sin(2*np.pi*freq*q)+.20*np.sin(2*np.pi*freq*2*q))*e
    # Warm Cmaj9 / Am7 pad, low-pass-like harmonic falloff, gently swaying stereo.
    for st,chord in [(0,[130.81,164.81,196,246.94]),(4,[110,130.81,164.81,196]),(8,[130.81,164.81,196,293.66])]:
        dur=min(10-st,4.7);q=np.arange(int(sr*dur))/sr
        env=np.minimum(1,q/.18)*np.minimum(1,(dur-q)/.6)
        for j,f in enumerate(chord):
            sig=(np.sin(2*np.pi*f*q)+.12*np.sin(2*np.pi*2*f*q))*env
            add(st,sig,.039,(j-1.5)*.22)
    notes=[523.25,659.25,783.99,659.25,587.33,783.99,880,783.99]
    for beat in range(20):
        st=beat*.5
        # Soft sine kick, rounded attack, no hard transient.
        q=np.arange(int(sr*.24))/sr;freq=48+60*np.exp(-q*28)
        phase=2*np.pi*np.cumsum(freq)/sr
        add(st,np.sin(phase)*(1-np.exp(-q*320))*np.exp(-q*18),.25)
        add(st,sine([65.406,65.406,55,65.406][min(3,beat//5)],.42),.17,-.08)
        if beat%2:
            q=np.arange(int(sr*.15))/sr
            noise=rng.normal(0,1,len(q));smooth=np.convolve(noise,np.ones(18)/18,mode='same')
            add(st,smooth*np.sin(np.pi*np.clip(q/.15,0,1))**2,.16,.1)
        add(st+.25,sine(notes[beat%8],.7),.105,(-1 if beat%2 else 1)*.42)
        # Quiet brushed tick, bandwidth intentionally subdued.
        q=np.arange(int(sr*.08))/sr;noise=rng.normal(0,1,len(q));noise=np.convolve(noise,np.ones(8)/8,mode='same')
        add(st+.25,noise*np.sin(np.pi*q/.08)*np.exp(-q*35),.042,.25)
    # Delicate transition accents; all synthesized, no sampled media.
    for st in [1.5,4,5.5,7,8.5]:
        q=np.arange(int(sr*.42))/sr
        add(st,np.sin(2*np.pi*(700*q-300*q*q))*np.sin(np.pi*q/.42)**2*np.exp(-q*7),.055,-.25)
    stereo=np.tanh(stereo*1.15)
    fade=np.minimum(1,t/.04)*np.minimum(1,(10-t)/.24)
    stereo*=fade[:,None]
    stereo*=.78/max(.001,np.max(np.abs(stereo)))
    wav=ROOT/'assets'/'soundtrack.wav'
    with wave.open(str(wav),'wb') as w:w.setnchannels(2);w.setsampwidth(2);w.setframerate(sr);w.writeframes((stereo*32767).astype('<i2').tobytes())
    (ROOT/'qa'/'audio_metrics.json').write_text(json.dumps({'sample_rate':sr,'samples':n,'channels':2,'duration_seconds':10,'peak_dbfs':float(20*np.log10(abs(stereo).max())),'rms_dbfs':float(20*np.log10(np.sqrt(np.mean(stereo**2)))),'bpm':120,'composition':'Original deterministic Cmaj9/Am7 synthesizer score; licensed under the repository MIT license'},indent=2))
    print('Audio created',wav,flush=True)
if __name__=='__main__':
    ap=argparse.ArgumentParser()
    ap.add_argument('--source',type=Path,help='Exact supplied 1920x1012 BT.709 source MP4')
    ap.add_argument('--audio',action='store_true')
    ap.add_argument('--matte',action='store_true')
    args=ap.parse_args();SOURCE=args.source
    if args.audio:soundtrack()
    elif args.matte:extract()
    else:soundtrack();extract()
