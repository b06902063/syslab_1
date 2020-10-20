import cv2
import numpy as np
import time

# 選擇攝影機
cap = cv2.VideoCapture(0)
cnt = 0



class Record():
	def __init__(self, H, W):
		self.H = H
		self.W = W
		self.records = np.zeros((1, H, W), dtype=np.uint8)
	

	def get_last_frame_finger_info(self):
		"""
		return a list in which each element is [id, (i, j)], where (i, j) is the coordinate of the {id}-th finger (i, j is in C order). 
		"""
		last_frame = self.records[-1, :, :]
		ids = list(set(last_frame.flat))
		ids.remove(0)
		if len(ids) == 0:
			return []
		coordinates = []
		for id in ids:
			try:
				coordinates.append([i.item() for i in (last_frame == id).nonzero()])
			except:
				print([i for i in (self.records == id).nonzero()])
				import ipdb; ipdb.set_trace()
				exit()
		return list(zip(ids, coordinates))


	def add_record(self, finger_map):
		if (finger_map == 0).all() or self.records.shape[0] > 120:
			self.init()
			stroke_end = True
		else:
			self.records = np.concatenate((self.records, np.expand_dims(finger_map, 0)), 0)
			stroke_end = False
			
		return stroke_end, self.records


	def init(self):
		self.records = np.zeros((1, self.H, self.W), dtype=np.uint8)
		self.history_ids = [0]


	def judge_id(self, cx, cy, used_ids):
		try:
			this_id = -1
			last_finger_info = self.get_last_frame_finger_info()
			
			if last_finger_info == []:
				this_id = max(used_ids) + 1
			for id, (m, n) in last_finger_info:
				if abs(cy-m) < 50 and abs(cx-n) < 50 and id not in used_ids:
					this_id = id
					break
			if this_id == -1:
				this_id = max(last_finger_info[-1][0] + 1, max(self.history_ids) + 1)
			
			assert this_id > 0
			if this_id not in self.history_ids:
				self.history_ids.append(this_id)
			return this_id
		except:
			import ipdb; ipdb.set_trace()


def classify_digit(records):
	# TODO
	pass



mode = 'color'
t0 = time.time()
frame_cnt = 0
record = None
while(True):
	# 從攝影機擷取一張影像
	ret, frame = cap.read()  # frame.shape: (480, 640, 3)
	frame = frame[:, ::-1, :]  # raw frame is mirrored
	gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
	thres = 30
	ret, bin = cv2.threshold(gray, thres, 255, cv2.THRESH_BINARY)
	bin = cv2.medianBlur(bin, 15)  # shape: (480, 640)

	h = bin.shape[0]
	w = bin.shape[1]
	if record == None:
		record = Record(h, w)
	finger_map = np.zeros(bin.shape, dtype=np.uint8)


	last_finger_info = record.get_last_frame_finger_info()
	contours, hierarchy = cv2.findContours(bin, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
	
	used_ids = [0]
	for i, cnt in enumerate(contours):
		area = cv2.contourArea(cnt)
		if area > 15000 or area < 1000:
			continue
		
		M = cv2.moments(cnt)
		if M['m10'] != 0 and M['m00'] != 0:
			cx = int(M['m10']/M['m00'])
			cy = int(M['m01']/M['m00'])

			this_id = record.judge_id(cx, cy, used_ids)
			finger_map[cy, cx] = this_id
			used_ids.append(this_id)

			frame = cv2.drawContours(frame, contours, i, (0,0,255), 2)
			cv2.circle(frame, (cx, cy), 10, (1, 227, 254), -1)
			cv2.putText(frame, f'ID: {this_id}', 
							(min(cx+16, w), cy), 
							cv2.FONT_HERSHEY_SIMPLEX, 
							0.5, (0, 255, 255), 1, cv2.LINE_AA)
			cv2.putText(frame, f'area: {area}', 
							(min(cx+16, w), cy+20), 
							cv2.FONT_HERSHEY_SIMPLEX, 
							0.5, (0, 255, 255), 1, cv2.LINE_AA)
			

	stroke_end, records = record.add_record(finger_map)
	if stroke_end:
		digit = classify_digit(records)
		# TODO: put predicted number on the frame
	

	# 顯示圖片
	if mode == 'color':
		cv2.imshow('frame', frame)
	elif mode == 'gray':
		cv2.imshow('frame', gray)
	elif mode == 'bin':
		cv2.imshow('frame', bin)
	frame_cnt += 1


	# 若按下 q 鍵則離開迴圈
	key = cv2.waitKey(1) & 0xFF
	
	if key == ord('q'):
		break
	elif key == ord('c'):
		cv2.imwrite(f'./frame_{cnt}.png', frame)
		cnt += 1
	elif key == ord('g'):
		mode = 'gray'
	elif key == ord('b'):
		cv2.imwrite(f'./frame_{cnt}.png', frame)
		mode = 'bin'



	dt = time.time() - t0
	# print('frame rate:', frame_cnt/dt, end='\r')
	if dt > 60:
		d0 = time.time()
		frame_cnt = 0

# 釋放攝影機
cap.release()

# 關閉所有 OpenCV 視窗
cv2.destroyAllWindows()