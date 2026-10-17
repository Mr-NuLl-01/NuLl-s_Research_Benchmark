"""Technical reproducibility and delivery audit. No model-quality score is implied."""
from pathlib import Path
import hashlib,json,subprocess,sys,wave,platform,importlib.util
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
SRC=Path(sys.argv[1]) if len(sys.argv)>1 else ROOT/'assets/source.mp4'
VIDEO=ROOT/'reference.mp4';QA=ROOT/'qa';QA.mkdir(exist_ok=True)
def sha(path):
 h=hashlib.sha256()
 with open(path,'rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def cmd(args):return subprocess.run(args,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=True)
probe=json.loads(cmd(['ffprobe','-v','error','-count_frames','-show_streams','-show_format','-of','json',str(VIDEO)]).stdout)
decode=cmd(['ffmpeg','-v','error','-i',str(VIDEO),'-map','0','-f','null','-'])
(QA/'decode_errors.txt').write_bytes(decode.stderr)
(QA/'ffprobe.json').write_text(json.dumps(probe,indent=2))
v=next(s for s in probe['streams'] if s['codec_type']=='video')
a=next(s for s in probe['streams'] if s['codec_type']=='audio')
assert (v['width'],v['height'],v['r_frame_rate'],v['nb_read_frames'])==(1920,1080,'24/1','240')
assert float(v['duration'])==10 and float(a['duration'])==10
small=cmd(['ffmpeg','-v','error','-i',str(VIDEO),'-vf','scale=96:54,format=gray','-f','rawvideo','-']).stdout
frames=np.frombuffer(small,np.uint8).reshape(240,54,96)
with wave.open(str(ROOT/'assets/soundtrack.wav'),'rb') as w:
 original=np.frombuffer(w.readframes(w.getnframes()),'<i2').reshape(-1,2).astype(np.float64)/32768
pcm=cmd(['ffmpeg','-v','error','-i',str(VIDEO),'-map','0:a:0','-ar','48000','-ac','2','-f','f32le','-']).stdout
actual=np.frombuffer(pcm,'<f4').reshape(-1,2)[:480000]
corr=float(np.corrcoef(original.ravel(),actual.ravel())[0,1])
boxes=[]
for p in sorted((ROOT/'render/actor').glob('*.png')):
 alpha=np.array(Image.open(p))[:,:,3];yy,xx=np.where(alpha>160)
 boxes.append([int(p.stem),int(xx.min()),int(yy.min()),int(xx.max()),int(yy.max())])
assert len(boxes)==240
boundary_hits=[b[0] for b in boxes if b[1]<=3 or b[3]>=442 or b[2]<=58]
# Compare uncompressed final graphic regions, excluding the moving source actor.
spec=importlib.util.spec_from_file_location('motion_renderer',ROOT/'source/render.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
i=np.array(mod.render_frame(228));j=np.array(mod.render_frame(239));mask=np.ones(i.shape[:2],bool);mask[230:950,590:1340]=False
stable=float(np.max(np.abs(i.astype(int)-j.astype(int))[mask]))
report={
 'status':'PASS',
 'video':{'path':'reference.mp4','bytes':VIDEO.stat().st_size,'sha256':sha(VIDEO),'width':1920,'height':1080,'fps':24,'frames':240,'duration_seconds':10.0,'codecs':['H.264','AAC'],'full_decode_errors':decode.stderr.decode()},
 'source':{'file_name':SRC.name,'sha256':sha(SRC),'mapping':'Output n uses source n for all n=0..239; same n in all three split panels','audio_included':False},
 'audio':{'file':'assets/soundtrack.wav','sha256':sha(ROOT/'assets/soundtrack.wav'),'original_samples_per_channel':len(original),'sample_rate':48000,'channels':2,'bpm':120,'aac_vs_supplied_wav_correlation':corr,'aac_peak_dbfs':float(20*np.log10(np.max(abs(actual)))),'clipped_aac_samples':int(np.sum(abs(actual)>=1)),'method':'Original deterministic synthesis; no external samples; licensed under the repository MIT license'},
 'matte':{'source_crop':[800,292,550,720],'frames_checked':len(boxes),'minimum_actor_x':min(b[1] for b in boxes),'maximum_actor_x':max(b[3] for b in boxes),'garbage_mask_boundary_hits':boundary_hits,'ground_contact':'Cuff-following floor mask plus deliberate stage foreground lip','note':'Procedural chroma key, not manual feature-film rotoscoping'},
 'visual_review':{'stills':'qa/contactsheet_final.jpg','inspected':'Not performed by this automatic audit. See the delivered original QA summary for the author-reviewed reference only.','last_half_second_graphics_max_pixel_change_outside_actor':stable,'note':'Automatic technical checks only. A modified or rebuilt video requires a fresh visual review; no subjective audio-listening claim.'},
 'frame_statistics':{'minimum_mean_luma':float(frames.mean(axis=(1,2)).min()),'maximum_mean_luma':float(frames.mean(axis=(1,2)).max()),'unique_low_resolution_frames':len({f.tobytes() for f in frames})},
 'software':{'python':platform.python_version(),'ffmpeg':cmd(['ffmpeg','-version']).stdout.decode().splitlines()[0]},
 'copyright':'Source footage CC BY 3.0, DejaVu font terms retained; new code/audio licensed under the repository MIT license.'
}
if boundary_hits or stable!=0 or corr<.98 or len(actual)!=480000:report['status']='REVIEW'
(QA/'qa_report.json').write_text(json.dumps(report,indent=2,ensure_ascii=False))
(QA/'matte_bounds.json').write_text(json.dumps({'columns':['frame','x_min','y_min','x_max','y_max'],'bounds':boxes},indent=2))
with open(QA/'frame_mapping.csv','w') as f:
 f.write('output_frame,source_frame,time_seconds,section\n')
 for n in range(240):
  section=next(j for j in range(6) if mod.BOUNDS[j]<=n<mod.BOUNDS[j+1])
  f.write(f'{n},{n},{n/24:.6f},{section+1}\n')
print(json.dumps(report,indent=2,ensure_ascii=False))
