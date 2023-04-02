# Video-Streaming-with-RTSP-and-RTP
Socket Programming in Python for video streaming with RTSP and RTP protocols.

Store all video files in a folder named `videos`. 

Connect:
1. python Server.py 1300

2. python ClientLauncher.py 127.0.0.1 1300 5008 movie.Mjpeg

Server will get file `./videos/movie.Mjpeg`

3. python ClientLauncher.py 127.0.0.1 1300 5008 rick_roll.mjpeg

Server will get file `./videos/rick_roll.mjpeg`