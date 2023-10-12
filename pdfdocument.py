###################################################################################################
#name:			pdfdocument.py
#created:		January 2019
#by:			paul.kennedy@guardiangeomatics.com
#description:	python module to create a standard report in native PDF format

#####################################################
#done
#27/2/20230 initial version
#the first table in the report needs to have a summary of:
# inputs and outputs  - done
# an image of the results
# the important metrics from th log file

#2DO
#####################################################
# nothing

import sys
import os
from argparse import ArgumentParser
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.units import mm, cm
from reportlab.platypus import BaseDocTemplate, SimpleDocTemplate, PageTemplate, Paragraph, Spacer, Frame, Table, Image, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib import utils
from functools import partial
import PIL
import rasterio as rio
from rasterio.plot import show
from rasterio.enums import Resampling
import matplotlib.pyplot as plt
import numpy as np
import math

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))
import fileutils
import cloud2tif

####################################################################################################
####################################################################################################
# def bathyqcreport(logfilename, resultfolder):
# 	'''create an bathyqc report into PDF'''
# 	# resultfolder should be 5_grid
# 	# logfilename should be args.inputfolder\bathyqc.log

# 	if not os.path.exists(resultfolder):
# 		return

# 	outfilename = os.path.join(resultfolder, "BathyQCReport.pdf")
# 	outfilename = fileutils.createOutputFileName(outfilename)
# 	myreport = REPORT("BathyQC Report", outfilename)
# 	log(filename, "BathyQCReport.pdf")
# 	#parse the bathyqc log file and make a summary table
# 	if os.path.exists(logfilename):
# 		bathyqcreportsummary(myreport, logfilename )


####################################################################################################
def collectinformation(line, msgid, username, metrics):
	if msgid in line:
		line = line.replace(msgid,"")
		line = line.strip()
		metrics.append([username, line])
	return line

# ####################################################################################################
# def bathyqcreportsummary(myreport, logfilename):

# 	if not os.path.exists(logfilename):
# 		return

# 	myreport.addtitle("BathyQC Principles")
# 	myreport.addspace()
# 	myreport.addspace()

# 	myreport.addparagraph("BathyQC is a tool developed by Guardian Geomatics to integrate many an unlimited quantity of of multibeam bathymetry survey lines, and generate a series of data products.  These products can be used to quality control in a consistent manner and when acceptable, deliver to the client.  The tool is rigorous and highly automated, producing consistent deliverable products.")
# 	myreport.addspace()

####################################################################################################
####################################################################################################
####################################################################################################
def reportdetail(myreport, KMALLBackscatterlogfilename, thisreport):

	#write out the per line stats...
	reportfilename = KMALLBackscatterlogfilename + "_detail.txt"
	f = open(reportfilename, 'w')
	f.write("Item Value\n")
	# loop through dictionary and write out the report
	for key in thisreport.keys():
		f.write("%s: %s\n" % (key, thisreport[key]))
	f.close()

	myreport.addspace()
	myreport.addtitle("Input File Configuration Details")
	myreport.addspace()
	myreport.addtable(reportfilename)

	image = thisreport["ARC_filename"]
	if os.path.exists(image):
		myreport.addimage(image, 450)

	image = thisreport["backscatter_raw_filename"]
	if os.path.exists(image):
		myreport.addimage(image, 450)
	image = thisreport["backscatter_processed_filename"]
	if os.path.exists(image):
		myreport.addimage(image, 450)

	myreport.story.append(PageBreak())

	return

####################################################################################################
def reportrecommendation(myreport, KMALLBackscatterlogfilename, thisreport):

	#write out the per line stats...
	reportfilename = KMALLBackscatterlogfilename + "_recommendation.txt"
	f = open(reportfilename, 'w')
	for result in thisreport:
		f.write(result + "\n")
	f.close()

	myreport.addspace()
	myreport.addtitle("Report Recommendations")
	myreport.addspace()
	myreport.addtable(reportfilename)
	# myreport.story.append(PageBreak())

	return

####################################################################################################
def report(KMALLBackscatterlogfilename, resultfolder, reports = [], recommendations = []):
	'''create an infinitpos QC report into PDF'''
	if not os.path.exists(resultfolder):
		return

	outfilename = os.path.join(resultfolder, "KMALLBackscatterQCReport.pdf")
	outfilename = fileutils.createOutputFileName(outfilename)
	myreport = REPORT("KMALL Backscatter Calibration Report", outfilename)

	reportrecommendation(myreport, KMALLBackscatterlogfilename, recommendations)

	#parse the KMALLBackscatter log file and make a summary table
	if os.path.exists(KMALLBackscatterlogfilename):
		reportsummary(myreport, KMALLBackscatterlogfilename )

	
	for rep in reports:
		reportdetail(myreport, KMALLBackscatterlogfilename, rep)

	myreport.save()
	myreport.viewpdf()

