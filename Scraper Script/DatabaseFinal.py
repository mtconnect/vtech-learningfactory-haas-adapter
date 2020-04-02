import requests,datetime,re

from threading import Timer, Thread
from xml.etree import ElementTree as ET
from xml.dom import minidom
import urllib3
import time
import mysql.connector

mydb = mysql.connector.connect(
    host = "localhost",
    user = "john",
    passwd = "Skybolt12$",
    database = "MTConnect"
)
mycursor = mydb.cursor()

#adjustable variables
sleeptime = 5 #time the program sleeps before it searches the MTConnect Client for new values | Should not be less than the update time of MTConnect Client

#functions block
def database_write(par1,par2,par3,par4,par5,par6,par7):
    current_time = time.strftime('%Y-%m-%d %H:%M:%S')
    #print(current_time)
    sql = "INSERT INTO haas(time,rotary_velocity,x_val,y_val,z_val,xw_val,yw_val,zw_val) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)"
    val = (current_time,par1,par2,par3,par4,par5,par6,par7)
    mycursor.execute(sql,val)
    mydb.commit()
    print(mycursor.rowcount, "record inserted")

def MTConnectXMLSearch():
    tag = str()#may need to change
    for i in range(20):
        try: 
            response = requests.get("http://localhost:5000/current")
        except requests.exceptions.ConnectionError:
            print("Connection Error retrying in " + str(sleeptime) + " secs")
            print(str(i)+"th time trying reconnection")
	    time.sleep(sleeptime)
            continue
        except requests.exceptions.MissingSchema:
            print("Missing Schema retrying in " + str(sleeptime) + " secs")
	    time.sleep(sleeptime)   
            print(str(i)+"th time trying reconnection")
            continue
        else: 
            break
    else: 
        raise Exception('Unreconverable Error')

    root = ET.fromstring(response.content)
    tag = root.tag.split('}')[0]+'}'#may need to change

    rotary_velocity = root.find(".//"+tag+"DeviceStream")
    rotary_velocity = float(rotary_velocity[0][0][3].text)
    print(rotary_velocity)

    x_val = root.find(".//"+tag+"DeviceStream")
    x_val = float(x_val[4][0][2].text)
    print(x_val)
    xw_val = x_val = root.find(".//"+tag+"DeviceStream")
    xw_val = float(x_val[4][0][3].text)
    print(xw_val)

    y_val = root.find(".//"+tag+"DeviceStream")
    y_val = float(y_val[5][0][2].text)
    print(y_val)
    yw_val = root.find(".//"+tag+"DeviceStream")
    y_wval = float(y_val[5][0][3].text)
    print(yw_val)

    z_val = root.find(".//"+tag+"DeviceStream")
    z_val = float(z_val[6][0][2].text)
    print(z_val)
    zw_val = root.find(".//"+tag+"DeviceStream")
    zw_val = float(z_val[6][0][3].text)
    print(zw_val)
    database_write(rotary_velocity,x_val,y_val,z_val,xw_val,yw_val,zw_val)

#Main infinite searching loop
while True:
    MTConnectXMLSearch()
    time.sleep(sleeptime)