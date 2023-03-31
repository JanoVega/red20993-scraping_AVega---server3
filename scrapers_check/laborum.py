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

from utils.csv_utils import save_to_check_csv

# ubicacion del ejecutable para chromedriver
path = os.getcwd() + '/chromedriver'
#path = '/snap/bin/chromium.chromedriver'
service = Service(executable_path=path)

# nota: el sitio cambia los nombre de los tags aparentemente

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
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, 'icon-light-money'))) 
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
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, 'icon-light-bookmark')))
        WebDriverWait(driver, 0.5)
        time.sleep(0.1)
        html = driver.page_source
    except :
        time.sleep(3)
        driver.get(url)
        WebDriverWait(driver, 10)
        html = driver.page_source
    finally:
        driver.quit()
    return BeautifulSoup(html,'html.parser')

def results_check(search_keyword):
    if len(search_keyword.split())>1:
        words =  search_keyword.split()
        a = ''
        for i in range(len(words)-1):
            a += words[i]
            a += '-'
        a += words[-1]
        search_keyword = a
    
    bs = get_page_safe_dynamic('https://www.laborum.cl/empleos-busqueda-'\
                 +str(search_keyword)+'.html')    
    num_results = re.sub('[\D]', '', \
                 re.sub('[\W+]', '', bs.find('h1').span.text))
    assert num_results != '', 'No se encontraron resultados'
    num_results = int(num_results)
    assert num_results != 0, 'No se encontraron resultados'

    # lista de avisos
    for i, div in enumerate(bs.find_all('div')):
        try:
            if div.attrs['id'] == 'listado-avisos':
                index = i
        except:
            continue
    # filtro sólo los con titulo "h2"
    results = []
    listado_avisos = bs.find_all('div')[index]
    for aviso in listado_avisos:
        try :
            aviso.find('h2').text 
            # guardo links
            results.append(aviso.a['href']) 
        except :
            continue
    assert results!=[], 'no se pudo acceder a los resultados'
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
    # en caso de más de 1 palabra, se ajusta al formato de la página
    if len(search_keyword.split())>1:
        words =  search_keyword.split()
        a = ''
        for i in range(len(words)-1):
            a += words[i]
            a += '-'
        a += words[-1]
        search_keyword = a
    
    bs = get_page_safe_dynamic('https://www.laborum.cl/empleos-busqueda-'\
                 +str(search_keyword)+'.html')


    num_results = re.sub('[\D]', '', \
                     re.sub('[\W+]', '', bs.find('h1').span.text))
    assert num_results != '', 'No se encontraron resultados'
    num_results = int(num_results)
    assert num_results != 0, 'No se encontraron resultados'
    
    # lista de avisos
    for i, div in enumerate(bs.find_all('div')):
        try:
            if div.attrs['id'] == 'listado-avisos':
                index = i
        except:
            continue
    # filtro sólo los con titulo "h2"
    results = []
    listado_avisos = bs.find_all('div')[index]
    for aviso in listado_avisos:
        try :
            aviso.find('h2').text 
            # guardo links
            results.append(aviso.a['href']) 
        except :
            continue

    n = 0
    # raspado de resultados
    for index, result_url in enumerate(results):
        time.sleep(np.random.uniform(-0.05,0.05)**2)
        try:
            url = 'https://www.laborum.cl'+ result_url
            scrape(url, search_keyword,True)  
            n += 1
        except:
            print('no raspado')
            continue

    informe_row = 'laborum: ' + str(n)+'/'+str(len(results)) 
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

    try:    
        bs = get_page_dynamic(url)
    except:
        raise Exception()
    # título
    try:
        title = bs.find('h1').text
    except:
        print('error al extraer el título')
    
    try:
        # los nombres de las clases variaban, ahora navega el \
        # sitio para rescatar la informacion
        section_detalle = bs.find('div',id='section-detalle')
        
        table_section = [tag for tag in section_detalle.children][0] 
        body_section = [tag for tag in section_detalle.children][1]
        
        corpus = body_section.find('div').find('div')

        # cuerpo
        body =  body_cleanser(corpus)
        
        table = table_section.find('div').find('div').find('div')
        columns = [tag for tag in table.children]
        
        col1 = columns[0].find_all('li')
        col2 = columns[1].find_all('li')
        try:
            col3 = columns[2].find_all('li')  # podria usarse para recolectar las vacantes
        except:
            col3 = []
    except Exception as e:
        print(e)
        body = ''
   
    # ubicación
    location = col1[1].text
    
    # modalidad
    modalidad = col1[2].text

    # jornada    
    jornada = col2[1].text
    
    # categoria
    category = col2[0].text
    
    # inclusividad 
    try:
        inclusividad = 'si' if columns[2].find_all('a') else 'no'
    except:
        inclusividad = 'no'
    # salario
    try:
        salario = col3[0].text 
    except:
        salario = ''
    # publicador
    try:
        tag = bs.find('h1')
        publicador = tag.findNextSibling().text
    except:
        publicador = ''
    # extras
    try:
        etiquetas = ''.join([subtag.text for subtag in col3])
    except:
        etiquetas = ''
    try:
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
                    'laborum',
                    ]    
    except Exception as e:
        print(str(e))

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
