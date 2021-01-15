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
    sckey, success, failure, result, phone, password = [], [], [], [], [], []
    #多人循环录入
    while True:
        try:
            users = input()
            info = users.split(',')
            phone.append(info[0])
            password.append(info[1])
            sckey.append(info[2])
        except:
            break

    #提交打卡
    for index,value in enumerate(phone):
        print("开始获取用户%s信息"%(value[-4:]))
        try:
            campus = CampusCard(phone[index], password[index])
            loginJson = campus.get_main_info()
            token = campus.user_info["sessionId"]
            driver.get('https://reportedh5.17wanxiao.com/collegeHealthPunch/index.html?token=%s#/punch?punchId=180'%token)
            #time.sleep(10)
            response = check_in(token)
            strTime = GetNowTime()
            if  response.json()["msg"] == '成功':
                success.append(value[-4:])
                msg = value[-4:]+"打卡成功-" + strTime
                result=response
            else:
                failure.append(value[-4:])
                msg = value[-4:] + "打卡异常-" + strTime
                time.sleep(15)
            print(response.text)
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
    except Exception as err:
        print("微信推送出错！%s"%(err))
#时间函数
def GetNowTime():
    cstTime = (datetime.datetime.utcnow() + datetime.timedelta(hours=8))
    strTime = cstTime.strftime("%H:%M:%S")
    return strTime

#打卡参数配置函数
def GetUserJson(token):
    sign_url = "https://reportedh5.17wanxiao.com/sass/api/epmpics"
    user_json = {
            "businessType": "epmpics",
            "jsonData": {
            "templateid": "pneumonia",
            "token": token
        },
            "method": "getUpDataInfoDetail"
    }
    response = requests.post(sign_url, json=user_json).json()
    #最近一次打卡记录
    lately_data = json.loads(response['data'])
    lately_json = {
            "add": lately_data['add'],
            "areaStr": lately_data['areaStr'],
            "updatainfo": [{"propertyname": i["propertyname"], "value": i["value"]} for i in lately_data['cusTemplateRelations']]
    }
    return  {
        "businessType": "epmpics",
        "method": "submitUpInfo",
        "jsonData": {
                "deptStr": lately_json['deptStr'],
                "areaStr": lately_json['areaStr'],
                "reportdate": round(time.time()*1000),
                "customerid": lately_json['customerid'],
                "deptid": lately_json['deptStr']['deptid'],
                "source": "app",
                "templateid": lately_json['templateid'],
                "stuNo": lately_json['syuNo'],
                "username": lately_json['username'],
                "phonenum": lately_json['phonenum'],
                "userid": lately_json['userid'],
                "updatainfo": lately_json['updatainfo'],
                "gpsType": 1,
                "token": token
         }
}

#打卡提交函数
def check_in(token):
    sign_url = "https://reportedh5.17wanxiao.com/sass/api/epmpics"
    jsons=GetUserJson(token)
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
