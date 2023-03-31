# -*- coding: utf-8 -*-
"""
Para chequear:
    
    raspar "jefe" primera pagina
    guardar info en csv especial
    
    comparar el raspado nuevo a traves de los links de los post anteriores 
    
"""

import csv
import gc
import time
import re

import pandas as pd

from scrapers_check import chiletrabajos
from scrapers_check import opcionempleo
from scrapers_check import computrabajo
from scrapers_check import elmercurio
from scrapers_check import laborum
from scrapers_check import indeed
from scrapers_check import trabajando
        
from utils.date_utils import get_date
from utils.csv_utils import new_check_csv    

def csv_fill(sites):
    """
    Descarga nuevas ofertas 
    
    Parameters
    ----------
    sites : 
        para raspar cada sitio

    Returns
    -------
    """

    date = get_date('hoy')
    date = re.sub('/', '.', date)
    f = open('check_scrap_'+date+'.txt', 'w') 
    f.write( 'datos nuevos en el csv / resultados según la página'+ '\n' )
    f.close()
    
    sites_dict={'chiletrabajos':chiletrabajos ,\
                'opcionempleo':opcionempleo,\
                'computrabajo':computrabajo,\
                'elmercurio':elmercurio,\
                'laborum':laborum,\
                'indeed':indeed,\
                'trabajando':trabajando
                  }
    search_keyword = 'jefe'
    check_row = date + ':' + '\n'

    for site in sites:
         try:
             check_row += '    '+sites_dict[site].results(search_keyword)+'\n'
         except AssertionError as e:
             check_row += '    '+site +': '+ str(e) +'\n'
         except Exception as e:
             check_row += '    '+site +': '+ str(e) +'\n'
         time.sleep(5)
             
    with open('check_scrap_'+date+'.txt', 'a') as f:
         f.write( check_row )
         f.write('-------------------------------------------------'+'\n')
             
def check_is_valid(csv_row):
    """
    Parameters
    ----------
    csv_row : List
        Lista con los datos raspados de una oferta.

    Returns
    -------
    Revisa si el cuerpo/titulo/publicador están vacios.
    """
    N = [2,3,10]
    is_valid = True
    for n in N:
        if csv_row[n]=='':
            is_valid = False
            
    return is_valid
    
    
    

def csv_check(sites):
    """
    Revisa que para las ofertas guardadas en el csv, los scrappers puedan 
     extraer la misma información.

    Returns
    -------
    None.
    """
    new_check_csv('check')
    csv_fill(sites)
    search_keyword = 'jefe'
    sites_dict={'chiletrabajos':chiletrabajos ,\
                'opcionempleo':opcionempleo,\
                'computrabajo':computrabajo,\
                'elmercurio':elmercurio,\
                'laborum':laborum,\
                'indeed':indeed,\
                'trabajando':trabajando
                  }
    
    cvs_row = ['concepto',\
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
    
    df = pd.read_csv(r'check.csv', encoding='utf-8')   
  
    date = get_date('hoy')    
    date = re.sub('/', '.', date)
    f = open('check_informe_'+date+'.txt', 'w') 
    f.close()       
    #%%
    for index, site in enumerate(sites):
        oferts = df.loc[df.pagina_web==str(site)]
        num_links = len(oferts)
        aux = min(num_links,15)
        
        fila_oferta = [0 for n in range(13)]
        for n in range(1,aux+1):
            pre_B = oferts.iloc[-n]
            pros_B = [re.sub( '[\s]', '', str(b)) for b in pre_B]
            pross_B = [re.sub( 'nan', '', b) for b in pros_B]

            for n,string in enumerate(pross_B):
                fila_oferta[n] += (string != '')
       
        check_row = str(site) +' '+ date + ' :'+'\n'
        
        try:
            sites_dict[site].results_check(search_keyword)
            check_row += '    '+'no hay problema con los resultados'+'\n'
        except Exception as e:    
            check_row += str(e) + '\n'
        for n in [2,3,-4]:
            check_row += '    '+str(cvs_row[n]) +': '+str(fila_oferta[n]) +'/'+str(aux)+'\n'  
        with open('check_informe_'+date+'.txt', 'a') as f:
            f.write( check_row )
            f.write('-------------------------------------------------'+'\n')
       
            
    return 0
    gc.collect()





def get_not_0():
    date = get_date('hoy')    
    date = re.sub('/', '.', date)
    try:
        with open('check_informe_'+date+'.txt') as f:
            lines = f.readlines()
    except:
        date = get_date('ayer')    
        date = re.sub('/', '.', date)  
        with open('check_informe_'+date+'.txt') as f:
            lines = f.readlines()     
    # los sitios ocupan 5 lineas cada uno
    N = int(len(lines)/6)
    not_0 = []
    #guardar los indices en donde si se pudo raspar
    for n in range(N):
        titulo = lines[6*n+2]
        try:
            titulo = int(re.sub('[\s\D]', '', titulo.split('/')[0]))
        except:
            titulo = 0
        cuerpo = lines[6*n+3]
        try:
            cuerpo = int(re.sub('[\s\D]', '', cuerpo.split('/')[0]))
        except:
            cuerpo = 0

        if titulo*cuerpo != 0:
            not_0.append(n)
        else:
            # añadir linea al mensaje del mail
            pass
    #mandar email
    return not_0



#%%
# añadir assertions para chequear que se encuentre:
    # el numero de resultados
    # que la lista de resultados no sea vacia si es que hay
    # si hay más de 40 resultados, chequear que haya botones.
    
    
    

#%%

# problema: como puedo chequear si el nombre de la label sigue igual
# si pudiese acceder a la label, sin usar su nombre usaria eso.
# (aunque algo así se hizo con laborum)

# puedo chequear que la busqueda del objeto no sea vacia, y buscar cosas
# que deban si o si estar.

#%%

                # raspar un item, contar las filas que quedan vacias.

                # añadir un check por si el cuerpo está vacíou otros esttan vacios.
                # aañadir un check para las labels de las páginas.
                
                #pre_A = sites_dict[site].scrape(url,'jefe', False)
                #pros_A = [re.sub( '[\s]', '', a) for a in pre_A]
                #pross_A = [re.sub( 'nan', '', a) for a in pros_A]
                
                #check_is_valid(pross_A)
                
                # Esto sólo revisa las ofertas guardadas en el csv, pero,
                # que pasa si dejan de llegar ofertas ??
               
            #






