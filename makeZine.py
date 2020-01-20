import json
from urllib.request import urlopen


from fpdf import FPDF
from PIL import Image
from PyPDF2 import PdfFileMerger
from PyPDF2 import PdfFileReader

## Image processing

def scaleToDefaultHeight(size, defaulSize):
	
	width = size[0]
	height = size[1]
	defaultHeight = defaulSize
	
	scale = height/defaultHeight
	
	newSize = (int(width/scale), int(height/scale))
	return newSize

def scaleToDefaultWidth(size, defaulSize):
	
	width = size[0]
	height = size[1]
	defaultWidth = defaulSize
	
	scale = width/defaultWidth
	
	newSize = (int(width/scale), int(height/scale))
	return newSize

def imageIsDownloaded(pathToFile):

	try:
		Image.open(pathToFile)
	except:
		return False
	return True

def downloadImage(url, name, path = 'src/images/collectionImages/', checkIfIsDownloaded = True):

	isDownloaded = False
	if checkIfIsDownloaded and imageIsDownloaded(path + name):
		isDownloaded = True

	# download img from url and save it
	if not isDownloaded:
		img = Image.open(urlopen(url))
		img.save(path + name)
		
		del img

## Extracting caracteristics

def getCleanImage(jsonImg):

	# returns url of clean image used
	return jsonImg['image']

# Google Cloud

def getGoogleSafeSearchAnnotations(jsonImg):

	# returns a dictionary with 5 safe annotations: adult, racy, violence, medical, spoof
	return jsonImg['googlecloud']['safeSearchAnnotation']

def getGoogleLabelAnnotations(jsonImg):
	
	labelsList = jsonImg['googlecloud']['labelAnnotations']
	for i, result in enumerate(labelsList):
		labelsList[i] = {'description': result['description'].lower(), 'score': result['score']}

	# returns a list of dictionaries of results {'description': nome da label, 'score': 0.1}
	return labelsList

def getGoogleBestGuessLabel(jsonImg):
	
	# return a string
	return jsonImg['googlecloud']['webDetection']['bestGuessLabels'][0]['label']

def getGoogleTextAnnotation(jsonImg):
	
	try:
		text = jsonImg['googlecloud']['textAnnotations'][0]['description'].strip()
		text = ' '.join(text.split('\n'))
	except:
		text = 'No texts found'

	return text

def getVisuallySimilarImages(jsonImg, pk):
	temp = jsonImg['googlecloud']['webDetection']['visuallySimilarImages']
	
	urls = []
	i = 0
	while len(urls) < 2 and i < len(temp):
		url = temp[i]['url']
		try:
			downloadImage(url, str(pk) + '_' + str(i+1) + '.jpg')
		except:
			i += 1
			continue
		i += 1
		urls.append(url)

	del temp

	# returns a list of 2 or less url of visually simillar images
	return urls

# Microssoft Azure

def getGuessName(jsonImg):

	try:
		caption = jsonImg['microsoftazure']['main']['description']['captions'][0]
	except:
		caption = {'text': 'no description', 'confidence': 1}

	# returns a dictionary of a produced by the AI, if it fails to find, returns {text: 'No title', confidence: 100}
	return caption

def getMicossoftAzureConfidenceTags(jsonImg):

	# returns a list of dictionaries with name and confidence for each tag
	return jsonImg['microsoftazure']['main']['tags']

def getMicossoftAzureDescriptionTags(jsonImg):

	# returns a list of tags
	return jsonImg['microsoftazure']['main']['description']['tags']

def getMicrosoftAzureAdult(jsonImg):
	return jsonImg['microsoftazure']['main']['adult']

def getMicrosoftAzureCategories(jsonImg):
	#return a list of dictionaries with category names and percentage
	#dict['name']
	#dict['score']
	return jsonImg['microsoftazure']['main']['categories']

# Densecap

def getDensecapImage(jsonImg):

	# returns a url of densecap full analysed image
	return jsonImg['dense_cap_image']


# Amazon Rekognition

def getAmazonLabelAnnotations(jsonImg):

	# returns a list of dictionaries with name and confidence for each label classified by the Amazon Rekog
	return jsonImg['amazonRekog']['labels']['Labels']



# ClarifAI

