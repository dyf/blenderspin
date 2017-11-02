cell=$1
ffmpeg -framerate 30 -i ${cell}/%04d.png -vf scale=1920x1080 -c:v libx264 -pix_fmt yuv420p -crf 22 ${cell}.mp4
