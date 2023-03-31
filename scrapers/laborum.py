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

from utils.date_utils import get_date
from utils.csv_utils import load_date, load_url, save_to_csv, save_urls
from utils.csv_utils import save_to_failed_links_csv
from utils.date_utils import is_newer_date

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
    results_dates = []
    listado_avisos = bs.find_all('div')[index]
    for aviso in listado_avisos:
        try :
            aviso.find('h2').text 
            # guardo links
            results.append(aviso.a['href']) 
            results_dates.append( get_date(aviso.find_all('h3')[1].text) )
        except :
            continue

    # variable auxiliar para cambiar páginas
    p = 1
    # resto de páginas
    new_results = ['','']
    Contador_ciclo = 0
    while len(new_results) != 0:
        p += 1 
        """
        recorré todas las páginas de resultados desde la 2da si es que hay más paginas que recorrer      
        """
        # lista para que funcione correctamente el while
        new_results = []
        assert Contador_ciclo < 200, '200 iteraciones en el ciclo' 
        try:
            bs = get_page_safe_dynamic('https://www.laborum.cl/empleos-busqueda-'\
                 + str(search_keyword) + '.html?page='+str(p))
        except:
            continue
        Contador_ciclo += 1
        # lista de avisos
        for i, div in enumerate(bs.find_all('div')):
            try:
                if div.attrs['id'] == 'listado-avisos':
                    index = i
            except:
                continue
        # filtro sólo los con titulo "h2"
        listado_avisos = bs.find_all('div')[index]
        for aviso in listado_avisos:
            try:
                aviso.find('h2').text 
                # guardo links
                results.append(aviso.a['href'])
                results_dates.append( get_date(aviso.find_all('h3')[1].text) )
                # para comprobar si siguen habiendo resultados
                new_results.append(1) 
            except:
                continue
            
    # fecha de la última vez que se ejecuto el main_scraper con este item
    try: 
       resume_date = load_date('laborum', search_keyword)
    except:
        resume_date = get_date('hace 999 dias')

    # registro donde hubo errores
    retry_links = []
    retry_links_dates = []
    n = 0
    # raspado de resultados
    for index, result_url in enumerate(results):
        time.sleep(np.random.uniform(-0.05,0.05)**2)
        date = results_dates[index]
        try:
            url = 'https://www.laborum.cl'+ result_url
            
            # reviso si es una nueva oferta para seguir o no
            if not is_newer_date(date, resume_date) \
                or str(url) in load_url('laborum', resume_date, search_keyword):
                continue   
    
            scrape(url, search_keyword)  
            
            # recoleccion
            if str(date) == str(get_date('hoy')):
                data_row = ['laborum',\
                            date,\
                            search_keyword,\
                            url,
                            ]
                save_urls(data_row) 
            
            n += 1
        except:
            retry_links.append('https://www.laborum.cl'+ result_url )
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
                or str(url) in load_url('laborum', resume_date, search_keyword):
                continue               
            #raspado
            scrape(url, search_keyword)
            # recoleccion
            if str(date) == str(get_date('hoy')):
                data_row = ['laborum',\
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
        csv_row=['laborum', search_keyword, link]
        save_to_failed_links_csv(csv_row) 

    informe_row = 'laborum: ' + str(n)+'/'+str(num_results) 
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
    
    # fecha
    date = get_date(col1[0].text)

    # ubicación
    location = col1[1].text
    
    # modalidad
    modalidad = col1[2].text

    # jornada    
    jornada = col2[1].text
    
    # categoria
    category = col2[0].text
    
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
        etiquetas = [subtag.text for subtag in col3]
    except:
        etiquetas = ''

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
                'laborum',
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