def getClarifAINsfw(jsonImg):
	# return a percentage value (0 to 100)
	index = 0
	if (jsonImg['clarifai']['nsfw']['concepts'][index]['name']) == 'sfw':
		index = 1
	return jsonImg['clarifai']['nsfw']['concepts'][index]['value']*100
def getClarifAIModeration(jsonImg):
	#return a dictionary with percentages indexed by tag name 
	result = {}
	for item in jsonImg['clarifai']['moderation']['concepts']:
		result[item['name']] = int(item['value']*100)
	return result

def getClarifAIGeneralResults(jsonImg):
	#return a list of tuples with label and percentage
	results = [ (jsonImg['clarifai']['general']['concepts'][index]['name'], jsonImg['clarifai']['general']['concepts'][index]['value']) for index in range(len(jsonImg['clarifai']['general']['concepts']))]
	return results


## Zine processing

def addImage(pdf, jsonImg, pk, path = 'src/images/collectionImages/', xShift = 10, yShift = 24):

	url = getDensecapImage(jsonImg)
	downloadImage(url, str(pk) + '.jpg', path)

	# getting img size to see if width is bigger then height
	imSize = Image.open(path + str(pk) + '.jpg').size

	maxSize = 83

	pdf.set_fill_color(245)
	pdf.rect(xShift-0.1, yShift-0.1, maxSize+0.2, maxSize+0.2, 'DF')

	# horizontal image
	if imSize[0] > imSize[1]:
		imSize = scaleToDefaultWidth(imSize, maxSize)
		pdf.image(path + str(pk) + '.jpg', x = xShift, y = yShift + (maxSize - imSize[1])/2, w = maxSize)
	
	# vertical image
	else:
		imSize = scaleToDefaultHeight(imSize, maxSize)
		pdf.image(path + str(pk) + '.jpg', x = xShift + (maxSize - imSize[0])/2, y = yShift, h = maxSize)
	
	del imSize

def addName(pdf, jsonImg, number):

	nameDict = getGuessName(jsonImg)
	name = nameDict['text']
	confidence = int(nameDict['confidence']*100)

	if number < 10:
		number = '0'+str(number)
	else:
		number = str(number)

	pdf.set_fill_color(240)
	pdf.set_text_color(0)
	pdf.set_font('NeutralStd', 'B', size = 9)
	pdf.cell(0, 8, txt='                 '+name, ln=1, align='L', border = 1, fill = True)
	
	pdf.set_fill_color(52, 152, 219)
	pdf.set_font('NeutralStd', '', size = 10)

	pdf.set_text_color(24, 188, 156)
	pdf.text(11, 15.1, txt=' #'+number)
	

	# ajustando espaçamento
	x, y = 131.5, 14.7
	if name == 'no description':
		addConfidenceBox(pdf, x, y, confidence = 0, printSlash = True, head = True)
	else:
		addConfidenceBox(pdf, x, y, confidence, head = True)

def addConfidenceBox(pdf, x, y, confidence, printSlash = False, head = False, color='blue'):
	
	if head:
		width = 8
		textSize = 7
		yAdjust = 0
		xAdjust = 0
	else:
		width = 7
		textSize = 6
		yAdjust = -0.3
		xAdjust = -0.2

	pdf.set_font('NeutralStd', 'B', size = textSize)
	pdf.set_text_color(255)
	if color == 'blue':
		pdf.image('src/images/pdfImages/confidenceBox.png', x - 2.8, y - 3, w = width)
	else:
		pdf.image('src/images/pdfImages/confidenceBoxSfw.png', x - 2.8, y - 3, w = width)
	if printSlash:
		pdf.text(x + xAdjust, y + yAdjust, txt='—')
	elif confidence < 10:
		pdf.text(x - 0.3 + xAdjust, y + yAdjust, txt=str(confidence) + '%')
	elif confidence < 100:
		pdf.text(x - 1.2 + xAdjust, y + yAdjust, txt=str(confidence) + '%')
	else:
		pdf.text(x - 2.2 + xAdjust, y + yAdjust, txt=str(confidence) + '%')
	pdf.set_text_color(0)


