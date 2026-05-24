import re
import os
import subprocess
import argparse


def validate_path(path):
    if not os.path.exists(path):
        raise argparse.ArgumentTypeError(f"{path} does not exist.")
    return path


def validate_album_art(image_path):
    valid_extensions = ['.png','.jpg','.jpeg','.webp']
    if not os.path.isfile(image_path):
        raise argparse.ArgumentTypeError(f"Album art file {image_path} does not exist.")
    
    if not os.path.splitext(image_path)[1].lower() in valid_extensions:
        raise argparse.ArgumentTypeError(f"Album art file {os.path.basename(image_path)} has an unsupported extension.")
    
    return image_path

metadata={
    b"TITLE":[],
    b"PERFORMER":[],
    b"INDEX":[],
    b"REM COMPOSER":[],
    b"REM DATE":[],
    b"REM GENRE":[]
}

album_title=""
album_performer=""
album_composer=""
album_date=""
album_genre=""

def timedif(i1,i2):
    i1,i2=i1.split(":"),i2.split(":")
    a=(int(i1[0])*60)+int(i1[1])
    b=(int(i2[0])*60)+int(i2[1])
    return b-a

    
def parsetrack(trackblock):
    track_title=None
    track_performer=None
    track_indexes=[]

    for spi in trackblock.split(b"\n"):

        spi=spi.strip()

        if spi.startswith(b"TITLE"):
            track_title=spi.split(b"TITLE",1)[1].strip().strip(b'"')
        elif spi.startswith(b"PERFORMER"):
            track_performer=spi.split(b"PERFORMER",1)[1].strip().strip(b'"')
        elif spi.startswith(b"INDEX"):
            parts=spi.split()
            idx_type=parts[1]
            idx_time=parts[2]
            if idx_type==b"01":
                track_indexes.append(idx_time)

    if track_title is None:
        track_title=b"UNKNOWN_TRACK"

    if track_performer is None:
        track_performer=b""

    return {
        "title":track_title,
        "performer":track_performer,
        "indexes":track_indexes
    }

def cuedata(pth):
 global metadata
 global album_title
 global album_performer
 global album_composer
 global album_date
 global album_genre

 metadata={
    b"TITLE":[],
    b"PERFORMER":[],
    b"INDEX":[],
    b"REM COMPOSER":[],
    b"REM DATE":[],
    b"REM GENRE":[]
 }

 album_title=""
 album_performer=""
 album_composer=""
 album_date=""
 album_genre=""
 
 with open(pth,"+r",encoding="utf-8") as ff:
  f=ff.read()
  k=f.encode('utf-8')
 
 # Parse album-level metadata
 for line in k.split(b"\n"):
  sline=line.strip()
  if sline.startswith(b"TITLE") and album_title=="":
    album_title=sline.split(b"TITLE")[1].strip().strip(b'"').decode("utf-8")
  elif sline.startswith(b"PERFORMER") and album_performer=="":
    album_performer=sline.split(b"PERFORMER")[1].strip().strip(b'"').decode("utf-8")
  elif sline.startswith(b"REM COMPOSER"):
    album_composer=sline.split(b"REM COMPOSER")[1].strip().strip(b'"').decode("utf-8")
  elif sline.startswith(b"REM DATE"):
    album_date=sline.split(b"REM DATE")[1].strip().decode("utf-8")
  elif sline.startswith(b"REM GENRE"):
    album_genre=sline.split(b"REM GENRE")[1].strip().strip(b'"').decode("utf-8")
 
 ff=re.split(rb'\n\s*TRACK\s+\d+\s+AUDIO',k)
 ff.pop(0)
 for i in ff:
    track=parsetrack(i)
    if len(track["indexes"])==0:
        print(f'WARNING: No INDEX 01 found for {track["title"]}')
        continue

    metadata[b"TITLE"].append(track["title"])
    metadata[b"PERFORMER"].append(track["performer"])
    metadata[b"INDEX"].append(track["indexes"][0])
 
def chaff(time):
    min,sec=time.split(':')
    min=int(min)
    sec=int(sec)
    if min>59:
        hr=min//60
        min%=60
        if hr==0:
            return "%02d:%02d" % (min, sec)
        elif hr < 10:
            return "0%0d:%02d:%02d" % (hr, min, sec)
        else:
            return "%d:%02d:%02d" % (hr, min, sec)
    return time
    
