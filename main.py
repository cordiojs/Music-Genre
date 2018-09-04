import sys
import os, glob, eyed3, ntpath
import audioBasicIO
import audioFeatureExtraction as aF
from pymongo import MongoClient
import datetime
import numpy

def main():
    print 'Converting mp3 to wav'
    if(len(sys.argv)>1):
        dirName=sys.argv[1]
        OpDir=convertDirMP3ToWav(dirName, 44100, 1, True)
        print 'Extracting features now'
        featureExtraction(OpDir)

def featureExtraction(dirName):
    types = (dirName+os.sep+'*.wav',)  # the tuple of file types
    filesToProcess = []
    for files in types:
        filesToProcess.extend(glob.glob(files))
    for f in filesToProcess:
        print f
        [Fs, x] = audioBasicIO.readAudioFile(f)
        Mt,St = aF.mtFeatureExtraction(x, Fs, 1 * Fs, 1 * Fs,0.500 * Fs, 0.500 * Fs)
        F=St
        BPM, ratio = aF.beatExtraction(F, 0.100, False)
        print "Beat: {0:d} bpm ".format(int(BPM))
        print "Ratio: {0:.2f} ".format(ratio)
        print("Storing features to monogodb")
        storeFeaturesToMongoDb(F,BPM,f)

def storeFeaturesToMongoDb(F,BPM,fname):
    client = MongoClient('mongodb://127.0.0.1:27017/')
    db = client.audio_analysis
    audios = db.audio_data
    doc = {"fileName":fname,"timestamp":datetime.datetime.utcnow(),"bpm":BPM,"zeroCrossingRate":F[0, :].tolist(),"energy":F[1, :].tolist(),"entropyOfEnergy":F[2, :].tolist(),"spectralCentroid":F[3, :].tolist(),"spectralSpread":F[4, :].tolist(),"spectralEntropy":F[5, :].tolist(),"spectralFlux":F[6, :].tolist(),"spectralRolloff":F[7, :].tolist(),"MFCCs":[F[8, :].tolist(),F[9, :].tolist(),F[10, :].tolist(),F[11, :].tolist(),F[12, :].tolist(),F[13, :].tolist(),F[15, :].tolist(),F[16, :].tolist(),F[17, :].tolist(),F[18, :].tolist(),F[19, :].tolist(),F[20, :].tolist()],"chromaVector":[F[21, :].tolist(),F[22, :].tolist(),F[23, :].tolist(),F[24, :].tolist(),F[25, :].tolist(),F[26, :].tolist(),F[27, :].tolist(),F[28, :].tolist(),F[29, :].tolist(),F[30, :].tolist(),F[31, :].tolist(),F[32, :].tolist()],"chromaDeviation":F[33, :].tolist()}
    audios.insert_one(doc)
    return True

def convertDirMP3ToWav(dirName, Fs, nC, useMp3TagsAsName = False):
    print 'starting Conversion'
    types = (dirName+os.sep+'*.mp3',)  # the tuple of file types
    filesToProcess = []
    cwd = os.getcwd()
    opPath = cwd + os.sep + 'op'
    for files in types:
        filesToProcess.extend(glob.glob(files))
    for f in filesToProcess:
        audioFile = eyed3.load(f)
        if useMp3TagsAsName and audioFile.tag != None:
            artist = audioFile.tag.artist
            title = audioFile.tag.title
            print("Processing " + title)
            if artist!=None and title!=None:
                if len(title)>0 and len(artist)>0:
                    wavFileName = ntpath.split(f)[0] + os.sep + artist.replace(","," ").replace(os.sep,"") + "-" + title.replace(","," ") + ".wav"
                else:
                    wavFileName = f.replace(".mp3",".wav")
            else:
                wavFileName = f.replace(".mp3",".wav")
        else:
            wavFileName = f.replace(".mp3",".wav")
        wavFileName= wavFileName.replace(" ", "_")
        finalWavFile = wavFileName.replace(dirName, opPath)
        if not os.path.exists(opPath):
            os.makedirs(opPath)
        command = "avconv -y -hide_banner -loglevel panic -i \"" + f + "\" -ar " +str(Fs) + " -ac " + str(nC) + " \"" + finalWavFile + "\"";
        os.system(command.decode('unicode_escape').encode('ascii','ignore').replace("\0",""))
        print 'Conversion Done'
    return opPath
if __name__ == "__main__": main()