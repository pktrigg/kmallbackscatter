# kmallbackscatter will read a KMALL file and compute the per sector misalignment so the KM backscatter across a ping can be aligned. 

# 2DO
# permit a user to specify a beam correction table
# if using reciprocal lines we need to merge results together
# save as a bscorr.txt file
# make a pdf report
# make a dictionary of reportable items

# DONE
# extract the runtime parameters so we can document if using FMMode, Frequency
# extract the backscatter into a numpy array
# basic reading of a kmall file
# identify the sectors
# option to bin on angular basis.  default 1 degree
# write the csv on a per sector basis of angle, backscatter, sectorID
# ensure the file can be opened in Excel
# compute the per sector misalignment values
# compute the angular correction table
# plot the sector in a nice plot so users can see how well it lines up
# compute statistics on the per sector basis so we can have a measure of confidence