####################################################################################################
def reportsummary(myreport, KMALLBackscatterlogfilename):

	if not os.path.exists(KMALLBackscatterlogfilename):
		return

	#process the log file
	surveylines = []
	KMALLBackscatterduration = ""
	surveyline = None
	status = []
	metrics = []
	metrics.append (["Inputs_Summary_Log", KMALLBackscatterlogfilename])

	with open(KMALLBackscatterlogfilename) as fp:
		for line in fp:
			line = line.replace("  ", " ")
			line = line.replace("  ", " ")
			line = line.replace("  ", " ")
			line = line.strip()
			line = line.lstrip()
			line = line.rstrip()

			collectinformation(line, "INFO:root:Username:", "Username", metrics)
			collectinformation(line, "INFO:root:Computer:", "Computer", metrics)
			collectinformation(line, "INFO:root:KMALLBackscatter Version:", "QC_Version", metrics)
			collectinformation(line, "INFO:root:Processing file:", "Input_Filename", metrics)
			collectinformation(line, "INFO:root:QC Duration:", "KMALLBackscatter_Duration", metrics)

			collectinformation(line, "INFO:root:AVG File Saved to:", "AVG_Plot", metrics)

			msg = "INFO:root:Processing file:"
			if msg in line:
				line = line.replace(msg,"")
				line = line.strip()
				depthfilename = line

			msg = "INFO:root:Created REGIONAL TIF file for IHO validation:"
			if msg in line:
				line = line.replace(msg,"")
				line = line.strip()
				metrics.append(["Regional_TIF", line])
				regionalfilename = line
		
			msg = "INFO:root:Created TXT file of outliers:"
			if msg in line:
				line = line.replace(msg,"")
				line = line.strip()
				metrics.append(["Outlier_TXT_Filename", line])
				outliertxtfilename = line

	totalpoints = 0

	#write out the per line stats...
	reportfilename = KMALLBackscatterlogfilename + "_adjustment.txt"
	f = open(reportfilename, 'w')
	f.write("Item Value\n")
	for rec in metrics:
		f.write("%s: %s\n" % (rec[0], rec[1]))
	f.close()

	myreport.addspace()
	myreport.addtitle("KMALLBackscatter Calibration : Summary of Results")
	myreport.addspace()
	myreport.addtable(reportfilename)

	myreport.addtitle("What is Backscatter Calibration?")
	myreport.addspace()
	myreport.addparagraph("Multibeam sonar systems are used for mapping the seafloor and underwater terrain by emitting multiple acoustic beams in a fan-like pattern and recording the backscattered signals that bounce back from the seafloor and submerged objects. The backscatter data provides information about the characteristics of the seafloor or underwater features, including the intensity and texture of the backscattered signals.")
	myreport.addparagraph("Here's what multibeam backscatter data can reveal:")
	myreport.addparagraph("* Seafloor Texture: The intensity of the backscattered signals can indicate the texture of the seafloor. For example, fine sediments will often result in weaker backscatter, while rocky or hard seafloor will produce stronger backscatter.")
	myreport.addparagraph("* Seafloor Features: Multibeam backscatter data can reveal the presence of seafloor features such as shipwrecks, boulders, coral reefs, or any other objects on the seabed.")
	myreport.addparagraph("* Environmental Information: It can provide insights into the environmental conditions of the underwater area, including information about the substrate composition, seafloor habitats, and the distribution of marine life.")
	myreport.addparagraph("* Geological Data: Geologists use multibeam backscatter data to study the geological characteristics of the seafloor, including fault lines, underwater volcanoes, and sedimentary deposits.")
	myreport.addparagraph("* Mapping and Navigation: The data is also crucial for creating accurate bathymetric maps and aiding in navigation for various underwater activities, including scientific research, offshore construction, and marine resource management.")
	myreport.addparagraph("Overall, multibeam backscatter data is a valuable tool for understanding and characterizing the seafloor and the underwater environment, making it essential for a wide range of applications in marine science, hydrography, and oceanography..")

	myreport.addtitle("KMALLBackscatter Principles")
	myreport.addspace()
	myreport.addparagraph("KMALLBackscatter is a tool developed by Guardian Geomatics to extract the RAW backscatter from a KMALL file, analyse the data and produce information to permit the backscatter data to be calibrated for operations..")
	myreport.addparagraph("Calibration means alignment rather than a scientific calibration against a known standard. this is in line with a patch test calibration which is also nothing more than alignment.")
	myreport.addparagraph("KMALLBackscatter does NOT modify the input file in any way. It is a read-only process.")
	myreport.addspace()

	myreport.addtitle("Definitions")
	myreport.addspace()
	myreport.addparagraph("'Backscatter' is the primary input. It is read from KMALL files MRZ datagram.  There are 2 backscatter values recorded on each and every beam of every ping..")
	myreport.addparagraph("The first backscatter value is the 'RAW' backscatter. This is the backscatter value as recorded by the sonar. It is a relative value and is not calibrated in any way. It is a value between 0 and 255.")
	myreport.addparagraph("The second backscatter value is the 'CALIBRATED' backscatter. This is the backscatter value after the sonar has applied a calibration curve to the RAW backscatter. It is a relative value and is not calibrated in any way. It is a value between 0 and 255.")
	myreport.addparagraph("The 'RAW' backscatter is the value used by KMALLBackscatter to analyse the backscatter data.")
	myreport.addparagraph("The 'CALIBRATED' backscatter is the value used by the sonar to display the backscatter data.")
	myreport.addspace()

	myreport.addtitle("Inputs")
	myreport.addspace()
	myreport.addparagraph("One or more KMALL files.")
	myreport.addparagraph("An existing BSCORR.TXT file if you have it.")
	myreport.addspace()

	myreport.addtitle("Outputs")
	myreport.addspace()
	myreport.addparagraph("This PDF report.")
	myreport.addparagraph("KMALLBackscatter will generate a QC report (this document) in order to enable rapid assessment of results.")
	myreport.addspace()
	
	myreport.addtitle("What to do with this report")
	myreport.addspace()
	myreport.addparagraph("The report will permit you to create a new BSCORR.TXT file which can then be uploaded into SIS.  SIS uses this file to improve the backscatter as computed at beam forming time which is why it needs to be applied BEFORE logging to new raw kmall files.")
	myreport.addparagraph("The report will permit you to review each file, check the Angular Response Curve ARC has a sensible shape without spikes.")
	myreport.addparagraph("The report will permit you to ensure the configuration of the sonar during acquisition has not changed.  Each kmall file should have a consistent set of parameters such as frequency, pulse length, gain, etc.")
	myreport.addspace()

	myreport.story.append(PageBreak())
	# myreport.addparagraph("")
	
	# image = os.path.join(os.path.dirname(__file__), "KMALLBackscatterExample.png")
	# myreport.addimage(image, 450)
	# myreport.addspace()
	# myreport.addparagraph("END OF REPORT.")

	return

