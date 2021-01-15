import time,json,requests,random,datetime,os,sys
from campus import CampusCard
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

chrome_options = Options()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
driver = webdriver.Chrome('/usr/bin/chromedriver', chrome_options=chrome_options)

def main():
    #sectets字段录入
    sckey, success, failure, result, phone, password,guardianPhone = [], [], [], [], [], [], []
    #多人循环录入
    while True:
        try:
            users = input()
            info = users.split(',')
            phone.append(info[0])
            password.append(info[1])
            guardianPhone.append(info[2])
            sckey.append(info[3])
        except:
            break

    #提交打卡
    for index,value in enumerate(phone):
        print("开始获取用户%s信息"%(value[-4:]))
        count = 0
        while (count < 3):
            try:
                campus = CampusCard(phone[index], password[index])
                loginJson = campus.get_main_info()
                token = campus.user_info["sessionId"]
                driver.get('https://reportedh5.17wanxiao.com/collegeHealthPunch/index.html?token=%s#/punch?punchId=180'%token)
                #time.sleep(10)
                response = check_in(loginJson["classId"],loginJson["classDescription"],loginJson["stuNo"],loginJson["username"],phone[index],guardianPhone[index],loginJson["userId"],loginJson["customerId"],token)
                if  response.json()["msg"] == '成功'and index == 0:
                    strTime = GetNowTime()
                    success.append(value[-4:])
                    print(response.text)
                    msg = value[-4:]+"打卡成功-" + strTime
                    result=response
                    break
                elif response.json()["msg"] == '业务异常'and index == 0:
                    strTime = GetNowTime()
                    failure.append(value[-4:])
                    print(response.text)
                    msg = value[-4:]+"打卡失败-" + strTime
                    result=response
                    count = count + 1
                elif response.json()["msg"] == '成功':
                    strTime = GetNowTime()
                    success.append(value[-4:])
                    print(response.text)
                    msg = value[-4:]+"打卡成功-" + strTime
                    break
                else:
                    strTime = GetNowTime()
                    failure.append(value[-4:])
                    print(response.text)
                    msg = value[-4:] + "打卡异常-" + strTime
                    count = count + 1
                    print('%s打卡失败，开始第%d次重试...'%(value[-6:],count))
                    time.sleep(15)

            except Exception as err:
                print(err)
                msg = "出现错误"
                failure.append(value[-4:])
                break
        print(msg)
        print("-----------------------")
    fail = sorted(set(failure),key=failure.index)
    strTime = GetNowTime()
    title = "成功: %s 人,失败: %s 人"%(len(success),len(fail))
    try:
        if  len(sckey[0])>2:
            print('主用户开始微信推送...')
            WechatPush(title,'https://sc.ftqq.com/'+sckey[0]+'.send',success,fail,result)
    except:
        print("微信推送出错！")
#时间函数
def GetNowTime():
    cstTime = (datetime.datetime.utcnow() + datetime.timedelta(hours=8))
    strTime = cstTime.strftime("%H:%M:%S")
    return strTime

#打卡参数配置函数
def GetUserJson(deptId,text,stuNum,userName,phone,guardianPhone,userId,customerId,token):
    return  {
	"businessType": "epmpics",
	"method": "submitUpInfo",
	"jsonData": {
		"deptStr": {
			"deptid": deptId,
			"text": text
		},
		"areaStr": {"streetNumber":"","street":"新七大道","district":"浉河区","city":"信阳市","province":"河南省","town":"","pois":"信阳师范学院","lng":114.04613300000214 + random.random()/100000,"lat":32.15061303752275 + random.random()/100000,"address":"浉河区新七大道信阳师范学院","text":"河南省-信阳市","code":""},
		"reportdate": round(time.time()*1000),
		"customerid": customerId,
		"deptid": deptId,
		"source": "app",
		"templateid": "pneumonia",
		"stuNo": stuNum,
		"username": userName,
		"phonenum": phone,
		"userid": userId,
		"updatainfo": [{
			"propertyname": "wendu",
			"value": round(random.uniform(36.2,36.8),1)
		}, {
			"propertyname": "symptom",
			"value": "无症状"
		}, {
			"propertyname": "jkzks",
			"value": "正常"
		}, {
			"propertyname": "jtcy",
			"value": "否"
		}, {
			"propertyname": "SFJCQZHYS",
			"value": "否"
		}, {
			"propertyname": "sfddgr",
			"value": "否"
		}, {
			"propertyname": "isTouch",
			"value": "否"
		}, {
			"propertyname": "是否途径或逗留过疫情中，高风险地区？",
			"value": ""
		}, {
			"propertyname": "isAlreadyInSchool",
			"value": "有"
		}, {
			"propertyname": "hsjc0511",
			"value": "否"
		}, {
			"propertyname": "ownPhone",
			"value": phone
		}, {
			"propertyname": "emergencyContact",
			"value": "监护人"
		}, {
			"propertyname": "mergencyPeoplePhone",
			"value": guardianPhone
		}],
		"gpsType": 0,
		"token": token
	}
}

#打卡提交函数
def check_in(deptId,text,stuNum,userName,phone,guardianPhone,userId,customerId,token):
    sign_url = "https://reportedh5.17wanxiao.com/sass/api/epmpics"
    jsons=GetUserJson(deptId,text,stuNum,userName,phone,guardianPhone,userId,customerId,token)
    #提交打卡
    response = requests.post(sign_url, json=jsons,)
    return response

#微信通知
def WechatPush(title,sckey,success,fail,result):
    strTime = GetNowTime()
    page = json.dumps(result.json(), sort_keys=True, indent=4, separators=(',', ': '),ensure_ascii=False)
    content = f"""
`{strTime}`
#### 打卡成功用户：
`{success}`
#### 打卡失败用户:
`{fail}`
#### 主用户打卡信息:
```
{page}
```
        """
    data = {
            "text":title,
            "desp":content
    }
    try:
        req = requests.post(sckey,data = data)
        if req.json()["errmsg"] == 'success':
            print("Server酱推送服务成功")
        else:
            print("Server酱推送服务失败")
    except:
        print("微信推送参数错误")
if __name__ == '__main__':
    main()
