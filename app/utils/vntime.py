import logging
import arrow, datetime
import datetime

def today_8am():
	dateNow = arrow.utcnow().to("Asia/Ho_Chi_Minh").date()
	hourNow = arrow.utcnow().to("Asia/Ho_Chi_Minh").time().hour
	if hourNow >=8:
		return(arrow.get(dateNow).shift(hours=8).timestamp - 25200)
	else:
		return(arrow.get(dateNow).shift(hours=-16).timestamp - 25200)

def tomorrow_8am():
	tomorrow = today_8am() +  86400
	return tomorrow

def now():
	return arrow.utcnow().to("Asia/Ho_Chi_Minh").timestamp()

def work_start(date):
	""" Lấy ngày theo giờ hiện tại
	"""
	hourNow = arrow.utcnow().to("Asia/Ho_Chi_Minh").time().hour
	if hourNow >= 8:
		return arrow.get(date + ' 01:00:00', 'DD-MM-YYYY HH:mm:ss').timestamp
	else: 
		return arrow.get(date + ' 01:00:00', 'DD-MM-YYYY HH:mm:ss').shift(days=-1).timestamp

def work_end(date):
	work_end = work_start(date) +  86399
	return work_end

def day_start(date):
	# logging.warning(date)
	return arrow.get(date, "DD-MM-YYYY", tzinfo="Asia/Ho_Chi_Minh").timestamp

def day_end(date):
	return arrow.get(date, "DD-MM-YYYY", tzinfo="Asia/Ho_Chi_Minh").shift(days=1).timestamp - 1

def today_start():
	""" Trả ra timestamp bắt đầu ngày hôm nay

	"""
	dateNow = arrow.utcnow().to("Asia/Ho_Chi_Minh").date()
	return(arrow.get(dateNow).timestamp - 25200)

def today_end():
	""" Trả ra timestamp kết thúc ngày hôm nay

	"""
	return today_start() +  86399

def get_date(timestamp):
	""" Trả ra string DD-MM-YYYY từ timestamp dầu vào

	"""
	return arrow.get(timestamp, tzinfo="Asia/Ho_Chi_Minh").format("DD-MM-YYYY")

def get_datetime(timestamp):
	""" Trả ra string HH:mm/DD-MM từ timestamp dầu vào

	"""
	return arrow.get(timestamp, tzinfo="Asia/Ho_Chi_Minh").format("HH:mm/DD-MM")

def month_start():
	""" Trả ra timestamp của ngày đầu tiên trong tháng

	"""
	now = arrow.utcnow().timestamp
	date=arrow.get(now, tzinfo="Asia/Ho_Chi_Minh").format("DD-MM-YYYY")
	date = "01" + date[2:]
	return arrow.get(date, "DD-MM-YYYY", tzinfo="Asia/Ho_Chi_Minh").timestamp

def create_date_list(dateFrom, dateTo):
	""" Tạo danh sách các ngày từ A -> B

	"""
	dateCurrent = arrow.get(dateFrom, "DD-MM-YYYY")
	dateTo = arrow.get(dateTo, "DD-MM-YYYY")

	datelist = []
	days_limit = 100
	while True:
		days_limit = days_limit - 1
		# mtimestamp = dateCurrent.timestamp
		if dateCurrent > dateTo or days_limit < 1:
			break
		else:
			# result[dateCurrent.format("DD-MM-YYYY")] = None
			datelist.append(dateCurrent.format("DD-MM-YYYY"))
			dateCurrent = dateCurrent.shift(days=1)
	return datelist

def create_datetime(date):
	dates = str(date)
	date = dates.split(" ")[0]
	date1 = datetime.datetime.strptime(date, "%Y-%m-%d").strftime("%d-%m-%Y")
	return arrow.get(date1, "DD-MM-YYYY", tzinfo="Asia/Ho_Chi_Minh").timestamp

def timestamp_today_at(time):
    dateNow = arrow.utcnow().to("Asia/Ho_Chi_Minh").date()
    todayStart = arrow.get(dateNow).timestamp()-25200
    b = time.split(":")
    delta = int(b[0])*3600+int(b[1])*60
    return todayStart + delta

def timestamp_tmr_at(time):
    dateNow = arrow.utcnow().to("Asia/Ho_Chi_Minh").date()
    todayStart = arrow.get(dateNow).timestamp()-25200
    b = time.split(":")
    delta = int(b[0])*3600+int(b[1])*60
    return todayStart + delta + 24*3600