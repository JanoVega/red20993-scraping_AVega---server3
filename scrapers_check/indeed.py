"""
Version para realizar chequeo en el cambio de la pagina,

se el quita el ciclo entre las paginas
"""


import time
import re
import numpy as np
import os
import gc

from bs4 import BeautifulSoup 
from selenium import webdriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver import ActionChains

from utils.csv_utils import save_to_check_csv

# ubicacion del ejecutable para chromedriver 
path = os.getcwd() + '/chromedriver'
#path = '/snap/bin/chromium.chromedriver'
service = Service(executable_path=path)

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
    chrome_options = Options()
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    #chrome_options.add_argument("--headless")
    driver = webdriver.Chrome(service=service, options=chrome_options)  
    driver.get(url)
    try:
        html = driver.page_source 
    except Exception as e:
        print(e)
    finally:
        driver.quit()
    return BeautifulSoup(html,'html.parser')

def get_page_safe_dynamic(url):
    """
    Método para extraer el html de las páginas con los resultados, 
    chequea si hay un error de conexión.

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
    chrome_options = Options()
    #chrome_options.add_argument("--headless")
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    driver = webdriver.Chrome(service=service, options=chrome_options)      
    try:
        driver.get(url)
        WebDriverWait(driver, 2)
        bait = driver.find_element(By.ID, "indeed-globalnav-logo")
        ActionChains(driver)\
            .move_to_element(bait)\
            .perform()
            
        WebDriverWait(driver, 25).until(EC.presence_of_element_located((By.ID, 'resultsCol')))
        html = driver.page_source
    except ConnectionError:
        time.sleep(3)
        driver.get(url)
        WebDriverWait(driver, 2)
        bait = driver.find_element(By.ID, "indeed-globalnav-logo")
        ActionChains(driver)\
            .move_to_element(bait)\
            .perform()
            
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, 'resultsCol')))
        html = driver.page_source 
    except:
        driver.quit()
        chrome_options = Options()
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        #chrome_options.add_argument("--headless")
        driver = webdriver.Chrome(service=service, options=chrome_options)  
        driver.get(url)
        html = driver.page_source
    finally:
        driver.quit()
    return BeautifulSoup(html,'html.parser')

def results_check(search_keyword):
    bs = get_page_safe_dynamic('https://cl.indeed.com/jobs?q='\
                         + str(search_keyword) +'&sort=date&filter=0')
    assert bs.find_all('div',{'class', 'jobsearch-NoResult-messageHeader'})==[]\
                 ,'La búsqueda empleos de '+\
                  search_keyword+' no ha producido ningún resultado.'     
                  
    num_results =  re.sub('[\D]', '', \
              bs.find('div', {'class' , 'jobsearch-JobCountAndSortPane-jobCount'})\
                  .find('span').text)
    num_results = int(num_results)
    assert num_results != 0, 'No se encontraron resultados' 
    
    assert bs.find_all('div',{'class','job_seen_beacon'})!=[], 'no se pudo acceder a los resultados'

    boton_sgt_pgn = bs.find_all('a', {'class', 'css-13p07ha e8ju0x50'})[-1]
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
    
    """ ajustar esto, para que compruebe correctamente"""



    bs = get_page_safe_dynamic('https://cl.indeed.com/jobs?q='\
                         + str(search_keyword) +'&sort=date&filter=0')


    assert bs.find_all('div',{'class', 'jobsearch-NoResult-messageHeader'})==[]\
                 ,'La búsqueda empleos de '+\
                  search_keyword+' no ha producido ningún resultado.'   

    results = [tag.a['href'] for tag in bs.find_all('div',{'class','job_seen_beacon'})]

    
    num_results =  re.sub('[\D]', '', \
              bs.find('div', {'class' , 'jobsearch-JobCountAndSortPane-jobCount'})\
                  .find('span').text)
    num_results = int(num_results)
    assert num_results != 0, 'No se encontraron resultados' 

    n = 0                                                       
    # raspado
    for index, result_url in enumerate(results):
        time.sleep(np.random.uniform(-0.05,0.05)**2)
        try:
            url = 'https://cl.indeed.com'\
                 + result_url        
            # raspado
            scrape(url, search_keyword,True)   
            n += 1
        except:
            continue      

    informe_row = 'indeed: ' + str(n)+'/'+str(len(results)) 
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
    # fecha de la última vez que se ejecuto el main_scraper con este item
#    try: 
#       resume_date = load_date('indeed', search_keyword)
#    except:
#        resume_date = get_date('hace 999 dias')

    bs = get_page_dynamic(url)
    
    # título
    try:
        title = bs.find('h1').text
    except:
        title
        
    # cuerpo
    try:
        body =  body_cleanser(bs.find('div', {'class', 'jobsearch-jobDescriptionText'}))
    except:
        body = ''
    # categoria   
    category = ''
    
    # modalidad
    modalidad = ''
    
    # inclusividad
    inclusividad =''
    
    # ubicación
    try:
        location = bs.find('div', {'class', 'jobsearch-InlineCompanyRating' \
                                 +' icl-u-xs-mt--xs jobsearch-DesktopSticky'\
                                 +'Container-companyrating'})\
                                 .findNextSibling()\
                                 .text
    except:
        location = ''
    
    # etiquetas donde tengo esa informacion
    divs = bs.find_all('div', {'class', \
    'jobsearch-JobDescriptionSection-sectionItemKey icl-u-textBold'})
        
    jornada = ''
    salario = ''
    publicador = ''
    
    for div in divs:
        # jornada
        try :
            if div.text == 'Tipo de empleo':
                jornada = div.nextSibling.text
        except:
            pass
        try:
        # salario           
            if div.text == 'Salario':
                salario = div.nextSibling.text
        except:
            pass
    # publicador
    try:
        tag = bs.find('div', {'class',\
        'jobsearch-InlineCompanyRating icl-u-xs-mt--xs jobsearch-DesktopStickyContainer-companyrating'})
        publicador = tag.find_all('div')[2].text
    except:
        pass
    # extras
    etiquetas = ''
     
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
                'indeed',
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
