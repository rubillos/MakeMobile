#!python3

srcPath = "/Users/randy/Sites/PortlandAve"
dstPath = "/Users/randy/Sites/PortlandAve-Mobile"

'''
(cd /Users/randy/Sites/PortlandAve-Mobile && zip -r -0 -v ../RickAndRandy.zip .)
'''

import os
import re
import shutil
from rich.console import Console
from rich.progress import Progress, BarColumn, TimeElapsedColumn, Task
from rich.text import Text
from rich.theme import Theme
from rich.panel import Panel
from rich.live import Live
from rich.table import Table

import copyfile

theme = Theme({
			"progress.percentage": "white",
			"progress.remaining": "green",
			"progress.elapsed": "cyan",
			"bar.complete": "green",
			"bar.finished": "green",
			"bar.pulse": "green",
			"repr.ellipsis": "white",
			"repr.number": "white",
			"repr.path": "white",
			"repr.filename": "white"
			})

progressDesc = "[progress.description]{task.description}"
progressPercent = "[progress.percentage]{task.percentage:>3.0f}% "
progressPercentCount = "[progress.percentage]{task.percentage:>3.0f}% ({task.fields[count]})"
progressPercentMedia = "[progress.percentage]{task.percentage:>3.0f}% (copied:{task.fields[count]}, reused:{task.fields[reuse]})"

console = Console(theme=theme)

filesToCopy = [
		"app.js",
		"apple-touch-icon.png",
		"bandb.pdf",
		"error.html",
		"favicon.ico",
		"imagepage-legacy.js",
		"imagepage.js",
		"index.html",
		"indexpage-legacy.js",
		"indexpage.js",
		"jquery-min.js",
		"links.txt",
		"moviepage.js",
		"panopage.js",
		"server.html",
]

foldersToCopy = [
		"ByeByeMeta",
		"FrontPageGraphics",
		"Holidays",
		"WheelieSchool",
		"Yvonka",
		"castrohouse",
		"gadgets",
		"losaltoshouse",
		"map",
		"meta",
		"movielist",
		"other",
		"randy",
		"recreation",
		"rick",
		"rubber",
		"sidepath",
]

pathsToSkip = [
		"meta/randy/",
		"meta/rick/",
]

eventFolders = [
		"Local",
		"travel",
]

copyByteCount = 0
copiedFileCount = 0

def formatBytes(size, precision=1):
	power = 1024
	n = 0
	labels = {0: ' bytes', 1: 'KB', 2: 'MB', 3: 'GB', 4: 'TB'}

	while size > power:
		size /= power
		n += 1

	return f"{size:.{precision}f}{labels[n]}"

def fileExists(path):
	return os.path.isfile(path)

def createFolder(path):
	if "." in path:
		path = os.path.dirname(path)
	try:
		os.makedirs(path, exist_ok=True)
		return True
	except OSError as e:
		console.print(f"Error creating folder '{path}': {e}")
		return False

def copyFile(srcPath, dstPath):
	global copyByteCount, copiedFileCount

	try:
		os.makedirs(os.path.dirname(dstPath), exist_ok=True)
		if os.path.isfile(dstPath):
			os.remove(dstPath)
		copyfile.copyfile(srcPath, dstPath)
		copyByteCount += os.path.getsize(srcPath)
		copiedFileCount += 1
		return True
	except OSError as e:
		console.print(f"Error copying '{srcPath}' to '{dstPath}' - {e}")
		return False
	
def copyFolder(srcFolder, dstFolder):
	skipPattern = re.compile("|".join(re.escape(path) for path in pathsToSkip))
	try:
		for item in removeHidden(os.listdir(srcFolder)):
			srcItem = os.path.join(srcFolder, item)
			dstItem = os.path.join(dstFolder, item)
			if not skipPattern.search(srcItem):
				if os.path.isdir(srcItem):
					copyFolder(srcItem, dstItem)
				else:
					copyFile(srcItem, dstItem)
	except OSError as e:
		console.print(f"Error copying folder '{srcFolder}' to '{dstFolder}' - {e}")

def copyFiles(fileList):
	for file in fileList:
		srcFile = os.path.join(srcPath, file)
		dstFile = os.path.join(dstPath, file)
		if fileExists(srcFile):
			if not copyFile(srcFile, dstFile):
				console.print(f"Failed to copy file '{srcFile}' to '{dstFile}'")
		else:
			console.print(f"File '{srcFile}' does not exist")

def copyFolders(folderList):
	with Progress(progressDesc, BarColumn(), progressPercent, console=console) as progress:
		task = progress.add_task("Copy folder list...", total=len(folderList))
		for folder in folderList:
			srcFolder = os.path.join(srcPath, folder)
			dstFolder = os.path.join(dstPath, folder)
			if os.path.isdir(srcFolder):
				copyFolder(srcFolder, dstFolder)
			else:
				console.print(f"Folder '{srcFolder}' does not exist")
			progress.update(task, advance=1)