def addVisualSimilarImages(pdf, jsonImg, pk, xShift = 100.5, yShift = 24, path = 'src/images/collectionImages/'):


	pdf.set_fill_color(245)

	# get visually simillar url lists
	urls = getVisuallySimilarImages(jsonImg, pk)
	for i in range(len(urls)):
		downloadImage(urls[i], str(pk)+'_'+str(i+1)+'.jpg')
	
	pdf.image('src/images/pdfImages/visuallySimilar.png', xShift - 4.5, yShift + 29, w = 3.5)
	
	for i in range(len(urls)):
		maxSize = 38
		pdf.rect(xShift-0.1, yShift + i*45 - 0.1, maxSize + 0.2, maxSize + 0.2, style = 'DF')

		imSize = Image.open(path + str(pk) + '_' + str(i+1) + '.jpg').size
		# horizontal image
		if imSize[0] > imSize[1]:
			imSize = scaleToDefaultWidth(imSize, maxSize)
			pdf.image(path + str(pk) + '_' + str(i+1) + '.jpg', x = xShift, y = i*45 + yShift + (maxSize - imSize[1])/2, w = maxSize-0.1)
		
		# vertical image
		else:
			imSize = scaleToDefaultHeight(imSize, maxSize)
			pdf.image(path + str(pk) + '_' + str(i+1) + '.jpg', x = xShift + (maxSize - imSize[0])/2, y =  i*45 + yShift, h = maxSize)

