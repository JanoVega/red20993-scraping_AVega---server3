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

from utils.date_utils import get_date
from utils.csv_utils import load_date, load_url, save_to_csv, save_urls
from utils.csv_utils import save_to_failed_links_csv
from utils.date_utils import is_newer_date


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
    results_dates = [get_date( tag.find_all('span')[1].text)\
                     for tag in bs.find_all('article',{'class','job clicky'})]
    # resto de páginas
    # variable auxiliar para avanzar la página
    p = 1
    # chequea si hay botones para la siguiente página 
    Contador_ciclo = 0
    boton_sgt_pgn = bs.find_all('a',{'class','btn btn-r btn-primary-inverted'})
    while boton_sgt_pgn:   
        # para esta página, p tiene un valor máximo de 100,
        # 20 resultados por página
        p += 1
        assert Contador_ciclo < 200, '200 iteraciones en el ciclo'
        """
        recorré todas las páginas de resultados desde la 2da si es que hay más paginas que recorrer      
        """
        try:
            bs =get_page_safe_dynamic('https://www.opcionempleo.cl/empleo-'\
                 +str(search_keyword)+'.html?radius=0&p='+str(p))
        except:
            continue   
        Contador_ciclo += 1
        assert len(bs.find_all('article',{'class','job clicky'})) != 0 
        # se expande la lista con links
        results += [ tag.a['href'] for tag in bs.find_all('article',{'class','job clicky'})]    
        results_dates += [get_date( tag.find_all('span')[1].text)\
                     for tag in bs.find_all('article',{'class','job clicky'})]
                     
        boton_sgt_pgn = bs.find_all('a',{'class','btn btn-r btn-primary-inverted'})
            
    # fecha de la última vez que se ejecuto el main_scraper con este item
    try: 
       resume_date = load_date('opcionempleo', search_keyword)
    except:
        resume_date = get_date('hace 999 dias')
        
    # registro donde hubo errores
    retry_links = []  
    retry_links_dates = []         
    # contador para imprimir por pantalla
    n = 0    

    # se raspan las urls
    for index, result_url in enumerate(results):
        time.sleep(np.random.uniform(-0.05,0.05)**2)
        date = results_dates[index]
        try:
            url ='https://www.opcionempleo.cl'+result_url
            # reviso si es una nueva oferta para seguir o no
            if not is_newer_date(date, resume_date) \
                or str(url) in load_url('opcionempleo', resume_date, search_keyword):
                continue       
            # raspo la página
            scrape(url, search_keyword) 
            
            # recoleccion
            if str(date) == str(get_date('hoy')):
                data_row = ['opcionempleo',\
                            date,\
                            search_keyword,\
                            url,
                            ]
                save_urls(data_row) 
            n += 1
        except:
            retry_links.append('https://www.opcionempleo.cl'+result_url)
            retry_links_dates.append(date)
            continue
        
    failed_links = []
    # intento de nuevo con los que no funcionaron
    for index, link in enumerate(retry_links):
        time.sleep(np.random.uniform(-0.05,0.05)**2)
        date = retry_links_dates[index]
        try:
            url = link
            # reviso si es una nueva oferta para seguir o no
            if not is_newer_date(date, resume_date) \
                or str(url) in load_url('opcionempleo', resume_date, search_keyword):
                continue 
            # raspo la página
            scrape(url, search_keyword) 
            # recoleccion de link si es de la última fecha de ejecucion
            if str(date) == str(get_date('hoy')):
                data_row = ['opcionempleo',\
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
        csv_row=['opcionempleo', search_keyword, link]
        save_to_failed_links_csv(csv_row) 

    informe_row = 'opcionempleo: ' + str(n)+'/'+str(num_results) 
    
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
    bs = get_page_dynamic(url)
    
    # título
    title = bs.find('h1').text
    
    # cuerpo
    body =  body_cleanser(bs.find('section',{'class','content'}))

    # fecha    
    date = get_date(bs.find('span', {'class', 'badge badge-r badge-s'}).text) 
    # posible cambio de nombre de la badge

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
        publicador = re.sub( '[\s]',' ',bs.find('p',{'class', 'company'}).strip())
    except:
        publicador = ''

    # extras
    try:
        etiquetas = [re.sub( '[\s]',' ',tag.text).strip()\
                     +'; ' for tag in bs.find('ul',{'class','details'})\
                         .find_all('li')]
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
                'opcionempleo',
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