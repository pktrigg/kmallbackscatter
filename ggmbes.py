#name:			ggmbes
#created:		July 2017
#by:			p.kennedy@guardiangeomatics.com
#description:	python module to represent MBES data so we can QC, compute and merge.
 
import pprint

###############################################################################
class GGPING:
	'''used to hold the metadata associated with a ping of data.'''
	def __init__(self):
		self.timestamp			= 0
		self.longitude 			= 0
		self.latitude 			= 0
		self.ellipsoidalheight 	= 0
		self.heading		 	= 0
		self.pitch			 	= 0
		self.roll			 	= 0
		self.heave			 	= 0
		self.tidecorrector	 	= 0
		self.hydroid		 	= 0
		self.hydroidsmooth	 	= 0
		self.waterLevelReRefPoint_m = 0
		self.txTransducerDepth_m = 0
		self.hydroidstandarddeviation = 0
	
	###############################################################################
	def __str__(self):
		return pprint.pformat(vars(self))

###############################################################################
class GGSECTOR:
	'''used to hold the metadata associated with a SECTOR of data within a ping.'''
	def __init__(self):
		self.txSectorNumb			= 0
		self.txArrNumber			= 0
		self.txSubArray				= 0
		self.padding0				= 0
		self.sectorTransmitDelay_sec= 0
		self.tiltAngleReTx_deg		= 0
		self.txNominalSourceLevel_dB= 0
		self.txFocusRange_m			= 0
		self.centreFreq_Hz			= 0
		self.signalBandWidth_Hz		= 0
		self.totalSignalLength_sec	= 0
		self.pulseShading			= 0
		self.signalWaveForm			= 0
		self.padding1				= 0
		self.highVoltageLevel_dB	= 0
		self.sectorTrackingCorr_dB	= 0
		self.effectiveSignalLength_sec = 0

	###############################################################################
	def __str__(self):
		return pprint.pformat(vars(self))
