import time
import numpy as np
import re
import os
import gc

from bs4 import BeautifulSoup 
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By


from utils.date_utils import get_date
from utils.csv_utils import save_to_csv
from utils.csv_utils import save_to_failed_links_csv
from utils.date_utils import is_newer_date

# ubicacion del ejecutable para chromedriver
path = os.getcwd() + '\\chromedriver'
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
    #chrome_options.add_argument("--headless")
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    driver = webdriver.Chrome(service=service, options=chrome_options)        
    try:
        driver.get(url)
        time.sleep(2)
        html = driver.page_source
    except ConnectionError:
        time.sleep(3)
        driver.get(url)
        time.sleep(2)
        html = driver.page_source
    finally:   
        driver.close()
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
       # chrome_options.add_argument("--headless")
        driver = webdriver.Chrome(service=service, options=chrome_options)        
        driver.get(url)
        html = driver.page_source
    except: 
        print('error al buscar resultados con get_page_dynamic()')
    finally:
       driver.close()
    return BeautifulSoup(html,'html.parser')

def results(search_keyword, url_collector):
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
    url_collector.reset()
    
    url ='https://www.bne.cl/ofertas?mostrar=empleo&textoLibre='+search_keyword+'&numPaginaRecuperar=1'
    bs = get_page_safe_dynamic(url)
    
    num_results = bs.find('span', {'class', 'labelNumeroOfertas'}).text
    num_results = re.sub('[\D]', '', num_results ) # quita puntos de ej:1.000
    num_results = int(num_results)    
    
    assert num_results != 0, 'No se encontraron resultados'
    assert bs.find('h3').text != 'No se encontraron resultados para su búsqueda.',\
                                 'No se encontraron resultados para su búsqueda.'
    # extraígo los links a las publicaciones
    results = [tag.a['href'] for tag in bs.find_all('article') ] 
  
    # resto de páginas
    p = 1
    # chequea si hay botones para la siguiente pagina 
    while bs.find_all('a',{'class','paginador page-link page-item-ant-sig'})[-1]\
                    .text == 'Siguiente >' :   
        """
        recorré todas las páginas de resultados desde la 2da si
        es que hay más paginas que recorrer      
        """
        p += 1
        time.sleep(np.random.uniform(-2,2)**2)
        
        try:
            url = 'https://www.bne.cl/ofertas?mostrar=empleo&textoLibre='\
                +search_keyword+'&numPaginaRecuperar='+str(p)
            bs = get_page_safe_dynamic(url)
        except:
            continue   

        assert len(bs.find_all('article')) != 0    
        results += [ tag.a['href'] for tag in bs.find_all('article')]  

    # registro donde hubo errores
    failed_links = []        
    n = 0
    # raspado
    for result_url in results:
        time.sleep(np.random.uniform(-1,1)**2)
        try:
            url = 'https://www.bne.cl'\
                    +result_url
            scrape(url, search_keyword, url_collector)  # raspo la página
            n+=1
        except:
            failed_links.append('https://www.bne.cl'\
                    +result_url)
            continue
   
    # intento de nuevo con los que no funcionaron
    for link in failed_links:
        time.sleep(np.random.uniform(-0.5,0.5)**2)
        try:
            url = link
            scrape(url, search_keyword, url_collector)  
            failed_links.remove(link)
            n += 1
        except:
            continue
    
    # guardo los links fallidos en otro csv
    for link in failed_links:
        csv_row=['bne', search_keyword, link]
        save_to_failed_links_csv(csv_row) 
    
    # guardo los links del día
    url_collector.end_collect('bne', search_keyword) 

    informe_row = 'bne: ' + str(n)+'/'+str(num_results) 
    try:
        return informe_row
    finally:
        gc.collect

def scrape(url,search_keyword, url_collector):
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
    try: 
       resume_date = np.load(os.getcwd() \
        +'/crawler_search_dates/'+search_keyword+'_resume_date.npy')[0]
    except:
        resume_date = get_date('hace 999 dias')

    bs = get_page_dynamic(url)
    
    # título
    title = bs.find('h1').find('span').find('span').text
    title = re.sub('[\s]', ' ', title).strip()

    # cuerpo
    body = body_cleanser(bs.find_all('article',\
             {'class', 'panel panel-default panelFormulario'})[1].find('p'))
    requisitos = bs.find_all('article', {'class',\
                 'panel panel-default panelFormulario'})[2].text
    body += re.sub('[\s]', ' ',requisitos).strip()


    # fecha
    date = bs.find_all('article', {'class', 'panel panel-default panelFormulario'})[1]\
        .find_all('span')[1].text.split('/')
    date = date[0].lstrip('0')+'/'\
            +date[1].lstrip('0')+'/'\
            +date[2]

    # categoría
    category = bs.find('h1').find('span').find('small').text

    # modalidad
    modalidad = ''
    
    # inclusividad
    inclusividad = 'si' if bs.find_all('div', {'class', 'botonVerModalDiscapacidad'}) else 'no'
    
    # ubicación
    try:
        location = bs.find_all('article', {'class', 'panel panel-default panelFormulario'})[1]\
            .find_all('span')[0].text.strip()
    except:
        location = ''

    # jornada
    try:
        jornada = bs.find_all('article', {'class', 'panel panel-default panelFormulario'})[1]\
            .find_all('span')[4].text.strip()
    except:
        jornada = ''
    
    # salario
    salario = bs.find_all('article', {'class', 'panel panel-default panelFormulario'})[1]\
        .find_all('span')[3].text
    
    # publicador
    publicador = bs.find_all('article', {'class',\
             'panel panel-default panelFormulario'})[0].find_all('span')[1].text

    # extras
    etiquetas = bs.find_all('article', {'class',\
                'panel panel-default panelFormulario'})[3]\
                .find('div', {'class', 'panel-body'})\
                .find_all('div', {'class', 'col-sm-6'})
        
    etiquetas = [re.sub('[\s]', ' ', etiqueta.text).strip()+'; ' for etiqueta\
                 in etiquetas[:4]]
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
                'computrabajo',
                ]   

    # recoleccion
    if str(date) == str(get_date('hoy')):
        url_collector.collect_url(url)    
    # reviso si es una nueva oferta para seguir o no
    if not is_newer_date(date, resume_date) \
        or str(url) in url_collector.load_data('bne', search_keyword):
        return

    save_to_csv(csv_row)
    # despues de guardar la info se libera ram
    gc.collect


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