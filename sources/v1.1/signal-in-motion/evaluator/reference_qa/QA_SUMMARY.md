# Final technical QA

PASS. reference.mp4 is 10.000 s, 1920×1080, 24 fps, 240 decoded video frames, H.264/AAC, 3,940,450 bytes. Full video/audio decode produced no errors. All 240 low-resolution decoded frames are distinct.

The exact supplied 48 kHz stereo soundtrack contains 480,000 samples per channel. Encoded AAC correlation to that WAV is 0.999748; no clipped decoded samples; peak −2.16 dBFS. The soundtrack is generated from oscillators/noise, not original film audio or external samples. These are technical measurements, not a listening-panel judgment.

All 240 actor mattes were checked for contact with the left/right/top garbage-mask boundaries: no hits. The expanded crop retains the early pointing gesture, held board, and hands. The lower source mat is removed with a procedural floor mask and the sole-contact edge is intentionally covered by a front stage lip. This remains a procedural key; it is not advertised as manual feature-film rotoscoping.

Assistant visual inspection covered six scenes, the boundary frames, orbit occlusion/foreshortening, synchronized triptych, ribbon depth, iris contraction/expansion, and final legibility. Last-half-second graphic pixels outside the moving actor region are identical in the uncompressed renders. The original actor continues sequentially, one source frame per output frame.

See qa_report.json, ffprobe.json, frame_mapping.csv, matte_bounds.json, and contactsheet_final.jpg. File hashes in qa_report.json identify the exact source, soundtrack, and final video.

## V1.1 integration notice

This is the original author-reference technical QA, retained as historical evidence.
The original qa_report.json records the then-pending new-material licensing decision;
the current component licensing decision is in ../../PACKAGE_LICENSE_STATUS.md.
That later decision does not change the measured source/video bytes or imply a fresh
model run, new visual review or V1.1 CI pass. Demo scripts now emit the current license
status on any future rerun.
