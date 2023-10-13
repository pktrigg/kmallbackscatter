# kmallbackscatter 
This tool will read a KMALL file and compute the per sector misalignment so the KM backscatter across a ping can be aligned. It will create a report which can be used to check the quality of backscatter and be used to make a new bscorr file.

# DONE
* report on the serial number of the sonar Tx and Rx so we can refer to teh reports in the future
* if using reciprocal lines we need to merge results together
* add section to report 'recommended corrections to be applied to bscorr file'
* add support for multiple input files.
* report now creates backscatter geotif file of raw reflectivity so we can 'see the data'
* report now creates backscatter geotif file of processed reflectivity so we can 'see the data'
* make a pdf report
* make a dictionary of reportable items
* extract the runtime parameters so we can document if using FMMode, Frequency
* extract the backscatter into a numpy array
* option to bin on angular basis.  default 1 degree
* write the csv on a per sector basis of angle, backscatter, sectorID
* ensure the file can be opened in Excel
* compute the per sector misalignment values
* compute the angular correction table
* plot the sector in a nice plot so users can see how well it lines up
* compute statistics on the per sector basis so we can have a measure of confidence
* basic reading of a kmall file
* identify the sectors

# 2DO
* save as a bscorr.txt file
* if the user specifies a target reflectivity we can incorporate into report and compute corrections
* apply corrections to processed backscatter and plot as mosaic

