#!/usr/bin/python

try:
    from django.conf import settings
    FFMPEG_PROGRAM = settings.FFMPEG_PROGRAM
    FFMPEG_OPTIONS = settings.FFMPEG_OPTIONS
except:
    FFMPEG_PROGRAM = "/Applications/ffmpegX.app/Contents/Resources/ffmpeg"
    #FFMPEG_OPTIONS = ["-vcodec", "libx264", "-an", "-vpre", "hq", "-crf", "22", "-threads", "0"]
    FFMPEG_OPTIONS = ["-vcodec", "h264", "-an"]

import sys, os, time, signal, shutil
from subprocess import Popen, PIPE
import re
import datetime
    
def parse_ffmpeg_output(text):
    """Get relevant info from the ffmpeg output"""
    
    state = None
    result = {'input': '', 'output': ''}
    for line in text.split('\n'):
        if line.startswith("Input"):
            state = "INPUT"
        elif line.startswith("Output"):
            state = "OUTPUT"
        elif line.startswith("Stream mapping:"):
            state = "OTHER"
        
        if state == "INPUT":
            result['input'] += line + "\n"

        if state == "OUTPUT":
            result['output'] += line + "\n"
            
    # check for video input format
    m = re.search("Video: ([^,]+),", result['input'])
    if m:
        result['inputvideoformat'] = m.groups()[0]
    else:
        result['inputvideoformat'] = 'unknown'
        
    return result
            
    
def ffmpeg(sourcefile, targetfile, timeout=300, options=[]):
    """Run FFMPEG with some command options, returning the output"""

    errormsg = ""
    
    ffmpeg = [FFMPEG_PROGRAM, "-y", "-i", sourcefile]
    ffmpeg += options
    ffmpeg += [targetfile]
 
    #print " ".join(ffmpeg)
    
    process =  Popen(ffmpeg, stdout=PIPE, stderr=PIPE)
    start = time.time()
    
    while process.poll() == None: 
        if time.time()-start > timeout:
            # we've gone over time, kill the process  
            os.kill(process.pid, signal.SIGKILL)
            print "Killing ffmpeg process for", sourcefile, " with arguments ", " ".join(ffmpeg)
            errormsg = "Conversion of video took too long.  This site is only able to host relatively short videos."
            return errormsg
        
    status = process.poll()
    out,err = process.communicate()
    #print "Ran ffmpeg ", " ".join(ffmpeg), " and got messages ", str(err)
    
    # should check status
    
    # return the error output - messages from ffmpeg
    return err

def extract_frame(sourcefile, targetfile):
    """Extract a single frame from the source video and 
    write it to the target file"""
    
    options = ["-r", "1", "-f", "mjpeg"]
    
    err = ffmpeg(sourcefile, targetfile, options=options)

def extract_median_frame(sourcefile, targetfile):
    """
    Extract the middle frame from the source video and write it to the target file
    Adapted from https://stackoverflow.com/questions/24142119/extract-the-middle-frame-of-a-video-in-python-using-ffmpeg?rq=1
    """

    result = ffmpeg(sourcefile, '')
    m = re.search(r"Duration:\s*(\d+):(\d+):(\d+)\.(\d+)", result)
    if not m:
        return None # Cannot determine duration
    # Avoiding strptime here because it has some issues handling milliseconds.
    m = [int(m.group(i)) for i in range(1, 5)]
    td = datetime.timedelta(hours=m[0],
                              minutes=m[1],
                              seconds=m[2],
                              # * 10 because truncated to 2 decimal places
                              milliseconds=m[3] * 10
                              )
    duration = (td.microseconds + (td.seconds + td.days * 24 * 3600) * 10**6) / 10.0**6
    position = 0.5 # Half way through
    target = max(0, min(duration * position, duration - 0.1))
    target = "{0:.3f}".format(target)
    options = [
            "-ss", target,     # half-way position
            "-map", "v:0",     # first video stream
            "-frames:v", "1",  # 1 frame
            "-f", "mjpeg",     # motion jpeg (aka. jpeg since 1 frame) output
            ]

    err = ffmpeg(sourcefile, targetfile, options=options)

def probe_format(file):
    """Find the format of a video file via ffmpeg,
    return a format name, eg mpeg4, h264"""
    
    # for info, convert just one second to a null output format
    info_options = ["-f", "null", "-t", "1"]
    
    b = ffmpeg(file, "tmp", options=info_options)
    r = parse_ffmpeg_output(b)
    #print "Probe format ", str(r)
    
    return r['inputvideoformat']



def convert_video(sourcefile, targetfile, force=False):
    """convert a video to h264 format
    if force=True, do the conversion even if the video is already
    h264 encoded, if False, then just copy the file in this case"""
    
    if not force:
        format = probe_format(sourcefile)
    else:
        format = 'force'
    
    if format == "h264":
        # just do a copy of the file
        shutil.copy(sourcefile, targetfile) 
    else: 
        # convert the video
        b = ffmpeg(sourcefile, targetfile, options=FFMPEG_OPTIONS)

    format = probe_format(targetfile)
    if format.startswith('h264'):
        return True
    else:
        print "File format was not h264, was ", format
        return False 
        
if __name__=='__main__':
    import sys
    
    if len(sys.argv) != 3:
        print "Usage: convertvideo.py <sourcefile> <targetfile>"
        exit()
        
    sourcefile = sys.argv[1]
    targetfile = sys.argv[2]
    
    convert_video(sourcefile, targetfile)
        
    
        
        
        
    
