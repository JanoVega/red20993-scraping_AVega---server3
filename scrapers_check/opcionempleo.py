"""
Version para realizar chequeo en el cambio de la pagina,

se el quita el ciclo entre las paginas
"""

import time
import numpy as np
import re
import gc
import os

from bs4 import BeautifulSoup 
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

from utils.csv_utils import save_to_check_csv

# ubicacion del ejecutable para chromedriver
path = os.getcwd() + '/chromedriver'
#path = '/snap/bin/chromium.chromedriver'
service = Service(executable_path=path)

def get_page_safe_dynamic(url):
    """
    Método para extraer el html de las páginas con los resultados, 
    chequea si hay un error de conexión.

    Parameters
    ----------    
    url : str
        dirección de la oferta

    Returns
    -------
    BeautifulSoup object.
    """  
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    driver = webdriver.Chrome(service=service, options=chrome_options)        
    try:
        driver.get(url)
        html = driver.page_source
    except ConnectionError:
        time.sleep(3)
        driver.get(url)
        html = driver.page_source
    finally:   
        driver.quit()
    return BeautifulSoup(html,'html.parser')    

def get_page_dynamic(url):
    """
    Método para extraer el html de las páginas con los resultados.

    Parameters
    ----------
    driver : selenium.webdriver
        instancia del navegador

    url : str
        dirección de la oferta

    Returns
    -------
    BeautifulSoup object.
    """
    try:
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        driver = webdriver.Chrome(service=service, options=chrome_options)        
        driver.get(url)
        html = driver.page_source
    except Exception as e: 
        print(e)
    finally:
       driver.quit()
    return BeautifulSoup(html,'html.parser')

def results_check(search_keyword):
    
    bs = get_page_safe_dynamic('https://www.opcionempleo.cl/buscar/empleos?s='\
                       +search_keyword+'&l=Chile')
    assert bs.find('h1').text != 'No se encontraron resultados',\
                    'No se encontraron resultados'
    num_results = re.sub('[\D]' ,'', \
                     bs.find('p',{'class','col col-xs-12 col-m-4 col-m-r cr'})\
                     .text.split()[0])
    num_results = int(num_results)     
    assert num_results != 0, 'No se encontraron resultados'

    assert bs.find_all('article',{'class','job clicky'})!=[], 'no se pudo acceder a los resultados'                   

    boton_sgt_pgn = bs.find_all('a',{'class','btn btn-r btn-primary-inverted'})
    assert boton_sgt_pgn!=[], 'boton siguiente pagina no encontrado'   

def results(search_keyword):
    """
    Método que recorre las páginas con los resultados

    Parameters
    ----------
    search_keyword : str
        Item para buscar en la página.

    Returns
    -------
    None
    """    
    # extraígo el html
    bs = get_page_safe_dynamic('https://www.opcionempleo.cl/buscar/empleos?s='\
                       +search_keyword+'&l=Chile')
    assert bs.find('h1').text != 'No se encontraron resultados',\
                    'No se encontraron resultados'
    
    num_results = re.sub('[\D]' ,'', \
                     bs.find('p',{'class','col col-xs-12 col-m-4 col-m-r cr'})\
                     .text.split()[0])
    num_results = int(num_results)     
    assert num_results != 0, 'No se encontraron resultados'

    # lista con links  
    results = [ tag.a['href'] for tag in bs.find_all('article',{'class','job clicky'})]    
        
    n = 0    

    # se raspan las urls
    for index, result_url in enumerate(results):
        time.sleep(np.random.uniform(-0.05,0.05)**2)

        try:
            url ='https://www.opcionempleo.cl'+result_url
            scrape(url, search_keyword,True)  
            n += 1
        except:
            continue
        
    informe_row = 'opcionempleo: ' + str(n)+'/'+str(len(results)) 
    
    try:
        return informe_row
    finally:
        gc.collect()

def scrape(url, search_keyword, save_row):
    """
    Método que extrae y guarda la información de la página de una
     oferta

    Parameters
    ----------
    url : str
        dirección web de la oferta.

    search_keyword : str
        Item buscado.

    Returns
    -------
    None
    """
    bs = get_page_dynamic(url)
    
    # título
    try:
        title = bs.find('h1').text
    except:
        title = ''
        
    # cuerpo
    try:
        body =  body_cleanser(bs.find('section',{'class','content'}))
    except:
        body = ''

    # categoria
    category = ''
    
    # modalidad
    modalidad = ''
    
    # inclusividad
    inclusividad = ''
    
    location = ''
    jornada = ''
    salario = ''
    
    for tag in bs.find('ul',{'class','details'}).find_all('li'):
        
        # ubicacion
        try:
            if tag.find('use')['xlink:href']=='#icon-location':
                location = tag.find('span').text
        except:
            location='' 
        
        # jornada
        try:  
            if tag.find('use')['xlink:href']=='#icon-duration':
                jornada = tag.text.strip(' ').strip('\n').strip('\n').strip()
        except:
            jornada=''
            
        # salario
        try:
            if tag.find('use')['xlink:href']=='#icon-money':
                salario = re.sub('[\s]',' ', tag.text).strip()
        except :
            salario = ''

    # publicador
    try:
        publicador = re.sub( '[\s]',' ', bs.find('p',{'class', 'company'}).text.strip())
    except:
        publicador = ''

    # extras
    try:
        etiquetas = [re.sub( '[\s]',' ',tag.text).strip()\
                     +'; ' for tag in bs.find('ul',{'class','details'})\
                         .find_all('li')]
    except:
        etiquetas = []
    etiquetas = ''.join(np.unique(etiquetas))
     
     
    csv_row = [ str(search_keyword),\
                category.strip('\n'),\
                title.strip('\n'),\
                body.strip('\n'),\
                #date,\
                location,\
                modalidad,\
                jornada,\
                inclusividad,\
                salario,\
                publicador,\
                etiquetas,\
                url,\
                'opcionempleo',
                ] 
           
    if save_row == True:
        save_to_check_csv(csv_row)
    return(csv_row)  
    # despues de guardar la info se libera ram
    gc.collect()

def body_cleanser(obj):
    """
    Método para limpiar un poco los elementos html del cuerpo de una oferta

    Parameters
    ----------
    obj : tag
        objeto que contiene una o más partes que forman el cuerpo de la 
        oferta.

    Returns
    -------
    body : str
        cuerpo de la oferta ligeramente preprocesado.
    """
    body = ''
    v = obj.text.split('\r')
    for content in v :
        body += content
    return body 