def removeIfPresent(list, item):
	if item in list:
		list.remove(item)

def removeHidden(fileList):
	for file in list(fileList):
		if file.startswith('.'):
			fileList.remove(file)
	return fileList

def copyEventFolder(srcFolder, dstFolder):
	try:
		movieList = []
		redirect = {}
		items = removeHidden(os.listdir(srcFolder))

		items3 = []
		for item in items:
			if "@3x" in item and "pictures" not in item and "thumbnails" not in item:
				items3.append(item)
		for item in items3:
			redirect[item.replace("@3x", "")] = item
			removeIfPresent(items, item)
			removeIfPresent(items, item.replace("@3x", "@2x"))

		items2 = []
		for item in items:
			if "@2x" in item and "pictures" not in item and "thumbnails" not in item:
				items2.append(item)
		for item in items2:
			redirect[item.replace("@2x", "")] = item
			removeIfPresent(items, item)

		sizeMatch = re.compile(r"@\d+x")

		for item in items:
			srcItem = os.path.join(srcFolder, redirect.get(item, item))
			dstItem = os.path.join(dstFolder, item)

			if ".mp4" in item or ".m4v" in item:
				if ("-1080p" in item or " - 1080p" in item) and not "-Original" in item and not "-Max" in item:
					movieList.append(item)
				elif "-Thumbnail" in item or " - Thumbnail" in item or not "-" in item:
					copyFile(srcItem, dstItem)
			elif not sizeMatch.search(item):
				if os.path.isdir(srcItem):
					if "thumbnails" in item or "pictures" in item:
						for file in removeHidden(os.listdir(srcItem)):
							srcItem2 = os.path.join(srcItem, file)
							for suffix in ["@3x", "@2x"]:
								bigPath = os.path.join(srcItem+suffix, file)
								if os.path.isfile(bigPath):
									srcItem2 = bigPath
									break
							copyFile(srcItem2, os.path.join(dstItem, file))
					elif "headers" in item:
						for file in removeHidden(os.listdir(srcItem)):
							if not sizeMatch.search(file):
								srcItem2 = os.path.join(srcItem, file)
								for suffix in ["@3x", "@2x"]:
									bigPath = srcItem2.replace(".", suffix+".")
									if os.path.isfile(bigPath):
										srcItem2 = bigPath
										break
								copyFile(srcItem2, os.path.join(dstItem, file))
					else:
						copyFolder(srcItem, dstItem)
				else:
					copyFile(srcItem, dstItem)
		for movie in list(movieList):
			if "-HEVC" in movie:
				baseMovie = movie.replace("-HEVC", "")
				if baseMovie in movieList:
					movieList.remove(baseMovie)
		for movie in movieList:
			srcItem = os.path.join(srcFolder, movie)
			dstItem = os.path.join(dstFolder, movie)
			copyFile(srcItem, dstItem)

	except OSError as e:
		console.print(f"Error copying event folder '{srcFolder}' to '{dstFolder}' - {e}")

def copyEvents(srcFolder, dstFolder):
	try:
		with Progress(progressDesc, BarColumn(), progressPercent, console=console) as progress:
			items = removeHidden(os.listdir(srcFolder))
			task = progress.add_task(f"Copy Events in {os.path.basename(srcFolder)}", total=len(items))
			for item in items:
				srcItem = os.path.join(srcFolder, item)
				dstItem = os.path.join(dstFolder, item)
				if os.path.isdir(srcItem):
					copyEventFolder(srcItem, dstItem)
				progress.update(task, advance=1)

	except OSError as e:
		console.print(f"Error copying event '{srcFolder}' to '{dstFolder}' - {e}")

def copyEventFolders(folderList):
	for event in folderList:
		srcFolder = os.path.join(srcPath, event)
		dstFolder = os.path.join(dstPath, event)
		if os.path.isdir(srcFolder):
			copyEvents(srcFolder, dstFolder)

def removeDestinationFolder(path):
	try:
		if os.path.exists(path):
			shutil.rmtree(path)
			console.print(f"Removed existing destination folder: {path}")
		os.makedirs(path, exist_ok=True)
	except OSError as e:
		console.print(f"Error removing or creating destination folder '{path}': {e}")

removeDestinationFolder(dstPath)
createFolder(dstPath)

copyFiles(filesToCopy)
copyFolders(foldersToCopy)
copyEventFolders(eventFolders)

console.print( f"Copied {copiedFileCount} files - {formatBytes(copyByteCount)}" )
console.print ("shell command for zip file:")
console.print( f"(cd {dstPath} && zip -r -0 -v ../RickAndRandy.zip .)")
