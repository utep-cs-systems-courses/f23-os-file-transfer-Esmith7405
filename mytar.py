#! /usr/bin/env python3

import sys        # command line arguments
import re         # regular expression tools
import os         # checking if file exists
import subprocess # executing program
import codecs

from buf import BufferedFdWriter, BufferedFdReader, bufferedCopy

debug = 0

byteWriter = BufferedFdWriter(1) # stdout

#Framer's job
  #Byte-array -> a framed sequence of bytes written to a fd
class Framer:
    def __init__(self, writeFD):
        self.writeFD = writeFD
    def frame(self) -> bytes:
        #Frame the file descriptor
        writeFDLen = len(self.writeFD)
        frame = b""
        frame += ((str(writeFDLen)).encode() + b':' + self.writeFD.encode() + b':')
        #Read file contents and add it to the frame
        fd = os.open(f"src/{self.writeFD}", os.O_RDONLY)        
        if debug: print(f"opening {self.writeFD}, fd={fd}\n")
        byteReader = BufferedFdReader(fd)
        #Buffered read throughout the entire file
        frame += ((str(os.path.getsize(fd))).encode() + b':')
        while (bv := byteReader.readByte()) is not None:
            frame += chr(bv).encode()
        byteReader.close()
        frame += b':'
        return frame

class TarWriter:
    def __init__(self, writeFD):
        self.writeFD = writeFD
        #sys.stdout.write("B\'") #begin the tar file
    def storeFile(self, fileName) -> None:
        tarFrame = Framer(fileName).frame()
        os.write(sys.stdout.fileno(), tarFrame)

#Unframer
  #Reading from a fd -> Byte array
class Unframer:
    def __init__(self, readFD):
        self.readFD = readFD
        self.byteReader = BufferedFdReader(self.readFD)
    def unFrame(self) -> bytes:
        fLength = b''
        #Buffered read frame length
        while (bv := self.byteReader.readByte()) != 58: #While bv != b':'
            if bv is None:
                return b''
            if debug: print(f"read byte: '{chr(bv)}'")
            fLength += chr(bv).encode()
        if debug:print("Finished Read")
        fLength = int(fLength) #Cast fileLength to int
        fContents = b''
        #read frame contents from Tar
        while(fLength) > 0:
            fContents += chr(self.byteReader.readByte()).encode()
            fLength-=1
        print("Unframed:'" + fContents.decode() + "'")
        self.byteReader.readByte()
        return fContents
        #Using the File Name, open and write to a file

class TarReader:
  def __init__(self, readFD):
      self.readFD = readFD
  def Untar(self) -> None:
    tarUnFramer = Unframer(self.readFD)
    #until input file end is reached
    while True: 
        readFrame = tarUnFramer.unFrame() #Unframe fileName
        if len(readFrame) == 0: #If an empty frame is read
            if debug: print("Empty frame, returning")
            return
        writeFD = os.open((b"tarOut/" + readFrame), os.O_WRONLY | os.O_CREAT)
        readFrame = tarUnFramer.unFrame() #Unframe fileContents
        os.write(writeFD, readFrame)
    
#Begin Execution
if len(sys.argv) < 2:
    print("Correct usage: mytar.py c <input1> <input2> ... <inputN> > <out.tar> \nmytar.py x <output.txt>")
    exit()

#mytar.py c <input1> <input2> > <out.tar> - Take the input files, encode them and aggregate them to 1 text file
if sys.argv[1] == "c":
    if debug: print("Create\n") 
    #Run through all inputs, adding them to a list
    filesIn = []
    for i in range(2, len(sys.argv)):
      filesIn.append(sys.argv[i])
      if debug: print(sys.argv[i])
    writer = TarWriter("out.tar") 
    for fd in filesIn:
        writer.storeFile(fd)

#mytar.py x <output.txt> - Take the output file and seperate it into its respective files
if sys.argv[1] == "x":
    readFD = os.open(sys.argv[2], os.O_RDONLY)
    if debug: print(f"opened {readFD}, begin extracting")
    reader = TarReader(readFD)
    reader.Untar()
    os.close(readFD)