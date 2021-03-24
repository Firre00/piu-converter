import sys
import time

#Returns the searched field data
def getField(data, fieldName):
	table = ""
	start = data.find(fieldName)+len(fieldName)
	end = data.find(";", start)
	for i in range(start, end):
		table += data[i]
	if table.find(",") != -1:
		table = table.split(",")
	else:
		table = table.strip()
		if table.find("=") != -1:
			table = table.split("=")
			table = [table]
		return table

	for i, item in enumerate(table):
		table[i] = item.strip()
		if item.find("=") != -1:
			table[i] = table[i].split("=")
		try:
			if table[i].find("\n") != -1:
				table[i] = table[i].split("\n")
		except:
			continue

	return table

#Returns the split of the measure
def getSplit(measure):
	split = len(measure)/4
	return int(split)

def splitTemplate(bpm, split, delay = 0, beat = 4):
	template = f""":BPM={bpm}
:Delay={delay}
:Beat={beat}
:Split={split}"""
	return template

def doubleMeasure(measureIndex, notes):
	for noteMeasure in range(getSplit(notes[measureIndex]) * 4, 0, -1):
		notes[measureIndex].insert(noteMeasure, "." * len(notes[0][0]))
	notes = addHoldsMeasure(measureIndex, notes)
	return notes

def addHoldsMeasure(measureIndex, notes):
	ishold = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
	#print(measureIndex)
	#print((notes[measureIndex - 1][-1]))
	for note in range(len(notes[measureIndex - 1][-1])):
		curNote = notes[measureIndex - 1][-1][note]
		if curNote == "M":
			ishold[note] = 1

		if curNote == "H":
			ishold[note] = 1

	#print(ishold)
	for beat in range(len(notes[measureIndex])):
			for note in range(len(notes[measureIndex][beat])):
						curNote = notes[measureIndex][beat][note]
						if ishold[note] == 1 and curNote != "W":
							tempnotes = list(notes[measureIndex][beat])
							tempnotes[note] = "H"
							notes[measureIndex][beat] = "".join(tempnotes)

						if curNote == "M":
							ishold[note] = 1

						if curNote == "W":
							ishold[note] = 0
	return notes

def addHolds(notes):
	for measureIndex in range(len(notes)):
		notes = addHoldsMeasure(measureIndex, notes)
	return notes

##
#Find all bpm changes in measure
#Remove everything but the decimal part of the position
#Multiply the decimal part with current split, if int then no change is required
#If not int, multiply the original decimal part by 2*split
#If int then double the measure, if not int then repeat untill int or untill measure is 128
##

def bpmMeasure(notes, bpm):
	measureIndex = int(bpm[0])
	print(bpm[0])
	decimal = bpm[0] - int(bpm[0])
	print(decimal)
	notInt = 1
	while notInt:
		if (decimal * getSplit(notes[measureIndex])).is_integer():
			notInt = 0
		else:
			notes = doubleMeasure(measureIndex, notes)

		if getSplit(notes[measureIndex]) >= 128:
			break
	return notes




def main():

	#Try to get offset list
	offsetList = ""
	try:
		f = open("list.txt", "r")
		offsetList = f.read()
		f.close()
		offsetList = offsetList.split("\n")
		for offset in range(len(offsetList)):
			offsetList[offset] = offsetList[offset].split(": ")
	except:
		print("No offset list")


	#Check for file name if file got pulled onto the script
	try:
		infile = sys.argv[1]
		loop = len(sys.argv)
	except:
		infile = input("Input file: ")
		loop = 2

	#Start looping throught the files
	for file in range(1, loop):
		if loop > 2:
			infile = sys.argv[file]

		outfile = infile.replace(".ssc", ".ucs")

		if infile == outfile:
			print(f"File: {infile} is not .ssc")
			time.sleep(2)
			continue

		print(f"Converting {infile} to {outfile}")

		f = open(infile, "r")
		indata = f.read()
		f.close()



		#Get notedata and replce chars with ucs style
		notes = getField(indata, "#NOTES:")
		replaceChars = [["0", "."], ["1", "X"], ["2", "M"], ["3", "W"]]
		for measure in range(len(notes)):
			for beat in range(len(notes[measure])):
				for char in replaceChars:
					notes[measure][beat] = notes[measure][beat].replace(char[0], char[1])



		#Get bpms
		bpms = getField(indata, "#BPMS:")

		for i, bpm in enumerate(bpms):
			bpms[i][0] = float(bpm[0])/4

		#Get tick counts
		tickCounts = getField(indata, "#TICKCOUNTS:")

		#Get offset
		offset = float(getField(indata, "#OFFSET:"))*1000

		if (offsetList):
			for off in offsetList:
				if (outfile.split("\\")[-1] == off[0]):
					offset = off[1]

		#Get stops
		stops = getField(indata, "#STOPS:")

		stepstyle = len(notes[0][0])
		if stepstyle == 10:
			stepstyle = "Double"
		else:
			stepstyle = "Single"


		#Add holds
		notes = addHolds(notes)


		#Fix measures so that bpm changes can fit
		for bpm in bpms:
			notes = bpmMeasure(notes, bpm)

		
		
		bpmCounter = 0
		split = 0
		actualNoteCount = 0
		actualNoteOffset = 0
		actualNote = 0
		splitTime = True


		#Start writing the file
		f = open(outfile, "w")

		f.write(f":Format=1\n:Mode={stepstyle}\n")

		#Loop through the measures
		for measureId, measure in enumerate(notes):
			if getSplit(notes[measureId]) != split:
				split = getSplit(notes[measureId])
				splitTime = True



			#Loop through the beats
			for beatId, beat in enumerate(measure):

				#Keeps track of where you are in the chart
				actualNoteCount += 1
				actualNoteOffset += 1/getSplit(measure)/4
				if ((actualNoteCount/getSplit(measure)/4) == 1):
					actualNote += 1
					actualNoteCount = 0
					actualNoteOffset = 0
				trueBeat = actualNote + actualNoteOffset

				#Print a template block
				if splitTime:
					splitTime = False
					f.write(splitTemplate(bpms[bpmCounter][1], split) + "\n")

				#New bpm for next beat
				if len(bpms) != bpmCounter+1:
					if trueBeat == bpms[bpmCounter+1][0]:
						print(f"{bpmCounter}, {trueBeat}, {bpms[bpmCounter][0]}, {bpms[bpmCounter][1]}")
						splitTime = True
						bpmCounter += 1

				f.write(beat + "\n")

		f.close()
	
	


if __name__ == '__main__':
	main()