####################################################################################################
# def report(KMALLBackscatterlogfilename, resultfolder, reports = []):
# 	'''create an infinitpos QC report into PDF'''
# 	if not os.path.exists(resultfolder):
# 		return

# 	outfilename = os.path.join(resultfolder, "KMALLBackscatterQCReport.pdf")
# 	outfilename = fileutils.createOutputFileName(outfilename)
# 	myreport = REPORT("KMALLBackscatter QCReport", outfilename)

# 	#parse the KMALLBackscatter log file and make a summary table
# 	if os.path.exists(KMALLBackscatterlogfilename):
# 		reportsummary(myreport, KMALLBackscatterlogfilename )

# 	for rep in reports:
# 		reportdetail(myreport, KMALLBackscatterlogfilename, rep)
# 	myreport.save()
# 	myreport.viewpdf()

####################################################################################################
def addQCImage(myreport, f, fragment, notes):
		if fragment in os.path.basename(f).lower():
			requiredwidth = 512
			cmapfilename = findcmap(os.path.dirname(myreport.filename), fragment+"_cmap")
			outfilename = os.path.join(f + "_QC.png")
			image = myreport.compositeimage(f, requiredwidth, cmapfilename, 15 ,outfilename)
			
			myreport.addtitle("File: %s" % (os.path.basename(f)))
			for note in notes:
				myreport.addparagraph(note)
			myreport.addimage(image, requiredwidth/3)

# ###################################################################################################
def findcmap(folder, text):
	cmapname = ""
	matches = fileutils.findFiles2(False, folder, "*"+text+"*")
	for f in matches:
		cmapname = f
		return cmapname
	return cmapname

# ###################################################################################################
def main():

	parser = ArgumentParser(description='\n * generate a PDF report from KMALLBackscatter Process one or many mission folders using KMALLBackscatter.')
	parser.add_argument('-i', 			dest='inputfolder', action='store', 		default='.',			help='the root folder to find one more more mission folders. Pease refer to procedure for the mission folder layout - e.g. c:/mysurveyarea')
	
	args = parser.parse_args()

	if args.inputfolder == '.':
		args.inputfolder = os.getcwd()

	# resultfolder = os.path.join(args.inputfolder, "8_cor").replace('\\','/')
	# KMALLBackscatterlogfilename = os.path.join(os.path.dirname(args.inputfolder), "KMALLBackscatter.log").replace('\\','/')
	# KMALLBackscatterreport(KMALLBackscatterlogfilename, resultfolder)

	# outfilename = "c:/temp/myfile.pdf"
	# outfilename = fileutils.createOutputFileName(outfilename)
	
	# myreport = REPORT("reportname", outfilename)
	# myreport.addheader("Report %s" % (outfilename))
	# myreport.addtitle("The quick brown fox jumped over the lazy dog.")
	# myreport.addparagraph("This is a bad world.  we need to take care of The BaseDocTemplate class implements the basic machinery for document formatting. An instance of the class contains a list of one or more PageTemplates that can be used to describe the layout of information on a single page. The build method can be used to process a list of Flowables to produce a PDF document.")
	# myreport.addparagraph("X")

	# myreport.addimage("guardian.png", 50, "the guardian logo")
	# myreport.addparagraph("This is a bad world.  we need to take care of The BaseDocTemplate class implements the basic machinery for document formatting. An instance of the class contains a list of one or more PageTemplates that can be used to describe the layout of information on a single page. The build method can be used to process a list of Flowables to produce a PDF document.")

	# myreport.newpage()
	# myreport.addheader("page2")

	# myreport.addimage("guardian.png", 50, "the guardian logo")
	# myreport.addparagraph("This is a bad world.  we need to take care of The BaseDocTemplate class implements the basic machinery for document formatting. An instance of the class contains a list of one or more PageTemplates that can be used to describe the layout of information on a single page. The build method can be used to process a list of Flowables to produce a PDF document.")

	# myreport.newpage()
	# myreport.addheader("Page 3")

	# myreport.save()
	# myreport.viewpdf()

# 	# move the origin up and to the left
# 	c.translate(mm,mm)
# 	# define a large font
# 	c.setFont("Helvetica", 10)
# 	# choose some colors
# 	c.setStrokeColorRGB(0.2,0.5,0.3)
# 	c.setFillColorRGB(1,0,1)
# 	# draw some lines
# 	c.line(0,0,0,10*mm)
# 	c.line(0,0,10*mm,0)
# 	# draw a rectangle
# 	c.rect(2*mm,2*mm,10*mm,15*mm, fill=1)
# 	# make text go straight up
# 	c.rotate(45)
# 	# change color
# 	# say hello (note after rotate the y coord needs to be negative!)
# 	c.drawString(100*mm,100*mm,"Hello World",)
# 	c.setFillColorRGB(0,0,0.77)
# 	c.rotate(-45)

