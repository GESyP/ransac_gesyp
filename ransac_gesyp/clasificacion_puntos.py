import pandas as pd
import numpy as np
import glob
import sys
import os
import math
from tkinter import *
from tkinter import messagebox

BACKUP_DIR = "backup/"


def classification_points(centroid_file, dir_points,sigma_mult):

    #Comprobación de que el fichero de puntos existe previamente
    if os.path.isdir(dir_points) == False:
        print(f"Folder {dir_points} doesn't exists")
        sys.exit(0)
    
    if centroid_file[-3:] != "csv":
        print("Centroid file isn't a CSV file ", centroid_file)
        sys.exit(1)

    if not os.path.isfile(centroid_file):
        print(f"File {centroid_file} doesn't exists")
        sys.exit(2)
    
    if not os.path.isdir(BACKUP_DIR):
        os.mkdir(BACKUP_DIR)

    #Lectura de todos los archivos csv existentes del directorio en el que se encuentran los puntos
    if dir_points[:-1] == "/":
        path = dir_points + "*.csv"
    else:
        path = dir_points + "/*.csv"
    files_list = glob.glob(path)

    #Lectura de los datos del csv en el que se almacenan los centroides y el diametro real de los arboles
    centr_reader = pd.read_csv(centroid_file, delimiter=None)
    max_x = centr_reader['X'].max()
    min_x = centr_reader['X'].min()
    max_y = centr_reader['Y'].max()
    min_y = centr_reader['Y'].min()
    caliper = centr_reader['Caliper_DBH'].to_numpy(dtype=np.float64)
    tree_ids = centr_reader['Tree'].to_numpy()
    centr_reader = centr_reader[['X','Y']].to_numpy(dtype=np.float64)

    
    capture_statistics = []

    root = Tk()
    frame = Frame(root, width=300, height=300)
    frame.pack()
    centr_len= centr_reader.shape[0]

    for num,i in enumerate(range(centr_reader.shape[0])):
        capture_points = []
        capture_dist = []
        first_intr = False
        #print(f'Centro: ({centr_reader[i,0]}, {centr_reader[i,1]})')

        for arch in files_list:

            points = pd.read_csv(arch,header=0,skiprows=0, sep=None, engine='python')
            points = points[['//X','Y']].to_numpy(dtype=np.float64)
            if len(np.where(np.logical_and(points[:,0] < min_x, points[:,0] > max_x))[0]) > 0 or len(np.where(np.logical_and(points[:,1] < min_y, points[:,1] > max_y))[0]) > 0:
                messagebox.showerror("POINTS OUT OF BOUNDS", "The csv clouds have points out of the established range")
                return
            

            dist = ((centr_reader[i,0]-points[:,0])**2) + ((centr_reader[i,1]-points[:,1])**2)
            dist = np.sqrt(dist)
            points_list = np.where(np.logical_and(dist < 1, dist !=0))[0]

            if len(points_list) > 0 and not first_intr:
                capture_points.append(centr_reader[i,:])
                capture_dist.append(caliper[i])
                first_intr = True

            for elem in points_list:
                capture_points.append(points[elem])
                capture_dist.append(dist[elem])
            
            

            
            
            #print(f'Num possible outliers: {inliers} Num points:{len(capture_points)}')

        
        if len(capture_points) > 10:
            processed_per = (num/centr_len)*100
            #print("Tree",tree_ids[i], "Number of points",len(capture_points))
            print_text = f'Classified {round(processed_per, 2)}% of the trees'
        
            lab = Label(frame, text=print_text)
            lab.pack()
            root.update()
            for widget in frame.winfo_children():
                widget.destroy()
            df = pd.DataFrame(data=capture_points,columns=["X","Y"], dtype=np.float64)
            df["Tree_id"] = tree_ids[i]
            df["Distance"] = capture_dist
            dist_std = np.array(capture_dist)[1:].std()
            dist_mean = np.array(capture_dist)[1:].mean()
            dist_int_min = dist_mean - (sigma_mult * dist_std)
            dist_int_max = dist_mean + (sigma_mult * dist_std)

            pos_inliers = np.array(capture_dist)
            inliers = len(capture_dist) - len(np.where(np.logical_or(pos_inliers < dist_int_min, pos_inliers > dist_int_max))[0])
            if inliers != 0:
                w = inliers/len(capture_points)
                if w != 1.0:
                    k_99=(math.log10(1-0.99))/(math.log10(1-(w**3)))
                else:
                    k_99 = 1
                
                statistics = [tree_ids[i],len(capture_points),dist_int_min, dist_int_max, inliers, w, k_99]
            capture_statistics.append(statistics)
            file_name= BACKUP_DIR + "points_tree"+str(tree_ids[i])+"_points.csv"
            df.to_csv(file_name,sep=";",columns=['Tree_id','X','Y',"Distance"], index=False)
    
    columns = ['Tree_ID','Num_points','Min Int Conf', 'Max Int Conf','Num inliers',"w","It 99%"]
    writer = pd.DataFrame(data=capture_statistics,columns=columns, dtype=np.float64)
    writer.to_csv("tree_statistics.csv",sep=";", columns=columns, index=False)


    