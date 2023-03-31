import requests
import time
import numpy as np
import re
import os
import gc

from bs4 import BeautifulSoup 
from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.relative_locator import locate_with
from selenium.webdriver.chrome.service import Service

from utils.date_utils import get_date
from utils.csv_utils import load_date, load_url, save_to_csv, save_urls
from utils.csv_utils import save_to_failed_links_csv
from utils.date_utils import is_newer_date

# ubicacion del ejecutable para chromedriver
path = os.getcwd() + '/chromedriver'
#path = '/snap/bin/chromium.chromedriver'
service = Service(executable_path=path)

def get_tricky_url(url,search_keyword):
    """
    Método para escribir search_keyword en la barra de busqueda, 
    hacer click para ingresar a la página con resultados y 
    extraer la url.

    Parameters
    ----------
    url : str
        dirección del sitio
    
    search_keyword : str
        Item para buscar en la página.

    Returns
    -------
    url : str
        dirección de los resultados
    """  
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    try:
        driver.get(url)
        WebDriverWait(driver, 2)
        text_input = driver.find_element(By.ID, "palabra")
        ActionChains(driver)\
            .send_keys_to_element(text_input, search_keyword )\
            .perform()
        botonn_locator=locate_with(By.TAG_NAME, "input").to_left_of({By.ID: "region"})
        boton   = driver.find_element(botonn_locator) 
        ActionChains(driver)\
            .click(boton)\
            .perform()
        url=driver.current_url
    finally:
        driver.quit()
    return url

def get_page_safe(url):
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
    try:
        req = requests.get(url)  
        return BeautifulSoup (req.text, 'html.parser')
    except ConnectionError:
        time.sleep(3)
        req = requests.get(url)  
        return BeautifulSoup (req.text, 'html.parser')      

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
    chrome_options.add_argument("--headless")
    driver = webdriver.Chrome(service=service, options=chrome_options)  
    try:      
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
    tricky_url = get_tricky_url('https://mundolaboral.elmercurio.com/home/'\
                              , search_keyword ) #puedo tenr exceptions
        
    bs = get_page_safe(tricky_url)

    assert not bs.find_all('h1',{'class','resultadoSinOFertasTitulo'}),\
        'No hay ofertas de empleo para tu búsqueda'

    #número de filas que debo extraer    
    num_results = re.sub('[\D]', '', \
                     bs.find('p', {'class','num_resultados'})\
                     .text.split()[0] )        
    num_results = int(num_results)  
    assert num_results != 0, 'No se encontraron resultados'

    # extraígo los links a las publicaciones
    results = [tag.a['href'] for tag in bs.find_all('div', {'class', 'md2_oferta'}) ]
    
    results_dates = [ tag.h3.text.split('/')[0].lstrip('0')\
                     +'/'+tag.h3.text.split('/')[1].lstrip('0')\
                     +'/'+tag.h3.text.split('/')[2]
                     for tag in bs.find_all('div', {'class', 'md2_oferta'})]
        
    # resto de páginas
    p = 1
    # chequea si hay botones para la siguiente pagina 
    Contador_ciclo = 0
    while bs.find_all('a', {'class', 'botonActivado'}):   
        p += 1    
        """
        recorré todas las páginas de resultados desde la 2da si es que
        hay más paginas que recorrer      
        """
        assert Contador_ciclo < 20, '20 iteraciones en el ciclo'
        try:
            url = tricky_url+'/'+str(p)
            bs = get_page_safe(url)
            # se expande la lista con links
            results += [ tag.a['href'] for tag in bs.find_all('div' ,{'class', 'md2_oferta'})] 
            results_dates += [ tag.h3.text.split('/')[0].lstrip('0')\
                     +'/'+tag.h3.text.split('/')[1].lstrip('0')\
                     +'/'+tag.h3.text.split('/')[2]
                     for tag in bs.find_all('div', {'class', 'md2_oferta'})]
        except:
            continue   
        assert len(results) != 0  
        Contador_ciclo += 1
    # fecha de la última vez que se ejecuto el main_scraper con este item
    try: 
       resume_date = load_date('elmercurio', search_keyword)
    except:
        resume_date = get_date('hace 999 dias')

    # registro donde hubo errores
    retry_links = [] 
    retry_links_dates = []
    n = 0
    # raspado
    for index, result_url in enumerate(results):
        time.sleep(np.random.uniform(-0.05,0.05)**2)
        date = results_dates[index]
        try:
            url = result_url
            
            # reviso si es una nueva oferta para seguir o no
            if not is_newer_date(date, resume_date) \
                or str(url) in load_url('elmercurio', resume_date, search_keyword):
                continue
            # raspo la página
            scrape(url, search_keyword)  
            
            # recoleccion
            if str(date) == str(get_date('hoy')):
                data_row = ['elmercurio',\
                            date,\
                            search_keyword,\
                            url,
                            ]
                save_urls(data_row)             
            
            n += 1
        except:
            retry_links.append(result_url)
            retry_links_dates.append(date)
            continue
    failed_links = []
    for index, link in enumerate(retry_links):
        time.sleep(np.random.uniform(-0.05,0.05)**2)
        date = retry_links_dates[index]
        try:
            url = link
            # reviso si es una nueva oferta para seguir o no
            if not is_newer_date(date, resume_date) \
                or str(url) in load_url('elmercurio', resume_date, search_keyword):
                continue
            # raspo la página
            scrape(url, search_keyword)
            
            # recoleccion
            if str(date) == str(get_date('hoy')):
                data_row = ['elmercurio',\
                            date,\
                            search_keyword,\
                            url,
                            ]
                save_urls(data_row)              
            
            failed_links.remove(link)  
            #failed_links_dates.remove(date)
            n += 1
        except:
            continue

    # guardo los links fallidos en otro csv
    for link in failed_links:
        csv_row=['elmercurio', search_keyword, link]
        save_to_failed_links_csv(csv_row) 

    informe_row = 'elmercurio: ' + str(n)+'/'+str(num_results) 
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
    body =  body_cleanser(bs.find_all('p',{'class','mb-0'})[0])\
             +  body_cleanser(bs.find('h2'))\
             +  body_cleanser(bs.find_all('p',{'class','mb-0'})[1])
    
    # fecha
    date = get_date(bs.find('div', {'class', 'col-md-12 mb-1 mb-md-0'}).text)
    
    spans = bs.find_all('span', {'class', \
        'badge badge-personalizado p-2 me-2 mb-2 fLight text-wrap text-start'})
    
    # ubicación
    location = spans[2].text.strip()+', '+spans[3].text.strip()
    
    # categoría
    category = spans[1].text.strip()
    
    # modalidad
    modalidad = ''
    
    # jornada
    jornada = spans[0].text.strip()

    # inclusividad
    inclusividad = ''
    
    # salario
    salario = ''
    
    # publicador
    try:
        publicador = bs.find('div', {'class', 'col-md-12 mb-1 mb-md-0'}).find('span').text
    except:
        publicador = ''
    # extras

    try:
        etiquetas = [span.text + '; ' for span in spans]
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
                'elmercurio',
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