# 	image = "guardian.png"
# 	x = 100
# 	y = 100
# 	c.drawImage(image, x,y, preserveAspectRatio=True, width=10*mm,height=10,mask=None)

# ###################################################################################################
# def header(c, title):
# 	headerheight = 25*mm
# 	top = c._pagesize[1]

# 	# move the origin up and to the left
# 	# c.translate(mm,mm)
# 	# define a font
# 	# choose some colors
# 	c.setStrokeColorRGB(0,0,0)
# 	c.setFillColorRGB(0,0,0)

# 	# set the title
# 	x = 10*mm
# 	y = top - 15*mm
# 	c.setFont("Helvetica", 18)
# 	c.drawString(x, y, title)

# 	# set the date
# 	x = 10*mm
# 	y = top - 22*mm
# 	c.setFont("Helvetica", 8)
# 	str = "Report Date: %s" % (datetime.now().strftime("%Y%m%d%H%M%S"))
# 	c.drawString(x, y, str)

# 	image = "guardian.png"
# 	x = c._pagesize[0]-(20*mm)
# 	y = top - 22*mm
# 	c.drawImage(image, x,y, preserveAspectRatio=True, width=15*mm, height=15*mm, mask=None)

# 	# draw header line
# 	c.line(5*mm, top-headerheight, c._pagesize[0]-(5*mm), c._pagesize[1]-headerheight)

##############################################################################
class REPORTSURVEYLINE:
	'''class to hold a group for reporting'''
	##############################################################################
	def __init__(self, name):
		self.group = ""
		words = name.split(" ")
		if len(words) > 0:
			self.name = words[0]

##############################################################################
class REPORT:
	'''class to create a PDF report'''
	##############################################################################
	def __init__(self, title, filename):
		self.filename = filename
		self.title = title
		styles = getSampleStyleSheet()
		self.normal = styles["Normal"]
		self.heading1 = styles['Heading1']
		# self.doc = SimpleDocTemplate(filename, pagesize=A4)
		# self.canvas = canvas.Canvas(filename, pagesize=A4)
		# self.cursor = self.canvas._pagesize[1]
		# self.leftmargin = self.canvas.leftMargin
		# self.rightmargin = self.canvas.rightMargin
		self.story = []

		self.doc = BaseDocTemplate(self.filename, pagesize=A4)
		frame = Frame(self.doc.leftMargin, self.doc.bottomMargin, self.doc.width, self.doc.height-0.5*cm, id='normal')
		# header_content = Paragraph("This is a multi-line header.  It goes on every page.  " * 8, self.normal)
		template = PageTemplate(id='header', frames=frame, onPage=partial(self.addheader, title=title))
		self.doc.addPageTemplates([template])

###################################################################################################
	def get_image(self, path, width=100*mm):
		img = utils.ImageReader(path)
		iw, ih = img.getSize()
		aspect = ih / float(iw)
		# scalefactor=min((self.doc.height/ih), (self.doc.width/iw))
		width=min(width, self.doc.width)
		
		height=min((width * aspect), self.doc.height - self.doc.topMargin - self.doc.bottomMargin)
		# width = self.doc.width * scalefactor
		# height= self.doc.height * scalefactor
		# return Image(path, width=iw, height=ih)
		return Image(path, width=width, height=height)

		# lowable <Image at 0x2baa2bbd390 frame=normal filename=KMALLBackscattergis.png>(1918 x 1032) too large on page 3 in frame 'normal'(439.27559055118115 x 671.716535433071*) of template 'header'

