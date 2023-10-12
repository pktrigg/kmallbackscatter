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
import rasterio as rio
from rasterio.enums import Resampling

#local imports
import kmall
import fileutils
import geodetic
# import multiprocesshelper 
import cloud2tif
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
    recommendations = []
    for file in matches:
        report, results = kmallbackscatter(file, args)
        reports.append(report)
        
    statistics = []
    #from the reports make some recommendations
    for report in reports:
        # results = report["MeanBSValues"]
        for result in results:
            statistics.append([report["depthmode"], int(result[0]), float(result[1])])
    
    #calculate the average backscatter for each sector  
    statistics = np.array(statistics)
    globalmean = np.mean(np.array(statistics[:, 2], dtype=float))
    log ("Mean of ALL data: %.4f" % (globalmean))
    sectors = np.unique(statistics[:, 1])
    recommendations.append("DepthMode SectorNumber GlobalMeanBackscatter(dB) SectorBackscatter(dB) RecommendedCorrection(dB)")
    for s in sectors:
        values = statistics[(statistics[:, 1] == s)]
        bs = np.mean(np.array(values[:, 2], dtype=float))
        log ("Sector, Mean Backscatter: %s, %s" % (s, bs))
        correction = globalmean - bs
        recommendations.append("%s %s %.4f %.4f %.4f" % (report["depthmode"], s, globalmean, bs, correction))

    #from the reports, create a pdf document
    pdfdocument.report(logfilename, args.odir, reports=reports, recommendations=recommendations)

###############################################################################
def plotbackscatter(filename, args, geo, intensity=1):

    #now lets make a plot of the raw backscastter so we can see if there are any features which might impact the calibration
    pointcloud = kmall.loaddata(filename, args, intensity=intensity)
    xyz = np.stack((pointcloud.xarr, pointcloud.yarr, pointcloud.zarr), axis=1)

    outfilename = os.path.join(args.odir, os.path.splitext(os.path.basename(filename))[0] + str(intensity) + "_BackscatterFloat.tif")
    outfilename = cloud2tif.point2raster(outfilename, geo, xyz)

    plt.ioff()
    dtm_dataset = rio.open(outfilename)
    NODATA = dtm_dataset.nodatavals[0]
    downscale_factor = max(math.ceil(dtm_dataset.width / 2048),1)
    dtm_data = dtm_dataset.read(1, out_shape=(
            dtm_dataset.count,
            int(dtm_dataset.height / downscale_factor),
            int(dtm_dataset.width / downscale_factor)
        ), resampling=Resampling.bilinear)
    dtm_data[dtm_data > 10000] = 0
    dtm_data[dtm_data <= -999] = 0

    ext = [dtm_dataset.bounds.left, dtm_dataset.bounds.right, dtm_dataset.bounds.bottom, dtm_dataset.bounds.top]
    #Overlay transparent hillshade on DTM:
    SMALL_SIZE = 8
    MEDIUM_SIZE = 10
    BIGGER_SIZE = 12

    plt.rc('font', size=SMALL_SIZE)          # controls default text sizes
    plt.rc('axes', titlesize=SMALL_SIZE)     # fontsize of the axes title
    plt.rc('axes', labelsize=SMALL_SIZE)    # fontsize of the x and y labels
    plt.rc('figure', titlesize=BIGGER_SIZE)  # fontsize of the figure title

    plt.figure().set_figwidth(10)
    plt.figure().set_figheight(20)
    plt.rcParams['figure.figsize'] = [8, 8]
    fig, ax = plt.subplots(1, 1)
    ax = plt.gca()
    ax.set_aspect('equal')
    plt.gca().set_aspect('equal', adjustable='box')

    im1 = plt.imshow(dtm_data,cmap='gray',extent=ext); 
    # im2 = plt.imshow(hs_data,cmap='Greys',alpha=0.8,extent=ext); 
    plt.axis('off')

    plt.grid()
    plt.title('Backscatter Surface:' + str(intensity))
    overviewimagefilename = outfilename + "_reflectivity.png"
    plt.savefig(overviewimagefilename, bbox_inches='tight', dpi=640)
    plt.close()
    return overviewimagefilename

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

    plt.figure().set_figwidth(10)
    plt.figure().set_figheight(10)
    plt.rcParams['figure.figsize'] = [8, 8]

    results = []
    colors = itertools.cycle(["r", "g", "b", "y", "c", "m", "k"])
    for s in range(int(np.max(avg[:, 2]))+1):
        sector1 = avg[(avg[:,2] == s)]
        bs = np.mean(sector1[:, 1])
        results.append([s,bs])
        log ("Sector, Backscatter: %s, %s" % (s, bs))
        # report["Sectornumber"] = s
        report["Sectornumber:%s" % (s)] = s
        # report["Sectornumber: %s" % (s)] = s
        # report["MeanBackscatterValue"] = bs
        report["MeanBackscatterValue:%s" % (bs)] = bs
        color=next(colors)
        plt.scatter(sector1[:,0], sector1[:,1], color=color, s=4)
        plt.plot(sector1[:, 0], sector1[:, 1], color=color, label="Sector"+ str(s) + " Backscatter Strength", linewidth=1)
        # plt.plot(sector1[:, 0], sector1[:, 3], color=color, label="Sector"+ str(s) + " Standard Deviation", linewidth=1)

    # report["MeanBSValues"] = results
    # plot the results in matplotl;ib so we can see the answers
    plt.legend(loc="upper left", fontsize="8",)
    plt.xlabel("Nadir Angle (degrees)")
    plt.ylabel("Backscatter Strength (dB)")
    plt.title("Backscatter Strength vs Nadir Angle\nDepth Mode: %s\nfilename: %s" % (report["depthmode"], os.path.basename(report["filename"])), fontsize=10,)    
    # plt.show()
    outfilename = os.path.join(args.odir, os.path.splitext(os.path.basename(filename))[0] + "_AngularDependence.png")
    plt.savefig(outfilename)
    plt.close()
    log("ARC File Saved to: %s" % (outfilename))
    report ["ARC_filename"] = outfilename

    # loop through dictionary and write out the report
    for key in report.keys():
        log("%s,%s\n" % (key, report[key]))

    #make a greyscale image of the backscatter for the report
    overviewimagefilename = plotbackscatter(filename, args, geo, intensity=1)
    report ["backscatter_raw_filename"] = overviewimagefilename
    log("backscatter raw raster: %s" % (overviewimagefilename))

    overviewimagefilename = plotbackscatter(filename, args, geo, intensity=2)
    report ["backscatter_processed_filename"] = overviewimagefilename
    log("backscatter processed raster: %s" % (overviewimagefilename))

    log("backscattering complete at: %s" % (datetime.now()))
    return report, results

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