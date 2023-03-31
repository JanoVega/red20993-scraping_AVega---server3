import csv
import numpy as np
import os
import pandas as pd
import gc

def new_csv(file_name):
    """  Reescrive un csv si existe, abre uno nuevo si no."""
    try:
        csv_jobs = open(file_name+'.csv', 'wt+', encoding='utf-8')
        writer = csv.writer(csv_jobs)

        cvs_row = [ 'concepto',\
                    'categoria',\
                    'titulo',\
                    'cuerpo',\
                    'fecha',\
                    'ubicacion',\
                    'modalidad',\
                    'jornada',\
                    'inclusividad',\
                    'salario',\
                    'publicador',\
                    'etiquetas',\
                    'url',\
                    'pagina_web',
                    ]

        # extras : información que podría ser útil, 
        # contenida en hastags/badges/etiquetas

        writer.writerow(cvs_row)
        """csv_config contiene el nombre del archivo"""
        np.save('cvs_config',np.array([file_name]))       
    finally:         
        # cierra el csv
        csv_jobs.close()

def save_to_csv(csv_row):
    """ Escribe una columna en el csv"""
    csv_row=[csv_item for csv_item in csv_row]
    file_name=np.load('cvs_config.npy')[0]
    try:
        # abre el csv 
        csv_jobs= open(file_name+'.csv', 'a+', encoding='utf-8')
        writer = csv.writer(csv_jobs)
        writer.writerow(csv_row)       
    finally:        
        # cierra el csv
        csv_jobs.close()
        gc.collect()

def create_failed_links_csv():
    """ Genera un csv para guardar links de 
    ofertas que no se pudieron extraer"""
    try:
        csv_jobs = open('failed_links.csv', 'wt+', encoding='utf-8')
        writer = csv.writer(csv_jobs)
        csv_row = ['Sitio','Ítem','Link' ]
        writer.writerow(csv_row)   
    finally:         
        # cierra el csv
        csv_jobs.close()

def save_to_failed_links_csv(csv_row):
    """ Guarda una columna en el csv para los 
    links que fallaron"""
    try:
        # abre el csv 
        csv_jobs= open('failed_links.csv', 'a+', encoding='utf-8')
        writer = csv.writer(csv_jobs)
        writer.writerow(csv_row)       
    finally:        
        # cierra el csv
        csv_jobs.close()
        gc.collect()


######### seguir enesto
# df.loc[(df.loc[:, 'pagina_web'] == 'trabajando')].iloc[1,:]
# guardar fecha -> link 
# pasar a lista

def create_urls_csv():
    """ Genera un csv para guardar url y 
    no volver a sobreescribir datos"""
    try:
        #csv_row = site date url
        file_name = 'last_urls'
        file_path = os.getcwd()
        csv_ = open(file_path +'//'+file_name+'.csv', 'w+', encoding='utf-8')
        writer = csv.writer(csv_)
        csv_row = ['sitio',\
                   'fecha',\
                   'concepto',\
                   'url',
                   ]
        writer.writerow(csv_row)   
    finally:         
        # cierra el csv
        csv_.close()   

def create_dates_csv():
    """ Genera un csv para guardar fechas y 
    no volver a sobreescribir datos"""
    try:
        #csv_row = site date 
        file_name = 'dates'
        file_path = os.getcwd()
        csv_ = open(file_path +'//'+file_name+'.csv', 'w+', encoding='utf-8')
        writer = csv.writer(csv_)
        csv_row = ['sitio',\
                   'fecha',\
                   'concepto',\
                   ]
        writer.writerow(csv_row)   
    finally:         
        # cierra el csv
        csv_.close()     

def save_urls(csv_row):
    """ Guarda urls en la ultima fecha de busqueda  
    para no volver a sobreescribir datos"""
    try:
        #csv_row = site date  url
        file_name = 'last_urls'
        file_path = os.getcwd()
        csv_ = open(file_path +'//'+file_name+'.csv', 'a+', encoding='utf-8')
        writer = csv.writer(csv_)
        writer.writerow(csv_row)   
    finally:         
        # cierra el csv
        csv_.close()
        gc.collect()   

def save_date(csv_row):
    """ guarda fechas de los sitios"""
    try:
        #csv_row = site date url
        file_name = 'dates'
        file_path = os.getcwd()
        csv_ = open(file_path +'//'+file_name+'.csv', 'a+', encoding='utf-8')
        writer = csv.writer(csv_)
        writer.writerow(csv_row)   
    finally:         
        # cierra el csv
        csv_.close()
        gc.collect()   

def load_date(site, keyword):
    """Carga la ultima fecha"""
    df = pd.read_csv(r'dates.csv', encoding='utf-8')
    last_date = df.loc[(df.loc[:, 'sitio'] == site)]\
                    .loc[(df.loc[:, 'concepto'] == keyword)]\
                    .fecha.iloc[-1]
    return last_date   

def load_url(site, keyword, last_date):
    """Carga las urls de la ultima fecha"""
    df = pd.read_csv(r'last_urls.csv', encoding='utf-8')
    return list(df.loc[(df.loc[:,'sitio'] == site)]\
                    .loc[(df.loc[:,'fecha'] == last_date)]\
                    .loc[(df.loc[:,'concepto'] == keyword)]\
                    .url )
#%%
def new_check_csv(file_name):
    """ Reescrive un csv si existe, crea uno nuevo si no.
        La fecha puede causar problemas la hora de realizar la comparacion
    """
    try:
        csv_jobs = open(file_name+'.csv', 'wt+', encoding='utf-8')
        writer = csv.writer(csv_jobs)
        cvs_row = [ 'concepto',\
                    'categoria',\
                    'titulo',\
                    'cuerpo',\
                    #'fecha',\
                    'ubicacion',\
                    'modalidad',\
                    'jornada',\
                    'inclusividad',\
                    'salario',\
                    'publicador',\
                    'etiquetas',\
                    'url',\
                    'pagina_web',
                    ]
        writer.writerow(cvs_row) 
    finally:         
        # cierra el csv
        csv_jobs.close()


def save_to_check_csv(csv_row):
    """ Escribe una columna en el csv"""
    csv_row=[csv_item for csv_item in csv_row]
    file_name='check'
    try:
        # abre el csv 
        csv_jobs= open(file_name+'.csv', 'a+', encoding='utf-8')
        writer = csv.writer(csv_jobs)
        writer.writerow(csv_row)       
    finally:        
        # cierra el csv
        csv_jobs.close()
        gc.collect()
    


