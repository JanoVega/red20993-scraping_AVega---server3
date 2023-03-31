"""
Version para realizar chequeo en el cambio de la página,

se el quita el ciclo entre las páginas
"""


import requests
import time
import numpy as np
import re
import gc
import os

from bs4 import BeautifulSoup 
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC


from utils.csv_utils import save_urls
from utils.csv_utils import load_date
from utils.csv_utils import save_to_csv
from utils.csv_utils import load_url
from utils.csv_utils import save_to_failed_links_csv
from utils.date_utils import get_date
from utils.date_utils import is_newer_date
from utils.csv_utils import save_to_check_csv


# ubicacion del ejecutable para chromedriver
path = os.getcwd() + '/chromedriver'
#print(path)
#path = '/snap/bin/chromium.chromedriver'
service = Service(executable_path=path)


def get_page_dynamic(url):
    """
    M�todo para extraer el html de las p�ginas con los resultados.

    Parameters
    ----------
    driver : selenium.webdriver
        instancia del navegador

    url : str
        direcci�n de la oferta

    Returns
    -------
    BeautifulSoup object.
    """
    try:
        chrome_options = Options()
        chrome_options.add_argument("--disable-dev-shm-usage")
        #chrome_options.add_argument("--headless")
        driver = webdriver.Chrome(service=service, options=chrome_options)        
        driver.get(url)
        WebDriverWait(driver, 2)
        html = driver.page_source
    #except Exception as e: 
        #print(e)
    finally:
       driver.close()
    return BeautifulSoup(html,'html.parser')

def get_page_safe_dynamic(url):
    """
    M�todo para extraer el html de las p�ginas con los resultados, 
    chequea si hay un error de conexi�n.

    Parameters
    ----------    
    url : str
        direcci�n de la oferta

    Returns
    -------
    BeautifulSoup object.
    """  
    chrome_options = Options()
    chrome_options.add_argument("--disable-dev-shm-usage")
    #chrome_options.add_argument("--headless")
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    driver = webdriver.Chrome(service=service, options=chrome_options)        
    try:
        driver.get(url)
        WebDriverWait(driver, 3)
        html = driver.page_source
    except ConnectionError:
        time.sleep(3)
        driver.get(url)
        WebDriverWait(driver, 3)
        html = driver.page_source
    finally:   
        driver.close()
    return BeautifulSoup(html,'html.parser')      
    
def results_check(search_keyword):

    bs = get_page_safe_dynamic('https://www.chiletrabajos.cl/encuentra-un-empleo?action=search&order_by=&ord=&within=25&2='\
                 +str(search_keyword)+'&filterSearch=Buscar')
        
    num_results = re.sub('[\D]', '',\
                     bs.find('h2',{'class','font-weight-light'})\
                     .text.split(' ')[0])    
        
    num_results = int(num_results)  
    assert num_results > 0, 'no hay resultados'
      
    assert bs.find_all('div',{'class','job-item with-thumb destacado no-hover'})!=[],'lista de resultados vacia'


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
    bs = get_page_safe_dynamic('https://www.chiletrabajos.cl/encuentra-un-empleo?action=search&order_by=&ord=&within=25&2='\
                 +str(search_keyword)+'&filterSearch=Buscar')
    num_results = re.sub('[\D]', '',\
                     bs.find('h2',{'class','font-weight-light'})\
                     .text.split(' ')[0])
        
    num_results = int(num_results)        
    assert num_results != 0, 'No se encontraron resultados'
    
    #extraígo los links a las publicaciones
    results = [tag.a['href'] for tag in \
               bs.find_all('div',{'class','job-item with-thumb destacado no-hover'})]
    

    n = 0
    for index, result_url in enumerate(results):
        time.sleep(np.random.uniform(-0.05,00.5)**2)

        try:
            url = result_url
            scrape(url, search_keyword,True) 
            n+=1
        except Exception as e:
            print(e)
            continue
        
    informe_row = 'chiletrabajos: ' + str(n)+'/'+str(len(results)) 
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
    save_row: boolean

    Returns
    -------
    None

    """

    # No tener try aqui es intencional    
    bs = get_page_dynamic(url)
    
    # título
    
    try:
        title = bs.find('h1').text
    except:
        title =''
        
    # cuerpo
    try:
        body = body_cleanser(bs.find_all('p',{'class','mb-0'})[1])
    except:
        body = ''
    # etiquetas con la informacion
    td_list = bs.find_all('td')
    td_list = [td.text for td in td_list]  
    
    
    # modalidad
    modalidad = ''
    if  bs.find_all('div',{'class',"beneficios-wrapper mb-4"})!=[]:
        if  bs.find('div',{'class',"beneficios-wrapper mb-4"})\
            .find_all('i',{'class','fas fa-laptop'}) != []:
                
            modalidad = bs.find('div',{'class',"beneficios-wrapper mb-4"})\
                .find_all('i',{'class','fas fa-laptop'})[-1].text    
                
            
    date = ''
    location = ''
    category = ''
    jornada = ''
    salario = ''
    publicador = ''

    for i, td  in enumerate(td_list):
        
        # fecha
        if td == 'Fecha':
            date = td_list[i+1]
            date = date.split()[0].split('-')[2].lstrip('0')+'/'\
                    +date.split()[0].split('-')[1].lstrip('0')\
                    +'/'+date.split()[0].split('-')[0]
       
        # ubicación
        if td == 'Ubicación':
            location = td_list[i+1]
            
        # categoría
        if td == 'Categoría':
            category = re.sub( '[\s]','', td_list[i+1])
        
        # jornada
        if td == 'Tipo':
            jornada = td_list[i+1]
            
        # salario
        if td == 'Salario':
            salario = td_list[i+1]
        
        # publicador
        if td == 'Buscado':
            publicador = re.sub( '[\s]','',td_list[i+1])

    # inclusividad
    inclusividad= 'no' if []==bs.find_all('span',{'class','inclusion'}) else 'si'


    # extras
    try:
        etiquetas = [re.sub( '[\s]',' ',tag.text).strip() + '; ' for tag in\
                     bs.find_all('div',{'class', 'beneficio-title'}) ]
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
                'chiletrabajos',
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