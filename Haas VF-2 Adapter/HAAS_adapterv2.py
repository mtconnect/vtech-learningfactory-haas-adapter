import threading, time, socket, sys, datetime, serial, re, requests

client_counter = 0
client_list = []
first_run_flag = 1
lock = threading.Lock()
event = threading.Event()
event.set()

# Initialising 7 global attributes for HAAS serial comm macros
mac_status = part_num = prog_name = sspeed = coolant = sload = cut_status = combined_output = 'Nil'

"""Creating Socket Objects"""
HOST = 'localhost'
PORT = 7878

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

"""Binding to the local port/host"""
try:
    s.bind((HOST, PORT))
except socket.error as msg:
    print ('Bind failed. Error Code : ' + str(msg[0]) + ' Message ' + msg[1])
    sys.exit()

"""Start Listening to Socket for Clients"""
s.listen(5)

"""Function to Clear Out Threads List Once All Threads are Empty"""

def thread_list_empty():
    global client_list, client_counter

    while True:
        try:
            if client_counter == 0 and first_run_flag == 0 and client_list != []:
                print("%d Clients Active" % client_counter)
                print("Clearing All threads....")
                for index, thread in enumerate(client_list):
                    thread.join()
                client_list = []
        except:
            print("Invalid Client List Deletion")


"""Function that parses attributes from the HAAS"""