def addMicrosoftAzure(pdf, jsonImg, xShift, yShift, second):
	pdf.set_text_color(24, 188, 156)
	pdf.set_font('NeutralStd', 'B', size = 9)
	pdf.set_fill_color(240)
	pdf.rect(xShift, yShift, 31, 8, 'DF')
	pdf.text(xShift + 2, yShift + 5, txt = 'Microsoft Azure')
	
	#moderation
	pdf.set_text_color(120)
	distanceY = 13
	distanceX = 2

	displaceX = 75
	displaceY = 4
	adult = getMicrosoftAzureAdult(jsonImg)
	racyScore = int(adult['racyScore']*100)
	isRacy = str(adult['isRacyContent'])
	adultScore = int(adult['adultScore']*100)
	isAdult = str(adult['isAdultContent'])

	pdf.set_font('NeutralStd', '', size = 9)
	pdf.text(xShift+displaceX, yShift+displaceY - 0.4, txt = 'is adult content?')
	pdf.text(xShift+displaceX, yShift+displaceY - 0.4 + 5, txt = 'is racy content?')
	pdf.set_text_color(0) #text color
	pdf.set_font('NeutralStd', '', size = 8)
	pdf.text(xShift+displaceX + 45, yShift+displaceY - 0.4, txt = 'adult')
	pdf.text(xShift+displaceX + 45, yShift+displaceY - 0.6 + 5, txt = 'racy')
	pdf.text(xShift+displaceX + 27.5, yShift+displaceY - 0.4, txt = isAdult)
	pdf.text(xShift+displaceX + 27.5, yShift+displaceY - 0.4 + 5, txt = isRacy)
	addConfidenceBox(pdf, xShift + displaceX + 40, yShift + displaceY-0.4, adultScore, color='green')
	addConfidenceBox(pdf, xShift + displaceX + 40, yShift + displaceY+4.6, racyScore, color='green')
	
	#Categories
	cat = getMicrosoftAzureCategories(jsonImg)
	displaceX = 6
	displaceY = 3.5
	pdf.set_text_color(120)
	pdf.set_font('NeutralStd', '', size = 9)
	pdf.text(xShift+displaceX + 26, yShift+displaceY, txt = "categorie:")
	pdf.set_text_color(0)
	pdf.set_font('NeutralStd', '', size = 8)
	imax = 0
	for i in range(len(cat)):
		if cat[i]['score'] > imax:
			imax = i
	pdf.text(xShift+displaceX + 29, yShift+displaceY+3, txt = cat[i]['name'])
	
	confidenceLabelsDictList = getMicossoftAzureConfidenceTags(jsonImg)
	descriptionLabels = getMicossoftAzureDescriptionTags(jsonImg)
	labelsList = []
	for i in range(max(len(confidenceLabelsDictList), len(descriptionLabels))):
		try:
			label1 = confidenceLabelsDictList[i]['name']
		except:
			label1 = None
		try:
			label2 = descriptionLabels[i]
		except:
			label2 = None
		
		if label1 is not None and label1 not in labelsList:
			labelsList.append(label1)
		if label2 is not None and label2 not in labelsList:
			labelsList.append(label2)

	pdf.set_text_color(120)
	pdf.set_font('NeutralStd', '', size = 9)
	pdf.text(xShift + 5, yShift + 12.8, txt = 'labels:')
	xSpacing = 30
	i, numPrintedLabels, numOnColumn, maxLabels, skipStart = 0, 0, 6, 24, 1
	while i < len(labelsList) and numPrintedLabels < maxLabels:
		label = labelsList[i]
		if skipStart > numPrintedLabels:
			numPrintedLabels += 1
			continue
		if len(label) <= 18:
			pdf.set_text_color(0)
			pdf.set_font('NeutralStd', '', size = 8)
			pdf.text(xShift + 5 + (numPrintedLabels//numOnColumn)*xSpacing, yShift + 8.8 + 4.5 + numPrintedLabels%numOnColumn * 4.5, txt = label.lower())
			numPrintedLabels += 1
		i += 1


def addClarifAI(pdf, jsonImg, xShift, yShift, second):
	pdf.set_text_color(24, 188, 156)
	pdf.set_font('NeutralStd', 'B', size = 9)
	pdf.set_fill_color(240)
	pdf.rect(xShift, yShift, 17, 8, 'DF')
	pdf.text(xShift + 2, yShift + 5, txt = 'ClarifAI')

	#General Results
	pdf.set_font('NeutralStd', '', size = 9)
	pdf.set_text_color(120)
	pdf.text(xShift + 5, yShift + 12.5, txt = 'labels:')
	distanceY = 13
	distanceX = 2
	
	#Labels
	xSpacing = 31.75
	i, numPrintedLabels, numOnColumn, maxLabels, skipStart = 0, 0, 5, 20, 1
	labelsList = getClarifAIGeneralResults(jsonImg)
	displaceY = 13
	displaceX = 8
	while i < len (labelsList) and numPrintedLabels < maxLabels:
		if skipStart > numPrintedLabels:
			numPrintedLabels += 1
			continue
		if len(labelsList[i][0]) <= 15:
			addConfidenceBox(pdf, xShift + displaceX + (numPrintedLabels//numOnColumn)*xSpacing, yShift + displaceY + numPrintedLabels%numOnColumn*4.5, int((labelsList[i][1]*100)//1))
			pdf.set_font('NeutralStd', '', size=8)
			pdf.text(xShift + displaceX + 5 + (numPrintedLabels//numOnColumn)*xSpacing, yShift + displaceY - 0.4 + numPrintedLabels%numOnColumn * 4.5, txt = labelsList[i][0])
			numPrintedLabels += 1
		i += 1

	#nsfw
	pdf.set_font('NeutralStd', '', size = 9)
	pdf.set_text_color(120)
	pdf.text(xShift + 21, yShift + 5.5, txt = 'safe for work?')


	displaceX = 49
	displaceY = 5.7
	pdf.set_font('NeutralStd', '', size = 8)
	value = getClarifAINsfw(jsonImg)
	pdf.set_text_color(0)
	pdf.text(xShift+displaceX + 5, yShift+displaceY - 0.4, txt = 'nsfw')
	addConfidenceBox(pdf, xShift + displaceX, yShift + displaceY, int(value), color='green')

	#moderation
	pdf.set_font('NeutralStd', '', size = 9)
	pdf.set_text_color(120)
	pdf.text(xShift + 5, yShift + 37, 'moderation:')

	pdf.set_text_color(0)
	pdf.set_font('NeutralStd', '', size = 8)
	displaceX = 30
	displaceY = 37
	value = getClarifAIModeration(jsonImg)
	sp = ' '*15
	text = 'safe:'+sp+'suggestive:'+sp+'explicit:'+sp+'gore:'+sp+'drug:'
	pdf.set_font('NeutralStd', '', size=8)
	pdf.text(xShift+displaceX+5, yShift+displaceY, txt = 'safe')
	pdf.text(xShift+displaceX+21, yShift+displaceY, txt = 'suggestive')
	pdf.text(xShift+displaceX+46, yShift+displaceY, txt = 'explicit')
	pdf.text(xShift+displaceX+66, yShift+displaceY, txt = 'gore')
	pdf.text(xShift+displaceX+83, yShift+displaceY, txt = 'drug')
	displaceY += 0.2
	color = 'green'
	addConfidenceBox(pdf, xShift + displaceX, yShift + displaceY, value['safe'], color=color)
	addConfidenceBox(pdf, xShift + displaceX + 16, yShift + displaceY, value['suggestive'], color=color)
	addConfidenceBox(pdf, xShift + displaceX + 41, yShift + displaceY, value['explicit'], color=color)
	addConfidenceBox(pdf, xShift + displaceX + 61, yShift + displaceY, value['gore'], color=color)
	addConfidenceBox(pdf, xShift + displaceX + 78, yShift + displaceY, value['drug'], color=color)


def addGoogleCloudVision(pdf, jsonImg, xShift, yShift, second):

	pdf.set_text_color(24, 188, 156)
	pdf.set_font('NeutralStd', 'B', size = 9)
	pdf.set_fill_color(240)
	pdf.rect(xShift, yShift, 37, 8, 'DF')
	pdf.text(xShift + 2, yShift + 5, txt = 'Google Cloud Vision')
	
	# best guess
	pdf.set_font('NeutralStd', '', size = 9)
	pdf.set_text_color(120)
	pdf.text(xShift + 42, yShift + 5.5, txt = 'best guess:')
	pdf.set_font('NeutralStd', '', size = 8)
	pdf.set_text_color(0)
	pdf.text(xShift + 61, yShift + 5.5, txt = getGoogleBestGuessLabel(jsonImg))

	# safe search annotations
	#pdf.set_font('NeutralStd', '', size = 9)
	#pdf.set_text_color(120)
	#pdf.text(xShift + 5, yShift + 18, txt = 'safe search annotations:')
	#pdf.set_text_color(0)
	
	safeAnnotationsDict = getGoogleSafeSearchAnnotations(jsonImg)
	pdf.set_text_color(120)
	yAdjust = 12.5
	pdf.set_font('NeutralStd', '', size = 9)
	pdf.text(xShift + 5, yShift + yAdjust, 'violence:')
	pdf.text(xShift + 30, yShift + yAdjust, 'medical:')
	pdf.text(xShift + 55, yShift + yAdjust, 'adult:')
	pdf.text(xShift + 80, yShift + yAdjust, 'spoof:')
	pdf.text(xShift + 105, yShift + yAdjust, 'racy:')

	pdf.set_text_color(0)
	pdf.set_font('NeutralStd', '', size = 8)
	pdf.text(xShift + 5, yShift + yAdjust + 4, ' '.join(safeAnnotationsDict['violence'].lower().split('_')))
	pdf.text(xShift + 30, yShift + yAdjust + 4, ' '.join(safeAnnotationsDict['medical'].lower().split('_')))
	pdf.text(xShift + 55, yShift + yAdjust + 4, ' '.join(safeAnnotationsDict['adult'].lower().split('_')))
	pdf.text(xShift + 80, yShift + yAdjust + 4, ' '.join(safeAnnotationsDict['spoof'].lower().split('_')))
	pdf.text(xShift + 105, yShift + yAdjust + 4, ' '.join(safeAnnotationsDict['racy'].lower().split('_')))


	# labels
	labelsDictList = getGoogleLabelAnnotations(jsonImg)

	labelsList = [item['description'] for item in labelsDictList]
	confidenceList = [int(item['score']*100) for item in labelsDictList]
	pdf.set_text_color(120)
	pdf.set_font('NeutralStd', '', size = 9)
	pdf.text(xShift + 5, yShift + 27, txt = 'labels:')
	xSpacing = 36
	i, numPrintedLabels, numOnColumn, maxLabels = 0, 0, 3, 9
	while i < len(labelsList) and numPrintedLabels < maxLabels:
		label, confidence = labelsList[i], confidenceList[i]
		if len(label) <= 18:
			addConfidenceBox(pdf, xShift + 20 + (numPrintedLabels//numOnColumn)*xSpacing, yShift + 23 + numPrintedLabels%numOnColumn * 4.5, confidence)
			pdf.set_font('NeutralStd', '', size = 8)
			pdf.text(xShift + 25 + (numPrintedLabels//numOnColumn)*xSpacing, yShift + 22.6 + numPrintedLabels%numOnColumn * 4.5, txt = label)
			numPrintedLabels += 1
		i += 1

	# text
	pdf.set_font('NeutralStd', '', size = 9)
	pdf.set_text_color(120)
	pdf.text(xShift + 5, yShift + 38.5, txt = 'text:')
	pdf.set_text_color(0)
	pdf.set_font('NeutralStd', '', size = 8)
	text = getGoogleTextAnnotation(jsonImg).lower()
	maxTextLen = 70
	if len(text) > maxTextLen:
		text = text[:maxTextLen] + '...'
	pdf.text(xShift + 14, yShift + 38.4, txt = text)

def addAmazonRekognition(pdf, jsonImg,  xShift, yShift, second):
	
	pdf.set_text_color(24, 188, 156)
	pdf.set_font('NeutralStd', 'B', size = 9)
	pdf.set_fill_color(240)
	pdf.rect(xShift, yShift, 39, 8, 'DF')
	pdf.text(xShift + 2, yShift + 5, txt = 'Amazon Rekognition')

	labelsDictList = getAmazonLabelAnnotations(jsonImg)

	labelsList = [item['Name'] for item in labelsDictList]
	confidenceList = [int(item['Confidence']) for item in labelsDictList]
	pdf.set_text_color(120)
	pdf.set_font('NeutralStd', '', size = 9)
	pdf.text(xShift + 5, yShift + 12.8, txt = 'labels:')
	xSpacing = 40
	i, numPrintedLabels, numOnColumn, maxLabels, skipStart = 0, 0, 7, 21, 2
	while i < len(labelsList) and numPrintedLabels < maxLabels:
		label, confidence = labelsList[i], confidenceList[i]
		if skipStart > numPrintedLabels:
			numPrintedLabels += 1
			continue
		if len(label) <= 18:
			addConfidenceBox(pdf, xShift + 8 + (numPrintedLabels//numOnColumn)*xSpacing, yShift + 9 + numPrintedLabels%numOnColumn * 4.5, confidence)
			pdf.set_font('NeutralStd', '', size = 8)
			pdf.text(xShift + 13 + (numPrintedLabels//numOnColumn)*xSpacing, yShift + 8.8 + numPrintedLabels%numOnColumn * 4.5, txt = label.lower())
			numPrintedLabels += 1
		i += 1


def addAiResults(pdf, jsonImg, kind = 'C', xShift = 10, yShift = 113, second = False):

	heigth, width = 40, 128.5
	if second:
		yShift += (heigth + 6)
	pdf.set_fill_color(250)
	pdf.rect(xShift, yShift, width, heigth, 'DF')

	# Google Cloud Vision
	if kind == 'G':
		addGoogleCloudVision(pdf, jsonImg,  xShift, yShift, second)
	
	# Amazon Rekognition
	if kind == 'A':
		addAmazonRekognition(pdf, jsonImg,  xShift, yShift, second)
		pass

	# IBM Watson
	if kind == 'I':
		pass

	#Microsoft Azure
	if kind == 'M':
		addMicrosoftAzure(pdf, jsonImg, xShift, yShift, second)

	# ClarifAI
	if kind == 'C':
		addClarifAI(pdf, jsonImg, xShift, yShift, second)

	# Dark YOLO
	if kind == 'D':
		pass


def addFonts(pdf):

	# add Neutral fonts to pdf object
	pdf.add_font('NeutralStd', '', 'src/fonts/NeutralStd-Regular.ttf', uni = True)
	pdf.add_font('NeutralStd', 'B', 'src/fonts/NeutralStd-Bold.ttf', uni = True)
	pdf.add_font('NeutralStd', 'I', 'src/fonts/NeutralStd-RegularItalic.ttf', uni = True)


def addResults(pdf, data, pkAIList):

	pkList, AIList = [], []
	for result in pkAIList:
		pkList.append(result[0])
		AIList.append(result[1])

	## results

	# all pk inside data
	allPk = [data['images'][i]['pk'] for i in range(len(data['images']))]

	i = 0
	while i < len(pkList):
		pdf.add_page()
		pk = pkList[i]
		AI = AIList[i]

		# check if pk is in list
		try:
			index = allPk.index(pk)
		except:
			print('Erro:', pk, 'not in data!')
			i += 1
			continue

		jsonImg = data['images'][index]

		addImage(pdf, jsonImg, pk)
		addName(pdf, jsonImg, number = i+1)
		addVisualSimilarImages(pdf, jsonImg, pk)
		addAiResults(pdf, jsonImg, AI[0])
		addAiResults(pdf, jsonImg, AI[1], second = True)
		i+=1

def addCollaborators(pdf, collaborators):

	pdf.add_page()

	# collaborators title
	pdf.ln(10)
	title1 = 'COLLABORATORS'
	pdf.set_font('NeutralStd', 'B', size = 23)
	pdf.cell(0, 20, txt=title1, ln=1, align="C")

	pdf.set_font('NeutralStd', '', size = 10)
	pdf.ln(10)
	for i in range(len(collaborators)):
		# next line
		pdf.ln(1)

		# select collaborator
		collaborator = collaborators[i]
		if i%2 == 0:
			pdf.cell(0, 3, txt='   '+collaborator, ln=1, align="L")
		else:
			pdf.cell(0, 3, txt=collaborator+'   ', ln=1, align="R")

def makeZine(jsonPath, collaborators, pkAIList):

	# read json file
	with open(jsonPath) as jsonFile:
		data = json.load(jsonFile)
	print('## json is ready!')

	# initialize pdf
	pdf = FPDF(orientation='P', unit='mm', format='A5')
	
	# add NeutralStd fonts
	addFonts(pdf)

	# add results
	addResults(pdf, data, pkAIList)
	print('## results are ready!')

	# add collaborators
	addCollaborators(pdf, collaborators)
	print('## collaborators is ready!')

	# add glossary page

	# output partial zine
	pdf.output("src/pdfPages/partialZine.pdf")

	# add cover page
	zine = PdfFileMerger()
	zine.merge(0, 'src/pdfPages/capa.pdf')
	zine.merge(1, 'src/pdfPages/blankPage.pdf')
	zine.merge(2, 'src/pdfPages/apresentacao.pdf')
	zine.merge(3, 'src/pdfPages/blankPage.pdf')
	zine.merge(4, 'src/pdfPages/partialZine.pdf')
	partialZine = PdfFileReader('src/pdfPages/partialZine.pdf')
	numPages = partialZine.getNumPages()
	if numPages%2 != 0:
		zine.merge(100, 'src/pdfPages/blankPage.pdf')
	zine.merge(200, 'src/pdfPages/contracapa.pdf')
	zine.write('zine.pdf')
	print('## zine is ready!')

def getCollaborators(path):

	# returns a sorted list of names

	listCollaborators = []
	with open(path, 'r') as file:
		collaborator = file.readline().strip()
		while not collaborator == '':
			listCollaborators.append(collaborator)
			collaborator = file.readline().strip()
	listCollaborators.sort()

	return listCollaborators

def getPkAIList(path):

	pkAIList = []
	with open(path, 'r') as file:
		temp = file.readline().split(',')
		temp = [item.strip() for item in temp]
		while len(temp) == 3:
			pkAIList.append([int(temp[0]), temp[1:]])
			
			temp = file.readline().split(',')
			temp = [item.strip() for item in temp]

	# return a list of [[pk, [AI1, AI2]], ...]
	return pkAIList

if __name__ == '__main__':

	jsonPath = input('Enter json file name, or \'0\' for defaut: ')
	if jsonPath == '0':
		jsonPath = 'src/jsonFiles/pinacoteca.json'
	else:
		jsonPath = 'src/jsonFiles/' + jsonPath

	collaboratorsPath = 'collaborators.txt'
	collaborators = getCollaborators(collaboratorsPath)

	pkAIPath = 'pkAIList.txt'
	pkAIList = getPkAIList(pkAIPath)

	print('Zine its being made, migth take some minutes...')
	makeZine(jsonPath, collaborators, pkAIList)
