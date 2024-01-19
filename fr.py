### LIBRARY LIST###
import tkinter as tk
import tkinter.messagebox
import tkinter.simpledialog as tsd
import cv2,os
import csv
import numpy as np
import pandas as pd
import datetime
import time
import pymysql as database
import mysql.connector
from PIL import Image
from tkinter import ttk
from tkinter import messagebox as mess

class tkinterApp(tk.Tk):
    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)
        #GUI RESOLUTION
        self.geometry("480x272")
        #self.geometry("480x250")

        container = tk.Frame(self)
        container.pack(side = "top", fill = "both", expand = True)

        container.grid_rowconfigure(0, weight = 1)
        container.grid_columnconfigure(0, weight = 1)

        self.frames = {}

        for F in (StartPage, Register):
            frame = F(container, self)
            self.frames[F] = frame
            frame.grid(row = 0, column = 0, sticky ="nsew")
        self.show_frame(StartPage)

    def show_frame(self, cont):
        frame = self.frames[cont]
        frame.tkraise()


#CLASS HALAMAN PERTAMA GUI (ATTENDANCE SYSTEM)
class StartPage(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        
        #LOAD TRAINER PADA DATASET
        recognizer = cv2.face.LBPHFaceRecognizer_create() 
        exists3 = os.path.isfile("TrainingImageLabel/Trainner.yml")
        if exists3:
            recognizer.read("TrainingImageLabel/Trainner.yml")
            harcascadePath = "haarcascade_frontalface_default.xml"
            faceCascade = cv2.CascadeClassifier(harcascadePath);
        else:
            mess._show(title='Warning', message='Tidak ada Data di Dataset')
        
        #FUNGSI LOOPING WAKTU
        def tick():
            time_string = time.strftime('%H:%M:%S')
            clock.config(text=time_string)
            clock.after(200,tick)
            #LOOPING PRIMARY RFID
            RFID()
            
        #MENGECEK FILE HAARCASCADE
        def check_haarcascadefile():
            exists = os.path.isfile("haarcascade_frontalface_default.xml")
            if exists:
                pass
            else:
                mess._show(title='Warning', message='File Cascade Hilang')
                window.destroy()
        
        #MENGECEK DIREKTORI
        def assure_path_exists(path):
            dir = os.path.dirname(path)
            if not os.path.exists(dir):
                os.makedirs(dir)
        
        #FUNGSI UNTUK MENENTUKAN KONDISI ABSEN (CHECK IN/OUT)
        def checkStats(stats):
            status = stats
            lbl_absensi.configure(text=str(status))
        
        #RFID ATTENDANCE SYSTEM
        def RFID():
            assure_path_exists("DataAbsensi/")
            ts = time.time()
            date = datetime.datetime.fromtimestamp(ts).strftime('%d-%m-%Y')
            timeStamp = datetime.datetime.fromtimestamp(ts).strftime('%H:%M:%S')
            hours,minutes,seconds=timeStamp.split(":")
            
            #PENYESUAIAN DIGIT RFID UID
            lenn = 9
            s=txt.get()
            
            if len(s)>lenn:
                tagId = txt.get()
                status = lbl_absensi['text']
                value = None
                
                #CHECK USER AVAILABILITY IN DATABASE
                mysqldb=mysql.connector.connect(host="localhost",user="pens",password="pens",database="dataset") 
                mycursor=mysqldb.cursor()
                cek_user_rfid = "SELECT * FROM user_baru WHERE rfid_uid=%s"
                mycursor.execute(cek_user_rfid,[str(tagId)])
                
                #MENGAMBIL DATA USER PADA DATABASE
                result = mycursor.fetchall()
                for row in result:
                    fID = row[1]
                    fName = row[2]
                    fDept = row[3]
                rc_user=mycursor.rowcount
                if (rc_user==1):
                    #RECORD ATTENDANCE INTO DATABASE
                    if(mycursor):
                        metode = "RFID"
                        query = "insert into absensi_baru (id,serial,nama,kelas,tanggal,waktu,status,metode,suhu) values(%s,%s,%s,%s,%s,%s,%s,%s)"
                        mycursor.execute(query,[value,str(fID),str(fName),str(fDept),str(date),str(timeStamp),str(status),str(metode)])  
                        mysqldb.commit()
                        lbl_nik.configure(text=str(fID))
                        lbl_stats.configure(text=str(status))
                        txtclear()
                    else:
                        mysqldb.rollback()
                    mysqldb.close()
                    
                    #RECORD ATTENDANCE INTO CSV
                    col_names = ['Id', '', 'Name', '', 'kelas', '', 'Date', '', 'Time', '', 'Status', '', 'Metode']
                    DataAbsensi = [str(fID), '', str(fName), '', str(fDept), '', str(date), '', str(timeStamp), '', str(status), '', str(metode)]
                    exists = os.path.isfile("DataAbsensi/DataAbsensi_" + date + ".csv")           
                    if exists:
                        with open("DataAbsensi/DataAbsensi_" + date + ".csv", 'a+') as csvFile1:
                            writer = csv.writer(csvFile1)
                            writer.writerow(DataAbsensi)
                        csvFile1.close()
                    else:
                        with open("DataAbsensi/DataAbsensi_" + date + ".csv", 'a+') as csvFile1:
                            writer = csv.writer(csvFile1)
                            writer.writerow(col_names)
                            writer.writerow(DataAbsensi)
                        csvFile1.close()
                else:
                    lbl_nik.configure(text="User Not Found")
                    lbl_stats.configure(text="Please Register")
                    txtclear()
                self.after(1000,lbl_clear)
                
        #FUNGSI UNTUK MENGHILANGKAN LABEL NIK DAN STATUS SAAT SUDAH ABSEN
        def lbl_clear():
            lbl_nik.configure(text="")
            lbl_stats.configure(text="")
            lbl_suhu.configure(text="")
        
        #RFID MEMORY CLEAR
        def txtclear():
            txt.delete(0, 'end')
        
        #FUNGSI AGAR RFID MENJADI PRIMARY DALAM ATTENDANCE SYSTEM
        def rfid_click():
            txt.focus_set()
            button3.configure(bg='red')
        
        #FUNGSI UNTUK PINDAH KE CLASS REGISTER PAGE
        def changeRegister():
            button3.configure(bg='white')
            controller.show_frame(Register)
        
        #FUNGSI UNTUK PENGENALAN WAJAH
        def TrackImages():
            #MENGECEK FILE HAARCASCADE DAN DIREKTORI
            check_haarcascadefile()
            assure_path_exists("DataAbsensi/")
            assure_path_exists("DataPegawai/")
            
            counter=0   #COUNTER FACE PREDICT SAAT WAJAH DIKENALI
            counterWr=0 #COUNTER FACE PREDICT SAAT WAJAH TIDAK DIKENALI
            
            cam = cv2.VideoCapture(2)
            font = cv2.FONT_HERSHEY_SIMPLEX
            
            #MENGECEK FILE DATA PEGAWAI CSV
            exists1 = os.path.isfile("DataPegawai/DataPegawai.csv")
            if exists1:
                df = pd.read_csv("DataPegawai/DataPegawai.csv")
            else:
                mess._show(title='Details Missing', message='Tidak ada Data Pegawai')
                cam.release()
                cv2.destroyAllWindows()
            while True:
                ret, im = cam.read()
                if ret is True:
                    gray = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
                    faces = faceCascade.detectMultiScale(gray, 1.2, 5)
                    for (x, y, w, h) in faces:
                        cv2.rectangle(im, (x, y), (x + w, y + h), (225, 0, 0), 2)
                        serial, conf = recognizer.predict(gray[y:y + h, x:x + w])
                        
                        #MENGATUR AKURASI FACE RECOGNITION
                        if (conf <55):
                            counter+=1
                            
                            #MENGAMBIL DATA DARI DATA PEGAWAI CSV
                            aa = df.loc[df['SERIAL NO.'] == serial]['NAME'].values
                            ID = df.loc[df['SERIAL NO.'] == serial]['ID'].values
                            dp = df.loc[df['SERIAL NO.'] == serial]['kelas'].values
                            dept = str(dp)
                            dept = dept[2:-2]
                            ID = str(ID)
                            ID = ID[2:-2]
                            bb = str(aa)
                            bb = bb[2:-2]
                            
                            #PENCEGAHAN KEKELIRUAN WAJAH
                            if (counter >= 500):
                                ts = time.time()
                                date = datetime.datetime.fromtimestamp(ts).strftime('%d-%m-%Y')
                                timeStamp = datetime.datetime.fromtimestamp(ts).strftime('%H:%M:%S')
                                hours,minutes,seconds=timeStamp.split(":")
                                
                                status = lbl_absensi['text']
                                metode = "Face Rec"
                                tanggal = str(date)
                                waktu = str(timeStamp)
                                value = None
                                
                                #RECORD DATA (DATABASE)
                                mysqldb=mysql.connector.connect(host="localhost",user="pens",password="pens",database="dataset") 
                                mycursor=mysqldb.cursor()
                                if(mycursor):
                                    query = "insert into absensi_baru (id,serial,nama,kelas,tanggal,waktu,status,metode) values(%s,%s,%s,%s,%s,%s,%s,%s)"
                                    mycursor.execute(query,[value,str(ID),bb,dept,tanggal,waktu,status,metode])  
                                    mysqldb.commit()
                                    
                                    counter = 0
                                    lbl_nik.configure(text=str(ID))
                                    lbl_stats.configure(text=str(status))
                                    
                                    cam.release()
                                    cv2.destroyAllWindows()
                                else:
                                    mysqldb.rollback()
                                mysqldb.close()
                                
                                #RECORD DATA (CSV)
                                col_names = ['Id', '', 'Name', '', 'kelas', '', 'Date', '', 'Time', '', 'Status', '', 'Metode']
                                DataAbsensi = [str(ID), '', bb, '', str(dept), '', str(date), '', str(timeStamp), '', str(status), '', str(metode)]
                                exists = os.path.isfile("DataAbsensi/DataAbsensi_" + date + ".csv")           
                                if exists:
                                    with open("DataAbsensi/DataAbsensi_" + date + ".csv", 'a+') as csvFile1:
                                        writer = csv.writer(csvFile1)
                                        writer.writerow(DataAbsensi)
                                    csvFile1.close()
                                else:
                                    with open("DataAbsensi/DataAbsensi_" + date + ".csv", 'a+') as csvFile1:
                                        writer = csv.writer(csvFile1)
                                        writer.writerow(col_names)
                                        writer.writerow(DataAbsensi)
                                    csvFile1.close()    
                                self.after(2500,lbl_clear)
                        else:
                            counterWr+=1
                            Id = 'Tidak Dikenali'
                            bb = str(Id)
                            
                            #JIKA WAJAH TIDAK DIKENALI MUNCUL 30x PREDICT MAKA KEMBALI KE GUI
                            if (counterWr>=50):
                                cam.release()
                                cv2.destroyAllWindows()
                                
                                lbl_nik.configure(text="Wajah Tidak")
                                lbl_stats.configure(text="Dikenali")
                                self.after(2500,lbl_clear)
                                counterWr=0
                                break
                        
                        #MEMUNCULKAN NAMA + AKURASI + SUHU SAAT FACE RECOGNITION
                        cv2.putText(im, str(bb), (x+5,y-5), font, 0.5, (255, 0, 0), 2)
                        conf = "  {0}%".format(round(100 - conf))
                        cv2.putText(im, str(conf), (x+5,y+h-5), font, 0.5, (0,0,255), 1)
                    
                    #OPENCV WINDOW CONFIGURE
                    imS = cv2.resize(im, (900, 440))
                    #cv2.moveWindow('absen', 225, 115)
                    cv2.imshow("absen", imS)
                    
                    #TOMBOL INTERUPSI KELUAR DARI FACE RECOGNITION (Q PADA KEYBOARD)
                    if (cv2.waitKey(1) == ord('q')):
                        cam.release()
                        cv2.destroyAllWindows()
                else:
                    break
            cam.release()
            cv2.destroyAllWindows()
            rfid_click()
        
        ### FRAME GUI CONFIG ###
        framebg = tk.Frame(self, bg="#081312")
        framebg.place(relx=0., rely=0, relwidth=1, relheight=1)
        
        frame1 = tk.Frame(self, bg="#5bcbfa")
        frame1.place(relx=0.43, rely=0.09, relwidth=0.55, relheight=0.75)
        
        frame2 = tk.Frame(self, bg="#5bcbfa")
        frame2.place(relx=0.016, rely=0.09, relwidth=0.38, relheight=0.75)

        Judul = tk.Label(self, text="Face Recognition TA-ku" ,fg="white",bg="#081312" ,width=30 ,height=1, font=('times', 14, ' bold '))
        Judul.place(relx=0.15, rely=0, relwidth=0.7, relheight=0.07)
        
        frame3 = tk.Frame(frame2, bg="#5bcbfa")
        frame3.place(relx=0, rely=0.22, relwidth=1, relheight=0.15)

        frame4 = tk.Frame(frame2, bg="#5bcbfa")
        frame4.place(relx=0, rely=0.10, relwidth=1, relheight=0.15)

        frame5 = tk.Frame(frame1, bg="#5bcbfb")
        frame5.place(relx=0.05, rely=0.11, relwidth=0.55, relheight=0.15)
        
        ts = time.time()
        date = datetime.datetime.fromtimestamp(ts).strftime('%d-%m-%Y')
        day,month,year=date.split("-")

        mont={'01':'Januari',
              '02':'Februari',
              '03':'Maret',
              '04':'April',
              '05':'Mei',
              '06':'Juni',
              '07':'Juli',
              '08':'Agustus',
              '09':'September',
              '10':'Oktober',
              '11':'November',
              '12':'Desember'
              }
        
        datef = tk.Label(frame4, text = day+"-"+mont[month]+"-"+year, fg="#081312",bg="#5bcbfa" ,width=40 ,height=1, font=('times', 12, ' bold '))
        datef.pack(fill='both',expand=1)

        clock = tk.Label(frame3,fg="#081312",bg="#5bcbfa" ,width=40 ,height=1,font=('times', 12, ' bold '))
        clock.pack(fill='both',expand=1)


        ### LABEL LIST ###
        lbl_kamera = tk.Label(frame2, text="Log Absensi", fg="black", bg="#35e541", font=('times', 11, ' bold ') )
        lbl_kamera.place(relx=0, rely=0, relwidth=1)

        lbl_absensi = tk.Label(frame1, text="Check In", fg="black", bg="#35e541", font=('times', 11, ' bold ') )
        lbl_absensi.place(relx=0, rely=0, relwidth=1)

        lbl_stats = tk.Label(frame2, text="" ,bg="#5bcbfa" ,fg="black"  ,width=14 ,height=1, activebackground = "yellow" ,font=('times', 18, ' bold '))
        lbl_stats.place(x=5, y=120)

        lbl_nik = tk.Label(frame2, text="" ,bg="#5bcbfa" ,fg="black"  ,width=14 ,height=1, activebackground = "yellow" ,font=('times', 18, ' bold '))
        lbl_nik.place(x=5, y=80)
        
        lbl_suhu = tk.Label(frame1, text="" ,bg="#5bcbfa" ,fg="black" ,height=1, activebackground = "yellow" ,font=('times', 18, ' bold '))
        lbl_suhu.place(relx=0, rely=0.4, relwidth=1)
        
        txt = tk.Entry(frame1,width=12 ,fg="black",font=('times', 1, ' bold '))
        txt.place(relx=0.55, rely=0.965, relwidth=0.4, relheight=0.01)


        ### BUTTON LIST ###
        button1 = ttk.Button(frame2, text ="Register",command = changeRegister)
        button1.place(relx=0.05, rely=0.825, relwidth=0.9)
        
        button2 = tk.Button(frame1, text ="FaceRec",bg="white",command = TrackImages)
        button2.place(relx=0.05, rely=0.825, relwidth=0.4)
        
        button3 = tk.Button(frame1, text ="RFID",bg="white",activebackground="red",command = rfid_click)
        button3.place(relx=0.55, rely=0.825, relwidth=0.4)
        
        checkIn = tk.Button(self, text="Check-In", command=lambda m="Check In": checkStats(m)  ,fg="black"  ,bg="yellow"  ,width=10  ,height=1, activebackground = "white" ,font=('times', 10, ' bold '))
        checkIn.place(x=25,y=235)
        
        checkOut = tk.Button(self, text="Check-Out", command=lambda m="Check Out": checkStats(m)  ,fg="black"  ,bg="yellow"  ,width=10 ,height=1, activebackground = "white" ,font=('times', 10, ' bold '))
        checkOut.place(x=135, y=235)
        
        breakIn = tk.Button(self, text="Break-In", command=lambda m="Break In": checkStats(m), fg="black", bg="yellow", width=10, heigh=1, activebackground = "white", font=('times',10,'bold'))
        breakIn.place(x=245, y=235)
        
        breakOut = tk.Button(self, text="Break-Out", command=lambda m="Break Out": checkStats(m), fg="black", bg="yellow", width=10, heigh=1, activebackground = "white", font=('times',10,'bold'))
        breakOut.place(x=355, y=235)
        
        #PEMANGGILAN FUNGSI WAKTU DAN SENSOR JARAK AGAR LOOPING PADA MAINLOOP GUI
        tick()
        rfid_click()
        
        

#CLASS UNTUK HALAMAN KEDUA DARI GUI
class Register(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        
        #CHECK FILE HAARCASCADE UNTUK METODE RECOGNITION
        def check_haarcascadefile():
            exists = os.path.isfile("haarcascade_frontalface_default.xml")
            if exists:
                pass
            else:
                mess._show(title='Warning', message='File Cascade Hilang')
        
        #MENGECEK ADANYA DIREKTORI DATASET
        def assure_path_exists(path):
            dir = os.path.dirname(path)
            if not os.path.exists(dir):
                os.makedirs(dir)
        
        #LOOPING WAKTU
        def tick():
            time_string = time.strftime('%H:%M:%S')
            clock.config(text=time_string)
            clock.after(200,tick)
        
        #VARIABLE PASSWORD UNTUK DAFTAR BARU
        global key
        key = ''
        
        #FUNGSI UNTUK PENGECEKAN PASSWORD SAAT REGISTER USER
        def psw():
            assure_path_exists("TrainingImageLabel/")
            exists1 = os.path.isfile("TrainingImageLabel/psd.txt")
            if exists1:
                tf = open("TrainingImageLabel/psd.txt", "r")
                key = tf.read()
            else:
                new_pas = tsd.askstring('Password lama tidak tersedia', 'Masukkan Password baru untuk akses', show='*')
                if new_pas == None:
                    mess._show(title='Warning', message='Masukkan Password dengan benar')
                else:
                    tf = open("TrainingImageLabel/psd.txt", "w")
                    tf.write(new_pas)
                    mess._show(title='Password Terdaftar', message='Password Berhasil Didaftarkan')
                    return
            password = tsd.askstring('Password', 'Masukkan Password', show='*')
            
            #SAAT PASSWORD BENAR MAKA AKAN MEMANGGIL FUNGSI TRAIN IMAGES
            if (password == key):
                TrainImages()
            elif (password == None):
                pass
            else:
                mess._show(title='Warning', message='Password Salah')
        
        #FUNGSI UNTUK CLEAR TEXT BOX
        def clear():
            txt.delete(0, 'end')

        def clear2():
            txt2.delete(0, 'end')
            
        def clear3():
            txt3.delete(0, 'end')
            
        def clear4():
            txt4.delete(0, 'end')
        
        #FUNGSI UNTUK MENGAMBIL GAMBAR DAN LABEL GAMBAR
        def getImagesAndLabels(path):
            imagePaths = [os.path.join(path, f) for f in os.listdir(path)]
            faces = []
            Ids = []
            for imagePath in imagePaths:
                pilImage = Image.open(imagePath).convert('L')
                imageNp = np.array(pilImage, 'uint8')
                ID = int(os.path.split(imagePath)[-1].split(".")[1])
                faces.append(imageNp)
                Ids.append(ID)
            return faces, Ids

        #FUNGSI PENGAMBILAN WAJAH
        def TakeImages():
            check_haarcascadefile()
            columns = ['SERIAL NO.', '', 'ID', '', 'NAME', '', 'kelas', '', 'UID']
            assure_path_exists("DataPegawai/")
            assure_path_exists("TrainingImage/")
            serial = 0
            
            #MENGECEK DATA PEGAWAI CSV
            exists = os.path.isfile("DataPegawai/DataPegawai.csv")
            if exists:
                with open("DataPegawai/DataPegawai.csv", 'r') as csvFile1:
                    reader1 = csv.reader(csvFile1)
                    for l in reader1:
                        serial = serial + 1
                csvFile1.close()
            else:
                with open("DataPegawai/DataPegawai.csv", 'a+') as csvFile1:
                    writer = csv.writer(csvFile1)
                    writer.writerow(columns)
                    serial = 1
                csvFile1.close()
            
            #MENGAMBIL DATA DARI ENTRY BOX REGISTER
            Id = (txt.get())
            name = (txt2.get())
            kelas = (txt3.get())
            uid = (txt4.get())
            if ((name.isalpha()) or (' ' in name)):
                cam = cv2.VideoCapture(2)
                harcascadePath = "haarcascade_frontalface_default.xml"
                detector = cv2.CascadeClassifier(harcascadePath)
                sampleNum = 0
                while (True):
                    ret, img = cam.read()
                    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                    faces = detector.detectMultiScale(gray, 1.3, 5)
                    for (x, y, w, h) in faces:
                        cv2.rectangle(img, (x, y), (x + w, y + h), (255, 0, 0), 2)
                        sampleNum = sampleNum + 1
                        cv2.imwrite("TrainingImage/ " + name + "." + str(serial) + "." + Id + '.' + str(sampleNum) + ".jpg",gray[y:y + h, x:x + w])
                        imS = cv2.resize(img, (640, 480))
                        #cv2.moveWindow('daftar', 300, 140)
                        cv2.imshow('daftar', imS)
                    
                    #TOMBOL INTERUPSI SAAT PENGAMBILAN DATA WAJAH (Q PADA KEYBOARD)
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break
                    
                    #MENENTUKAN JUMLAH SAMPLING YANG AKAN DI TRAIN PADA DATASET (PER USER)
                    elif sampleNum >=  10:
                        break
                cam.release()
                cv2.destroyAllWindows()
                
                row = [serial, '', Id, '', name, '', kelas, '', uid]
                
                #RECORD USER INTO DATABASE
                mysqldb=mysql.connector.connect(host="localhost",user="pens",password="pens",database="dataset") 
                mycursor=mysqldb.cursor()
                if(mycursor):
                    query = "insert into user_baru (id,serial,nama,kelas,rfid_uid) values(%s,%s,%s,%s,%s)"
                    mycursor.execute(query,[serial,Id,name,kelas,uid])  
                    mysqldb.commit()
                else:
                    mysqldb.rollback()
                mysqldb.close()
                
                #RECORD USER INTO DATA PEGAWAI CSV
                with open('DataPegawai/DataPegawai.csv', 'a+') as csvFile:
                    writer = csv.writer(csvFile)
                    writer.writerow(row)
                csvFile.close()
                
                res = "Wajah Terdaftar untuk ID"
                res1 = Id
                message1.configure(text=res)
                message2.configure(text=res1)
            else:
                if (name.isalpha() == False):
                    res = "Data diatas masih kosong"
                    res1 = "Silahkan isi data"
                    message1.configure(text=res)
                    message2.configure(text=res1)

        #FUNGSI UNTUK TRAINING WAJAH
        def TrainImages():
            check_haarcascadefile()
            assure_path_exists("TrainingImageLabel/")
            recognizer = cv2.face_LBPHFaceRecognizer.create()
            harcascadePath = "haarcascade_frontalface_default.xml"
            detector = cv2.CascadeClassifier(harcascadePath)
            faces, ID = getImagesAndLabels("TrainingImage")
            try:
                recognizer.train(faces, np.array(ID))
            except:
                mess._show(title='Warning', message='Isikan ID dan Nama User Dahulu')
                return
            recognizer.save("TrainingImageLabel/Trainner.yml")
            res = "Wajah Berhasil Terdaftar"
            res1 = "Terima Kasih"
            message1.configure(text=res)
            message2.configure(text=res1)
        
        
        ### FRAME GUI CONFIG ###
        framebg = tk.Frame(self, bg="#081312")
        framebg.place(relx=0., rely=0, relwidth=1, relheight=1)
        
        frame1 = tk.Frame(self, bg="#5bcbfa")
        frame1.place(relx=0.016, rely=0.17, relwidth=0.55, relheight=0.80)

        frame2 = tk.Frame(self, bg="#5bcbfa")
        frame2.place(relx=0.60, rely=0.17, relwidth=0.38, relheight=0.80)

        frame3 = tk.Frame(self, bg="#c4c6ce")
        frame3.place(relx=0, rely=0.07, relwidth=1, relheight=0.07)

        frame4 = tk.Frame(self, bg="#c4c6ce")
        frame4.place(relx=0, rely=0, relwidth=1, relheight=0.07)
        
        ts = time.time()
        date = datetime.datetime.fromtimestamp(ts).strftime('%d-%m-%Y')
        day,month,year=date.split("-")

        mont={'01':'Januari',
              '02':'Februari',
              '03':'Maret',
              '04':'April',
              '05':'Mei',
              '06':'Juni',
              '07':'Juli',
              '08':'Agustus',
              '09':'September',
              '10':'Oktober',
              '11':'November',
              '12':'Desember'
              }

        datef = tk.Label(frame4, text = day+"-"+mont[month]+"-"+year, fg="orange",bg="#081312" ,width=40 ,height=1, font=('times', 12, ' bold '))
        datef.pack(fill='both',expand=1)
        
        clock = tk.Label(frame3,fg="orange",bg="#081312" ,width=30 ,height=1,font=('times', 12, ' bold '))
        clock.pack(fill='both',expand=1)
        tick()
        
        
        ### LABEL AND MESSAGE ###
        lbl_kamera = tk.Label(frame2, text="Face Recognition", fg="black", bg="#35e541", font=('times', 11, ' bold ') )
        lbl_kamera.place(relx=0, rely=0, relwidth=1)

        lbl_absensi = tk.Label(frame1, text="Form Pendaftaran", fg="black", bg="#35e541", font=('times', 11, ' bold ') )
        lbl_absensi.place(relx=0, rely=0, relwidth=1)

        message1 = tk.Label(frame2, text="Hadapkan Wajah ke Kamera" ,bg="white" ,fg="black"  ,width=24 ,height=1, activebackground = "yellow" ,font=('times', 10, ' bold '))
        message1.place(x=5, y=140)
        
        message2 = tk.Label(frame2, text="Saat Kamera Menyala" ,bg="white" ,fg="black"  ,width=24 ,height=1, activebackground = "yellow" ,font=('times', 10, ' bold '))
        message2.place(x=5, y=165)


        ### BUTTON ###
        button1 = ttk.Button(self, text ="Absensi", command = lambda : controller.show_frame(StartPage))
        button1.place(relx=0.05, rely=0.03, relwidth=0.25, relheigh=0.1)

        clearButton = tk.Button(frame1, text="Bersihkan", command=clear  ,fg="black"  ,bg="#ea2a2a"  ,width=8 ,activebackground = "white" ,font=('times', 7, ' bold '))
        clearButton.place(x=190, y=38)
        
        clearButton2 = tk.Button(frame1, text="Bersihkan", command=clear2  ,fg="black"  ,bg="#ea2a2a"  ,width=8 , activebackground = "white" ,font=('times', 7, ' bold '))
        clearButton2.place(x=190, y=78)
        
        clearButton3 = tk.Button(frame1, text="Bersihkan", command=clear3  ,fg="black"  ,bg="#ea2a2a"  ,width=8 , activebackground = "white" ,font=('times', 7, ' bold '))
        clearButton3.place(x=190, y=118)
        
        clearButton4 = tk.Button(frame1, text="Bersihkan", command=clear4  ,fg="black"  ,bg="#ea2a2a"  ,width=8 , activebackground = "white" ,font=('times', 7, ' bold '))
        clearButton4.place(x=190, y=158)
        
        takeImg = tk.Button(frame1, text="Daftarkan Wajah", command=TakeImages )
        takeImg.place(relx=0.05, rely=0.87, relwidth=0.9, relheigh=0.12)
        
        trainImg = tk.Button(frame2, text="Train Images", command=psw )
        trainImg.place(relx=0.05, rely=0.87, relwidth=0.9, relheigh=0.12)


        ### ENTRY BOX ###
        lbl = tk.Label(frame1, text="Masukkan ID",width=12 ,height=1 ,fg="black" ,bg="#5bcbfa" ,font=('times', 9, 'bold'))
        lbl.place(x=10, y=22)

        txt = tk.Entry(frame1,width=25 ,fg="black",font=('times', 10, ' bold '))
        txt.place(x=10, y=40)

        lbl2 = tk.Label(frame1, text="Masukan Nama",width=13 ,height=1 ,fg="black" ,bg="#5bcbfa" ,font=('times', 9, 'bold'))
        lbl2.place(x=10, y=62)

        txt2 = tk.Entry(frame1,width=25 ,fg="black",font=('times', 10, ' bold ')  )
        txt2.place(x=10, y=80)

        lbl3 = tk.Label(frame1, text="Kelas",width=6  ,fg="black"  ,bg="#5bcbfa" ,font=('times', 9, ' bold '))
        lbl3.place(x=10, y=102)

        txt3 = tk.Entry(frame1,width=25 ,fg="black",font=('times', 10, 'bold')  )
        txt3.place(x=10, y=120)
        
        lbl4 = tk.Label(frame1, text="RFID UID",width=9  ,fg="black"  ,bg="#5bcbfa" ,font=('times', 9, ' bold '))
        lbl4.place(x=10, y=142)
        
        txt4 = tk.Entry(frame1,width=25 ,fg="black",font=('times', 10, 'bold')  )
        txt4.place(x=10, y=160)

app = tkinterApp()
app.mainloop()

### PENS 2019 ###
### TA-ku ###