"""
Version para realizar chequeo en el cambio de la pagina,

se el quita el ciclo entre las paginas
"""


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

from utils.csv_utils import save_to_check_csv

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
    except Exception as e: 
        print(e)
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

def results_check(_):
    assert 0!=0, 'no se checkea elmercurio'

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
           
    # fecha de la última vez que se ejecuto el main_scraper con este item


    n = 0
    # raspado
    for index, result_url in enumerate(results):
        time.sleep(np.random.uniform(-0.05,0.05)**2)
        try:
            url = result_url
            # raspo la página
            scrape(url, search_keyword, True)
            n += 1
        except:
            continue



    informe_row = 'elmercurio: ' + str(n)+'/'+str(len(results)) 
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
        body =  body_cleanser(bs.find_all('p',{'class','mb-0'})[0])\
             +  body_cleanser(bs.find('h2'))\
             +  body_cleanser(bs.find_all('p',{'class','mb-0'})[1])
    except:
        body = ''
    
    spans = bs.find_all('span', {'class', \
        'badge badge-personalizado p-2 me-2 mb-2 fLight text-wrap text-start'})
    
    # ubicación
    try:
        location = spans[2].text.strip()+', '+spans[3].text.strip()
    except:
        location = ''
    # categoría
    try:
        category = spans[1].text.strip()
    except:
        category = ''
    # modalidad
    modalidad = ''
    
    # jornada
    try:
        jornada = spans[0].text.strip()
    except:
        jornada = ''
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
                'elmercurio',
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