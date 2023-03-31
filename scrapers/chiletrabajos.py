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


# ubicacion del ejecutable para chromedriver
path = os.getcwd() + '/chromedriver'
#print(path)
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
    try:
        chrome_options = Options()
        chrome_options.add_argument("--disable-dev-shm-usage")
        #hrome_options.add_argument("--headless")
        driver = webdriver.Chrome(service=service, options=chrome_options)        
        driver.get(url)
        WebDriverWait(driver, 10)
        html = driver.page_source
    #except Exception as e: 
        #print(e)
    finally:
       driver.close()
    return BeautifulSoup(html,'html.parser')

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
    chrome_options.add_argument("--disable-dev-shm-usage")
    #chrome_options.add_argument("--headless")
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    driver = webdriver.Chrome(service=service, options=chrome_options)        
    try:
        driver.get(url)
        WebDriverWait(driver, 10)
        html = driver.page_source
    except ConnectionError:
        time.sleep(3)
        driver.get(url)
        WebDriverWait(driver, 10)
        html = driver.page_source
    finally:   
        driver.close()
    return BeautifulSoup(html,'html.parser')     

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
    
    meses_dict = {'Enero':'1',\
                  'Febrero':'2',\
                  'Marzo':'3',\
                  'Abril':'4',\
                  'Mayo':'5',\
                  'Junio':'6',\
                  'Julio':'7',\
                  'Agosto':'8',\
                  'Septiembre':'9',\
                  'Octubre':'10',\
                  'Noviembre':'11',\
                  'Diciembre':'12',\
                  }
    
    results_dates = [ tag.i.nextSibling.split('de')[0].strip().lstrip('0')\
                     +'/'+ meses_dict[tag.i.nextSibling.split('de')[1].strip()]\
                     +'/'+ tag.i.nextSibling.split('de')[2].strip()\
                     for tag in bs.find_all('div',{'class','job-item with-thumb destacado no-hover'})]
        
    results_per_page = len(results)
      
    # resto de páginas
    # chequea si hay botones para la siguiente pagina   
    Contador_ciclo = 0
    if bs.find_all('ul',{'class','pagination m-0 float-right'}):
        for i in range(2,num_results//results_per_page+1):
            """
            recorré todas las páginas de resultados desde la 2da si es que 
            hay más paginas que recorrer      
            """
            assert Contador_ciclo < 200, '200 iteraciones en el ciclo'

            try:
                bs = get_page_safe_dynamic('https://www.chiletrabajos.cl/encuentra-un-empleo/'\
                                  +str(i*results_per_page)\
                                  +'?action=search&order_by=&ord=&within=25&2='\
                                  +str(search_keyword)+'&filterSearch=Buscar')
            except:
                continue   

            Contador_ciclo += 1
            assert len(bs.find_all('div',{'class','job-item with-thumb destacado no-hover'})) != 0    
            #extraigo las ofertas
            results += [tag.a['href'] for tag in\
                        bs.find_all('div',{'class','job-item with-thumb destacado no-hover'})]
            results_dates += [ tag.i.nextSibling.split('de')[0].strip().lstrip('0')\
                     +'/'+ meses_dict[tag.i.nextSibling.split('de')[1].strip()]\
                     +'/'+ tag.i.nextSibling.split('de')[2].strip()\
                     for tag in bs.find_all('div',{'class','job-item with-thumb destacado no-hover'})]  
    
    # fecha de la última vez que se ejecuto el main_scraper con este item
    try: 
        resume_date = load_date('chiletrabajos', search_keyword)
    except:
        resume_date = get_date('hace 999 dias')
    # registro donde hubo errores
    retry_links = []              
    retry_links_dates = []
    n = 0
    # raspado
    
    for index, result_url in enumerate(results):
        time.sleep(np.random.uniform(-0.05,00.5)**2)
        date = results_dates[index]
        try:
            url = result_url
            # reviso si es una nueva oferta para seguir o no
            if not is_newer_date(date, resume_date) \
                or str(url) in load_url('chiletrabajos', resume_date, search_keyword):
                continue          
            # raspo la página
            scrape(url, search_keyword) 
            
            # recoleccion
            if str(date) == str(get_date('hoy')):
                data_row = ['chiletrabajos',\
                            date,\
                            search_keyword,\
                            url,
                            ]
                save_urls(data_row) 
            n+=1
        except:
            retry_links.append(result_url)
            retry_links_dates.append(date)
            continue
        

    # intento de nuevo con los que no funcionaron
    failed_links = []
    for index, link in enumerate(retry_links):
        time.sleep(np.random.uniform(-0.05,0.05)**2)
        date = retry_links_dates[index]
        try:
            url = link
            # reviso si es una nueva oferta para seguir o no
            if not is_newer_date(date, resume_date) \
                or str(url) in load_url('chiletrabajos', resume_date, search_keyword):
                continue  
            
            #raspado
            scrape(url, search_keyword)  
            
            # recoleccion
            if str(date) == str(get_date('hoy')):
                data_row = ['chiletrabajos',\
                            date,\
                            search_keyword,\
                            url,
                            ]
                save_urls(data_row) 
            failed_links.append(link)
            #failed_links_dates.remove(date)
            n += 1
        except:
            continue
        
    
    # guardo los links fallidos en otro csv
    for link in failed_links:
        csv_row=['chiletrabajos', search_keyword, link]
        save_to_failed_links_csv(csv_row)      

    informe_row = 'chiletrabajos: ' + str(n)+'/'+str(num_results) 
    try:
        return informe_row
    finally:
        gc.collect()

def scrape(url, search_keyword):
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

    # No tener try aqui es intencional    
    bs = get_page_dynamic(url)
    
    # título
    title = bs.find('h1').text
    
    # cuerpo
    body =  body_cleanser(bs.find_all('p',{'class','mb-0'})[1])

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
    etiquetas = ''.join(etiquetas)

    csv_row = [ str(search_keyword),\
                category.strip('\n'),\
                title.strip('\n'),\
                body.strip('\n'),\
                date,\
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
      
    save_to_csv(csv_row)
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