###################################################################################################
	def compositeimage(self, filename, requiredwidth, legendfilename, legendwidth, outfilename):

		#the image we need to add a legend to
		PIL.Image.MAX_IMAGE_PIXELS = None
		img = PIL.Image.open(filename, 'r')
		img_w, img_h = img.size

		MAXWIDTH = requiredwidth
		ratio = MAXWIDTH/img.size[0]
		newimg = img.resize((int(img.size[0]*ratio), int(img.size[1]*ratio)), PIL.Image.ANTIALIAS)
		newimg_w, newimg_h = newimg.size

		#the new image for compositing into
		background = PIL.Image.new('RGBA', (newimg_w, newimg_h), (255, 255, 255, 255))
		bg_w, bg_h = background.size
	
		offset = ((bg_w - newimg_w) // 2, (bg_h - newimg_h) // 2)
		background.paste(newimg, offset)

		#the legend
		if os.path.exists(legendfilename):
			imglegend = PIL.Image.open(legendfilename, 'r')
			# imglegend_w, imglegend_h = imglegend.size
			MAXWIDTH = legendwidth
			ratio = MAXWIDTH/imglegend.size[0]
			newlegend = imglegend.resize((int(imglegend.size[0]*ratio), int(imglegend.size[1]*ratio)), PIL.Image.ANTIALIAS)
			background.paste(newlegend, (0,0))

		background.save(outfilename)
		return outfilename

###################################################################################################
	def addimagetable(self, filename, width, legendfilename, legendheight):
		'''write an image'''

		self.story.append(self.get_image(filename, width=40*mm))

###################################################################################################
	def addimage(self, filename, width=320, height=640):
		'''write an image'''

		self.story.append(self.get_image(filename, width=width))
		# image = Image(filename, width=height, height=height)
		# image = Image(filename, width=height, height=height, preserveAspectRatio=True)
		# self.story.append(image)

		# x = ((self.docrightmargin - self.leftmargin) / 2 ) + self.leftmargin
		# y = self.cursor - (height*1.5)
		# self.canvas.drawImage(filename, x,y, preserveAspectRatio=True, width=height*mm, height=height*mm, mask=None, anchorAtXY=True, anchor='c')

		# self.setcursor(height*3.2)

		# if len(label) == 0:
		# 	return

		# self.canvas.drawCentredString(x, self.cursor, label)
		# self.setcursor(10)


	###################################################################################################
	def addheader(self,canvas, doc, title):
		canvas.saveState()

		top = doc.height + doc.topMargin + (5 * mm)
		#do the title
		header_content = Paragraph(title, self.heading1)
		w, h = header_content.wrap(doc.width, doc.topMargin)
		header_content.drawOn(canvas, doc.leftMargin, top)
		
		
		# # set the date
		canvas.setFont("Helvetica", 8)
		str = "Creation Date: %s" % (datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
		canvas.drawString(doc.leftMargin, top - 5*mm, str)

		# set the user
		canvas.setFont("Helvetica", 6)
		str = "User : %s" % (os.getlogin())
		canvas.drawString(doc.leftMargin + 130*mm, top - 5*mm, str)

		image = os.path.join(os.path.dirname(__file__), "guardian.png")
		x = doc.width + (15 * mm)
		y = top - 6*mm
		canvas.drawImage(image, x,y, preserveAspectRatio=True, width=15*mm, height=15*mm, mask=None)

		# # draw header line
		y = top - 7*mm
		canvas.line(doc.leftMargin, y, doc.width + (30*mm), y)

		canvas.restoreState()

	###################################################################################################
	# def setcursor(self, dy):
	# 	self.cursor -= dy

	# ###################################################################################################
	# def resetcursor(self):
	# 	self.cursor = self.canvas._pagesize[1]

	###################################################################################################
	def viewpdf(self):
		os.startfile(self.filename, 'open')

	###################################################################################################
	def save(self):
		self.doc.build(self.story)
		# self.doc.save()

	# ###################################################################################################
	def newpage(self):
		self.story.append(PageBreak())
	# 	self.canvas.showPage()
	# 	self.resetcursor()

	###################################################################################################
	def addparagraph(self, text):
		'''write a paragraph of text '''

		# text.append(Paragraph("This is line %d." % i, styleN))

		styles = getSampleStyleSheet()
		style = styles["Normal"]
		# story = [Spacer(1,2*mm)]
		p = Paragraph(text, style)
		self.story.append(p)
		# Story.append(Spacer(1,0.2*mm))
		# self.canvas.build(Story)

		# width = self.rightmargin - self.leftmargin
		# # pixperchar = style.fontSize
		# charsperline = width / style.fontSize * .15
		# height = max(35, len(text) / charsperline)
		# f = Frame(self.leftmargin, self.cursor-height, width, height, leftPadding=0, bottomPadding=1, rightPadding=0, topPadding=0, showBoundary=1 )
		# f.addFromList(story, self.canvas)

		# # self.canvas.setFont("Helvetica", 12)
		# # self.canvas.drawString(self.leftmargin, self.cursor, text)

		# self.setcursor(height)

###################################################################################################
	def addspace(self, height=1):
		self.story.append(Spacer(1,float(height)*mm))

###################################################################################################
	def addtable(self, filename):

		# data= [['00', '01', '02', '03', '04', '04', '04', '04', '04', '04', '04', '04', '04', '04', '04', '04', '04', '04', '04', '04', '04', '04', '04', '04', '04', '04', '04', '04', '04', '04', '04', '04', '04', '04', '04', '04', '04', '04'],
		# ['10', '11', '12', '13', '14'],
		# ['20', '21', '22', '23', '24'],
		# ['30', '31', '32', '33', '34']]
		# t=Table(data)
		# t.setStyle(TableStyle([('BACKGROUND',(1,1),(-2,-2),colors.green),
		# ('TEXTCOLOR',(0,0),(1,-1),colors.red)]))
		# self.story.append(t)
		# return


		styles = getSampleStyleSheet()

		style = styles["Normal"]
		style.fontSize=6
		# story = [Spacer(1,2*mm)]

		data = []
		with open(filename) as fp:
			for line in fp:
				line = line.strip()
				line = line.lstrip()
				line = line.rstrip()
				line = line.replace("  ", " ")
				line = line.replace("  ", " ")
				line = line.replace("  ", " ")
				line = line.replace("  ", " ")
				line = line.replace("  ", " ")
				line = line.replace("  ", " ")
				line = line.replace("  ", " ")
				words = line.split(" ")
				# data.append([Paragraph(words[0], style), Paragraph(words[1], style)])
				row=[]
				for word in words:
					row.append([Paragraph(word, style)])
				data.append(row)
		t=Table(data, rowHeights=None, style=None, splitByRow=1, repeatRows=0, repeatCols=0, rowSplitRange=None, spaceBefore=None, spaceAfter=None)
		# t=Table(data, rowHeights=None, style=None, splitByRow=1, repeatRows=0, repeatCols=0, rowSplitRange=None, spaceBefore=None, spaceAfter=None, colWidths=[5 * cm, 10 * cm])
		t.setStyle(TableStyle([('FONTNAME',(0,0),(-1,0), "Helvetica-Bold")]))
		t.setStyle(TableStyle([('FONTSIZE',(0,0),(-1,-1), 6)]))
		t.setStyle(TableStyle([('LEFTPADDING',(0,0),(-1,-1), 2)]))
		t.setStyle(TableStyle([('RIGHTPADDING',(0,0),(-1,-1), 2)]))
		t.setStyle(TableStyle([('TOPPADDING',(0,0),(-1,-1), 2)]))
		t.setStyle(TableStyle([('BOTTOMPADDING',(0,0),(-1,-1), 2)]))
		t.setStyle(TableStyle([('INNERGRID',(0,0),(-1,-1), 0.25, colors.black)]))
		t.setStyle(TableStyle([('BOX',(0,0),(-1,-1), 0.25, colors.black)]))
		t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),colors.lightblue), ('TEXTCOLOR',(0,0),(0,0),colors.black)]))
		# t.setStyle(TableStyle([('BACKGROUND',(1,1),(-2,-2),colors.green),
		# ('TEXTCOLOR',(0,0),(1,-1),colors.red)]))
		width, height = A4
		# c = canvas.Canvas("a.pdf", pagesize=A4)

		# w, h = t.wrap(width, height)
		# table.wrapOn(c, width, height)
		# table.drawOn(c, *coord(ml - 0.05, y + 4.6, height - h, cm))

		# t.wrapOn(c, width, height)
		# t.drawOn(c, *self.coord(1.8, 9.6, height - h, cm))
		self.story.append(t)