def fetch_from_HAAS():
    global mac_status, part_num, prog_name, sspeed, coolant, sload, cut_status, combined_output
    

    ser = serial.Serial(bytesize=serial.SEVENBITS, xonxoff=True)
    ser.baudrate = 9600
    # Assuming HAAS is connected to ttyUSB0 port of Linux System
    ser.port = '/dev/ttyUSB0' 
    ser.timeout = 1

    try:
        ser.open()
    except serial.SerialException:
        if ser.is_open:
            try:
                print("Port was open. Attempting to close.")
                ser.close()
                time.sleep(2)
                ser.open()
            except:
                print("Port is already open. Failed to close. Try again.")
                event.clear()
        else:
            print("Failed to connect to serial port. Make sure it is free or it exists. Try again.")
            event.clear()

    print("ok1")
    sspeed_prev = "novalue"
    sload_prev = "novalue"
    coord_x_prev = "novalue"
    coord_xw_prev = "novalue"
    coord_y_prev = "novalue"
    coord_yw_prev = "novalue"
    coord_z_prev = "novalue"
    coord_zw_prev = "novalue"
    coord_a_prev = "novalue"
    coord_b_prev = "novalue"
    coord_aw_prev = "novalue"
    coord_bw_prev = "novalue"
    out_initial = '|Srpm|' + 'Nil' + '|Sload|' + 'Nil' + '|Xabs|' + 'Nil' + '|Yabs|' + 'Nil' + '|Zabs|' + 'Nil' #+ '|Aabs|' + 'Nil' + '|Babs|' + 'Nil'
    combined_output = '\r\n' + datetime.datetime.utcnow().isoformat() + 'Z' + out_initial
    time.sleep(2)

    while True:
        updated = False
        out = ''
        try:
            """
            # Reading Status
            ser.write(b"?Q500\r\n")
            status = ser.readline()
            status = status[2:-3]
            print(status)

            if status != '':
                mac_status = 'ON'
            else:
                mac_status = 'OFF'

            out += '|power|' + str(mac_status)

            if 'PART' in status:
                part_num = (re.findall(r"[-+]?\d*\.\d+|\d+", status.split(',')[-1])[0])
                prog_name = status.split(',')[1]
            else:
                part_num = 'Nil'
                prog_name = 'Nil'
            out += '|PartCountAct|' + str(part_num) + '|program|' + str(prog_name)
	"""

            # Reading Spindle Speed
            sspeed = ""
            sload=""
            coord_x = ""
            coord_y = ""
            coord_z = ""
            coolant = ""
            data = {"header":"HAASData","body":[]}

            print("ok2")
            #coolant
            try:
                ser.write(b"?Q600 1094\r\n")
                
                while True:
                    coolant = ser.readline().decode("utf-8").strip()
                    if len(coolant) > 4:
                        break
                coolant = coolant.split(",")[2].strip()
                
            except:
                coolant = '0'
            print("coolant to int " + coolant)
            data["body"].append({"timestamp": 0, "name":"coolant_level", "value":int(float(coolant.replace(chr(23), '')))})

            print(data)
            #spindle speed
            try:
                ser.write(b"?Q600 3027\r\n")
                while True:
                    sspeed = ser.readline().decode("utf-8").strip()
                    if len(sspeed) > 4:
                        break
                sspeed = sspeed.split(",")[2].strip()
            except:
                sspeed = 'Nil'
            if sspeed != sspeed_prev:
                updated = True
                out += '|Srpm|' + sspeed
                sspeed_prev = sspeed
            data["body"].append({"timestamp": 0, "name":"spindle_rpm", "value":int(float(sspeed.replace(chr(23), '')))})
            print(data)
            # Quering Spindle Load
            try:
                ser.write(b"?Q600 1098\r")
                while True:
                    sload = ser.readline()
                    sload = sload.decode("utf-8").strip()
                    if len(sload)>4:
                        break
                    time.sleep(.01)
                sload = sload.split(",")
                sload=sload[2].strip()
            except:
                sload = 'Nil'
            if sload != sload_prev:
                updated = True
                sload_prev = sload
                out += '|Sload|' + sload

            #Present Machine Coordinates
            try:
                ser.write(b"?Q600 5021\r")
                while True:
                    coord_x = ser.readline().decode("utf-8").strip()
                    if len(coord_x)>4:
                        break
                coord_x = coord_x.split(",")
                coord_x=coord_x[2].strip()
            except:
                coord_x = 'Nil'
            if coord_x == '':
                coord_x = 'Nil'
            if coord_x != coord_x_prev:
                updated = True
                coord_x_prev = coord_x
                out += '|Xabs|' + str(coord_x).replace(" ", "")
            data["body"].append({"timestamp": 0, "name":"machine_x", "value":float(coord_x.replace(chr(23), ''))})

            #Xpw
            try:
                ser.write(b"?Q600 5041\r")
                while True:
                    coord_xw = ser.readline().decode("utf-8").strip()
                    if len(coord_xw)>4:
                        break
                coord_xw = coord_xw.split(",")
                coord_xw=coord_xw[2].strip()
            except:
                coord_xw = 'Nil'
            if coord_xw == '':
                coord_xw = 'Nil'
            if coord_xw != coord_xw_prev:
                updated = True
                coord_xw_prev = coord_xw
                out += '|Xpos|' + str(coord_xw).replace(" ", "")
            data["body"].append({"timestamp": 0, "name":"work_x", "value":float(coord_xw.replace(chr(23), ''))})

            try:
                ser.write(b"?Q600 5022\r")
                while True:
                    coord_y = ser.readline().decode("utf-8").strip()
                    if len(coord_y)>4:
                        break
                coord_y = coord_y.split(",")
                coord_y=coord_y[2].strip()
            except:
                coord_y = 'Nil'
            if coord_y == '':
                coord_y = 'Nil'
            if coord_y != coord_y_prev:
                coord_y_prev = coord_y
                updated = True
                out += '|Yabs|' + str(coord_y).replace(" ", "")
            data["body"].append({"timestamp": 0, "name":"machine_y", "value":float(coord_y.replace(chr(23), ''))})

            #Ypw
            try:
                ser.write(b"?Q600 5042\r")
                while True:
                    coord_yw = ser.readline().decode("utf-8").strip()
                    if len(coord_yw)>4:
                        break
                coord_yw = coord_yw.split(",")
                coord_yw=coord_yw[2].strip()
            except:
                coord_yw = 'Nil'
            if coord_yw == '':
                coord_yw = 'Nil'
            if coord_yw != coord_yw_prev:
                coord_yw_prev = coord_yw
                updated = True
                out += '|Ypos|' + str(coord_yw).replace(" ", "")
            data["body"].append({"timestamp": 0, "name":"work_y", "value":float(coord_yw.replace(chr(23), ''))})
            
            try:
                ser.write(b"?Q600 5023\r")
                while True:
                    coord_z = ser.readline().decode("utf-8").strip()
                    if len(coord_z) > 4:
                        break
                coord_z = coord_z.split(",")
                coord_z = coord_z[2].strip()
            except:
                coord_z = 'Nil'
            if coord_z == '':
                coord_z = 'Nil'
            if coord_z != coord_z_prev:
                coord_z_prev = coord_z
                updated = True
                out += '|Zabs|' + str(coord_z).replace(" ", "")
            data["body"].append({"timestamp": 0, "name":"machine_z", "value":float(coord_z.replace(chr(23), ''))})

            #Zw
            try:
                ser.write(b"?Q600 5043\r")
                while True:
                    coord_zw = ser.readline().decode("utf-8").strip()
                    if len(coord_zw) > 4:
                        break
                coord_zw = coord_zw.split(",")
                coord_zw = coord_zw[2].strip()
            except:
                coord_zw = 'Nil'
            if coord_zw == '':
                coord_zw = 'Nil'
            if coord_zw != coord_zw_prev:
                coord_zw_prev = coord_zw
                updated = True
                out += '|Zpos|' + str(coord_zw).replace(" ", "")
            data["body"].append({"timestamp": 0, "name":"work_z", "value":float(coord_zw.replace(chr(23), ''))})

            #machine a
            try:
                ser.write(b"?Q600 5024\r")
                coord_a = ""
                while True:
                    coord_a = ser.readline().decode("utf-8").strip()
                    if len(coord_a) > 4:
                        break
                coord_a = coord_a.split(",")
                coord_a = coord_a[2].strip()
            except:
                coord_a = 'Nil'
            if coord_a == '':
                coord_a = 'Nil'
            if coord_a != coord_a_prev:
                coord_a_prev = coord_a
                updated = True
            data["body"].append({"timestamp": 0, "name":"machine_a", "value":float(coord_a.replace(chr(23), ''))})

            #machine b
            try:
                ser.write(b"?Q600 5025\r")
                coord_b = ""
                while True:
                    coord_b = ser.readline().decode("utf-8").strip()
                    if len(coord_b) > 4:
                        break
                coord_b = coord_b.split(",")
                coord_b = coord_b[2].strip()
            except:
                coord_b = 'Nil'
            if coord_b == '':
                coord_b = 'Nil'
            if coord_b != coord_b_prev:
                coord_b_prev = coord_b
                updated = True
            data["body"].append({"timestamp": 0, "name":"machine_b", "value":float(coord_b.replace(chr(23), ''))})

            #work a
            try:
                ser.write(b"?Q600 5044\r")
                coord_aw = ""
                while True:
                    coord_aw = ser.readline().decode("utf-8").strip()
                    if len(coord_aw) > 4:
                        break
                coord_aw = coord_a.split(",")
                coord_aw = coord_a[2].strip()
            except:
                coord_aw = 'Nil'
            if coord_aw == '':
                coord_aw = 'Nil'
            if coord_aw != coord_aw_prev:
                coord_aw_prev = coord_aw
                updated = True
            data["body"].append({"timestamp": 0, "name":"work_a", "value":float(coord_aw.replace(chr(23), ''))})

            #work b
            try:
                ser.write(b"?Q600 5045\r")
                coord_bw = ""
                while True:
                    coord_bw = ser.readline().decode("utf-8").strip()
                    if len(coord_bw) > 4:
                        break
                coord_bw = coord_bw.split(",")
                coord_bw = coord_b[2].strip()
            except:
                coord_bw = 'Nil'
            if coord_bw == '':
                coord_bw = 'Nil'
            if coord_bw != coord_bw_prev:
                coord_bw_prev = coord_bw
                updated = True
            data["body"].append({"timestamp": 0, "name":"work_b", "value":float(coord_bw.replace(chr(23), ''))})



            """


            # Quering Cutting Status
            try:
                cut_status = status.split(',')[status.split(',').index('PARTS') - 1]
                if 'FEED' in cut_status:
                    cut_status = 'FEED_HOLD'
                elif 'IDLE' in cut_status:
                    cut_status = 'IDLE'
            except:
                cut_status = 'Nil'
            out += '|execution|' + cut_status
            
        
            # Reading Coolant Level
            try:
                ser.write(b"Q600 1094\r")
                coolant = ser.readline()
                coolant = str(float(coolant[15:26]))
            except:
                pass


            """

            requests.post("http://128.173.94.111/api/devices/registerData", json=data)

            # Final data purge
            combined_output = '\r\n' + datetime.datetime.now().isoformat() + 'Z' + out
            if updated:
                pass
        except Exception as ex:
            print("Failed fetching values from machine " + ex)
            time.sleep(2)

        # time.sleep(0.1)

    ser.close()


