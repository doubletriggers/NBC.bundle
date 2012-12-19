NAME = 'NBC'
ART = 'art-default.jpg'
ICON = 'icon-default.png'

BASE_URL = 'http://www.nbc.com'
FULL_EPS_URL = '%s/video/library/full-episodes/' % BASE_URL

# Thumbs
# %d = 360, or 480 for classic tv
# %s = 'nbc2', or 'nbcrewind2' for classic tv
# %s = pid
THUMB_URL = 'http://video.nbc.com/player/mezzanine/image.php?w=640&h=%d&path=%s/%s_mezzn.jpg&trusted=yes'

RE_BASE_URL = Regex('(http://[^/]+)')
RE_PATH_PID = Regex('\.com/(.+?)/thumb/(.+?)_large')
RE_THUMB_SIZE = Regex('w=[0-9]+&h=[0-9]+')

####################################################################################################
def Start():

	Plugin.AddViewGroup('List', viewMode='List', mediaType='items')
	Plugin.AddViewGroup('InfoList', viewMode='InfoList', mediaType='items')

	ObjectContainer.title1 = NAME
	ObjectContainer.art = R(ART)
	DirectoryObject.thumb = R(ICON)
	VideoClipObject.thumb = R(ICON)

	HTTP.CacheTime = CACHE_1HOUR
	HTTP.Headers['User-Agent'] = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.8; rv:16.0) Gecko/20100101 Firefox/16.0'

####################################################################################################
@handler('/video/nbc', NAME, thumb=ICON, art=ART)
def MainMenu():

	oc = ObjectContainer(view_group='List')
	content = HTML.ElementFromURL(FULL_EPS_URL)

	for show in content.xpath('//div[contains(@class, "group-full-eps")]//li'):
		title = show.xpath('./p/text()[last()]')[0].strip()
		url = show.xpath('./a')[0].get('href')
		thumb = show.xpath('./a/img')[0].get('src')

		oc.add(DirectoryObject(key=Callback(Show, show=title, url=url, thumb=thumb), title=title, thumb=Callback(GetThumb, url=thumb)))

	return oc

####################################################################################################
@route('/video/nbc/show')
def Show(show, url, thumb):

	oc = ObjectContainer(title2=show, view_group='List')

	try: base = RE_BASE_URL.search(url).group(1)
	except: base = BASE_URL

	if url.find('http://') == -1:
		url = base + url

	content = HTML.ElementFromURL(url)

	for category in content.xpath('//*[text()="Full Episodes" or text()="FULL EPISODES"]/following-sibling::ul[1]/li/a[contains(@href, "categories")]'):
		title = category.text.strip()
		url = category.get('href')

		if url.find('http://') == -1:
			url = base + url

		oc.add(DirectoryObject(key=Callback(Episodes, show=show, title=title, url=url, base=base), title=title, thumb=Callback(GetThumb, url=thumb)))

	if len(oc) == 0:
		return ObjectContainer(header='Empty', message='This directory is empty')

	return oc

####################################################################################################
@route('/video/nbc/episodes')
def Episodes(show, title, url, base):

	oc = ObjectContainer(title1=show, title2=title, view_group='InfoList')
	content = HTML.ElementFromURL(url)

	for episode in content.xpath('//div[contains(@class, "thumb-view")]//div[contains(@class, "thumb-block")]'):
		video_url = episode.xpath('./a')[0].get('href')

		if video_url.find('http://') == -1:
			video_url = base + video_url

		episode_title = episode.xpath('.//div[@class="title"]')[0].text.strip()
		air_date = episode.xpath('./div[@class="meta"]/p')[0].text.split(': ', 1)[1]
		date = Datetime.ParseDate(air_date).date()
		thumb_url = episode.xpath('.//img')[0].get('src')
		thumb_url = RE_THUMB_SIZE.sub('w=640&h=360', thumb_url)

		oc.add(EpisodeObject(
			url = video_url,
			show = show,
			title = episode_title,
			originally_available_at = date,
			thumb = Callback(GetThumb, url=thumb_url)
		))

	# More than 1 page?
	if len(content.xpath('//div[@class="nbcu_pager"]')) > 0:
		next_url = base + content.xpath('//div[@class="nbcu_pager"]//a[text()="Next"]')[0].get('href')

		if next_url != url:
			oc.add(NextPageObject(key=Callback(Episodes, title=title, url=next_url, base=base), title='Next ...'))

	if len(oc) == 0:
		return ObjectContainer(header='Empty', mesage='This directory is empty')

	return oc

####################################################################################################
def GetThumb(url=None, path=None, pid=None, classic_tv=False):

	if url == None:
		if classic_tv == True:
			url = THUMB_URL % (480, path, pid)
		else:
			url = THUMB_URL % (360, path, pid)

	try:
		data = HTTP.Request(url, cacheTime=CACHE_1MONTH).content
		return DataObject(data, 'image/jpeg')
	except:
		return Redirect(R(ICON))