###################################################################################################
	def coord(self, x, y, height, unit=1):
		x, y = x * unit, height -  y * unit
		return x, y
###################################################################################################
	def addtitle(self, text):
		'''write a title of text '''

		styles = getSampleStyleSheet()
		style = styles["Heading2"]
		p = Paragraph(text, style)
		self.story.append(p)
		# Story.append(Spacer(1,0.2*mm))
		# self.canvas.build(Story)

		# width = self.rightmargin - self.leftmargin
		# # pixperchar = style.fontSize
		# charsperline = width / style.fontSize * .15
		# height = max(50, len(text) / charsperline)
		# f = Frame(self.leftmargin, self.cursor-height, width, height, leftPadding=0, bottomPadding=1, rightPadding=0, topPadding=0, showBoundary=0 )
		# f.addFromList(story, self.canvas)

		# # self.canvas.setFont("Helvetica", 12)
		# # self.canvas.drawString(self.leftmargin, self.cursor, text)

		# self.setcursor(height)

	# ###################################################################################################
	# def oldaddheader(self, title):
	# 	headerheight = 25*mm
	# 	top = self.canvas.height

	# 	# move the origin up and to the left
	# 	# c.translate(mm,mm)
	# 	# define a font
	# 	# choose some colors
	# 	# self.canvas.setStrokeColorRGB(0,0,0)
	# 	# self.canvas.setFillColorRGB(0,0,0)

	# 	# set the title
	# 	x = 10*mm
	# 	y = top - 15*mm
	# 	self.canvas.setFont("Helvetica-Bold", 14)

	# 	self.canvas.drawString(x, y, title)

	# 	# set the date
	# 	x = 10*mm
	# 	y = top - 20*mm
	# 	self.canvas.setFont("Helvetica", 8)
	# 	str = "Creation Date: %s" % (datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
	# 	self.canvas.drawString(x, y, str)

	# 	# set the user
	# 	x = 150*mm
	# 	y = top - 20*mm
	# 	self.canvas.setFont("Helvetica", 8)
	# 	str = "User : %s" % (os.getlogin())
	# 	self.canvas.drawString(x, y, str)

	# 	# set the user
	# 	x = 10*mm
	# 	y = top - 23*mm
	# 	self.canvas.setFont("Helvetica", 8)
	# 	str = "Filename : %s" % (self.filename)
	# 	self.canvas.drawString(x, y, str)

	# 	image = "guardian.png"
	# 	x = self.canvas._pagesize[0]-(20*mm)
	# 	y = top - 22*mm
	# 	self.canvas.drawImage(image, x,y, preserveAspectRatio=True, width=15*mm, height=15*mm, mask=None)

	# 	# draw header line
	# 	self.canvas.line(5*mm, top-headerheight, self.canvas._pagesize[0]-(5*mm), self.canvas._pagesize[1]-headerheight)

	# 	self.setcursor(headerheight)




##############################################################################
##############################################################################
##############################################################################
##############################################################################
##############################################################################
# class REPORTORI:
# 	'''class to create a PDF report'''
# 	##############################################################################
# 	def __init__(self, filename):
# 		self.filename = filename
# 		self.title = ""
# 		self.doc = SimpleDocTemplate(filename, pagesize=A4)
# 		self.canvas = canvas.Canvas(filename, pagesize=A4)
# 		self.cursor = self.canvas._pagesize[1]
# 		self.leftmargin = 10 * mm
# 		self.rightmargin = self.canvas._pagesize[0] - (10 * mm)

# 	###################################################################################################
# 	def setcursor(self, dy):
# 		self.cursor -= dy

# 	###################################################################################################
# 	def resetcursor(self):
# 		self.cursor = self.canvas._pagesize[1]

# 	###################################################################################################
# 	def viewpdf(self):
# 		os.startfile(self.filename, 'open')

# 	###################################################################################################
# 	def save(self):
# 		self.canvas.save()

# 	###################################################################################################
# 	def newpage(self):
# 		self.canvas.showPage()
# 		self.resetcursor()

