ffmpeg -framerate 30 -i black/frame_%04d.png -vf scale=1024x1024 -c:v libx264 -pix_fmt yuv420p -crf 22 hmtg.mp4