def validtitle(name):
    for inva in ['/', '\\', '?', '%', '*', ':', '|', '"', '<', '>', '”', '“']:
        if inva in name:
            name=name.replace(inva,'')
    
    name=name.strip().rstrip('.')

    return name

def main(args):
    repm = args.i
    if args.o:
        dspth = args.o
    else:
        dspth=""
    
    print("\nLocation of CUE:", repm)
    print("Extract Location:", dspth)

    if args.c:
        asmodeus = args.c
        print("Custom Album Art:",os.path.basename(asmodeus))
    reps=os.listdir(repm)
    treatgm=0
    for rep in reps:
     if rep.lower().endswith('.cue'):
        treatgm=1
        chk=0
        rep=os.sep.join([repm,rep])
        for i in ['flac','m4a','mp3','aac','wav','ogg']:
            loc=rep[:-3]+i
            if os.path.exists(loc):
                chk=1
                break
        if chk:            
            cuedata(rep)
            datacu=metadata
            mfile=loc
            ext=loc[loc.rindex('.'):]
            if not args.c:
             cimg=["ffmpeg","-hide_banner","-y","-i",mfile,"-an","-vcodec","copy","cover.png"]
             aimg=subprocess.run(cimg,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
             asmodeus='cover.png'
            a=0
            b=0
            totaltracks=len(datacu[b'INDEX'])
            wolfe=0
            
            print("\n","—"*55)
            for i in datacu[b'TITLE']:
                i=i.decode('utf-8')
                ior=validtitle(i)
                otfl=f'{ior+"_tmp"+ext}'
                otfl_fn=f'{ior+ext}'
                if dspth:
                    otfl=os.sep.join([dspth,otfl])
                    otfl_fn=os.sep.join([dspth,otfl_fn])
                tit=f'title={i}'
                try:
                    artt='artist='+datacu[b'PERFORMER'][a].decode('utf-8')
                except:
                    artt='artist='
                stime=datacu[b'INDEX'][b].decode('utf-8').strip()
                if b+1<totaltracks:
                    etime=datacu[b'INDEX'][b+1].decode('utf-8').strip()
                    diff=str(timedif(stime,etime))
                    wolfe=0
                else:
                    wolfe=1
                stime=stime.rsplit(":",1)[0]
                stime=chaff(stime)
                a+=1
                b+=1
                trno=f'track={a}'
                print(f"TRACK {a}: {i}")
                cmd=["ffmpeg","-hide_banner","-ss",stime,"-y","-i",mfile]
                
                if not wolfe:
                    cmd+=["-t",diff]
                
                cmd += ["-avoid_negative_ts","make_zero"]
                
                if ext=='.flac':
                    cmd+=["-map","0","-c:a","flac"]
                else:
                    cmd+=["-c","copy"]
                cmd+=[
                    "-metadata",tit,
                    "-metadata",artt,
                    "-metadata",trno,
                    "-metadata",f'album={album_title}',
                    "-metadata",f'album_artist={album_performer}',
                    "-metadata",f'composer={album_composer}',
                    "-metadata",f'date={album_date}',
                    "-metadata",f'genre={album_genre}',
                    otfl
                ]
                
                aa=subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                cimgad=['ffmpeg','-hide_banner','-y','-i',otfl,'-i',asmodeus,'-map','0:a','-map','1','-codec','copy','-metadata:s:v','title="Album cover"','-metadata:s:v','comment="Cover (front)"','-disposition:v','attached_pic',otfl_fn]
                aimgad=subprocess.run(cimgad, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                if b"No such file or directory" in aimgad.stdout:
                    subprocess.run(['ffmpeg','-hide_banner','-y','-i',otfl,'-c:v','copy','-c:a','copy',otfl_fn],stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                os.remove(otfl)

            if not args.c:
                try:
                    os.remove(asmodeus)
                except:
                    pass
        else:
            print("\nAudio file not found.")
    if not treatgm:
     print("\nNo CUE file found.")        

if __name__=='__main__':
    parser = argparse.ArgumentParser(description="Extract tracks from a file with CUE sheet.Also can add custom album art to the tracks.")
    parser.add_argument("-i", help="Path to the CUE file", type=validate_path,required=True)
    parser.add_argument("-o", help="Path where to extract files", type=validate_path,required=False)
    parser.add_argument("-c", help="Optional path to custom album cover art image for the tracks", type=validate_album_art, required=False)
    
    args = parser.parse_args()
    
    main(args)