# 	###################################################################################################
# 	def addparagraph(self, text):
# 		'''write a paragraph of text '''

# 		styles = getSampleStyleSheet()
# 		style = styles["Normal"]
# 		story = [Spacer(1,2*mm)]
# 		p = Paragraph(text, style)
# 		story.append(p)
# 		# Story.append(Spacer(1,0.2*mm))
# 		# self.canvas.build(Story)

# 		width = self.rightmargin - self.leftmargin
# 		# pixperchar = style.fontSize
# 		charsperline = width / style.fontSize * .15
# 		height = max(35, len(text) / charsperline)
# 		f = Frame(self.leftmargin, self.cursor-height, width, height, leftPadding=0, bottomPadding=1, rightPadding=0, topPadding=0, showBoundary=1 )
# 		f.addFromList(story, self.canvas)

# 		# self.canvas.setFont("Helvetica", 12)
# 		# self.canvas.drawString(self.leftmargin, self.cursor, text)

# 		self.setcursor(height)

# ###################################################################################################
# 	def addtable(self, filename):

# 		data = []
# 		with open(filename) as fp:
# 			line = fp.readline()
# 			cnt = 1
# 			while line:
# 				print("Line {}: {}".format(cnt, line.strip()))
# 				line = fp.readline()
# 				words = line.split(" ")
# 				data.append([words])
# 				cnt += 1

# 		styles = getSampleStyleSheet()
# 		style = styles["Normal"]
# 		story = [Spacer(1,2*mm)]
# 		t = Table(data, colWidths=10, rowHeights=None, style=None, splitByRow=1, repeatRows=0, repeatCols=0, rowSplitRange=None, spaceBefore=None, spaceAfter=None)
# 		# t = Table(data)

# 		width = 200
# 		height = 200
# 		# self.canvas.wrapOn(t, width, height)
# 		t.drawOn(self.canvas, self.leftmargin, self.cursor-200)
		
# 		# col_widths = 10
# 		# story.append(Table(data, colWidths=col_widths))

# 		# # self.canvas.append(t)

# 		# height = 200
# 		# t.drawOn(self.canvas, self.leftmargin, self.cursor-height, _sW=0)

# 		# story.append(t)
# 		# width = self.rightmargin - self.leftmargin
# 		# charsperline = width / style.fontSize * .15
# 		# height = max(135, len(data) / charsperline)
# 		# f = Frame(self.leftmargin, self.cursor-height, width, height, leftPadding=0, bottomPadding=1, rightPadding=0, topPadding=0, showBoundary=0 )
# 		# f.addFromList(story, self.canvas)
# 		# f = Frame(self.leftmargin, self.cursor-height, width, height, leftPadding=0, bottomPadding=1, rightPadding=0, topPadding=0, showBoundary=1 )
# 		# f.addFromList(story, self.canvas)

# ###################################################################################################
# 	def addtitle(self, text):
# 		'''write a title of text '''

# 		styles = getSampleStyleSheet()
# 		style = styles["Heading2"]
# 		story = [Spacer(1,2*mm)]
# 		p = Paragraph(text, style)
# 		story.append(p)
# 		# Story.append(Spacer(1,0.2*mm))
# 		# self.canvas.build(Story)

# 		width = self.rightmargin - self.leftmargin
# 		# pixperchar = style.fontSize
# 		charsperline = width / style.fontSize * .15
# 		height = max(50, len(text) / charsperline)
# 		f = Frame(self.leftmargin, self.cursor-height, width, height, leftPadding=0, bottomPadding=1, rightPadding=0, topPadding=0, showBoundary=0 )
# 		f.addFromList(story, self.canvas)

# 		# self.canvas.setFont("Helvetica", 12)
# 		# self.canvas.drawString(self.leftmargin, self.cursor, text)

# 		self.setcursor(height)

# 	###################################################################################################
# 	def addheader(self, title):
# 		headerheight = 25*mm
# 		top = self.canvas._pagesize[1]

# 		# move the origin up and to the left
# 		# c.translate(mm,mm)
# 		# define a font
# 		# choose some colors
# 		self.canvas.setStrokeColorRGB(0,0,0)
# 		self.canvas.setFillColorRGB(0,0,0)

# 		# set the title
# 		x = 10*mm
# 		y = top - 15*mm
# 		self.canvas.setFont("Helvetica-Bold", 14)

# 		self.canvas.drawString(x, y, title)

# 		# set the date
# 		x = 10*mm
# 		y = top - 20*mm
# 		self.canvas.setFont("Helvetica", 8)
# 		str = "Creation Date: %s" % (datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
# 		self.canvas.drawString(x, y, str)

# 		# set the user
# 		x = 150*mm
# 		y = top - 20*mm
# 		self.canvas.setFont("Helvetica", 8)
# 		str = "User : %s" % (os.getlogin())
# 		self.canvas.drawString(x, y, str)

# 		# set the user
# 		x = 10*mm
# 		y = top - 23*mm
# 		self.canvas.setFont("Helvetica", 8)
# 		str = "Filename : %s" % (self.filename)
# 		self.canvas.drawString(x, y, str)

# 		image = "guardian.png"
# 		x = self.canvas._pagesize[0]-(20*mm)
# 		y = top - 22*mm
# 		self.canvas.drawImage(image, x,y, preserveAspectRatio=True, width=15*mm, height=15*mm, mask=None)

# 		# draw header line
# 		self.canvas.line(5*mm, top-headerheight, self.canvas._pagesize[0]-(5*mm), self.canvas._pagesize[1]-headerheight)

