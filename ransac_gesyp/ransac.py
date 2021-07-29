from os import error
import pandas as pd
import glob
import numpy as np
import random
import math
from tkinter import * 
from tkinter import messagebox

from pandas.core import frame

BACKUP_DIR = "backup/"
  
def findCentre(point_1, point_2, point_3):
    np.seterr(divide="ignore", invalid="ignore")
    c = (point_1[0]-point_2[0])**2 + (point_1[1]-point_2[1])**2
    a = (point_2[0]-point_3[0])**2 + (point_2[1]-point_3[1])**2
    b = (point_3[0]-point_1[0])**2 + (point_3[1]-point_1[1])**2
    s = 2*(a*b + b*c + c*a) - (a*a + b*b + c*c) 
    px = (a*(b+c-a)*point_1[0] + b*(c+a-b)*point_2[0] + c*(a+b-c)*point_3[0]) / s
    py = (a*(b+c-a)*point_1[1] + b*(c+a-b)*point_2[1] + c*(a+b-c)*point_3[1]) / s 
    ar = a**0.5
    br = b**0.5
    cr = c**0.5 
    r = ar*br*cr / ((ar+br+cr)*(-ar+br+cr)*(ar-br+cr)*(ar+br-cr))**0.5
    
    #print(f'Centre ({px},{py}), Radius:{r}')


    centre = [px, py]
    
    return centre, r


def ransac(max_iterations, coords, thresh,rad_int_min, rad_int_max):

    max_inliers = 0
    best_rad = 0

    for it in range(max_iterations):
        points = random.sample(range(0,coords.shape[0]-1), 3)
        point_1 = coords[points[0],:]
        point_2 = coords[points[1],:]
        point_3 = coords[points[2],:]

        centre, radius = findCentre(point_1, point_2, point_3)
        dist = ((centre[0] - coords[:,0])**2) + ((centre[1] - coords[:,1])**2)
        dist = np.abs((dist**0.5) - radius)
        inliers = len(np.where(dist <= thresh)[0])
        #print(f'Num of inliers: {inliers} Radius:{radius} Rad_int_min:{rad_int_min} Rad_int_max:{rad_int_max}')
        if max_inliers < inliers and (radius >= rad_int_min and radius <=rad_int_max):
            max_inliers = inliers
            best_rad = radius

    return max_inliers, best_rad
    

def ransac_call(ransac_num, columns, sigma_mult, thresh):

    path = BACKUP_DIR + "*.csv"
    files_list = glob.glob(path)
    if len(files_list) == 0:
        messagebox.showerror('RANSAC Failure', 'RANSAC coudn\'t performed due to lack of archives')
        return
    inform_list=[]
    root = Tk()
    frame = Frame(root, width=300, height=300)
    frame.pack()
    files_list_len= len(files_list)
    

    for num,f in enumerate(files_list):

        df = pd.read_csv(f,sep=";", float_precision="high", dtype=np.float64)
        id_tree = set(df["Tree_id"]).pop()
        rads = df["Distance"].to_numpy(dtype=np.float64)
        coords = df[['X','Y']].to_numpy(dtype=np.float64)
        caliper = rads[0]
        capture_values = []
        capture_rads = []
        capture_values.append(id_tree)
        processed_per  = (num/files_list_len)*100
        
        print_text = f'Processed {round(processed_per, 2)}% of the trees'
        
        lab = Label(frame, text=print_text)
        lab.pack()
        root.update()
        for widget in frame.winfo_children():
            widget.destroy()
        rad_mean = rads[1:].mean()
        rad_std = rads[1:].std()

        rad_int_min = rad_mean - (sigma_mult * rad_std)
        rad_int_max = rad_mean + (sigma_mult * rad_std)

        inliers = rads[1:].shape[0] - len(np.where(np.logical_or(rads[1:] < rad_int_min, rads[1:] > rad_int_max))[0])
        if inliers != 0:
            w = inliers/rads.shape[0]
            if w != 1.0:
                k_99=(math.log10(1-0.99))/(math.log10(1-(w**3)))
            else:
                k_99 = 1
        k_99 = round(k_99)

        

        total_points = coords.shape[0]
        porcentage_points = []
        
        for num_it in range(ransac_num):
            print(f'Tree {id_tree} ransac execution {num_it}')
            max_inliers, best_rad = ransac(k_99, coords, thresh,rad_int_min, rad_int_max)
            #print(f'Max inliers: {max_inliers}')


            capture_rads.append(best_rad)
            porcentage_points.append((max_inliers/total_points)*100)

        #print(f'Capture values:{capture_rads} Porcentage points:{porcentage_points}')
        
        mean = np.array(capture_rads).mean()
        
        std_dev = np.array(capture_rads).std()
        porcentage_mean = np.array(porcentage_points).mean()
        error = abs(caliper - (mean*2))
        
        
        capture_values.append(mean)
        capture_values.append(std_dev)
        
        capture_values.append(caliper)
        capture_values.append(error)
        capture_values.append(total_points)
        capture_values.append(porcentage_mean)
        inform_list.append(capture_values)


    writer = pd.DataFrame(data=inform_list,columns=columns, dtype=np.float64)

    #means = writer['Diameter error'].mean()

    #print("Diameter error mean: ",means)

    messagebox.showinfo("Program finished successfully","RANSAC results found on results.csv")
    writer.to_csv("results.csv",sep=";",columns=columns, index=False)

    return writer
    