"""Main Thread Class For Clients"""


class NewClientThread(threading.Thread):
    # init method called on thread object creation,
    def __init__(self, conn, string_address):
        threading.Thread.__init__(self)
        self.connection_object = conn
        self.client_ip = string_address

    # run method called on .start() execution
    def run(self):
        global client_counter, combined_output
        global lock
        while True:
            try:
                #print("Sending data to Client {} in {}".format(self.client_ip, self.getName()))
                out = combined_output
                print("OUT: "+ out)
                self.connection_object.sendall(out.encode())
                time.sleep(0.5)

            except err:
                lock.acquire()
                try:
                    print(err)
                    client_counter = client_counter - 1
                    print("Connection disconnected for ip {} ".format(self.client_ip))
                    break
                finally:
                    lock.release()


"""Starts From Here"""
t1 = threading.Thread(target=thread_list_empty)
t2 = threading.Thread(target=fetch_from_HAAS)
t1.setDaemon(True)
t2.setDaemon(True)
t1.start()
t2.start()
time.sleep(2)

while event.is_set():

    if first_run_flag == 1:
        print("Listening to Port: %d...." % PORT)


    try:
        conn, addr = s.accept()
        lock.acquire()
        client_counter = client_counter + 1
        first_run_flag = 0
        print("Accepting Comm From:" + " " + str(addr))
        new_Client_Thread = NewClientThread(conn, str(addr))
        new_Client_Thread.setDaemon(True)
        client_list.append(new_Client_Thread)
        print(client_list)
        new_Client_Thread.start()
        lock.release()
    except KeyboardInterrupt:
        print("\nExiting Program")
        sys.exit()

if not event.is_set():
    print("\nExiting Program")
    sys.exit()