# 		self.setcursor(headerheight)

# ###################################################################################################
# 	def addimage(self, filename, height, label=""):
# 		'''write an image'''

# 		x = ((self.rightmargin - self.leftmargin) / 2 ) + self.leftmargin
# 		y = self.cursor - (height*1.5)
# 		self.canvas.drawImage(filename, x,y, preserveAspectRatio=True, width=height*mm, height=height*mm, mask=None, anchorAtXY=True, anchor='c')

# 		self.setcursor(height*3.2)

# 		if len(label) == 0:
# 			return

# 		self.canvas.drawCentredString(x, self.cursor, label)
# 		self.setcursor(10)

# ###################################################################################################
# def main2():
# 	outfilename = "c:/temp/myfile.pdf"
# 	outfilename = fileutils.createOutputFileName(outfilename)
# 	resultfolder = os.path.dirname(outfilename)

# 	styles = getSampleStyleSheet()
# 	styleN = styles['Normal']
# 	# styleH = styles['Heading1']

# 	myreport = REPORT("KMALLBackscatter QC Report %s" % (os.path.dirname(resultfolder)), outfilename)

# 	myreport.addparagraph("hello")
# 	myreport.addparagraph("hello2")
# 	myreport.addimage("guardian.png", 10)
# 	myreport.addparagraph("hello3")
# 	myreport.addparagraph("hello")
# 	myreport.addparagraph("hello2")
# 	myreport.addimage("guardian.png", 10)
# 	myreport.addparagraph("hello3")
# 	myreport.addparagraph("hello")
# 	myreport.addparagraph("hello2")
# 	myreport.addimage("guardian.png", 10)
# 	myreport.addparagraph("hello3")
# 	myreport.addparagraph("hello")
# 	myreport.addparagraph("hello2")
# 	myreport.addimage("guardian.png", 10)
# 	myreport.addparagraph("hello3")
# 	myreport.addparagraph("hello")
# 	myreport.addparagraph("hello2")
# 	myreport.addimage("guardian.png", 10)
# 	myreport.addparagraph("hello3")
# 	myreport.addparagraph("hello")
# 	myreport.addparagraph("hello2")
# 	myreport.addimage("guardian.png", 10)
# 	myreport.addparagraph("hello3")
# 	# story = []
# 	myreport.addparagraph("This is a bad world.  we need to take care of The BaseDocTemplate class implements the basic machinery for document formatting. An instance of the class contains a list of one or more PageTemplates that can be used to describe the layout of information on a single page. The build method can be used to process a list of Flowables to produce a PDF document.")
# 	myreport.addspace(2)

# 	myreport.addparagraph("This is a bad world.  we need to take care of The BaseDocTemplate class implements the basic machinery for document formatting. An instance of the class contains a list of one or more PageTemplates that can be used to describe the layout of information on a single page. The build method can be used to process a list of Flowables to produce a PDF document.")
# 	myreport.addparagraph("This is a bad world.  we need to take care of The BaseDocTemplate class implements the basic machinery for document formatting. An instance of the class contains a list of one or more PageTemplates that can be used to describe the layout of information on a single page. The build method can be used to process a list of Flowables to produce a PDF document.")
# 	myreport.addparagraph("This is a bad world.  we need to take care of The BaseDocTemplate class implements the basic machinery for document formatting. An instance of the class contains a list of one or more PageTemplates that can be used to describe the layout of information on a single page. The build method can be used to process a list of Flowables to produce a PDF document.")
# 	myreport.addparagraph("This is a bad world.  we need to take care of The BaseDocTemplate class implements the basic machinery for document formatting. An instance of the class contains a list of one or more PageTemplates that can be used to describe the layout of information on a single page. The build method can be used to process a list of Flowables to produce a PDF document.")
# 	myreport.doc.build(myreport.story)
# 	# myreport.doc.build(myreport.story)
	
# 	# for i in range(111):
# 	# 	story.append(Paragraph("This is line %d." % i, styleN))
# 	# myreport.doc.build(story)

# 	# myreport.addtitle("The quick brown fox jumped over the lazy dog.")
# 	# myreport.addparagraph("X")

# 	# myreport.addimage("guardian.png", 50, "the guardian logo")
# 	# myreport.addparagraph("This is a bad world.  we need to take care of The BaseDocTemplate class implements the basic machinery for document formatting. An instance of the class contains a list of one or more PageTemplates that can be used to describe the layout of information on a single page. The build method can be used to process a list of Flowables to produce a PDF document.")

# 	# myreport.newpage()
# 	# myreport.addheader("page2")

# 	# myreport.addimage("guardian.png", 50, "the guardian logo")
# 	# myreport.addparagraph("This is a bad world.  we need to take care of The BaseDocTemplate class implements the basic machinery for document formatting. An instance of the class contains a list of one or more PageTemplates that can be used to describe the layout of information on a single page. The build method can be used to process a list of Flowables to produce a PDF document.")

# 	# myreport.newpage()
# 	# myreport.addheader("Page 3")

# 	myreport.save()
# 	myreport.viewpdf()


###################################################################################################
if __name__ == "__main__":

	main()
	# resultfolder = "E:/projects/KMALLBackscatter/A14/IP_Result_20200725013252/8_cor"
	# KMALLBackscatterlogfilename = "E:/projects/KMALLBackscatter/A14/KMALLBackscatter.log"

	# KMALLBackscatterreport(KMALLBackscatterlogfilename, resultfolder)
