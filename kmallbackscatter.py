#name:              kmallbackscatter
#created:        August 2023
#by:            paul.kennedy@guardiangeomatics.com
#description:   python module to read a Kongsberg KMALL file, create a point cloud, identify outliers, write out a NEW kmall file with flags set
 
import os.path
from argparse import ArgumentParser
from datetime import datetime
import math
import numpy as np
# import open3d as o3d
import sys
import time
# import glob
# import rasterio
import multiprocessing as mp
# import shapefile
import logging
import matplotlib.pyplot as plt
import itertools

#local imports
import kmall
import fileutils
import geodetic
# import multiprocesshelper 
# import cloud2tif
# import ggmbesstandard
import pdfdocument

###########################################################################
def main():

    parser = ArgumentParser(description='backscatter a KMALL file.')
    parser.add_argument('-epsg',     action='store',         default="0",    dest='epsg',             help='Specify an output EPSG code for transforming from WGS84 to East,North,e.g. -epsg 4326')
    parser.add_argument('-i',         action='store',            default="",     dest='inputfolder',         help='Input filename/folder to process.')
    parser.add_argument('-odir',     action='store',         default="",    dest='odir',             help='Specify a relative output folder e.g. -odir GIS')
    parser.add_argument('-debug',     action='store',         default="1000",    dest='debug',             help='Specify the number of pings to process.  good only for debugging. [Default:-1]')

    matches = []
    args = parser.parse_args()
    # args.inputfolder = "C:/sampledata/kmall/B_S2980_3005_20220220_084910.kmall"

    if os.path.isfile(args.inputfolder):
        matches.append(args.inputfolder)

    if len (args.inputfolder) == 0:
        # no file is specified, so look for a .pos file in the current folder.
        inputfolder = os.getcwd()
        matches = fileutils.findFiles2(False, inputfolder, "*.kmall")

    if os.path.isdir(args.inputfolder):
        matches = fileutils.findFiles2(False, args.inputfolder, "*.kmall")

    #make sure we have a folder to write to
    args.inputfolder = os.path.dirname(matches[0])

    #make an output folder
    if len(args.odir) == 0:
        args.odir = os.path.join(args.inputfolder, str("KMALLBackscatter_%s" % (time.strftime("%Y%m%d-%H%M%S"))))
    makedirs(args.odir)

    logfilename = os.path.join(args.odir,"kmallbackscatter_log.txt")
    logging.basicConfig(filename = logfilename, level=logging.INFO)
    log("Configuration: %s" % (str(args)))
    log("Output Folder: %s" % (args.odir))
    log("KMALLBackscatter Version: 3.01")
    log("KMALLBackscatter started at: %s" % (datetime.now()))
    log("Username: %s" %(os.getlogin()))
    log("Computer: %s" %(os.environ['COMPUTERNAME']))
    log("Number of CPUs %d" %(mp.cpu_count()))	

    reports = []
    for file in matches:
        report = kmallbackscatter(file, args)
        reports.append(report)
    
    pdfdocument.report(logfilename, args.odir, reports=reports)

############################################################
def kmallbackscatter(filename, args):
    '''we will try to auto calibrate backscatter beams by extracting the beam xyzF flag data'''

    #load the python proj projection object library if the user has requested it
    if args.epsg != "0":
        geo = geodetic.geodesy(args.epsg)
    else:
        args.epsg = kmall.getsuitableepsg(filename)
        geo = geodetic.geodesy(args.epsg)

    log("Processing file: %s" % (filename))

    maxpings = int(args.debug)
    if maxpings == -1:
        maxpings = 999999999

    pingcounter = 0
    beamcountarray = 0
    
    log("Reading runtime parameters...")
    runtime = kmall.getruntime(filename)

    log("Loading Backscatter...")
    anglebuckets, report = kmall.loadbackscatterdata(filename, args)
    avg = np.array(anglebuckets)
    outfile = os.path.join(args.odir, os.path.basename(filename) + "_avg.txt")
    np.savetxt(outfile, avg, fmt='%.5f', delimiter=',')

    colors = itertools.cycle(["r", "g", "b", "y", "c", "m", "k"])
    for s in range(int(np.max(avg[:, 2]))+1):
        sector1 = avg[(avg[:,2] == s)]
        bs = np.mean(sector1[:, 1])
        log ("Sector, Backscatter: %s, %s" % (s, bs))
        report["Sectornumber: %s" % (s)] = s
        report["MeanBackscatterValue: %s" % (bs)] = bs
        color=next(colors)
        plt.scatter(sector1[:,0], sector1[:,1], color=color, s=4)
        plt.plot(sector1[:, 0], sector1[:, 1], color=color, label="Sector"+ str(s) + " Backscatter Strength", linewidth=1)
        plt.plot(sector1[:, 0], sector1[:, 3], color=color, label="Sector"+ str(s) + " Standard Deviation", linewidth=1)

    # plot the results in matplotl;ib so we can see the answers


    plt.legend(loc="upper left", fontsize="8",)
    plt.xlabel("Nadir Angle (degrees)")
    plt.ylabel("Backscatter Strength (dB)")
    plt.title("Backscatter Strength vs Nadir Angle\nDepth Mode: %s\n filename: %s" % (report["depthmode"], os.path.basename(report["filename"])), fontsize=10,)    
    # plt.show()
    outfilename = os.path.join(os.path.dirname(filename), os.path.splitext(os.path.basename(filename))[0] + "_AngularDependence.png")
    plt.savefig(outfilename)
    log("AVG File Saved to: %s" % (outfilename))
    report ["ARC_filename"] = outfilename

    # loop through dictionary and write out the report
    for key in report.keys():
        log("%s,%s\n" % (key, report[key]))

    log("backscattering complete at: %s" % (datetime.now()))
    return report

###############################################################################
def update_progress(job_title, progress):
    '''progress value should be a value between 0 and 1'''
    length = 20 # modify this to change the length
    block = int(round(length*progress))
    msg = "\r{0}: [{1}] {2}%".format(job_title, "#"*block + "-"*(length-block), round(progress*100, 2))
    if progress >= 1: msg += " DONE\r\n"
    sys.stdout.write(msg)
    sys.stdout.flush()

###############################################################################
def    makedirs(odir):
    if not os.path.isdir(odir):
        os.makedirs(odir, exist_ok=True)

###############################################################################
def    log(msg, error = False, printmsg=True):
        if printmsg:
            print (msg)
        if error == False:
            logging.info(msg)
        else:
            logging.error(msg)

###############################################################################
if __name__ == "__main__":
        main()