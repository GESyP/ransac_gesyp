import ransac_gesyp.clasificacion_puntos, ransac_gesyp.ransac
import os
import shutil

centroid_file = os.path.abspath("ransac_gesyp/centroid_file.csv")
dir_points = os.path.abspath("cloud")

columns = ["ID_Tree"]
columns.append('Ransac Radius Mean')
columns.append('Ransac Radius Std')
columns.append('Caliper DBH')
columns.append('Diameter error')
columns.append('Total points')
columns.append('% Points taken')



ransac_gesyp.clasificacion_puntos.classification_points(centroid_file,dir_points,0.5)

ransac_gesyp.ransac.ransac_call(100,columns, 0.5, 0.05)

shutil.rmtree("backup")

